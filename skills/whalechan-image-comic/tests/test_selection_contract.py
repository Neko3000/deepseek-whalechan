"""Fixed candidate tournament and one informed execution confirmation."""
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

    def test_tournament_has_ten_candidates_and_all_45_unique_pairs(self):
        value = fixtures.assignment()
        results = manage.tournament_results(value)
        self.assertEqual([row["points"] for row in results], list(range(18, -1, -2)))
        self.assertEqual([row["idea_id"] for row in results[:5]], value["ranked_ideas"])
        for defect in ("missing", "duplicate", "self", "unknown", "winner", "pool"):
            broken = copy.deepcopy(value)
            if defect == "missing":
                broken["duels"].pop()
            elif defect == "duplicate":
                broken["duels"][-1] = copy.deepcopy(broken["duels"][0])
            elif defect == "self":
                broken["duels"][0]["b"] = broken["duels"][0]["a"]
            elif defect == "unknown":
                broken["duels"][0]["a"] = "unknown"
            elif defect == "winner":
                broken["duels"][0]["winner"] = "idea_10"
            else:
                broken["creative_pool"].pop()
            with self.subTest(defect=defect), self.assertRaises(manage.RunError):
                manage.tournament_results(broken)
        reordered = copy.deepcopy(value)
        reordered["creative_pool"].reverse()
        reordered["duels"].reverse()
        self.assertEqual(manage.tournament_results(reordered), results)
        # Arbitrary labels must not determine ranking or win counts.
        relabeled = copy.deepcopy(value)
        aliases = {idea["id"]: f"idea_{10 - index:02d}" for index, idea in enumerate(value["creative_pool"])}
        for idea in relabeled["creative_pool"]:
            idea["id"] = aliases[idea["id"]]
        for duel in relabeled["duels"]:
            for key in ("a", "b", "winner"):
                duel[key] = aliases[duel[key]]
        self.assertEqual([row["idea_id"] for row in manage.tournament_results(relabeled)],
                         [aliases[row["idea_id"]] for row in results])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            path.write_text(json.dumps(value))
            original = path.read_bytes()
            response = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), "rank-ideas",
                                       "--draft", str(path)], capture_output=True, text=True, check=True)
            self.assertEqual(json.loads(response.stdout)["ranked_ideas"], value["ranked_ideas"])
            self.assertEqual(path.read_bytes(), original)

    def test_draws_cycles_and_ties_have_explicit_order_independent_decisions(self):
        value = fixtures.assignment()
        for duel in value["duels"]:
            duel["winner"] = None
        with self.assertRaises(manage.RunError):
            manage.tournament_results(value)
        order = [idea["id"] for idea in reversed(value["creative_pool"])]
        value["tie_breaks"] = [{"ideas": order, "reason": "Reverse order has the stronger source-specific visual reveals."}]
        results = manage.tournament_results(value)
        self.assertEqual([row["idea_id"] for row in results], order)
        self.assertTrue(all(row["points"] == 9 for row in results))
        cyclic = fixtures.assignment()
        # The top three beat all others, then form a genuine three-way cycle.
        for duel in cyclic["duels"]:
            if duel["a"] == "idea_01" and duel["b"] == "idea_03":
                duel["winner"] = "idea_03"
        cyclic["tie_breaks"] = [{"ideas": ["idea_02", "idea_03", "idea_01"],
                                 "reason": "The exposed factory log lands most clearly; recognition is second."}]
        result = manage.tournament_results(cyclic)
        self.assertEqual([row["idea_id"] for row in result[:3]], ["idea_02", "idea_03", "idea_01"])
        cyclic["creative_pool"].reverse()
        cyclic["duels"].reverse()
        self.assertEqual(manage.tournament_results(cyclic), result)

    def test_five_distinct_winners_each_have_one_image_and_three_panel_counts(self):
        normalized = self.validate(fixtures.assignment())
        self.assertEqual(len(normalized["images"]), 5)
        self.assertEqual(normalized["budget"]["maximum_total"], 15)
        self.assertEqual({image["panel_count"] for image in normalized["images"]}, {1, 2, 4})
        for defect in ("duplicate-idea", "missing-image", "wrong-winner", "uniform-panels", "changed-scene", "changed-twist"):
            value = fixtures.assignment()
            if defect == "duplicate-idea":
                value["images"][1]["idea_id"] = value["images"][0]["idea_id"]
            elif defect == "missing-image":
                value["images"].pop()
            elif defect == "wrong-winner":
                value["ranked_ideas"][-1] = "idea_06"
            elif defect == "changed-scene":
                value["proposal"]["options"][0]["scene"] = "An unrelated courtroom replaces the factory"
            elif defect == "changed-twist":
                value["proposal"]["options"][0]["twist"] = "A different payoff replaces the tournament winner"
            else:
                self.uniform_panels(value)
            with self.subTest(defect=defect), self.assertRaises(manage.RunError):
                self.validate(fixtures.confirm_fixture_plan(value))
        override = fixtures.assignment()
        self.uniform_panels(override)
        override["panel_policy"] = {"mode": "user-override", "user_instruction": "Use one panel for all five images."}
        self.validate(fixtures.confirm_fixture_plan(override))

    @staticmethod
    def uniform_panels(value):
        for option, image in zip(value["proposal"]["options"], value["images"]):
            option["panel_count"] = 1
            image.update(panel_count=1, layout="single")
            for key in ("action_plan", "expression_plan"):
                image[key] = image[key][:1]
            for line in image["dialogue_plan"]:
                line["panel"] = 1

    def test_confirmation_binds_content_counts_panel_policy_and_workers(self):
        mutations = (
            lambda v: v["proposal"]["options"][0].update(key_lines=["Changed words"]),
            lambda v: v["proposal"]["options"][0].update(staging="Different dramatic action"),
            lambda v: v["images"].pop(),
            lambda v: v["worker_plan"]["workers"][0].update(id="replacement-worker"),
            lambda v: v.update(panel_policy={"mode": "user-override", "user_instruction": "Use any count"}),
        )
        for mutate in mutations:
            value = fixtures.assignment()
            before = value["confirmation"]["summary_sha256"]
            mutate(value)
            with self.subTest(mutation=mutate):
                try:
                    after = manage.selection_summary(value)["summary_sha256"]
                except manage.RunError:
                    pass
                else:
                    self.assertNotEqual(before, after)
                with self.assertRaises(manage.RunError):
                    self.validate(value)
        for defect in ("duplicate", "empty", "unknown", "excess-capacity", "mismatched-capacity"):
            broken = fixtures.assignment()
            if defect == "duplicate":
                broken["worker_plan"]["workers"][0]["idea_ids"].append("idea_02")
            elif defect == "empty":
                broken["worker_plan"]["workers"][0]["idea_ids"] = []
            elif defect == "unknown":
                broken["worker_plan"]["workers"][0]["idea_ids"][0] = "idea_10"
            elif defect == "excess-capacity":
                broken["worker_plan"]["max_parallelism"] = 6
            else:
                broken["execution"]["requested_parallelism"] = 1
            with self.subTest(worker_defect=defect), self.assertRaises(manage.RunError):
                self.validate(fixtures.confirm_fixture_plan(broken))

    def test_single_gate_is_informed_and_blocks_generation_until_confirmed(self):
        value = fixtures.assignment()
        self.assertNotIn("selection", value)
        summary = manage.selection_summary(value)
        table = manage.selection_markdown(summary)
        self.assertEqual((summary["proposal_count"], summary["image_count"]), (5, 5))
        for text in ("worker-1", "worker-2", "worker-3", "15", "确认"):
            self.assertIn(text, table)
        self.assertNotIn("你想生成哪些方案", table)
        self.assertNotIn("推荐程度", table)
        self.assertNotIn("全选共 25", table)
        draft = copy.deepcopy(value)
        images = draft.pop("images")
        draft.pop("confirmation")
        draft_summary = manage.selection_summary(draft)
        self.assertIn("worker-1", manage.selection_markdown(draft_summary))
        self.assertEqual(draft_summary["summary_sha256"], summary["summary_sha256"])
        fixtures.confirm_fixture_plan(draft)
        draft["images"] = images
        normalized = self.validate(draft)
        self.assertEqual(manage.selection_summary(normalized)["summary_sha256"], draft_summary["summary_sha256"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "draft.json"
            for confirmation in (None, {"status": "pending"}):
                pending = copy.deepcopy(value)
                pending.pop("confirmation")
                if confirmation:
                    pending["confirmation"] = confirmation
                path.write_text(json.dumps(pending), encoding="utf-8")
                with self.subTest(confirmation=confirmation):
                    with self.assertRaises(builder.manage.RunError):
                        builder.build_prompt(pending, pending["images"][0])
                    result = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), "init",
                                             "--assignment", str(path), "--root", str(Path(directory) / "runs")],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(list(Path(directory).iterdir()), [path])
            rendered = manage.cmd_render_proposal(argparse.Namespace(draft=str(path)))
            self.assertIn("worker-1", rendered["markdown"])
            self.assertEqual(manage.cmd_summarize_selection(argparse.Namespace(draft=str(path)))["image_count"], 5)
            self.assertEqual(json.loads(path.read_text())["confirmation"]["status"], "pending")


if __name__ == "__main__":
    unittest.main()
