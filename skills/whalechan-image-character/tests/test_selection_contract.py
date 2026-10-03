"""Synthetic gate records test consistency, not real user consent."""
import argparse
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage_run


class SelectionContractTests(unittest.TestCase):
    def assignment(self, count=1):
        helper = fixtures.AssignmentTests()
        return fixtures.confirm_fixture(helper.assignment([
            helper.image(f"scene_{index}") for index in range(count)
        ]))

    def validate(self, value, directory):
        path = Path(directory) / "assignment.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return manage.validate_assignment(path)

    def test_default_count_and_direct_or_explore_options(self):
        value = self.assignment(5)
        value["proposal"]["mode"] = "explore"
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        for row in value["selection"]["choices"]:
            row.pop("count")
        summary = manage.selection_summary(value, fixtures.SKILL_ROOT / "draft.json")
        self.assertEqual((summary["proposal_count"], summary["image_count"]), (5, 5))
        self.assertEqual(summary["budget"]["estimated_maximum"], 40)
        value["proposal"]["options"].pop()
        with self.assertRaisesRegex(manage.RunError, "five ordered"):
            manage.proposal_markdown(value["proposal"])
        single = self.assignment()
        self.assertEqual(len(manage.proposal_options(single["proposal"])), 1)

    def test_gate_helpers_are_read_only_and_need_no_images(self):
        value = self.assignment()
        value.pop("images")
        value.pop("confirmation")
        value["proposal"]["options"][0]["title"] = "Title|line\nnext"
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            before = path.read_bytes()
            for command in ("render-proposal", "summarize-selection"):
                result = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), command,
                                         "--draft", str(path)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                rendered = json.loads(result.stdout)["markdown"]
                self.assertIn("Title\\|line<br>next", rendered)
                self.assertEqual(before, path.read_bytes())
                self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_invalid_quantities_and_old_schema_are_rejected(self):
        for count in (0, -1, True, 1.5, "2"):
            value = self.assignment()
            value["selection"]["choices"][0]["count"] = count
            with self.subTest(count=count), self.assertRaisesRegex(manage.RunError, "positive integer"):
                manage.selection_summary(value, fixtures.SKILL_ROOT / "draft.json")
        value = self.assignment()
        value["schema_version"] = 4
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "schema_version must be 5"):
                self.validate(value, directory)

    def test_multiple_configuration_groups_for_one_selected_proposal(self):
        value = self.assignment(2)
        value["selection"]["choices"] = [{"choice": "A", "count": 2}]
        value["scope"]["configurations"][1]["choice"] = "A"
        value["images"][1]["proposal_choice"] = "A"
        with tempfile.TemporaryDirectory() as directory:
            summary = manage.selection_summary(value, Path(directory) / "assignment.json")
            self.assertEqual((summary["proposal_count"], summary["image_count"]), (1, 2))
            value["confirmation"]["summary_sha256"] = summary["summary_sha256"]
            self.validate(value, directory)

    def test_missing_gate_cannot_initialize(self):
        for missing in ("selection", "confirmation"):
            value = self.assignment()
            value.pop(missing)
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "assignment.json"
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(manage.RunError):
                    manage.cmd_init(argparse.Namespace(assignment=str(path), root=str(Path(directory) / "runs"), effective_parallelism=1))
                self.assertFalse((Path(directory) / "runs").exists())

    def test_changed_proposal_requires_gate_one(self):
        value = self.assignment()
        value["proposal"]["options"][0]["scene"] = "A different scene"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "repeat Gate 1"):
                self.validate(value, directory)

    def test_scope_changes_invalidate_gate_two(self):
        def requirements(value):
            return value["scope"]["configurations"][0]["requirements"]
        changes = {
            "adjustments": lambda v: v["selection"]["adjustments"].append("Smile"),
            "background": lambda v: requirements(v)["background"].update(description="pure white"),
            "resolution": lambda v: requirements(v)["output"].update(resolution={"mode": "exact", "width": 1024, "height": 1024}),
            "action": lambda v: requirements(v).update(action="sit"),
            "reference permission": lambda v: requirements(v)["references"][0].update(instruction="Identity only"),
            "budget": lambda v: v["budget"].update(per_provider_candidates=1),
            "parallelism": lambda v: v["execution"].update(mode="parallel", requested_parallelism=2),
            "variation": lambda v: v["scope"]["configurations"][0].update(variation="Different expression"),
        }
        for label, mutate in changes.items():
            value = self.assignment()
            mutate(value)
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                    self.validate(value, directory)

    def test_text_and_transparency_changes_require_new_confirmation(self):
        for field in ("text", "alpha"):
            value = self.assignment()
            req = value["scope"]["configurations"][0]["requirements"]
            if field == "text":
                req["text"] = {"content": "你好", "languages": ["zh-Hans"],
                               "direction": "ltr", "placement": "above", "style": "navy"}
            else:
                req["background"] = {"mode": "transparent", "description": "transparent"}
                req["output"]["alpha"] = True
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                    self.validate(value, directory)

    def test_locked_expression_and_permitted_variation(self):
        value = self.assignment()
        value["images"][0]["expression"] = "smiling"
        with tempfile.TemporaryDirectory() as directory:
            self.validate(value, directory)
            config = value["scope"]["configurations"][0]
            config["requirements"]["expression"] = "calm"
            summary = manage.selection_summary(value, Path(directory) / "assignment.json")
            value["confirmation"]["summary_sha256"] = summary["summary_sha256"]
            with self.assertRaisesRegex(manage.RunError, "image differs from confirmed requirements"):
                self.validate(value, directory)

    def test_confirmed_scope_cannot_be_bypassed_by_expansion(self):
        for change in ("extra", "missing", "unselected", "configuration", "background"):
            value = self.assignment()
            if change == "extra":
                extra = copy.deepcopy(value["images"][0])
                extra["name"] = "extra"
                value["images"].append(extra)
                value["image_count"] = 2
                value["budget"]["run_candidates"] = 16
            elif change == "missing":
                value["images"] = []
                value["image_count"] = 0
            elif change == "unselected":
                value["images"][0]["proposal_choice"] = "B"
            elif change == "configuration":
                value["images"][0]["configuration_id"] = "unknown"
            else:
                value["images"][0]["background"]["description"] = "white"
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(manage.RunError):
                    self.validate(value, directory)

    def test_quantity_change_requires_new_summary_confirmation(self):
        value = self.assignment()
        value["selection"]["choices"][0]["count"] = 2
        value["scope"]["configurations"][0]["count"] = 2
        value["budget"]["run_candidates"] = 16
        extra = copy.deepcopy(value["images"][0])
        extra["name"] = "second_execution"
        value["images"].append(extra)
        value["image_count"] = 2
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                self.validate(value, directory)
            summary = manage.selection_summary(value, Path(directory) / "assignment.json")
            value["confirmation"]["summary_sha256"] = summary["summary_sha256"]
            self.assertEqual(self.validate(value, directory)["image_count"], 2)

    def test_over_24_approval_is_in_gate_two(self):
        value = self.assignment(4)
        value["budget"]["confirmed_over_24"] = False
        summary = manage.selection_summary(value, fixtures.SKILL_ROOT / "draft.json")
        self.assertIn("超过常规 24", manage.selection_markdown(summary))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "confirmed_over_24"):
                self.validate(value, directory)
            value["budget"]["confirmed_over_24"] = True
            self.assertEqual(self.validate(value, directory)["image_count"], 4)

    def test_frozen_run_rechecks_approval_even_with_updated_manifest_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            value = self.assignment()
            self.validate(value, directory)
            run = manage.cmd_init(argparse.Namespace(assignment=str(Path(directory) / "assignment.json"),
                                  root=str(Path(directory) / "runs"), effective_parallelism=1))["run_dir"]
            assignment_path = Path(run) / "assignment.json"
            frozen = manage.read_json(assignment_path)
            frozen["confirmation"]["status"] = "pending"
            manage.write_json(assignment_path, frozen)
            manifest_path = Path(run) / "manifest.json"
            manifest = manage.read_json(manifest_path)
            manifest["assignment_sha256"] = manage.sha256(assignment_path)
            manage.write_json(manifest_path, manifest)
            with self.assertRaisesRegex(manage.RunError, "Gate 2"):
                manage.load_run(run)

    def test_reference_paths_can_freeze_but_content_cannot_change(self):
        with tempfile.TemporaryDirectory() as directory:
            helper = fixtures.AssignmentTests()
            image = helper.image("reference_scene")
            reference = Path(directory) / "external.webp"
            shutil.copy2(helper.primary("semi-chibi"), reference)
            image["references"].append({"id": "pose", "path": str(reference),
                "roles": ["pose_action"], "instruction": "Use this pose"})
            value = fixtures.confirm_fixture(helper.assignment([image]))
            original = reference.read_bytes()
            shutil.copy2(helper.auxiliary("semi-chibi"), reference)
            with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                self.validate(value, directory)
            reference.write_bytes(original)
            self.validate(value, directory)
            run = manage.cmd_init(argparse.Namespace(assignment=str(Path(directory) / "assignment.json"),
                                  root=str(Path(directory) / "runs"), effective_parallelism=1))["run_dir"]
            reference.unlink()
            _, frozen, _ = manage.load_run(run)
            frozen_ref = frozen["scope"]["configurations"][0]["requirements"]["references"][1]
            self.assertTrue(Path(frozen_ref["path"]).is_relative_to(run))
            self.assertEqual(frozen["confirmation"]["summary_sha256"], value["confirmation"]["summary_sha256"])


if __name__ == "__main__":
    unittest.main()
