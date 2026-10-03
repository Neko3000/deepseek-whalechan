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
                value = self.validate(fixtures.selected_assignment(choices))
                self.assertEqual(len(value["images"]), total)
                self.assertEqual(value["budget"]["maximum_total"], total * 3)
                self.assertEqual(manage.selection_summary(value)["proposal_count"], len(choices))

    def test_changed_selection_or_content_invalidates_confirmation(self):
        for mutate in (
            lambda v: v["selection"]["choices"][0].update(count=2),
            lambda v: v["selection"]["choices"][0].update(choice="B"),
            lambda v: v["selection"]["adjustments"].append("Change the last line to 明天再说。"),
        ):
            value = fixtures.selected_assignment([{"choice": "A", "count": 1}])
            mutate(value)
            with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                self.validate(value)
        value = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        value["proposal"]["options"][0]["key_lines"] = ["Changed wording"]
        with self.assertRaisesRegex(manage.RunError, "repeat Gate 1"):
            self.validate(value)
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
            self.validate(value)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(fixtures.selected_assignment([{"choice": "A", "count": 1}])))
            result = manage.cmd_init(argparse.Namespace(assignment=str(path), root=directory, effective_parallelism=1))
            run = Path(result["run_dir"])
            frozen = manage.read_json(run / "assignment.json")
            frozen["confirmation"]["status"] = "pending"
            manage.write_json(run / "assignment.json", frozen)
            manifest = manage.read_json(run / "manifest.json")
            manifest["assignment_sha256"] = manage.sha256(run / "assignment.json")
            manage.write_json(run / "manifest.json", manifest)
            with self.assertRaisesRegex(manage.RunError, "Gate 2"):
                manage.load_run(str(run))

    def test_task_counts_and_selected_ideas_cannot_drift(self):
        for change in ("missing", "extra", "unselected"):
            value = fixtures.selected_assignment([{"choice": "A", "count": 2}])
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

    def test_rendered_table_and_second_gate_summary(self):
        value = fixtures.selected_assignment([{"choice": "A"}, {"choice": "C"}])
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

    def test_both_user_gates_are_required_before_generation(self):
        approved = self.validate(fixtures.selected_assignment([{"choice": "A", "count": 1}]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            for missing in ("selection", "confirmation"):
                value = copy.deepcopy(approved)
                value.pop(missing)
                path.write_text(json.dumps(value), encoding="utf-8")
                with self.subTest(missing=missing):
                    with self.assertRaises(builder.manage.RunError):
                        builder.build_prompt(value, value["images"][0])
                    result = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), "init",
                                             "--assignment", str(path), "--root", str(Path(directory) / "runs")],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("Gate", result.stderr)
                    self.assertEqual(list(Path(directory).iterdir()), [path])
            summary = manage.cmd_summarize_selection(argparse.Namespace(draft=str(path)))
            self.assertEqual(summary["image_count"], 1)
            self.assertNotIn("confirmation", json.loads(path.read_text()))


if __name__ == "__main__":
    unittest.main()
