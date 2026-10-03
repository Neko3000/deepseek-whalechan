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
        value = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        value["input"]["participants"] = [{"id": "user", "role": "user", "source_evidence": "The user asks about the unfinished task."}]
        value["selection"]["adjustments"] = ["Keep the accusation in English"]
        value["confirmation"]["summary_sha256"] = manage.selection_summary(value)["summary_sha256"]
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
        path = Path(self.temporary.name) / "design.json"
        path.write_text(json.dumps({**value, "images": [{**image, "dialogue_plan": [image["dialogue_plan"][0], {k: v for k, v in image["dialogue_plan"][1].items() if k != "prop"}]}]}))
        with self.assertRaisesRegex(manage.RunError, "dialogue_plan.prop"):
            manage.validate_assignment(path)
        path.write_text(json.dumps(value))
        normalized = manage.validate_assignment(path)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        for expected in ("Proposal A", "Keep the accusation in English", "speaker=user",
                         "ROLE user: physical", "tight face close-up", "do not add a full-body inset",
                         "TEXT TEMPLATE: " + image["text_style"],
                         "written on the factory's brass nameplate", "never glyph-like marks",
                         "References never supply facial expression", "never elongate them"):
            self.assertIn(expected, prompt)
        unselected = copy.deepcopy(normalized["images"][0])
        unselected["idea_id"] = "idea_04"
        with self.assertRaisesRegex(builder.manage.RunError, "confirmed assignment"):
            builder.build_prompt(normalized, unselected)

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
        first = fixtures.selected_assignment([{"choice": "A", "count": 1}])
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
