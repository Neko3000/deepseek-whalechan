"""Schema and QA protocol regressions; fixtures are not real image reviews."""
import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage


class AssignmentContractTests(unittest.TestCase):
    def validate(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return manage.validate_assignment(path)

    def test_source_brief_is_required_and_typed(self):
        value = fixtures.assignment()
        value["input"].pop("source_analysis")
        with self.assertRaisesRegex(manage.RunError, "source_analysis"):
            self.validate(value)
        for field in ("source_event", "expectation", "actual_turn", "comic_target", "tone", "language_notes"):
            for wrong in (None, "  ", []):
                value = fixtures.assignment()
                value["input"]["source_analysis"][field] = wrong
                with self.subTest(field=field, wrong=wrong), self.assertRaisesRegex(manage.RunError, field):
                    self.validate(value)
        for wrong in (None, "none", [1]):
            value = fixtures.assignment()
            value["input"]["source_analysis"]["user_constraints"] = wrong
            with self.subTest(wrong=wrong), self.assertRaisesRegex(manage.RunError, "user_constraints"):
                self.validate(value)

    def test_creative_decisions_require_reasons(self):
        for field in ("mechanism", "gate_reason"):
            value = fixtures.assignment()
            value["creative_pool"][0].pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, field):
                self.validate(value)
        value = fixtures.assignment()
        value.pop("selection_reason")
        with self.assertRaisesRegex(manage.RunError, "selection_reason"):
            self.validate(value)

    def test_creative_record_renders_reasoning(self):
        value = fixtures.assignment()
        value["images"][0]["proportion_check"] = "visible-only"
        normalized = self.validate(value)
        record = manage.creative_markdown(normalized)
        self.assertIn("## Source analysis", record)
        self.assertIn(json.dumps(normalized["input"]["source_analysis"], ensure_ascii=False, indent=2), record)
        self.assertIn(f"Selection reason: {normalized['selection_reason']}", record)
        for idea in normalized["creative_pool"]:
            self.assertIn(f"Mechanism: {idea['mechanism']}", record)
            self.assertIn(f"Gate reason: {idea['gate_reason']}", record)
        for image in normalized["images"]:
            self.assertIn(f"Idea: {image['idea_id']}; execution note: {image['execution_note']}", record)
            self.assertIn(json.dumps(image["composition"], ensure_ascii=False), record)
            self.assertIn(f"Proportion check: {image['proportion_check']}", record)

    def test_one_passing_idea_can_fill_five_tasks_without_any_quotas(self):
        value = fixtures.assignment()
        value["creative_pool"] = value["creative_pool"][:1]
        value["ranked_ideas"] = ["idea_01"]
        value.pop("duels")
        for index, image in enumerate(value["images"], 1):
            image.update(idea_id="idea_01", premise="premise 1", execution=index * 2,
                         intensity="B", panel_count=1, layout="single", text_style=fixtures.TEXT_STYLE)
            image.pop("source_rank")
            image["expression_plan"] = image["expression_plan"][:1]
            image["action_plan"] = image["action_plan"][:1]
            image["references"] = [fixtures.text_style_reference()]
            for line in image["dialogue_plan"]:
                line["panel"] = 1
        result = self.validate(value)
        self.assertEqual(result["duels"], [])
        self.assertEqual([image["source_rank"] for image in result["images"]], [1] * 5)
        self.assertTrue(all(image["qa_contract_version"] == manage.QA_CONTRACT_VERSION for image in result["images"]))
        value["text_style_policy"] = {"mode": "varied"}
        with self.assertRaisesRegex(manage.RunError, "text_style_policy.mode"):
            self.validate(value)

    def test_large_all_pass_pool_and_five_ranks_are_valid(self):
        value = fixtures.assignment()
        ninth = copy.deepcopy(value["creative_pool"][0])
        ninth["id"] = "idea_09"
        value["creative_pool"].append(ninth)
        for idea in value["creative_pool"]:
            idea["gate"] = "PASS"
            idea.pop("rejection_reason", None)
        value["ranked_ideas"] = [f"idea_{number:02d}" for number in range(1, 6)]
        value["duels"] = []
        for index, image in enumerate(value["images"], 1):
            image.update(idea_id=f"idea_{index:02d}", premise=f"premise {index}", execution=7)
            image.pop("source_rank")
        self.assertEqual(len(self.validate(value)["creative_pool"]), 9)

    def test_ranking_and_pool_order_do_not_imply_image_identity(self):
        value = fixtures.assignment()
        value["creative_pool"].reverse()
        value["ranked_ideas"].reverse()
        value["images"].reverse()
        for image in value["images"]:
            image.pop("source_rank")
        result = self.validate(value)
        self.assertEqual([image["source_rank"] for image in result["images"]], [1, 2, 3, 3, 3])
        self.assertEqual([image["idea_id"] for image in result["images"]],
                         ["idea_03", "idea_02", "idea_01", "idea_01", "idea_01"])

    def test_idea_rank_premise_and_source_mismatches_are_rejected(self):
        for field, wrong, error in (("idea_id", "idea_04", "ranked_ideas"),
                                    ("source_rank", 2, "contradicts"),
                                    ("premise", "unrelated premise", "premise"),
                                    ("fact_anchor", "unrelated event", "fact_anchor")):
            value = fixtures.assignment()
            value["images"][0][field] = wrong
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, error):
                self.validate(value)
        value = fixtures.assignment()
        value["creative_pool"][0]["fact_anchor"] = "unrelated event"
        with self.assertRaisesRegex(manage.RunError, "fact_anchor"):
            self.validate(value)

    def test_pool_ranking_and_execution_bounds(self):
        for field, wrong in (("creative_pool", []), ("ranked_ideas", []),
                             ("ranked_ideas", ["idea_01"] * 2),
                             ("ranked_ideas", [f"idea_{i:02d}" for i in range(1, 7)]),
                             ("ranked_ideas", ["idea_05"]), ("duels", {})):
            value = fixtures.assignment()
            value[field] = wrong
            with self.subTest(field=field, wrong=wrong), self.assertRaises(manage.RunError):
                self.validate(value)
        for wrong in (0, -1, True, 1.5, "1"):
            value = fixtures.assignment()
            value["images"][0]["execution"] = wrong
            with self.subTest(wrong=wrong), self.assertRaisesRegex(manage.RunError, "execution"):
                self.validate(value)
        value = fixtures.assignment()
        value["images"][1]["execution"] = 1
        with self.assertRaisesRegex(manage.RunError, "unique within"):
            self.validate(value)
        value = fixtures.assignment()
        value["images"][1]["execution_note"] = value["images"][0]["execution_note"]
        with self.assertRaisesRegex(manage.RunError, "differentiate"):
            self.validate(value)
        value = fixtures.assignment()
        value["images"].pop()
        with self.assertRaisesRegex(manage.RunError, "exactly 5"):
            self.validate(value)

    def test_composition_is_required_without_shot_keyword_heuristics(self):
        for field in ("shot", "staging", "text_placement", "reason"):
            value = fixtures.assignment()
            value["images"][0]["composition"].pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, field):
                self.validate(value)
        value = fixtures.assignment()
        value["images"][0]["composition"]["shot"] = "脸部特写"
        value["images"][0]["proportion_check"] = "visible-only"
        result = self.validate(value)
        self.assertEqual(result["images"][0]["composition"]["shot"], "脸部特写")
        for wrong in (None, "", "full-body"):
            value["images"][0]["proportion_check"] = wrong
            with self.subTest(wrong=wrong), self.assertRaisesRegex(manage.RunError, "proportion_check"):
                self.validate(value)

    def test_batch_matrix_warns_on_same_slot_even_within_set_variety(self):
        first = self.validate(fixtures.assignment())
        second = copy.deepcopy(first)
        second["run_name"] = "another-case"
        summary = manage.design_summary([first, second])
        self.assertTrue(summary["structurally_valid"])
        self.assertTrue(summary["creative_review_required"])
        self.assertIsNone(summary["creative_approval"])
        self.assertEqual(len(summary["matrix"]), 2)
        column = summary["matrix"][0]["columns"][0]
        self.assertTrue({"index", "mechanism", "panel_count", "layout", "shot", "staging", "text_placement", "template"} <= column.keys())
        codes = [item["code"] for item in summary["warnings"]]
        self.assertEqual(codes.count("same_index_layout_template"), 5)
        for code in ("repeated_panel_sequence", "repeated_mechanism", "repeated_beats", "repeated_staging"):
            self.assertIn(code, codes)

    def test_multicase_still_needs_creative_review_without_warnings(self):
        # Isolate summary semantics from assignment validation and make all positions distinct.
        rows = []
        for case in range(2):
            value = fixtures.assignment()
            value["run_name"] = f"case-{case}"
            for index, image in enumerate(value["images"]):
                idea = copy.deepcopy(value["creative_pool"][0])
                idea["id"] = f"slot_{index}"
                idea["mechanism"] = f"mechanism {case}-{index}"
                value["creative_pool"].append(idea)
                image["idea_id"] = idea["id"]
                image["text_style"] = f"template-{case}-{index}"
                image["composition"]["staging"] = f"staging {case}-{index}"
                image["action_plan"] = [{"action": f"beat {case}-{index}"}]
            if case:
                value["images"][0]["panel_count"] = 4
            rows.append(value)
        result = manage.design_summary(rows)
        self.assertEqual(result["warnings"], [])
        self.assertTrue(result["creative_review_required"])


