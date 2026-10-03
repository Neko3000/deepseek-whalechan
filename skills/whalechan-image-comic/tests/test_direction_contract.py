"""Comedy directions, native-direction coverage, the character-gag cap and soft warnings."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import test_manage_run as fixtures

manage = fixtures.manage
spec = importlib.util.spec_from_file_location("direction_prompt", fixtures.SKILL_ROOT / "scripts/build-prompt.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def reconfirm(value):
    choices = value["selection"]["choices"]
    return fixtures.confirm_fixture_selection(value, choices)


def set_direction(value, choice, direction, carrier, is_native=False):
    option = next(item for item in value["proposal"]["options"] if item["choice"] == choice)
    idea = next(item for item in value["creative_pool"] if item["id"] == option["idea_id"])
    for field in ("expectation", "reversal", "surface", "truth", "exposure", "steps", "situation", "recognition", "trait", "trigger"):
        idea.pop(field, None)
    idea.update(direction=direction, **carrier)
    option.update(direction=direction, is_native=is_native)


class DirectionTests(unittest.TestCase):
    def validate(self, value):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            return manage.validate_assignment(path)

    def test_each_direction_requires_only_its_own_carrier(self):
        value = self.validate(fixtures.selected_assignment([{"choice": ch, "count": 1} for ch in "ABCDE"]))
        directions = {idea["direction"] for idea in value["creative_pool"]}
        self.assertEqual(directions, set(manage.DIRECTION_CARRIERS))
        self.assertTrue(all("reversal" not in idea for idea in value["creative_pool"] if idea["direction"] != "reversal"))
        self.assertNotIn("expectation", value["input"]["source_analysis"])
        for direction, fields in manage.DIRECTION_CARRIERS.items():
            for field in fields:
                broken = fixtures.selected_assignment([{"choice": "A", "count": 1}])
                idea = next(item for item in broken["creative_pool"] if item["direction"] == direction)
                idea.pop(field)
                with self.subTest(direction=direction, field=field), self.assertRaisesRegex(manage.RunError, field):
                    self.validate(broken)
        short = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        next(item for item in short["creative_pool"] if item["direction"] == "escalation")["steps"].pop()
        with self.assertRaisesRegex(manage.RunError, "at least 3"):
            self.validate(short)
        unknown = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        unknown["creative_pool"][0]["direction"] = "slapstick"
        with self.assertRaisesRegex(manage.RunError, "direction must be one of"):
            self.validate(unknown)

    def test_native_direction_coverage_and_character_cap(self):
        base = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        cases = {
            "no native proposal": (lambda v: v["proposal"]["options"][0].update(is_native=False), "native direction"),
            "wrong native label": (lambda v: v["proposal"]["options"][1].update(is_native=True), "marked native"),
            "two character gags": (lambda v: set_direction(v, "B", "character", {"trait": "rice", "trigger": "comma hunt"}), "pure character gag"),
            "option/idea mismatch": (lambda v: v["proposal"]["options"][1].update(direction="recognition"), "match its idea"),
        }
        for name, (mutate, message) in cases.items():
            value = copy.deepcopy(base)
            mutate(value)
            with self.subTest(case=name), self.assertRaisesRegex(manage.RunError, message):
                self.validate(reconfirm(value))
        mismatch = copy.deepcopy(base)
        mismatch["input"]["source_analysis"]["native_direction"]["direction"] = "exposure"
        with self.assertRaisesRegex(manage.RunError, "must match input.source_analysis"):
            self.validate(mismatch)
        # A source with no inherent joke frees every proposal, but none may claim to be native.
        free = copy.deepcopy(base)
        for native in (free["proposal"]["native_direction"], free["input"]["source_analysis"]["native_direction"]):
            native.update(direction=None, reason="A plain permission; the joke is entirely Whale-chan's.")
        free["proposal"]["options"][0]["is_native"] = False
        self.assertNotIn("（原）", manage.proposal_markdown(self.validate(reconfirm(free))["proposal"]))
        free["proposal"]["options"][0]["is_native"] = True
        with self.assertRaisesRegex(manage.RunError, "marked native"):
            self.validate(reconfirm(free))

    def test_soft_warnings_need_a_written_disposition(self):
        value = fixtures.selected_assignment([{"choice": "A", "count": 1}])
        for choice in "BCD":
            set_direction(value, choice, "reversal", {"expectation": "a fix", "reversal": "a factory"})
        with self.assertRaisesRegex(manage.RunError, "4 of 5 proposals use direction reversal"):
            self.validate(reconfirm(value))
        value["proposal"]["warning_dispositions"] = [{"code": "same_direction", "reason": "Every proposal stays on the source's literal hinge."}]
        self.validate(reconfirm(value))

        rhythmic = fixtures.selected_assignment([{"choice": "A", "count": 2}])
        for bad in ({"type": "drumroll", "panel": 1, "reason": "x"}, {"type": "triple", "panel": 9, "reason": "x"},
                    {"type": "triple", "panel": 1}):
            broken = copy.deepcopy(rhythmic)
            broken["images"][0]["rhythm"] = bad
            with self.subTest(rhythm=bad), self.assertRaisesRegex(manage.RunError, "rhythm"):
                self.validate(broken)
        rhythmic["images"][0]["rhythm"] = {"type": "triple", "panel": 1, "reason": "The repeated identical reply is the source's joke."}
        rhythmic["images"][1]["rhythm"] = {"type": "deadpan", "panel": 1, "reason": "The flat delivery lands the verdict."}
        with self.assertRaisesRegex(manage.RunError, "2 of 2 images declare a rhythm layer"):
            self.validate(rhythmic)
        rhythmic["images"][1]["rhythm"] = None
        normalized = self.validate(rhythmic)
        self.assertEqual(manage.design_summary([normalized])["rhythm_images"], 1)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        self.assertIn("COMEDY DIRECTION: reversal", prompt)
        self.assertIn("RHYTHM: triple, landing in panel 1", prompt)
        self.assertIn("final beat deviate", prompt)
        self.assertNotIn("RHYTHM:", builder.build_prompt(normalized, normalized["images"][1]))


if __name__ == "__main__":
    unittest.main()
