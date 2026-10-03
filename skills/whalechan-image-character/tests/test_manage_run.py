"""Nine core run, QA and proportion contracts; no provider calls."""
import argparse
import copy
import importlib.util
import shutil
import unittest
from pathlib import Path

import helpers as fixtures

manage = fixtures.manage_run


class RunContractTests(fixtures.FixtureCase):
    def test_screenshot_inputs_are_archived_in_order(self):
        first = self.png("first.png", color="red")
        second = self.png("second.png", color="blue")
        value = self.assignment()
        value["input"] = {"type": "screenshot", "content": [first.name, second.name]}
        run = self.initialize(value)
        expected = [first.read_bytes(), second.read_bytes()]
        first.unlink()
        second.unlink()
        self.assertEqual([(run / "source" / f"original-{i:02d}.png").read_bytes()
                          for i in (1, 2)], expected)
        self.assertEqual(manage.read_json(run / "source/input.json"), value["input"])
        manage.load_run(str(run))

    def test_missing_screenshot_is_rejected_before_initializing(self):
        value = self.assignment()
        value["input"] = {"type": "screenshot", "content": ["missing.png"]}
        with self.assertRaisesRegex(manage.RunError, "existing source files"):
            self.initialize(value)
        self.assertFalse((self.root / "runs").exists())

    def test_candidate_budgets_require_approval_and_stop_retries(self):
        value = self.assignment()
        value["budget"]["run_candidates"] = 1
        with self.assertRaisesRegex(manage.RunError, "estimated maximum 8"):
            self.validate(value)
        value = self.assignment(count=4)
        value["budget"]["confirmed_over_24"] = False
        summary = manage.selection_summary(value, self.root / "assignment.json")
        self.assertIn("超过常规 24", manage.selection_markdown(summary))
        with self.assertRaisesRegex(manage.RunError, "confirmed_over_24"):
            self.validate(value)
        value["budget"]["confirmed_over_24"] = True
        self.validate(value)
        value = self.assignment()
        value["budget"].update(per_image_candidates=2, per_provider_candidates=1, run_candidates=2)
        fixtures.confirm_fixture(value)
        run = self.initialize(value)
        first = self.candidate(run, visual_pass=False)
        manage.cmd_record_candidate(first)
        with self.assertRaisesRegex(manage.RunError, "Per-provider candidate budget is exhausted"):
            manage.cmd_record_candidate(self.candidate(run, visual_pass=False))
        manage.cmd_record_candidate(self.candidate(run, provider="openai", visual_pass=False))
        with self.assertRaisesRegex(manage.RunError, "Per-image candidate budget is exhausted"):
            manage.cmd_record_candidate(self.candidate(run, provider="openai", visual_pass=False))
        self.assertEqual(manage.load_run(str(run))[2]["candidate_count"], 2)

    def test_promotion_requires_both_automatic_and_visual_pass(self):
        for failed in ("automatic", "visual"):
            with self.subTest(failed=failed):
                run = self.initialize()
                args = self.candidate(run, visual_pass=failed != "visual",
                                      size="64x32" if failed == "automatic" else "64x64")
                record = manage.cmd_record_candidate(args)
                self.assertEqual(record["verdict"], "FAIL")
                with self.assertRaisesRegex(manage.RunError, "Only one recorded PASS"):
                    manage.cmd_promote(argparse.Namespace(run_dir=str(run), image=args.image, attempt=1))
                self.assertEqual(list((run / "final").iterdir()), [])

    def test_safety_rejection_halts_the_whole_run(self):
        run = self.initialize(self.assignment(count=2))
        args = argparse.Namespace(run_dir=str(run), image="01_scene_0", provider="codex",
                                  model="synthetic", category="safety_rejection", details="blocked")
        manage.cmd_record_error(args)
        self.assertEqual(manage.load_run(str(run))[2]["status"], "safety_blocked")
        args.image = "02_scene_1"
        args.category = "service"
        with self.assertRaisesRegex(manage.RunError, "Run is not open"):
            manage.cmd_record_error(args)
        with self.assertRaisesRegex(manage.RunError, "Run is not open"):
            manage.cmd_record_candidate(self.candidate(run))

    def test_freezing_preserves_reference_identity_and_rejects_tampering(self):
        external = self.root / "pose.webp"
        shutil.copy2(self.primary("semi-chibi"), external)
        image = self.image("scene_0")
        image["references"].append({"id": "pose", "path": str(external),
                                    "roles": ["pose_action"], "instruction": "Pose only"})
        value = self.assignment([image])
        run = self.initialize(value)
        external.unlink()
        _, frozen, _ = manage.load_run(str(run))
        reference = frozen["scope"]["configurations"][0]["requirements"]["references"][1]
        self.assertTrue(Path(reference["path"]).is_relative_to(run))
        self.assertEqual(value["confirmation"]["summary_sha256"], frozen["confirmation"]["summary_sha256"])
        assignment_path = run / "assignment.json"
        original = assignment_path.read_bytes()
        changed = copy.deepcopy(frozen)
        changed["images"][0]["action"] = "tampered"
        manage.write_json(assignment_path, changed)
        with self.assertRaisesRegex(manage.RunError, "assignment SHA-256 mismatch"):
            manage.load_run(str(run))
        assignment_path.write_bytes(original)
        Path(reference["path"]).write_bytes(b"tampered")
        with self.assertRaisesRegex(manage.RunError, "Frozen reference SHA-256 mismatch"):
            manage.load_run(str(run))

    def test_automatic_qa_is_bound_to_candidate_and_fresh_inspection(self):
        run = self.initialize()
        args = self.candidate(run)
        automatic = manage.read_json(Path(args.automatic_json))
        image = manage.load_run(str(run))[1]["images"][0]
        candidate = Path(args.candidate)
        digest = manage.sha256(candidate)
        manage.validate_automatic_qa(automatic, image, candidate, digest)
        for field, expected in (("sha256", "does not match the candidate"),
                                ("alpha_policy", "alpha_policy must be forbidden"),
                                ("width", "does not match fresh candidate inspection")):
            changed = copy.deepcopy(automatic)
            if field == "sha256":
                changed[field] = "0" * 64
            else:
                changed["metrics"][field] = "required" if field == "alpha_policy" else 128
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, expected):
                manage.validate_automatic_qa(changed, image, candidate, digest)

    def test_approved_run_records_promotes_and_finalizes_actual_output(self):
        value = self.assignment()
        value["execution"].update(mode="parallel", requested_parallelism=3)
        fixtures.confirm_fixture(value)
        run = self.initialize(value, effective_parallelism=1)
        args = self.candidate(run)
        audit = self.root / "candidate.png.codex.json"
        manage.write_json(audit, {"provider": "codex", "transport": "cli", "usable": None,
                                  "output_sha256": manage.sha256(Path(args.candidate))})
        for transport, audit_path, message in ((None, None, "--transport cli or --transport builtin"),
                                               ("cli", None, "require --provider-audit"),
                                               ("builtin", str(audit), "no provider audit")):
            trial = argparse.Namespace(**{**vars(args), "transport": transport, "provider_audit": audit_path})
            with self.subTest(transport=transport), self.assertRaisesRegex(manage.RunError, message):
                manage.cmd_record_candidate(trial)
        args.transport, args.provider_audit = "cli", str(audit)
        manage.cmd_record_candidate(args)
        promoted = manage.cmd_promote(argparse.Namespace(run_dir=str(run), image=args.image, attempt=1))
        _, frozen, manifest = manage.load_run(str(run))
        self.assertEqual(manifest["execution"]["requested_parallelism"], 3)
        self.assertEqual(manifest["execution"]["effective_parallelism"], 1)
        attempt = manifest["images"][args.image]["attempts"][0]
        self.assertEqual(attempt["requested_output"], frozen["images"][0]["output"])
        self.assertIsNone(attempt["provider_output_request"]["size"])
        self.assertEqual((attempt["actual_output"]["width"], attempt["actual_output"]["height"]), (64, 64))
        self.assertEqual(promoted["output"], attempt["actual_output"])
        self.assertEqual(Path(promoted["final"]).read_bytes(), Path(args.candidate).read_bytes())
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(run), allow_failures=False))
        self.assertEqual((result["status"], result["passed"], result["total"]), ("complete", 1, 1))
        self.assertEqual(result["unverified_provider_audits"], [args.image])
        self.assertEqual(manage.load_run(str(run))[2]["images"][args.image]["attempts"][0]["transport"], "cli")

    def test_head_ratio_is_measured_and_checked_against_the_target(self):
        spec = importlib.util.spec_from_file_location("measure_form", fixtures.SKILL_ROOT / "scripts/measure-form.py")
        measurement = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(measurement)
        image = self.png("measure.png", size="64x64")
        overlay = self.root / "overlay.png"
        # Synthetic straight skeleton: 10-pixel head + 30-pixel body = 4 heads.
        points = ([30, 5], [30, 15], [30, 25], [30, 35], [30, 45])
        measurement.render_overlay(image, overlay, *points)
        measured = measurement.build_result(image, "standard", overlay, *points, 4.0, [3.85, 4.15])
        self.assertEqual(measured["form_evidence"]["calculated_head_ratio"], 4.0)
        self.assertTrue(measured["within_range"])
        target = fixtures.image_spec("standard")
        target["proportion"].update(mode="custom", preset=None, target_head_ratio=4.0,
                                    acceptance_range=[3.85, 4.15], proportion_reference=None)
        target["proportion_sha256"] = manage.target_sha256("custom", None, 4.0, [3.85, 4.15])
        visual = fixtures.visual_qa("standard", 4.0)
        visual["candidate_sha256"] = measured["candidate_sha256"]
        visual["form_evidence"].update(measured["form_evidence"])
        manage.validate_visual_qa(visual, target, expected_candidate_sha256=manage.sha256(image), overlay_root=self.root)
        wrong = copy.deepcopy(visual)
        wrong["form_evidence"]["calculated_head_ratio"] = 4.1
        with self.assertRaisesRegex(manage.RunError, "does not match the landmarks"):
            manage.validate_visual_qa(wrong, target)
        outside = measurement.build_result(image, "standard", overlay, *points[:-1], [30, 55], 4.0, [3.85, 4.15])
        self.assertFalse(outside["within_range"])
        visual["form_evidence"].update(outside["form_evidence"])
        with self.assertRaisesRegex(manage.RunError, "target head ratio must be between"):
            manage.validate_visual_qa(visual, target)

    def test_pairwise_qa_requires_bound_evidence_and_a_sufficient_gap(self):
        profile = fixtures.CATALOG["forms"]["chibi"]
        ratio = profile["mean_head_ratio"]
        target = fixtures.image_spec("chibi", "expanded")
        visual = fixtures.visual_qa("chibi", ratio)
        with self.assertRaisesRegex(manage.RunError, "requires pairwise_evidence"):
            manage.validate_visual_qa(visual, target, compact_pair=True)
        visual = fixtures.visual_qa("chibi", ratio, "expanded", "standard")
        expanded = visual["pairwise_evidence"]["expanded_form_head_ratio"]
        manage.validate_visual_qa(visual, target, counterpart_ratio=expanded, compact_pair=True)
        visual["pairwise_evidence"]["expanded_form_head_ratio"] = ratio + 0.01
        with self.assertRaisesRegex(manage.RunError, "gap of at least"):
            manage.validate_visual_qa(visual, target, counterpart_ratio=ratio + 0.01, compact_pair=True)
        target.pop("pairwise_minimum_head_ratio_gap")
        with self.assertRaisesRegex(manage.RunError, "requires frozen pairwise"):
            manage.validate_visual_qa(visual, target, compact_pair=True)

    def test_custom_visual_fields_keep_their_own_authority(self):
        image = self.image("custom", "standard")
        image["style"] = {"mode": "custom", "description": "watercolor"}
        image["costume"] = {"mode": "custom", "description": "white spacesuit"}
        image["background"] = {"mode": "custom", "description": "observatory"}
        image["text"] = {"content": "你好 / Hello", "languages": ["zh-Hans", "en"],
                         "direction": "ltr", "placement": "above", "style": "navy"}
        image["proportion"] = {"mode": "custom", "preset": None, "target_head_ratio": 5.0,
                               "acceptance_range": [4.85, 5.15], "proportion_reference": None}
        image["references"][0]["roles"] = ["identity"]
        value = self.assignment([image])
        resolved = self.validate(value)["images"][0]
        for field in ("style", "costume", "background", "text", "proportion"):
            self.assertEqual(resolved[field], image[field])
        value["images"][0]["references"][0]["roles"].append("style")
        with self.assertRaisesRegex(manage.RunError, "cannot control overridden roles"):
            self.validate(value)


if __name__ == "__main__":
    unittest.main()
