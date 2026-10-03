"""Seven core selection and consent contracts; replies are synthetic fixtures."""
import copy
import json
import subprocess
import sys
import unittest

import helpers as fixtures

manage = fixtures.manage_run


class SelectionContractTests(fixtures.FixtureCase):
    def test_both_gates_are_required_before_initialization(self):
        for missing in ("selection", "confirmation"):
            value = self.assignment()
            value.pop(missing)
            with self.subTest(missing=missing), self.assertRaisesRegex(manage.RunError, f"missing required fields: {missing}"):
                self.initialize(value)
            self.assertFalse((self.root / "runs").exists())
        old = self.assignment()
        old["schema_version"] = 4
        with self.assertRaisesRegex(manage.RunError, "schema_version must be 6"):
            self.initialize(old)
        self.assertFalse((self.root / "runs").exists())

    def test_changed_proposal_invalidates_gate_one(self):
        value = self.assignment()
        value["proposal"]["options"][0]["scene"] = "A different scene"
        with self.assertRaisesRegex(manage.RunError, "repeat Gate 1"):
            self.validate(value)

    def test_changed_scope_invalidates_gate_two(self):
        changes = {
            "background": lambda v: v["scope"]["configurations"][0]["requirements"]["background"].update(description="white"),
            "reference permissions": lambda v: v["scope"]["configurations"][0]["requirements"]["references"][0].update(instruction="Identity only"),
            "budget": lambda v: v["budget"].update(per_provider_candidates=1),
        }
        for label, mutate in changes.items():
            value = self.assignment()
            mutate(value)
            with self.subTest(label=label), self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
                self.validate(value)
        value = self.assignment()
        value["selection"]["choices"][0]["count"] = 2
        value["scope"]["configurations"][0]["count"] = 2
        value["budget"]["run_candidates"] = 16
        extra = copy.deepcopy(value["images"][0])
        extra["name"] = "second"
        value["images"].append(extra)
        value["image_count"] = 2
        with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is stale"):
            self.validate(value)
        summary = manage.selection_summary(value, self.root / "assignment.json")
        value["confirmation"]["summary_sha256"] = summary["summary_sha256"]
        self.assertEqual(self.validate(value)["image_count"], 2)

    def test_expansion_matches_confirmed_counts_choices_and_locks(self):
        base = self.assignment(count=2)
        # Approve spare run capacity first, so extra images reach the count check.
        base["budget"]["run_candidates"] = 24
        base["scope"]["configurations"][0]["variation"] = "May vary expression"
        summary = manage.selection_summary(base, self.root / "assignment.json")
        base["confirmation"]["summary_sha256"] = summary["summary_sha256"]
        base["images"][0]["expression"] = "smiling"
        self.validate(base)
        for defect in ("extra", "missing", "choice", "configuration", "background"):
            value = copy.deepcopy(base)
            expected = "images must match confirmed configuration counts"
            if defect == "extra":
                extra = copy.deepcopy(value["images"][0])
                extra["name"] = "extra"
                value["images"].append(extra)
            elif defect == "missing":
                value["images"].pop()
            elif defect == "choice":
                value["images"][0]["proposal_choice"] = "B"
                expected = "proposal_choice must match"
            elif defect == "configuration":
                value["images"][0]["configuration_id"] = "unknown"
            else:
                value["images"][0]["background"]["description"] = "white"
                expected = "image differs from confirmed requirements"
            value["image_count"] = len(value["images"])
            with self.subTest(defect=defect), self.assertRaisesRegex(manage.RunError, expected):
                self.validate(value)
        locked = copy.deepcopy(base)
        locked["scope"]["configurations"][0]["requirements"]["expression"] = "calm"
        summary = manage.selection_summary(locked, self.root / "assignment.json")
        locked["confirmation"]["summary_sha256"] = summary["summary_sha256"]
        with self.assertRaisesRegex(manage.RunError, "image differs from confirmed requirements"):
            self.validate(locked)

    def test_frozen_run_rechecks_consent_after_manifest_hash_update(self):
        run = self.initialize()
        path = run / "assignment.json"
        frozen = manage.read_json(path)
        frozen["confirmation"]["status"] = "pending"
        manage.write_json(path, frozen)
        manifest = manage.read_json(run / "manifest.json")
        manifest["assignment_sha256"] = manage.sha256(path)
        manage.write_json(run / "manifest.json", manifest)
        with self.assertRaisesRegex(manage.RunError, "Gate 2 confirmation is required"):
            manage.load_run(str(run))

    def test_proposal_modes_and_selected_quantities(self):
        value = self.assignment(count=5)
        value["proposal"]["mode"] = "explore"
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        for row in value["selection"]["choices"]:
            row.pop("count")
        summary = manage.selection_summary(value, self.root / "draft.json")
        self.assertEqual((summary["proposal_count"], summary["image_count"]), (5, 5))
        value["proposal"]["options"].pop()
        with self.assertRaisesRegex(manage.RunError, "five ordered"):
            manage.proposal_markdown(value["proposal"])
        self.assertEqual(len(manage.proposal_options(self.assignment()["proposal"])), 1)
        value = self.assignment(count=2)
        value["selection"]["choices"] = [{"choice": "A", "count": 2}]
        value["scope"]["configurations"][1]["choice"] = "A"
        value["images"][1]["proposal_choice"] = "A"
        summary = manage.selection_summary(value, self.root / "draft.json")
        self.assertEqual((summary["proposal_count"], summary["image_count"]), (1, 2))
        value["confirmation"]["summary_sha256"] = summary["summary_sha256"]
        self.validate(value)
        value["selection"]["choices"][0]["count"] = 0
        with self.assertRaisesRegex(manage.RunError, "positive integer"):
            manage.selection_summary(value, self.root / "draft.json")

    def test_gate_cli_renders_read_only_drafts_without_images(self):
        value = self.assignment()
        value.pop("images")
        value.pop("confirmation")
        value["proposal"]["options"][0]["title"] = "Title|line\nnext"
        value["selection"]["proposal_sha256"] = manage.contract_hash(value["proposal"])
        path = self.root / "draft.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        before = path.read_bytes()
        for command in ("render-proposal", "summarize-selection"):
            result = subprocess.run([sys.executable, "-B", str(fixtures.MODULE_PATH), command,
                                     "--draft", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Title\\|line<br>next", json.loads(result.stdout)["markdown"])
            self.assertEqual(before, path.read_bytes())
            self.assertEqual(list(self.root.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
