"""Two core pixel-output contracts, using real ImageMagick images."""
import importlib.util
import unittest

import helpers as fixtures

spec = importlib.util.spec_from_file_location("validate_image", fixtures.SKILL_ROOT / "scripts/validate-image.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ImageValidationTests(fixtures.FixtureCase):
    def test_native_and_exact_geometry_have_different_acceptance_rules(self):
        square = self.png("square.png", size="64x64")
        self.assertEqual(validator.validate(square)["overall"], "PASS")
        self.assertEqual(validator.validate(square, resolution_mode="exact", width=64, height=64)["overall"], "PASS")
        self.assertEqual(validator.validate(square, resolution_mode="exact", width=128, height=128)["gates"]["T1"]["verdict"], "FAIL")
        rectangle = self.png("rectangle.png", size="64x32")
        self.assertEqual(validator.validate(rectangle)["gates"]["T1"]["verdict"], "FAIL")

    def test_alpha_policy_requires_meaningful_transparency(self):
        cases = (("transparent", "none", True, "required", "PASS"),
                 ("no-alpha", "red", False, "required", "FAIL"),
                 ("nearly-opaque", "rgba(255,0,0,0.988)", True, "required", "FAIL"),
                 ("forbidden", "none", True, "forbidden", "FAIL"))
        for name, color, alpha, policy, expected in cases:
            with self.subTest(case=name):
                image = self.png(f"{name}.png", color=color, alpha=alpha)
                self.assertEqual(validator.validate(image, alpha=policy)["gates"]["T2"]["verdict"], expected)


if __name__ == "__main__":
    unittest.main()
