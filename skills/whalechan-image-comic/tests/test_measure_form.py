from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "measure-form.py"
SPEC = importlib.util.spec_from_file_location("comic_measure_form", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
measure = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure)


class ProportionMeasurementTests(unittest.TestCase):
    def test_custom_ratio_uses_frozen_target_without_proportion_reference(self) -> None:
        image = SKILL_ROOT / "assets/character-references/standard/01_gentle_wave.webp"
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory) / "overlay.png"
            measure.render_overlay(
                image,
                overlay,
                [100.0, 0.0],
                [100.0, 100.0],
                [100.0, 250.0],
                [100.0, 400.0],
                [100.0, 500.0],
            )
            result = measure.build_result(
                image,
                "standard",
                overlay,
                [100.0, 0.0],
                [100.0, 100.0],
                [100.0, 250.0],
                [100.0, 400.0],
                [100.0, 500.0],
                5.0,
                [4.85, 5.15],
            )
        evidence = result["form_evidence"]
        self.assertEqual(evidence["target_source"], "custom")
        self.assertEqual(evidence["calculated_head_ratio"], 5.0)
        self.assertTrue(result["within_range"])

    def test_rejects_ratio_at_or_below_one(self) -> None:
        catalog = measure.load_catalog()
        profile = catalog["character_forms"]["semi-chibi"]
        with self.assertRaisesRegex(measure.MeasurementError, "Invalid"):
            measure.resolve_target(profile, 1.0, [0.9, 1.1])


if __name__ == "__main__":
    unittest.main()
