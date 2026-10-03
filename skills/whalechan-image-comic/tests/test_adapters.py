from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


def load_module(name: str, filename: str):
    path = SKILL_ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTERS = {
    "openai": load_module("comic_openai", "generate-openai.py"),
    "nano-banana": load_module("comic_nano", "generate-nanobanana.py"),
    "seedream": load_module("comic_seedream", "generate-seedream.py"),
}
ADAPTER_FILES = {
    "openai": "generate-openai.py",
    "nano-banana": "generate-nanobanana.py",
    "seedream": "generate-seedream.py",
}


AUTO_SQUARE = {
    "format": "png",
    "aspect_ratio": "1:1",
    "resolution": {"mode": "auto", "recommended": "1024x1024"},
}


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.references = [
            str(SKILL_ROOT / "assets/character-references/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp"),
        ]

    def request(self, directory: str, references: list[str]) -> Path:
        path = Path(directory) / "request.json"
        path.write_text(json.dumps({
            "prompt": "test",
            "output": AUTO_SQUARE,
            "references": [
                {"id": f"reference-{index}", "path": reference, "roles": ["identity"]}
                for index, reference in enumerate(references, 1)
            ],
        }), encoding="utf-8")
        return path

    def test_accepts_role_scoped_references_and_checks_hash(self) -> None:
        reference = Path(self.references[0])
        digest = hashlib.sha256(reference.read_bytes()).hexdigest()
        for name, module in ADAPTERS.items():
            with self.subTest(adapter=name), tempfile.TemporaryDirectory() as directory:
                request = Path(directory) / "request.json"
                request.write_text(json.dumps({
                    "prompt": "test",
                    "output": AUTO_SQUARE,
                    "references": [{
                        "id": "canonical-identity",
                        "path": str(reference),
                        "roles": ["identity"],
                        "instruction": "identity only",
                        "sha256": digest,
                    }],
                }), encoding="utf-8")
                value = module.load_request(request)
                self.assertEqual(value["reference_paths"], [reference])
                self.assertEqual(value["references"][0]["roles"], ["identity"])
                payload = json.loads(request.read_text(encoding="utf-8"))
                payload["references"][0]["sha256"] = "0" * 64
                request.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(module.AdapterError, "SHA-256"):
                    module.load_request(request)

    def dry_run(self, adapter: str, request: Path, output: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "python3",
                str(SKILL_ROOT / "scripts" / ADAPTER_FILES[adapter]),
                "--request",
                str(request),
                "--output",
                str(output),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )

    def test_provider_order_and_explicit_size_capability(self) -> None:
        state = {"attempts": [], "provider_errors": []}
        fixtures.manage.provider_allowed(state, "codex")
        with self.assertRaisesRegex(fixtures.manage.RunError, "first provider"):
            fixtures.manage.provider_allowed(state, "openai")
        state["provider_errors"].append({"provider": "codex", "category": "capability"})
        fixtures.manage.provider_allowed(state, "openai")
        with self.assertRaisesRegex(fixtures.manage.RunError, "skip"):
            fixtures.manage.provider_allowed(state, "nano-banana")
        explicit = {
            "format": "png",
            "aspect_ratio": "1:1",
            "resolution": {"mode": "explicit", "width": 1024, "height": 1024},
        }
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as directory:
                request = self.request(directory, self.references)
                payload = json.loads(request.read_text(encoding="utf-8"))
                payload["output"] = explicit
                request.write_text(json.dumps(payload), encoding="utf-8")
                completed = self.dry_run(adapter, request, Path(directory) / "output.png")
                if adapter == "nano-banana":
                    self.assertEqual(completed.returncode, 2)
                    error = json.loads(completed.stderr)
                    self.assertEqual(error["category"], "capability")
                else:
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertEqual(json.loads(completed.stdout)["size"], "1024x1024")

        # The Codex adapter: precise auth markers and a three-state usable verdict.
        codex = load_module("comic_codex", "generate-codex.py")
        self.assertEqual(codex.classify_text("Error: not logged in to Codex"), "authentication")
        self.assertEqual(codex.classify_text("HTTP 401 Unauthorized"), "authentication")
        self.assertEqual(codex.classify_text("upstream failed while rendering the login page"), "service")
        self.assertEqual(codex.classify_text("usage limit reached"), "quota")
        self.assertIs(codex.usable_verdict(True, 2, 2), True)
        self.assertIs(codex.usable_verdict(None, 2, 2), None)
        self.assertIs(codex.usable_verdict(True, None, 2), None)
        self.assertIs(codex.usable_verdict(False, None, 2), False)
        self.assertIs(codex.usable_verdict(True, 1, 2), False)


if __name__ == "__main__":
    unittest.main()
