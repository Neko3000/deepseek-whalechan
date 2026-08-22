from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
            str(SKILL_ROOT / "assets/character-references/semi-chibi/0015_data_still_in_brain_rendered_isolated.webp"),
            str(SKILL_ROOT / "assets/comic-references/0015_data_still_in_brain_rendered.webp"),
            str(SKILL_ROOT / "assets/text-style-templates/06_top-bottom-punchline/reference.webp"),
            str(SKILL_ROOT / "assets/supporting-character-references/abstract-user-pose-sheet.webp"),
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

    def test_accepts_one_to_five_references(self) -> None:
        for name, module in ADAPTERS.items():
            for count in range(1, 6):
                with self.subTest(adapter=name, count=count), tempfile.TemporaryDirectory() as directory:
                    value = module.load_request(self.request(directory, self.references[:count]))
                    self.assertEqual(len(value["reference_paths"]), count)

    def test_rejects_zero_or_six_references(self) -> None:
        values = self.references + [self.references[0]]
        for name, module in ADAPTERS.items():
            for references in ([], values):
                with self.subTest(adapter=name, count=len(references)), tempfile.TemporaryDirectory() as directory:
                    with self.assertRaisesRegex(module.AdapterError, "1 to 5"):
                        module.load_request(self.request(directory, references))

    def test_requires_structured_references(self) -> None:
        for name, module in ADAPTERS.items():
            with self.subTest(adapter=name), tempfile.TemporaryDirectory() as directory:
                request = Path(directory) / "request.json"
                request.write_text(json.dumps({
                    "prompt": "test",
                    "reference_images": [self.references[0]],
                }), encoding="utf-8")
                with self.assertRaisesRegex(module.AdapterError, "1 to 5"):
                    module.load_request(request)

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

    def test_auto_square_dry_runs_use_provider_native_settings(self) -> None:
        expected = {
            "openai": {"size": "1024x1024"},
            "nano-banana": {"aspect_ratio": "1:1", "image_size": "1K"},
            "seedream": {"size": "1024x1024"},
        }
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as directory:
                request = self.request(directory, self.references[:1])
                completed = self.dry_run(adapter, request, Path(directory) / "output.png")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                result = json.loads(completed.stdout)
                self.assertEqual(result["requested_output"], AUTO_SQUARE)
                for key, value in expected[adapter].items():
                    self.assertEqual(result[key], value)

    def test_explicit_square_is_exact_or_reports_capability(self) -> None:
        explicit = {
            "format": "png",
            "aspect_ratio": "1:1",
            "resolution": {"mode": "explicit", "width": 1024, "height": 1024},
        }
        for adapter in ADAPTERS:
            with self.subTest(adapter=adapter), tempfile.TemporaryDirectory() as directory:
                request = self.request(directory, self.references[:1])
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

    def test_rejects_legacy_top_level_size_fields(self) -> None:
        for name, module in ADAPTERS.items():
            with self.subTest(adapter=name), tempfile.TemporaryDirectory() as directory:
                request = self.request(directory, self.references[:1])
                payload = json.loads(request.read_text(encoding="utf-8"))
                del payload["output"]
                payload["size"] = "1024x1024"
                payload["aspect_ratio"] = "1:1"
                request.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaisesRegex(module.AdapterError, "request.output"):
                    module.load_request(request)


if __name__ == "__main__":
    unittest.main()
