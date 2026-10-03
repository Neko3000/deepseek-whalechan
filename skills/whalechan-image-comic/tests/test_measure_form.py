"""Keep numeric measurement distinct from visible-only proportion review."""
import copy
import importlib.util
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage
spec = importlib.util.spec_from_file_location("comic_measure_form", fixtures.SKILL_ROOT / "scripts/measure-form.py")
measure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(measure)


class ProportionMeasurementTests(unittest.TestCase):
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files

    def test_measured_and_visible_only_proportions_have_distinct_evidence(self):
        args = self.files(1, "PASS")
        path = Path(args.visual_json)
        qa = manage.read_json(path)
        candidate = Path(args.candidate)
        points = ([100, 0], [100, 100], [100, 160], [100, 220], [100, 280])
        overlay = candidate.with_name("measured.png")
        measure.render_overlay(candidate, overlay, *points)
        result = measure.build_result(candidate, "semi-chibi", overlay, *points)
        self.assertEqual(result["form_evidence"]["calculated_head_ratio"], 2.8)
        self.assertTrue(result["within_range"])
        qa["evidence"]["form_evidence"] = result["form_evidence"]
        manage.write_json(path, qa)
        digest = manage.sha256(candidate)
        self.assertEqual(manage.validate_qa(path, digest, image_spec=self.image_spec)["verdict"], "PASS")
        qa["evidence"]["form_evidence"]["calculated_head_ratio"] = 9.0
        manage.write_json(path, qa)
        with self.assertRaises(manage.RunError):
            manage.validate_qa(path, digest, image_spec=self.image_spec)
        qa["gates"]["H1"] = "NA"
        qa["evidence"]["form_evidence"] = {
            "mode": "visible-only", "candidate_sha256": digest,
            "reason": "The planned close-up excludes lower-body landmarks",
            "observed_cues": ["Rounded head and compact shoulders"],
        }
        manage.write_json(path, qa)
        with self.assertRaisesRegex(manage.RunError, "proportion_check"):
            manage.validate_qa(path, digest, image_spec=self.image_spec)
        closeup = copy.deepcopy(self.image_spec)
        closeup["proportion_check"] = "visible-only"
        self.assertEqual(manage.validate_qa(path, digest, image_spec=closeup)["verdict"], "PASS")
        qa["evidence"]["form_evidence"]["calculated_head_ratio"] = 2.8
        manage.write_json(path, qa)
        with self.assertRaisesRegex(manage.RunError, "must not claim"):
            manage.validate_qa(path, digest, image_spec=closeup)


if __name__ == "__main__":
    unittest.main()
