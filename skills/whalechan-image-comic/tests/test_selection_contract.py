"""Two user gates and variable run sizes; replies/QA here are synthetic fixtures."""
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
spec = importlib.util.spec_from_file_location("selection_prompt", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def selected_assignment(choices):
    value = fixtures.assignment()
    template = copy.deepcopy(value["images"][0])
    options = {item["choice"]: item for item in value["proposal"]["options"]}
    value["images"] = []
    value["ranked_ideas"] = []
    for selection in choices:
        option = options[selection["choice"]]
        value["ranked_ideas"].append(option["idea_id"])
        for number in range(1, selection.get("count", 5) + 1):
            image = copy.deepcopy(template)
            image.pop("source_rank")
            image.update(name=f"{selection['choice'].lower()}_{number}",
                         idea_id=option["idea_id"], premise=option["premise"], execution=number,
                         execution_note=f"Consequence {selection['choice']} {number}")
            value["images"].append(image)
    return fixtures.confirm_fixture_selection(value, choices)


class SelectionTests(unittest.TestCase):
    def validate(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return manage.validate_assignment(path)

    def test_counts_and_budget_follow_selection(self):
        cases = [([{"choice": "A"}], 5), ([{"choice": "A"}, {"choice": "C"}], 10),
                 ([{"choice": ch} for ch in "ABCDE"], 25),
                 ([{"choice": ch, "count": 1} for ch in "ABCDE"], 5),
                 ([{"choice": "A", "count": 2}, {"choice": "C", "count": 1}], 3)]
        for choices, total in cases:
            with self.subTest(choices=choices):
                value = self.validate(selected_assignment(choices))
                self.assertEqual(len(value["images"]), total)
                self.assertEqual(value["budget"]["maximum_total"], total * 3)
                self.assertEqual(manage.selection_summary(value)["proposal_count"], len(choices))

    def test_gate_one_never_authorizes_generation(self):
        value = selected_assignment([{"choice": "A", "count": 1}])
        normalized = self.validate(value)
        for missing in ("selection", "confirmation"):
            invalid = copy.deepcopy(normalized)
            invalid.pop(missing)
            with self.subTest(missing=missing), self.assertRaises(manage.RunError):
                self.validate(invalid)
            with self.assertRaises(builder.manage.RunError):
                builder.build_prompt(invalid, invalid["images"][0])
        for confirmation in (None, True, {"status": "pending"}, {"status": "confirmed"}):
            value["confirmation"] = confirmation
            with self.subTest(confirmation=confirmation), self.assertRaises(manage.RunError):
                self.validate(value)

    def test_changed_selection_or_content_invalidates_confirmation(self):
        for mutate in (
            lambda v: v["selection"]["choices"][0].update(count=2),
            lambda v: v["selection"]["choices"][0].update(choice="B"),
            lambda v: v["selection"]["adjustments"].append("Change the last line to 明天再说。"),
        ):
            value = selected_assignment([{"choice": "A", "count": 1}])
            mutate(value)
            with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                self.validate(value)
        value = selected_assignment([{"choice": "A", "count": 1}])
        value["proposal"]["options"][0]["key_lines"] = ["Changed wording"]
        with self.assertRaisesRegex(manage.RunError, "repeat Gate 1"):
            self.validate(value)
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
            self.validate(value)

    def test_task_counts_and_selected_ideas_cannot_drift(self):
        for change in ("missing", "extra", "unselected"):
            value = selected_assignment([{"choice": "A", "count": 2}])
            if change == "missing":
                value["images"].pop()
            elif change == "extra":
                extra = copy.deepcopy(value["images"][0])
                extra.update(name="extra", execution=3, execution_note="Extra consequence")
                value["images"].append(extra)
            else:
                value["ranked_ideas"].append("idea_02")
            with self.subTest(change=change), self.assertRaisesRegex(manage.RunError, "confirmed counts|user-selected"):
                self.validate(value)

    def test_bad_choices_counts_and_replies_are_rejected(self):
        for choices in ([], [{"choice": "F"}], [{"choice": "A"}] * 2,
                        *[[{"choice": "A", "count": count}] for count in (0, -1, True, 1.5, "5")]):
            value = fixtures.assignment()
            value["selection"]["choices"] = choices
            with self.subTest(choices=choices), self.assertRaises(manage.RunError):
                manage.selection_summary(value)
        for field in ("selection", "confirmation"):
            value = fixtures.assignment()
            value[field]["user_reply"] = " "
            with self.subTest(field=field), self.assertRaisesRegex(manage.RunError, "user_reply"):
                self.validate(value)

    def test_five_proposals_must_link_to_passing_ideas(self):
        for change in ("four", "duplicate", "failed", "premise", "rating"):
            value = fixtures.assignment()
            if change == "four":
                value["proposal"]["options"].pop()
            elif change == "duplicate":
                value["proposal"]["options"][4]["idea_id"] = "idea_01"
            elif change == "failed":
                value["creative_pool"][4].update(gate="FAIL", rejection_reason="Flat")
            elif change == "premise":
                value["creative_pool"][4]["premise"] = "Other premise"
            else:
                value["proposal"]["options"][0]["rating"] = True
            with self.subTest(change=change), self.assertRaises(manage.RunError):
                self.validate(value)

    def test_rendered_table_and_second_gate_summary(self):
        value = selected_assignment([{"choice": "A"}, {"choice": "C"}])
        table = manage.proposal_markdown(value["proposal"])
        rows = [line for line in table.splitlines() if line.startswith("|")]
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(len(row.split("|")) == 9 for row in rows))
        self.assertIn("推荐程度与理由", rows[0])
        self.assertGreater(table.index("你想生成哪些方案"), table.index("| E |"))
        self.assertIn("全选共 25 张", table)
        summary = manage.selection_summary(value)
        rendered = manage.selection_markdown(summary)
        self.assertIn("2 个方案，共 10 张图片", rendered)
        self.assertIn("**C｜Proposal C**：5 张", rendered)
        self.assertIn("确认按以上方案和数量开始生成吗", rendered)
        value["proposal"]["options"][0]["title"] = "A|B\nC"
        self.assertIn("A\\|B<br>C", manage.proposal_markdown(value["proposal"]))

    def test_cli_gates_do_not_create_runs_or_synthesize_confirmation(self):
        value = selected_assignment([{"choice": "A"}])
        value.pop("confirmation")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            before = path.read_bytes()
            for command in ("render-proposal", "summarize-selection"):
                result = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), command,
                                         "--draft", str(path)], capture_output=True, text=True, check=True)
                self.assertIn("markdown", json.loads(result.stdout))
            initialized = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), "init",
                                          "--assignment", str(path), "--root", str(Path(directory) / "runs")],
                                         capture_output=True, text=True)
            self.assertEqual(initialized.returncode, 2)
            self.assertIn("Gate 2", initialized.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [path])
            self.assertEqual(path.read_bytes(), before)

    def test_current_prompt_and_audit_keep_approved_proposal(self):
        value = selected_assignment([{"choice": "C", "count": 1}])
        value["selection"]["adjustments"] = ["Keep the user's face offscreen"]
        value["confirmation"]["summary_sha256"] = manage.selection_summary(value)["summary_sha256"]
        normalized = self.validate(value)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        self.assertIn("USER-SELECTED PROPOSAL", prompt)
        self.assertIn("Proposal C", prompt)
        self.assertIn("Keep the user's face offscreen", prompt)
        record = manage.creative_markdown(normalized)
        self.assertIn("Synthetic Gate 2 confirmation", record)
        self.assertIn("1 个方案，共 1 张图片", record)
        unselected = copy.deepcopy(normalized["images"][0])
        unselected["idea_id"] = "idea_01"
        with self.assertRaisesRegex(builder.manage.RunError, "belong to the confirmed"):
            builder.build_prompt(normalized, unselected)


