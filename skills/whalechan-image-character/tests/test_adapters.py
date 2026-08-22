from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, filename: str):
    path = SKILL_ROOT / "scripts" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTERS = {
    "openai": load_module("whalechan_openai", "generate-openai.py"),
    "nano-banana": load_module("whalechan_nano_banana", "generate-nanobanana.py"),
    "seedream": load_module("whalechan_seedream", "generate-seedream.py"),
}


class AdapterReferenceCountTests(unittest.TestCase):
    def write_request(self, directory: str, value: dict) -> Path:
        path = Path(directory) / "request.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def reference_paths(self) -> list[str]:
        return [
            str(SKILL_ROOT / "assets/reference-images/standard/01_gentle_wave.webp"),
            str(SKILL_ROOT / "assets/reference-images/standard/03_light_turning_step.webp"),
            str(SKILL_ROOT / "assets/reference-images/standard/05_side_reclining_pose.webp"),
        ]

    def request(self, references: list[dict], **changes) -> dict:
        value = {
            "prompt": "test",
            "references": references,
            "aspect_ratio": "1:1",
            "resolution": {"mode": "provider-native", "width": None, "height": None},
            "output": {"format": "png", "alpha": False},
        }
        value.update(changes)
        return value

    def test_rejects_zero_references(self) -> None:
        valid_reference = {"path": self.reference_paths()[0], "roles": ["identity"]}
        for name, module in ADAPTERS.items():
            with self.subTest(adapter=name):
                with tempfile.TemporaryDirectory() as directory:
                    request = self.write_request(directory, self.request([]))
                    with self.assertRaisesRegex(module.AdapterError, "at least 1 reference"):
                        module.load_request(request)
            for missing in ("output", "aspect_ratio", "resolution"):
                with self.subTest(adapter=name, missing=missing):
                    with tempfile.TemporaryDirectory() as directory:
                        value = self.request([valid_reference])
                        del value[missing]
                        request = self.write_request(directory, value)
                        with self.assertRaises(module.AdapterError):
                            module.load_request(request)
            with self.subTest(adapter=name, missing="output.alpha"):
                with tempfile.TemporaryDirectory() as directory:
                    value = self.request([valid_reference], output={"format": "png"})
                    request = self.write_request(directory, value)
                    with self.assertRaises(module.AdapterError):
                        module.load_request(request)

    def test_validates_typed_reference_fields(self) -> None:
        primary = self.reference_paths()[0]
        invalid_references = [
            [{"path": primary}],
            [{"roles": ["identity"]}],
            [{"path": primary, "roles": "identity"}],
            [{"path": primary, "instruction": 3}],
            [{"path": primary, "roles": ["unknown"]}],
            [{"path": primary, "roles": ["style", "style"]}],
            [{"path": primary, "roles": ["identity"], "sha256": "0" * 64}],
        ]
        for name, module in ADAPTERS.items():
            for references in invalid_references:
                with self.subTest(adapter=name, references=references):
                    with tempfile.TemporaryDirectory() as directory:
                        request = self.write_request(
                            directory,
                            self.request(references),
                        )
                    with self.assertRaises(module.AdapterError):
                        module.load_request(request)

    def test_rejects_legacy_size_field(self) -> None:
        primary = self.reference_paths()[0]
        for name, module in ADAPTERS.items():
            with self.subTest(adapter=name):
                with tempfile.TemporaryDirectory() as directory:
                    value = self.request([{"path": primary, "roles": ["identity"]}])
                    value["size"] = "1024x1024"
                    request = self.write_request(directory, value)
                    with self.assertRaisesRegex(module.AdapterError, "unsupported fields"):
                        module.load_request(request)

    def test_alpha_dry_run_routes_only_to_verified_native_adapter(self) -> None:
        references = [
            {"path": path, "roles": [role]}
            for path, role in zip(self.reference_paths(), ["identity", "style", "pose_action"])
        ]
        scripts = {
            "openai": "generate-openai.py",
            "nano-banana": "generate-nanobanana.py",
            "seedream": "generate-seedream.py",
        }
        for name, filename in scripts.items():
            with self.subTest(adapter=name):
                with tempfile.TemporaryDirectory() as directory:
                    request = self.write_request(
                        directory,
                        self.request(
                            references,
                            output={"format": "png", "alpha": True},
                        ),
                    )
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(SKILL_ROOT / "scripts" / filename),
                            "--request",
                            str(request),
                            "--output",
                            str(Path(directory) / "candidate.png"),
                            "--dry-run",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if name == "openai":
                        self.assertEqual(result.returncode, 0)
                        summary = json.loads(result.stdout)
                        self.assertEqual(summary["reference_count"], 3)
                        self.assertEqual(
                            summary["reference_roles"],
                            [["identity"], ["style"], ["pose_action"]],
                        )
                        self.assertTrue(summary["output_alpha"])
                        self.assertEqual(summary["transparency_handling"], "native")
                    else:
                        self.assertEqual(result.returncode, 2)
                        error = json.loads(result.stderr)
                        self.assertEqual(error["category"], "capability")

    def test_openai_rejects_exact_resolution_that_conflicts_with_aspect_ratio(self) -> None:
        primary = self.reference_paths()[0]
        with tempfile.TemporaryDirectory() as directory:
            request = self.write_request(
                directory,
                self.request(
                    [{"path": primary, "roles": ["identity"]}],
                    aspect_ratio="1:1",
                    resolution={"mode": "exact", "width": 1024, "height": 1792},
                ),
            )
            with self.assertRaisesRegex(ADAPTERS["openai"].AdapterError, "does not match"):
                ADAPTERS["openai"].load_request(request)

    def test_openai_accepts_flexible_gpt_image_2_size(self) -> None:
        primary = self.reference_paths()[0]
        with tempfile.TemporaryDirectory() as directory:
            request = self.write_request(
                directory,
                self.request(
                    [{"path": primary, "roles": ["identity"]}],
                    aspect_ratio="3:2",
                    resolution={"mode": "exact", "width": 1536, "height": 1024},
                ),
            )
            value = ADAPTERS["openai"].load_request(request)
            self.assertEqual(value["aspect_ratio"], "3:2")
            self.assertEqual(value["size"], "1536x1024")

    def test_provider_native_resolution_uses_each_provider_capability(self) -> None:
        primary = self.reference_paths()[0]
        cases = (
            ("openai", "1:1", "1024x1024"),
            ("nano-banana", "1:1", None),
            ("seedream", "9:16", "1024x1792"),
        )
        for name, aspect_ratio, expected_size in cases:
            with self.subTest(adapter=name):
                with tempfile.TemporaryDirectory() as directory:
                    request = self.write_request(
                        directory,
                        self.request(
                            [{"path": primary, "roles": ["identity"]}],
                            aspect_ratio=aspect_ratio,
                        ),
                    )
                    value = ADAPTERS[name].load_request(request)
                    self.assertEqual(value["resolution"]["mode"], "provider-native")
                    if expected_size is not None:
                        self.assertEqual(value["size"], expected_size)

    def test_nano_banana_rejects_exact_resolution(self) -> None:
        primary = self.reference_paths()[0]
        with tempfile.TemporaryDirectory() as directory:
            request = self.write_request(
                directory,
                self.request(
                    [{"path": primary, "roles": ["identity"]}],
                    resolution={"mode": "exact", "width": 1024, "height": 1024},
                ),
            )
            with self.assertRaisesRegex(
                ADAPTERS["nano-banana"].AdapterError,
                "cannot guarantee an exact",
            ):
                ADAPTERS["nano-banana"].load_request(request)

    def test_seedream_exact_resolution_must_match_native_size(self) -> None:
        primary = self.reference_paths()[0]
        with tempfile.TemporaryDirectory() as directory:
            request = self.write_request(
                directory,
                self.request(
                    [{"path": primary, "roles": ["identity"]}],
                    resolution={"mode": "exact", "width": 1536, "height": 1536},
                ),
            )
            with self.assertRaisesRegex(
                ADAPTERS["seedream"].AdapterError,
                "must match its verified native size",
            ):
                ADAPTERS["seedream"].load_request(request)

    def test_openai_rejects_sizes_outside_gpt_image_2_constraints(self) -> None:
        primary = self.reference_paths()[0]
        cases = (
            ("125:128", 1000, 1024),
            ("4:1", 2048, 512),
            ("1:1", 512, 512),
            ("1:1", 3008, 3008),
        )
        for aspect_ratio, width, height in cases:
            with self.subTest(aspect_ratio=aspect_ratio, width=width, height=height):
                with tempfile.TemporaryDirectory() as directory:
                    request = self.write_request(
                        directory,
                        self.request(
                            [{"path": primary, "roles": ["identity"]}],
                            aspect_ratio=aspect_ratio,
                            resolution={"mode": "exact", "width": width, "height": height},
                        ),
                    )
                    with self.assertRaisesRegex(
                        ADAPTERS["openai"].AdapterError,
                        "gpt-image-2 size constraints",
                    ):
                        ADAPTERS["openai"].load_request(request)

    def test_reference_mime_uses_bytes_not_filename(self) -> None:
        source = Path(self.reference_paths()[0])
        with tempfile.TemporaryDirectory() as directory:
            mislabeled = Path(directory) / "reference.png"
            mislabeled.write_bytes(source.read_bytes())
            for name, module in ADAPTERS.items():
                with self.subTest(adapter=name):
                    self.assertEqual(module.mime(mislabeled), "image/webp")

if __name__ == "__main__":
    unittest.main()
