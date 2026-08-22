from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "measure-form.py"
SPEC = importlib.util.spec_from_file_location("whalechan_measure_form", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
measure_form = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure_form)


class ProportionTargetTests(unittest.TestCase):
    def test_target_digest_matches_assignment_contract(self) -> None:
        digest = measure_form.target_sha256("custom", None, 5.0, [4.85, 5.15])
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, measure_form.target_sha256("custom", None, 5.0, [4.85, 5.15]))

    def test_rejects_partial_override(self) -> None:
        with self.assertRaisesRegex(measure_form.MeasurementError, "provided together"):
            measure_form.resolve_target(
                {"mean_head_ratio": 4.0, "acceptance_range": [3.85, 4.15]},
                5.0,
                None,
            )

    def test_rejects_ratio_at_or_below_one(self) -> None:
        for ratio in (0.5, 1.0):
            with self.subTest(ratio=ratio):
                with self.assertRaisesRegex(measure_form.MeasurementError, "Invalid confirmed"):
                    measure_form.resolve_target(
                        {"mean_head_ratio": 4.0, "acceptance_range": [3.85, 4.15]},
                        ratio,
                        [0.1, 1.1],
                    )


if __name__ == "__main__":
    unittest.main()