class VariableRunTests(unittest.TestCase):
    files = fixtures.RunStateTests.files

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.magick = fixtures.shutil.which("magick")
        if self.magick is None:
            self.skipTest("ImageMagick is required")

    def initialize(self, choices):
        root = Path(self.temporary.name)
        path = root / "assignment.json"
        path.write_text(json.dumps(selected_assignment(choices)), encoding="utf-8")
        result = manage.cmd_init(argparse.Namespace(assignment=str(path), root=str(root), effective_parallelism=1))
        self.run_dir = Path(result["run_dir"])
        frozen = manage.read_json(self.run_dir / "assignment.json")
        self.image_spec = frozen["images"][0]
        self.image = self.image_spec["id"]
        return frozen

    def test_single_image_can_promote_and_finalize(self):
        self.initialize([{"choice": "C", "count": 1}])
        manage.record_image(self.files(1, "PASS"), component=False)
        manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=False))
        self.assertEqual((result["status"], result["passed"], result["expected"]), ("complete", 1, 1))
        self.assertEqual(result["proposals"][0]["choice"], "C")
        self.assertEqual(result["proposals"][0]["missing"], [])
        self.assertEqual(len(result["proposals"][0]["final_paths"]), 1)

    def test_partial_reports_missing_images_by_proposal(self):
        frozen = self.initialize([{"choice": "A", "count": 1}, {"choice": "C", "count": 2}])
        manage.record_image(self.files(1, "PASS"), component=False)
        manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        with self.assertRaisesRegex(manage.RunError, "viable attempt"):
            manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        for image in frozen["images"][1:]:
            for provider in manage.PROVIDERS:
                manage.cmd_record_error(argparse.Namespace(run_dir=str(self.run_dir), image=image["id"],
                                                            provider=provider, model="test", category="unavailable", details="offline test"))
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        self.assertEqual((result["status"], result["passed"], result["expected"]), ("partial", 1, 3))
        self.assertEqual(len(result["proposals"][1]["missing"]), 2)

    def test_ten_images_finalize_with_five_results_in_each_proposal(self):
        frozen = self.initialize([{"choice": "A"}, {"choice": "C"}])
        for number, image in enumerate(frozen["images"], 1):
            self.image_spec = image
            self.image = image["id"]
            manage.record_image(self.files(number, "PASS"), component=False)
            manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=False))
        self.assertEqual((result["status"], result["passed"], result["expected"]), ("complete", 10, 10))
        self.assertEqual([len(item["final_paths"]) for item in result["proposals"]], [5, 5])
        self.assertTrue(all(not item["missing"] for item in result["proposals"]))

    def test_frozen_run_rechecks_gate_two_even_with_updated_file_hash(self):
        frozen = self.initialize([{"choice": "A"}, {"choice": "C"}])
        self.assertEqual(len(frozen["images"]), 10)
        frozen["confirmation"]["status"] = "pending"
        manage.write_json(self.run_dir / "assignment.json", frozen)
        manifest = manage.read_json(self.run_dir / "manifest.json")
        manifest["assignment_sha256"] = manage.sha256(self.run_dir / "assignment.json")
        manage.write_json(self.run_dir / "manifest.json", manifest)
        with self.assertRaisesRegex(manage.RunError, "Gate 2"):
            manage.load_run(str(self.run_dir))


if __name__ == "__main__":
    unittest.main()
