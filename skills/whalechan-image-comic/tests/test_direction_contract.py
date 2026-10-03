"""Direction carriers remain explicit; stylistic preferences do not eliminate candidates."""
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


def set_direction(value, index, direction, carrier, is_native=False):
    option = value["proposal"]["options"][index]
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
        value = self.validate(fixtures.assignment())
        self.assertEqual({idea["direction"] for idea in value["creative_pool"]}, set(manage.DIRECTION_CARRIERS))
        self.assertTrue(all("reversal" not in idea for idea in value["creative_pool"] if idea["direction"] != "reversal"))
        for direction, fields in manage.DIRECTION_CARRIERS.items():
            for field in fields:
                broken = fixtures.assignment()
                next(item for item in broken["creative_pool"] if item["direction"] == direction).pop(field)
                with self.subTest(direction=direction, field=field), self.assertRaisesRegex(manage.RunError, field):
                    self.validate(broken)
        short = fixtures.assignment()
        next(item for item in short["creative_pool"] if item["direction"] == "escalation")["steps"].pop()
        with self.assertRaisesRegex(manage.RunError, "at least 3"):
            self.validate(short)

    def test_native_and_character_preferences_do_not_override_tournament(self):
        value = fixtures.assignment()
        set_direction(value, 0, "character", {"trait": "rice", "trigger": "comma hunt"})
        set_direction(value, 1, "character", {"trait": "self interest", "trigger": "unpaid work"})
        # Three character winners and no native winner remain legitimate tournament results.
        normalized = self.validate(fixtures.confirm_fixture_plan(value))
        self.assertEqual(normalized["ranked_ideas"], value["ranked_ideas"])
        self.assertNotIn("gate", normalized["creative_pool"][0])
        for field in ("gate", "gate_reason", "rejection_reason"):
            broken = fixtures.assignment()
            broken["creative_pool"][0][field] = "PASS"
            with self.subTest(field=field), self.assertRaises(manage.RunError):
                self.validate(broken)

    def test_direction_concentration_and_rhythm_are_review_signals(self):
        value = fixtures.assignment()
        for index in (1, 2, 3):
            set_direction(value, index, "reversal", {"expectation": "a fix", "reversal": "a factory"}, is_native=True)
        self.validate(fixtures.confirm_fixture_plan(value))
        rhythmic = fixtures.assignment()
        for bad in ({"type": "drumroll", "panel": 1, "reason": "x"},
                    {"type": "triple", "panel": 9, "reason": "x"}, {"type": "triple", "panel": 1}):
            broken = copy.deepcopy(rhythmic)
            broken["images"][0]["rhythm"] = bad
            with self.subTest(rhythm=bad), self.assertRaises(manage.RunError):
                self.validate(fixtures.confirm_fixture_plan(broken))
        rhythmic["images"][0]["rhythm"] = {"type": "triple", "panel": 1,
                                            "reason": "The repeated reply builds the source's joke."}
        normalized = self.validate(fixtures.confirm_fixture_plan(rhythmic))
        self.assertEqual(manage.design_summary([normalized])["rhythm_images"], 1)
        prompt = builder.build_prompt(normalized, normalized["images"][0])
        self.assertIn("COMEDY DIRECTION: reversal", prompt)
        self.assertIn("RHYTHM: triple, landing in panel 1", prompt)
        self.assertIn("final beat deviate", prompt)
        self.assertNotIn("RHYTHM:", builder.build_prompt(normalized, normalized["images"][1]))


if __name__ == "__main__":
    unittest.main()