class QAProtocolTests(unittest.TestCase):
    setUp = fixtures.RunStateTests.setUp
    tearDown = fixtures.RunStateTests.tearDown
    files = fixtures.RunStateTests.files

    def qa(self, args):
        return manage.read_json(Path(args.visual_json))

    def test_qa_requires_specification_for_every_verdict(self):
        for number, verdict in enumerate(("PASS", "FAIL"), 1):
            args = self.files(number, verdict)
            for component in (False, True):
                with self.subTest(verdict=verdict, component=component), self.assertRaisesRegex(manage.RunError, "specification"):
                    manage.validate_qa(Path(args.visual_json), manage.sha256(Path(args.candidate)),
                                       component=component, image_spec=None)

    def test_qa_contract_marker_cannot_disable_review(self):
        args = self.files(1, "FAIL")
        for marker in (None, 6, 7, 8, 999):
            spec = copy.deepcopy(self.image_spec)
            spec["qa_contract_version"] = marker
            with self.subTest(marker=marker), self.assertRaisesRegex(manage.RunError, "qa_contract_version"):
                self.validate(args, self.qa(args), spec=spec)

    def test_frozen_run_requires_assignment_hash(self):
        path = self.run_dir / "manifest.json"
        original = manage.read_json(path)
        for wrong in (None, "", "not-a-hash"):
            manifest = copy.deepcopy(original)
            manifest["assignment_sha256"] = wrong
            manage.write_json(path, manifest)
            with self.subTest(wrong=wrong), self.assertRaisesRegex(manage.RunError, "assignment_sha256"):
                manage.load_run(str(self.run_dir))

    def test_frozen_image_contract_cannot_fall_back(self):
        assignment_path = self.run_dir / "assignment.json"
        manifest_path = self.run_dir / "manifest.json"
        original = manage.read_json(assignment_path)
        for field, wrong, error in (("qa_contract_version", None, "qa_contract_version"),
                                    ("qa_contract_version", 8, "qa_contract_version"),
                                    ("references", [], "references"),
                                    ("supporting_character", {}, "unsupported fields")):
            invalid = copy.deepcopy(original)
            invalid["images"][0][field] = wrong
            manage.write_json(assignment_path, invalid)
            manifest = manage.read_json(manifest_path)
            manifest["assignment_sha256"] = manage.sha256(assignment_path)
            manage.write_json(manifest_path, manifest)
            with self.subTest(field=field, wrong=wrong), self.assertRaisesRegex(manage.RunError, error):
                manage.load_run(str(self.run_dir))

    def validate(self, args, value, component=False, spec=None):
        manage.write_json(Path(args.visual_json), value)
        return manage.validate_qa(Path(args.visual_json), manage.sha256(Path(args.candidate)),
                                  component=component, image_spec=spec or self.image_spec)

    def test_pending_and_missing_review_reject_pass_fail_and_components_before_record(self):
        number = 0
        for verdict in ("PASS", "FAIL"):
            for component in (False, True):
                for status in (None, "pending"):
                    number += 1
                    args = self.files(number, verdict)
                    value = self.qa(args)
                    value["review_status"] = status
                    if component:
                        value["gates"] = {key: "PASS" for key in manage.COMPONENT_GATES}
                        if verdict == "FAIL":
                            value["gates"]["T1"] = "FAIL"
                    manage.write_json(Path(args.visual_json), value)
                    with self.subTest(verdict=verdict, component=component, status=status), self.assertRaisesRegex(manage.RunError, "review_status"):
                        manage.record_image(args, component=component)
        _, _, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(manifest["images"][self.image]["attempts"], [])

    def test_pass_and_fail_require_candidate_bound_direct_observation(self):
        for number, verdict in enumerate(("PASS", "FAIL"), 1):
            args = self.files(number, verdict)
            original = self.qa(args)
            for field, wrong in (("candidate_sha256", "0" * 64), ("reviewer", ""),
                                 ("method", "planned-evidence"), ("panels", []),
                                 ("text_transcription", None)):
                value = copy.deepcopy(original)
                value["observation"][field] = wrong
                with self.subTest(verdict=verdict, field=field), self.assertRaisesRegex(manage.RunError, "observation"):
                    self.validate(args, value)
            value = copy.deepcopy(original)
            value.pop("observation")
            with self.assertRaisesRegex(manage.RunError, "observation"):
                self.validate(args, value)

    def test_observed_transcript_is_independent_of_planned_evidence(self):
        args = self.files(1, "PASS")
        value = self.qa(args)
        value["observation"]["text_transcription"] = ["wrong visible words"]
        with self.assertRaisesRegex(manage.RunError, "observation.text_transcription"):
            self.validate(args, value)
        value["verdict"] = "FAIL"
        value["gates"]["T1"] = "FAIL"
        value["defects"] = ["The visible words are wrong"]
        value["targeted_retry"] = "Correct the visible words"
        self.assertEqual(self.validate(args, value)["verdict"], "FAIL")

    def test_failed_panel_count_can_be_observed_honestly(self):
        args = self.files(1, "FAIL")
        value = self.qa(args)
        value["observation"]["panels"].append({"panel": 2, "observed_scene": "Unwanted duplicate scene"})
        value["gates"]["P1"] = "FAIL"
        self.validate(args, value)
        value["verdict"] = "PASS"
        value["gates"] = {key: "PASS" for key in manage.CONFIGURABLE_GATES}
        value["defects"] = []
        value["targeted_retry"] = None
        with self.assertRaisesRegex(manage.RunError, "observation.panels"):
            self.validate(args, value)

    def test_component_observation_uses_its_panels_exact_transcript(self):
        args = self.files(1, "PASS")
        value = self.qa(args)
        value["gates"] = {key: "PASS" for key in manage.COMPONENT_GATES}
        value.pop("evidence")
        spec = copy.deepcopy(self.image_spec)
        spec["panel_count"] = 2
        spec["layout"] = "top-bottom"
        spec["expression_plan"].append({**spec["expression_plan"][0], "panel": 2})
        spec["action_plan"].append({**spec["action_plan"][0], "panel": 2})
        spec["dialogue_plan"][1]["panel"] = 2
        value["observation"]["panels"] = [{"panel": 2, "observed_scene": "The resulting comma"}]
        value["observation"]["text_transcription"] = [spec["core_text"][1]]
        self.validate(args, value, component=True, spec=spec)
        value["observation"]["text_transcription"] = spec["core_text"]
        with self.assertRaisesRegex(manage.RunError, "observation.text_transcription"):
            self.validate(args, value, component=True, spec=spec)

    def test_na_is_candidate_bound_visible_only_and_allows_other_failed_gates(self):
        args = self.files(1, "PASS")
        original = self.qa(args)
        original["gates"]["H1"] = "NA"
        original["evidence"]["form_evidence"] = {
            "mode": "visible-only", "candidate_sha256": original["candidate_sha256"],
            "reason": "The deliberate close shot excludes lower body landmarks",
            "observed_cues": ["Rounded head and compact shoulders remain consistent"],
        }
        with self.assertRaisesRegex(manage.RunError, "proportion_check"):
            self.validate(args, original)
        spec = copy.deepcopy(self.image_spec)
        spec["composition"]["shot"] = "close-up"
        spec["proportion_check"] = "visible-only"
        self.assertEqual(self.validate(args, original, spec=spec)["verdict"], "PASS")
        for field, wrong in (("mode", "measured"), ("candidate_sha256", "0" * 64),
                             ("reason", ""), ("observed_cues", []), ("calculated_head_ratio", 2.8),
                             ("head_axis", {}), ("body_segments", [])):
            value = copy.deepcopy(original)
            value["evidence"]["form_evidence"][field] = wrong
            with self.subTest(field=field), self.assertRaises(manage.RunError):
                self.validate(args, value, spec=spec)
        value = copy.deepcopy(original)
        value["gates"]["T1"] = "FAIL"
        with self.assertRaisesRegex(manage.RunError, "verdict must agree"):
            self.validate(args, value, spec=spec)
        value["verdict"] = "FAIL"
        value["defects"] = ["The close-up has unreadable text"]
        value["targeted_retry"] = "Correct the lettering in the same close-up"
        self.assertEqual(self.validate(args, value, spec=spec)["verdict"], "FAIL")
        value["gates"]["H1"] = "FAIL"
        value["defects"] = ["The visible head shape is deformed"]
        self.assertEqual(self.validate(args, value, spec=spec)["verdict"], "FAIL")
        value = copy.deepcopy(original)
        value["gates"]["T1"] = "NA"
        with self.assertRaisesRegex(manage.RunError, "only H1"):
            self.validate(args, value, spec=spec)
        value = copy.deepcopy(original)
        value["gates"]["H1"] = "PASS"
        with self.assertRaises(manage.RunError):
            self.validate(args, value, spec=spec)

    def test_closeup_text_failure_records_without_fake_measurement(self):
        path = self.run_dir / "assignment.json"
        frozen = manage.read_json(path)
        frozen["images"][0]["proportion_check"] = "visible-only"
        manage.write_json(path, frozen)
        manifest = manage.read_json(self.run_dir / "manifest.json")
        manifest["assignment_sha256"] = manage.sha256(path)
        manage.write_json(self.run_dir / "manifest.json", manifest)
        args = self.files(1, "FAIL")
        value = self.qa(args)
        value["gates"]["J1"] = "PASS"
        value["gates"]["T1"] = "FAIL"
        value["gates"]["H1"] = "NA"
        value["observation"]["text_transcription"] = ["incorrect words"]
        value["evidence"]["form_evidence"] = {
            "mode": "visible-only", "candidate_sha256": value["candidate_sha256"],
            "reason": "The intentional close-up excludes whole-body landmarks",
            "observed_cues": ["Rounded head and compact shoulders"],
        }
        value["defects"] = ["The visible wording is incorrect"]
        value["targeted_retry"] = "Replace only the incorrect wording"
        manage.write_json(Path(args.visual_json), value)
        result = manage.record_image(args, component=False)
        self.assertEqual(result["verdict"], "FAIL")
        _, _, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 1)

    def test_promote_rechecks_review_status_and_candidate_hash(self):
        args = self.files(1, "PASS")
        record = manage.record_image(args, component=False)
        visual_path = Path(record["visual_qa"])
        value = manage.read_json(visual_path)
        value["review_status"] = "pending"
        manage.write_json(visual_path, value)
        with self.assertRaisesRegex(manage.RunError, "review_status"):
            manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        self.assertFalse((self.run_dir / "final" / f"{self.image}.png").exists())
        value["review_status"] = "reviewed"
        manage.write_json(visual_path, value)
        Path(record["candidate"]).write_bytes(b"changed test candidate")
        with self.assertRaisesRegex(manage.RunError, "SHA-256 mismatch"):
            manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))

    def test_component_record_and_composite_reject_pending_review(self):
        self.image = "02_comic_2"
        frozen = manage.read_json(self.run_dir / "assignment.json")
        self.image_spec = frozen["images"][1]
        sources = []
        for panel in (1, 2):
            args = self.files(panel, "PASS")
            value = self.qa(args)
            value["gates"] = {key: "PASS" for key in manage.COMPONENT_GATES}
            value["observation"]["panels"] = [{"panel": panel, "observed_scene": f"Synthetic component {panel}"}]
            value["observation"]["text_transcription"] = [self.image_spec["core_text"][panel - 1]]
            value.pop("evidence")
            manage.write_json(Path(args.visual_json), value)
            sources.append(manage.record_image(args, component=True)["attempt_id"])
        args = self.files(3, "PASS")
        args.source_attempt = sources
        value = self.qa(args)
        value["review_status"] = "pending"
        manage.write_json(Path(args.visual_json), value)
        with self.assertRaisesRegex(manage.RunError, "review_status"):
            manage.cmd_record_composite(args)
        _, _, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(manifest["images"][self.image]["derived"], [])
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 2)

    def test_current_run_and_qa_require_complete_contract(self):
        before = (self.run_dir / "assignment.json").read_bytes()
        _, loaded, _ = manage.load_run(str(self.run_dir))
        self.assertEqual(loaded["schema_version"], manage.ASSIGNMENT_SCHEMA_VERSION)
        self.assertEqual((self.run_dir / "assignment.json").read_bytes(), before)
        for number, verdict in enumerate(("PASS", "FAIL"), 1):
            args = self.files(number, verdict)
            original = self.qa(args)
            for field in ("review_status", "observation"):
                invalid = copy.deepcopy(original)
                invalid.pop(field)
                with self.subTest(verdict=verdict, field=field), self.assertRaisesRegex(manage.RunError, field):
                    self.validate(args, invalid)
            for field in ("dialogue_plan", "expression_plan", "cast_plan", "proportion_check"):
                spec = copy.deepcopy(self.image_spec)
                spec.pop(field)
                with self.subTest(verdict=verdict, field=field), self.assertRaisesRegex(manage.RunError, field):
                    self.validate(args, original, spec=spec)


if __name__ == "__main__":
    unittest.main()
