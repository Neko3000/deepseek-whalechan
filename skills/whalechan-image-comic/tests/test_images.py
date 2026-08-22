from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "validate-image.py"
SPEC = importlib.util.spec_from_file_location("comic_validate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)


class ImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.magick = shutil.which("magick")
        if self.magick is None:
            self.skipTest("ImageMagick is required")

    def test_auto_square_accepts_any_square_size_and_rejects_non_square(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recommended = root / "recommended.png"
            native = root / "native.png"
            bad = root / "bad.png"
            subprocess.run([self.magick, "-size", "1024x1024", "xc:rgb(245,234,221)", str(recommended)], check=True)
            subprocess.run([self.magick, "-size", "1254x1254", "xc:rgb(245,234,221)", str(native)], check=True)
            subprocess.run([self.magick, "-size", "1254x1024", "xc:rgb(245,234,221)", str(bad)], check=True)
            self.assertEqual(validate.validate(recommended)["overall"], "PASS")
            self.assertEqual(validate.validate(native)["overall"], "PASS")
            self.assertEqual(validate.validate(bad)["overall"], "FAIL")

    def test_explicit_resolution_requires_exact_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exact = root / "exact.png"
            native = root / "native.png"
            subprocess.run([self.magick, "-size", "1024x1024", "xc:rgb(245,234,221)", str(exact)], check=True)
            subprocess.run([self.magick, "-size", "1254x1254", "xc:rgb(245,234,221)", str(native)], check=True)
            output = {
                "format": "png",
                "aspect_ratio": "1:1",
                "resolution": {"mode": "explicit", "width": 1024, "height": 1024},
            }
            self.assertEqual(validate.validate(exact, output)["overall"], "PASS")
            self.assertEqual(validate.validate(native, output)["overall"], "FAIL")

    def test_auto_ratio_allows_one_pixel_rounding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "wide.png"
            subprocess.run([self.magick, "-size", "1365x768", "xc:rgb(245,234,221)", str(path)], check=True)
            output = {
                "format": "png",
                "aspect_ratio": "16:9",
                "resolution": {"mode": "auto", "recommended": None},
            }
            self.assertEqual(validate.validate(path, output)["overall"], "PASS")

    def test_composes_two_panels_to_native_square(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            second = root / "second.png"
            output = root / "comic.png"
            subprocess.run([self.magick, "-size", "1254x1254", "xc:red", str(first)], check=True)
            subprocess.run([self.magick, "-size", "600x800", "xc:blue", str(second)], check=True)
            completed = subprocess.run(
                ["python3", str(SKILL_ROOT / "scripts/compose-panels.py"), "--layout", "left-right", "--output", str(output), str(first), str(second)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(validate.validate(output)["overall"], "PASS")
            self.assertEqual(validate.inspect(output)["width"], 1254)
            self.assertEqual(validate.inspect(output)["height"], 1254)

    def test_composes_to_explicit_widescreen_dimensions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            second = root / "second.png"
            output = root / "comic.png"
            subprocess.run([self.magick, "-size", "800x600", "xc:red", str(first)], check=True)
            subprocess.run([self.magick, "-size", "600x800", "xc:blue", str(second)], check=True)
            completed = subprocess.run(
                [
                    "python3", str(SKILL_ROOT / "scripts/compose-panels.py"),
                    "--layout", "left-right", "--output", str(output),
                    "--resolution-mode", "explicit", "--width", "1920", "--height", "1080",
                    "--aspect-ratio", "16:9", str(first), str(second),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(validate.inspect(output)["width"], 1920)
            self.assertEqual(validate.inspect(output)["height"], 1080)


if __name__ == "__main__":
    unittest.main()
