"""Selected designs, independent text observations and batch review boundaries."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage
PROMPT_SPEC = importlib.util.spec_from_file_location("comic_build_prompt", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
builder = importlib.util.module_from_spec(PROMPT_SPEC)
PROMPT_SPEC.loader.exec_module(builder)


class DesignContractTests(unittest.TestCase):
    setUp = fixtures.RunStateTests.setUp
    initialize = fixtures.RunStateTests.initialize
    files = fixtures.RunStateTests.files

    def test_prompt_preserves_selected_proposal_dialogue_and_framing(self):
        value = fixtures.assignment()
        value["input"]["participants"] = [{"id": "user", "role": "user", "source_evidence": "The user asks about the unfinished task."}]
        value["input"]["source_analysis"]["user_constraints"] = ["Keep the accusation in English"]
        image = value["images"][0]
        image["proportion_check"] = "visible-only"
        image["composition"]["shot"] = "tight face close-up"
        image["dialogue_plan"][0]["speaker"] = "user"
        image["cast_plan"] = [{"participant": "user", "representation": "physical", "panels": [1],
                              "staging": "The user points at the task from the left.",
                              "reason": "The accusation establishes the expectation."}]
        image["references"].append({
            "id": "abstract-user", "path": str(fixtures.SKILL_ROOT / "assets/supporting-character-references/abstract-user-pose-sheet.webp"),
            "roles": ["identity"], "instruction": "Only the blank indigo user's identity.",
        })
        image["dialogue_plan"][1].update(speaker="narrator", delivery="label", prop="the factory's brass nameplate")
        for other in value["images"][1:]:
            other["cast_plan"] = [{"participant": "user", "representation": "absent", "panels": [],
                                   "reason": "This idea lands through Whale-chan's action alone."}]
        path = Path(self.temporary.name) / "design.json"
        broken = copy.deepcopy(value)
        broken["images"][0]["dialogue_plan"][1].pop("prop")
        path.write_text(json.dumps(fixtures.confirm_fixture_plan(broken)))
        with self.assertRaisesRegex(manage.RunError, "dialogue_plan.prop"):
            manage.validate_assignment(path)
        path.write_text(json.dumps(fixtures.confirm_fixture_plan(value)))
        normalized = manage.validate_assignment(path)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        for expected in ("Proposal A", "Keep the accusation in English", "speaker=user",
                         "ROLE user: physical", "tight face close-up", "do not add a full-body inset",
                         "TEXT TEMPLATE: " + image["text_style"],
                         "written on the factory's brass nameplate", "never glyph-like marks",
                         "References never supply facial expression", "never elongate them"):
            self.assertIn(expected, prompt)
        unselected = copy.deepcopy(normalized["images"][0])
        unselected["idea_id"] = "idea_06"
        with self.assertRaisesRegex(builder.manage.RunError, "confirmed assignment"):
            builder.build_prompt(normalized, unselected)

    def test_each_prompt_contains_only_its_own_idea_and_no_planning_metadata(self):
        frozen = manage.read_json(self.run_dir / "assignment.json")
        for index, image in enumerate(frozen["images"]):
            prompt = builder.build_prompt(frozen, image)
            for line in image["core_text"]:
                self.assertIn(line, prompt)
            for other in frozen["images"]:
                if other["idea_id"] != image["idea_id"]:
                    for line in other["core_text"]:
                        self.assertNotIn(line, prompt)
            for hidden in ("worker-1", "worker-2", "worker-3", frozen["duels"][0]["reason"],
                           frozen["proposal"]["options"][index]["selection_reason"]):
                self.assertNotIn(hidden, prompt)

    def test_repeated_scripts_are_visible_but_shared_setup_is_not_a_hard_gate(self):
        value = fixtures.assignment()
        value["images"][1]["core_text"] = list(value["images"][0]["core_text"])
        repeated = manage.design_summary([value])
        warnings = [item for item in repeated["warnings"] if item["code"] == "repeated_dialogue"]
        self.assertTrue(warnings)
        self.assertIn(value["images"][0]["core_text"][0], json.dumps(warnings, ensure_ascii=False))
        self.assertTrue(repeated["creative_review_required"])
        self.assertIsNone(repeated["creative_approval"])
        shared = fixtures.assignment()
        for image, option in zip(shared["images"], shared["proposal"]["options"]):
            image["core_text"][0] = "What happened to the comma?"
            option["key_lines"] = list(image["core_text"])
        path = Path(self.temporary.name) / "shared-setup.json"
        path.write_text(json.dumps(fixtures.confirm_fixture_plan(shared)))
        normalized = manage.validate_assignment(path)
        review = manage.design_summary([normalized])
        self.assertIn("repeated_line", [item["code"] for item in review["warnings"]])
        self.assertNotIn("repeated_dialogue", [item["code"] for item in review["warnings"]])

    def test_observation_must_match_candidate_and_transcript(self):
        args = self.files(1, "PASS")
        path = Path(args.visual_json)
        qa = manage.read_json(path)
        candidate_hash = manage.sha256(Path(args.candidate))
        self.assertEqual(manage.validate_qa(path, candidate_hash, image_spec=self.image_spec)["verdict"], "PASS")
        for defect in ("missing", "wrong-image", "planned-evidence"):
            broken = copy.deepcopy(qa)
            if defect == "missing":
                broken.pop("observation")
            elif defect == "wrong-image":
                broken["observation"]["candidate_sha256"] = "0" * 64
            else:
                broken["observation"]["method"] = "planned-evidence"
            manage.write_json(path, broken)
            with self.subTest(defect=defect), self.assertRaisesRegex(manage.RunError, "observation"):
                manage.validate_qa(path, candidate_hash, image_spec=self.image_spec)
        qa["observation"]["text_transcription"] = ["wrong visible words"]
        manage.write_json(path, qa)
        with self.assertRaisesRegex(manage.RunError, "observation.text_transcription"):
            manage.validate_qa(path, candidate_hash, image_spec=self.image_spec)
        qa.update(verdict="FAIL", defects=["The visible words are wrong"], targeted_retry="Correct the lettering")
        qa["gates"]["T1"] = "FAIL"
        manage.write_json(path, qa)
        self.assertEqual(manage.validate_qa(path, candidate_hash, image_spec=self.image_spec)["verdict"], "FAIL")

    def test_batch_warnings_never_grant_creative_approval(self):
        first = fixtures.assignment()
        first["images"] = first["images"][:1]
        second = copy.deepcopy(first)
        second["run_name"] = "second-case"
        repeated = manage.design_summary([first, second])
        self.assertIn("same_index_layout_template", [item["code"] for item in repeated["warnings"]])
        # Change the second case's actual structural signals, not only its ordinal.
        second["creative_pool"][0]["mechanism"] = "A different source-specific mechanism"
        second["images"] = [copy.deepcopy(fixtures.assignment()["images"][1])]
        image = second["images"][0]
        image["composition"]["staging"] = "The partner reveals the result on the right"
        for action in image["action_plan"]:
            action["action"] = f"Different source-specific reveal in panel {action['panel']}"
        distinct = manage.design_summary([first, second])
        self.assertEqual(distinct["warnings"], [])
        for result in (repeated, distinct):
            self.assertTrue(result["creative_review_required"])
            self.assertIsNone(result["creative_approval"])


if __name__ == "__main__":
    unittest.main()
