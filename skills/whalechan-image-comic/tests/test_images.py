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

    def test_native_aspect_ratio_and_explicit_dimensions(self):
        automatic = {"format": "png", "aspect_ratio": "1:1",
                     "resolution": {"mode": "auto", "recommended": "1024x1024"}}
        explicit = {"format": "png", "aspect_ratio": "1:1",
                    "resolution": {"mode": "explicit", "width": 1024, "height": 1024}}
        with tempfile.TemporaryDirectory() as directory:
            for size, output, verdict in (("1254x1254", automatic, "PASS"),
                                          ("1254x1024", automatic, "FAIL"),
                                          ("1024x1024", explicit, "PASS"),
                                          ("1254x1254", explicit, "FAIL")):
                with self.subTest(size=size, mode=output["resolution"]["mode"]):
                    path = Path(directory) / "candidate.png"
                    subprocess.run([self.magick, "-size", size, "xc:rgb(245,234,221)", str(path)], check=True)
                    result = validate.validate(path, output)
                    self.assertEqual(result["overall"], verdict)


if __name__ == "__main__":
    unittest.main()
