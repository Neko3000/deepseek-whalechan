"""Regressions for uniform typography and silently removed dialogue partners."""
import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage
PROMPT_SPEC = importlib.util.spec_from_file_location("comic_build_prompt", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
builder = importlib.util.module_from_spec(PROMPT_SPEC)
PROMPT_SPEC.loader.exec_module(builder)


def with_user(representation="physical"):
    value = fixtures.assignment()
    value["input"]["participants"] = [{"id": "user", "role": "user", "source_evidence": "The user asks why the task is unfinished."}]
    for image in value["images"]:
        image["dialogue_plan"][0]["speaker"] = "user"
        image["cast_plan"] = [{
            "participant": "user", "representation": representation, "panels": [1],
            "staging": "The user points at the unfinished task from the left." if representation in {"physical", "avatar"} else None,
            "reason": "The user's accusation establishes the expectation she overturns.",
        }]
        if representation in {"physical", "avatar"}:
            image["references"].append({
                "id": "abstract-user", "path": str(fixtures.SKILL_ROOT / "assets/supporting-character-references/abstract-user-pose-sheet.webp"),
                "roles": ["identity"], "instruction": "Only the subordinate blank indigo user's identity.",
            })
    return value


class DesignContractTests(unittest.TestCase):
    def validate(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return manage.validate_assignment(path)

    def test_semantic_policy_allows_same_style_without_count_quota(self):
        value = fixtures.assignment()
        for image in value["images"]:
            image["text_style"] = "07_casual-dialogue"
            image["references"] = [fixtures.text_style_reference("07_casual-dialogue")]
        result = self.validate(value)
        self.assertEqual(result["text_style_policy"], {"mode": "semantic"})

    def test_rejects_unexplained_offscreen_user(self):
        value = fixtures.assignment()
        value["input"]["participants"] = [
            {"id": "user", "role": "user", "source_evidence": "The user asks why the task is unfinished."}
        ]
        for image in value["images"]:
            image["dialogue_plan"][0]["speaker"] = "user"
            image["cast_plan"] = [
                {"participant": "user", "representation": "offscreen", "panels": [1],
                 "staging": None, "reason": ""}
            ]
        with self.assertRaisesRegex(manage.RunError, "reason"):
            self.validate(value)

    def test_explicit_uniform_typography_is_honored_and_audited(self):
        value = fixtures.assignment()
        for image in value["images"]:
            image["text_style"] = fixtures.TEXT_STYLE
            image["references"] = [fixtures.text_style_reference()]
        value["text_style_policy"] = {"mode": "uniform", "template": fixtures.TEXT_STYLE,
                                      "user_instruction": "Use the same top-bottom punchline lettering in all five comics."}
        result = self.validate(value)
        self.assertEqual(manage.design_summary([result])["text_styles"], {fixtures.TEXT_STYLE: 5})
        self.assertIn(value["text_style_policy"]["user_instruction"], manage.creative_markdown(result))
        value["text_style_policy"].pop("user_instruction")
        with self.assertRaisesRegex(manage.RunError, "user_instruction"):
            self.validate(value)

    def test_decisions_cannot_be_silently_defaulted(self):
        for field in ("text_style_reason", "dialogue_plan", "cast_plan"):
            value = fixtures.assignment()
            value["images"][0].pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, field):
                self.validate(value)
        value = fixtures.assignment()
        value["input"].pop("participants")
        with self.assertRaisesRegex(manage.RunError, "participants"):
            self.validate(value)

    def test_solo_source_needs_no_invented_supporting_character(self):
        result = self.validate(fixtures.assignment())
        self.assertTrue(all(image["cast_plan"] == [] for image in result["images"]))
        self.assertTrue(all("supporting_character" not in image for image in result["images"]))
        self.assertEqual(manage.design_summary([result])["cast_images"]["physical"], 0)

    def test_offscreen_voice_requires_a_narrative_decision(self):
        value = with_user("offscreen")
        for image in value["images"]:
            image["cast_plan"][0]["reason"] = "The caller is on a remote audio-only connection; the punchline depends on the unseen caller."
        result = self.validate(value)
        self.assertEqual(manage.design_summary([result])["cast_images"]["offscreen"], 5)

    def test_avatar_is_not_counted_as_a_physical_partner(self):
        result = self.validate(with_user("avatar"))
        summary = manage.design_summary([result])
        self.assertEqual(summary["cast_images"]["avatar"], 5)
        self.assertEqual(summary["cast_images"]["physical"], 0)

    def test_source_roles_and_dialogue_cannot_disappear(self):
        value = with_user()
        value["images"][0]["cast_plan"] = []
        with self.assertRaisesRegex(manage.RunError, "every input participant"):
            self.validate(value)
        value = with_user("absent")
        value["images"][0]["cast_plan"][0]["panels"] = []
        with self.assertRaisesRegex(manage.RunError, "speaker is absent"):
            self.validate(value)
        for key, wrong, error in [("speaker", "unknown", "unknown speaker"), ("panel", 7, "reading order"), ("text_index", 1, "consecutive")]:
            value = with_user()
            value["images"][0]["dialogue_plan"][0][key] = wrong
            with self.subTest(key=key), self.assertRaisesRegex(manage.RunError, error):
                self.validate(value)

    def test_unsupported_cast_field_is_rejected(self):
        value = with_user()
        value["images"][0]["supporting_character"] = {"present": False, "interaction": None}
        with self.assertRaisesRegex(manage.RunError, "unsupported fields"):
            self.validate(value)

    def test_builder_uses_selected_template_and_onstage_speakers(self):
        value = with_user()
        image = value["images"][0]
        image["text_style"] = "04_burst-command"
        image["references"][0] = fixtures.text_style_reference("04_burst-command")
        value["input"]["language"] = "en"
        normalized = self.validate(value)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        for expected in ("TEXT TEMPLATE: 04_burst-command", "jagged", "LANGUAGE: en", "speaker=user", "ROLE user: physical", "never an off-panel substitute"):
            self.assertIn(expected, prompt)
        self.assertNotIn("07_casual-dialogue", prompt)
        self.assertNotIn("No visible user", prompt)
        self.assertEqual(len(normalized["images"][0]["references"]), 3)

    def test_builder_preserves_visible_only_framing_and_source_decisions(self):
        value = fixtures.assignment()
        value["images"][0]["proportion_check"] = "visible-only"
        value["images"][0]["composition"]["shot"] = "tight face close-up"
        normalized = self.validate(value)
        image = normalized["images"][0]
        prompt = builder.build_prompt(normalized, image)
        self.assertIn("SOURCE INTERPRETATION:", prompt)
        self.assertIn(normalized["input"]["source_analysis"]["actual_turn"], prompt)
        self.assertIn(image["composition"]["shot"], prompt)
        self.assertIn(image["execution_note"], prompt)
        self.assertIn("do not add a full-body inset", prompt)
        self.assertNotIn("Keep assessable full-body landmarks", prompt)
        self.assertNotIn("Include a measurable full-body view", prompt)
        image["proportion_check"] = "measured"
        self.assertIn("Keep assessable full-body landmarks", builder.build_prompt(normalized, image))

    def test_builder_is_independent_of_image_order_and_ids(self):
        original = self.validate(fixtures.assignment())
        before = {image["name"]: builder.build_prompt(original, image) for image in original["images"]}
        reordered = copy.deepcopy(original)
        reordered["images"].reverse()
        for index, image in enumerate(reordered["images"], 1):
            image["id"] = f"{index:02d}_{image['name']}"
        for image in reordered["images"]:
            self.assertEqual(builder.build_prompt(reordered, image), before[image["name"]])

    def test_builder_requires_current_contract(self):
        value = self.validate(fixtures.assignment())
        for version in (None, 5, 6, 7, 8, manage.ASSIGNMENT_SCHEMA_VERSION + 1):
            invalid = copy.deepcopy(value)
            invalid["schema_version"] = version
            with self.subTest(version=version), self.assertRaisesRegex(builder.manage.RunError, "schema_version"):
                builder.build_prompt(invalid, invalid["images"][0])
        for field in ("proportion_check", "qa_contract_version"):
            invalid = copy.deepcopy(value["images"][0])
            invalid.pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(builder.manage.RunError, field):
                builder.build_prompt(value, invalid)

    def test_qa_requires_visible_typography_dialogue_and_cast_evidence(self):
        image = self.validate(with_user())["images"][0]
        evidence = fixtures.design_evidence(image)
        manage.validate_design_evidence(evidence, image)
        for field in ("text_style_match", "dialogue_match", "cast_match"):
            broken = copy.deepcopy(evidence)
            broken.pop(field)
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, field):
                manage.validate_design_evidence(broken, image)
        for field, key, wrong in [("cast_match", "representation", "avatar"), ("dialogue_match", "speaker", "whalechan")]:
            broken = copy.deepcopy(evidence)
            broken[field][0][key] = wrong
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, "does not match"):
                manage.validate_design_evidence(broken, image)

    def test_batch_checks_every_group_before_any_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for index in range(2):
                value = fixtures.assignment()
                value["run_name"] = f"case-{index}"
                if index == 1:
                    for image in value["images"]:
                        image["text_style"] = fixtures.TEXT_STYLE
                        image["references"] = [fixtures.text_style_reference()]
                path = Path(directory) / f"case-{index}.json"
                path.write_text(json.dumps(value))
                paths.append(str(path))
            result = manage.cmd_validate_batch(argparse.Namespace(assignment=paths))
            self.assertTrue(result["structurally_valid"])
            self.assertTrue(result["creative_review_required"])
            self.assertEqual(len(list(Path(directory).iterdir())), 2)

    def test_prompt_cli_preserves_its_reference_order_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(with_user()))
            result = manage.cmd_init(argparse.Namespace(assignment=str(path), root=directory, effective_parallelism=1))
            run = Path(result["run_dir"])
            command = [sys.executable, "-B", str(fixtures.SKILL_ROOT / "scripts/build-prompt.py"),
                       "--run-dir", str(run), "--image", "01_comic_1"]
            first = subprocess.run(command, capture_output=True, text=True, check=True)
            built = json.loads(first.stdout)
            frozen = manage.read_json(run / "assignment.json")
            self.assertEqual(built["references"], [ref["path"] for ref in frozen["images"][0]["references"]])
            prompt = Path(built["prompt_file"])
            before = prompt.read_bytes()
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(prompt.read_bytes(), before)

    def test_frozen_run_rejects_noncurrent_versions_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(fixtures.assignment()))
            initialized = manage.cmd_init(argparse.Namespace(assignment=str(path), root=directory, effective_parallelism=1))
            run = Path(initialized["run_dir"])
            original = manage.read_json(run / "assignment.json")
            for version in (None, 5, 6, 7, 8, manage.ASSIGNMENT_SCHEMA_VERSION + 1):
                invalid = copy.deepcopy(original)
                invalid["schema_version"] = version
                manage.write_json(run / "assignment.json", invalid)
                before = (run / "assignment.json").read_bytes()
                with self.subTest(version=version), self.assertRaisesRegex(manage.RunError, "schema_version"):
                    manage.load_run(str(run))
                self.assertEqual((run / "assignment.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
