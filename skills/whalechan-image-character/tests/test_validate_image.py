from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "validate-image.py"
SPEC = importlib.util.spec_from_file_location("whalechan_validate_image", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
validate_image = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_image)


class ImageValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.magick = shutil.which("magick")
        self.assertIsNotNone(self.magick)

    def create_image(self, path: Path, *arguments: str) -> None:
        subprocess.run(
            [self.magick, *arguments, str(path)],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_provider_native_accepts_non_1024_square(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native-square.png"
            self.create_image(
                path,
                "-size",
                "1536x1536",
                "xc:red",
                "-define",
                "png:color-type=2",
            )

            result = validate_image.validate(path)

            self.assertEqual(result["overall"], "PASS")
            self.assertEqual(result["metrics"]["resolution_mode"], "provider-native")
            self.assertEqual(result["metrics"]["width"], 1536)

    def test_provider_native_rejects_wrong_aspect_ratio(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wrong-ratio.png"
            self.create_image(
                path,
                "-size",
                "1536x1024",
                "xc:red",
                "-define",
                "png:color-type=2",
            )

            result = validate_image.validate(path)

            self.assertEqual(result["gates"]["T1"]["verdict"], "FAIL")

    def test_exact_resolution_rejects_other_square_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "other-square.png"
            self.create_image(
                path,
                "-size",
                "1536x1536",
                "xc:red",
                "-define",
                "png:color-type=2",
            )

            result = validate_image.validate(
                path,
                resolution_mode="exact",
                width=1024,
                height=1024,
            )

            self.assertEqual(result["gates"]["T1"]["verdict"], "FAIL")

    def test_transparent_rgba_passes_when_alpha_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "transparent.png"
            self.create_image(
                path,
                "-size",
                "1024x1024",
                "xc:none",
                "-fill",
                "red",
                "-draw",
                "rectangle 0,0 511,1023",
                "-define",
                "png:color-type=6",
            )

            result = validate_image.validate(path, alpha="required")

            self.assertEqual(result["overall"], "PASS")
            self.assertLess(result["metrics"]["alpha_minimum"], 1.0)

    def test_fully_opaque_rgba_fails_when_alpha_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "opaque-rgba.png"
            self.create_image(
                path,
                "-size",
                "1024x1024",
                "xc:red",
                "-define",
                "png:color-type=6",
            )

            result = validate_image.validate(path, alpha="required")

            self.assertEqual(result["overall"], "FAIL")
            self.assertEqual(result["gates"]["T2"]["verdict"], "FAIL")
            self.assertEqual(result["metrics"]["alpha_minimum"], 1.0)

    def test_rgb_fails_when_alpha_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rgb.png"
            self.create_image(
                path,
                "-size",
                "1024x1024",
                "xc:red",
                "-define",
                "png:color-type=2",
            )

            result = validate_image.validate(path, alpha="required")

            self.assertEqual(result["overall"], "FAIL")
            self.assertEqual(result["gates"]["T2"]["verdict"], "FAIL")
            self.assertIsNone(result["metrics"]["alpha_minimum"])

    def test_nearly_opaque_uniform_alpha_is_not_meaningful_transparency(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nearly-opaque.png"
            self.create_image(
                path,
                "-size",
                "1024x1024",
                "xc:rgba(255,0,0,0.988)",
                "-define",
                "png:color-type=6",
            )

            result = validate_image.validate(path, alpha="required")

            self.assertEqual(result["overall"], "FAIL")
            self.assertLess(result["metrics"]["alpha_minimum"], 1.0)
            self.assertEqual(result["metrics"]["transparent_fraction"], 0.0)


if __name__ == "__main__":
    unittest.main()
