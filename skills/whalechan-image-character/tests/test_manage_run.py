from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "manage-run.py"
SPEC = importlib.util.spec_from_file_location("whalechan_manage_run", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
manage_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_run)
CATALOG, CATALOG_SHA256 = manage_run.load_catalog()


def visual_qa(form: str, ratio: float, counterpart: str | None = None, counterpart_form: str | None = None) -> dict:
    head_height = 100.0
    body_height = (ratio - 1.0) * head_height
    segment_height = body_height / 3.0
    profile = CATALOG["forms"][form]
    visual = {
        "verdict": "PASS",
        "candidate_sha256": "a" * 64,
        "gates": {gate: "PASS" for gate in manage_run.REQUIRED_VISUAL_GATES},
        "form_evidence": {
            "measurement_method": "pose-neutralized-skeleton",
            "head_axis": {"top": [0, 0], "chin": [0, head_height]},
            "body_segments": [
                {"name": "chin_to_pelvis", "start": [0, head_height], "end": [0, head_height + segment_height]},
                {"name": "pelvis_to_knee", "start": [0, head_height + segment_height], "end": [0, head_height + 2 * segment_height]},
                {"name": "knee_to_sole", "start": [0, head_height + 2 * segment_height], "end": [0, head_height + 3 * segment_height]},
            ],
            "calculated_head_ratio": ratio,
            "measurement_overlay": "measurement.png",
            "measurement_overlay_sha256": "b" * 64,
            "catalog_sha256": CATALOG_SHA256,
            "target_source": "preset",
            "target_sha256": manage_run.target_sha256(
                "preset", form, profile["mean_head_ratio"], profile["acceptance_range"]
            ),
            "mean_head_ratio": profile["mean_head_ratio"],
            "acceptance_range": profile["acceptance_range"],
            "torso": "Torso matches the selected form.",
            "arms": "Arms match the selected form.",
            "legs": "Legs match the selected form.",
            "hands_feet": "Hands and feet match the selected form.",
            "pose_retargeted": True,
        },
        "defects": [],
        "targeted_retry": None,
    }
    if counterpart and counterpart_form:
        counterpart_mean = CATALOG["forms"][counterpart_form]["mean_head_ratio"]
        expanded = max(ratio, counterpart_mean)
        compact = min(ratio, counterpart_mean)
        visual["pairwise_evidence"] = {
            "counterpart": counterpart,
            "expanded_form_head_ratio": expanded,
            "compact_form_head_ratio": compact,
            "head_ratio_clearly_different": True,
            "compact_form_torso_visibly_shorter": True,
            "compact_form_limbs_visibly_shorter": True,
            "apparent_age_unchanged": True,
        }
    return visual


def image_spec(form: str, counterpart: str | None = None) -> dict:
    profile = CATALOG["forms"][form]
    proportion = {
        "mode": "preset",
        "preset": form,
        "target_head_ratio": profile["mean_head_ratio"],
        "acceptance_range": profile["acceptance_range"],
        "proportion_reference": profile["primary"],
    }
    value = {
        "counterpart": counterpart,
        "proportion": proportion,
        "identity_anchor_form": form,
        "proportion_sha256": manage_run.target_sha256(
            "preset", form, profile["mean_head_ratio"], profile["acceptance_range"]
        ),
        "pairwise_minimum_head_ratio_gap": CATALOG["pairwise_minimum_head_ratio_gap"],
    }
    return value


class VisualQaTests(unittest.TestCase):
    def test_rejects_ratios_outside_each_catalog_range(self) -> None:
        for form, profile in CATALOG["forms"].items():
            for ratio in (profile["acceptance_range"][0] - 0.01, profile["acceptance_range"][1] + 0.01):
                with self.subTest(form=form, ratio=ratio):
                    with self.assertRaisesRegex(manage_run.RunError, "head ratio"):
                        manage_run.validate_visual_qa(visual_qa(form, ratio), image_spec(form))

    def test_rejects_ratio_not_recomputed_from_landmarks(self) -> None:
        ratio = CATALOG["forms"]["standard"]["mean_head_ratio"]
        visual = visual_qa("standard", ratio)
        visual["form_evidence"]["calculated_head_ratio"] = ratio + 0.1
        with self.assertRaisesRegex(manage_run.RunError, "does not match the landmarks"):
            manage_run.validate_visual_qa(visual, image_spec("standard"))

    def test_requires_pairwise_evidence_for_more_compact_form(self) -> None:
        counterpart = "same_action_standard"
        ratio = CATALOG["forms"]["chibi"]["mean_head_ratio"]
        with self.assertRaisesRegex(manage_run.RunError, "PASS requires pairwise_evidence"):
            manage_run.validate_visual_qa(
                visual_qa("chibi", ratio),
                image_spec("chibi", counterpart),
                compact_pair=True,
            )

    def test_rejects_small_pairwise_gap(self) -> None:
        counterpart = "same_action_semi"
        ratio = CATALOG["forms"]["chibi"]["acceptance_range"][1]
        visual = visual_qa("chibi", ratio, counterpart, "semi-chibi")
        visual["pairwise_evidence"]["expanded_form_head_ratio"] = ratio + 0.2
        missing_gap_spec = image_spec("chibi", counterpart)
        del missing_gap_spec["pairwise_minimum_head_ratio_gap"]
        with self.assertRaisesRegex(manage_run.RunError, "requires frozen pairwise"):
            manage_run.validate_visual_qa(
                visual,
                missing_gap_spec,
                counterpart_ratio=ratio + 0.2,
                compact_pair=True,
            )
        with self.assertRaisesRegex(manage_run.RunError, "gap of at least"):
            manage_run.validate_visual_qa(
                visual,
                image_spec("chibi", counterpart),
                counterpart_ratio=ratio + 0.2,
                compact_pair=True,
            )

    def test_accepts_bound_measurement_overlay(self) -> None:
        ratio = CATALOG["forms"]["semi-chibi"]["mean_head_ratio"]
        visual = visual_qa("semi-chibi", ratio)
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory) / "measurement.png"
            overlay.write_bytes(b"measurement")
            visual["form_evidence"]["measurement_overlay_sha256"] = hashlib.sha256(overlay.read_bytes()).hexdigest()
            manage_run.validate_visual_qa(visual, image_spec("semi-chibi"), overlay_root=Path(directory))

class AssignmentTests(unittest.TestCase):
    def image(self, name: str, form: str | None = None, references: list[str] | None = None) -> dict:
        actual_form = form or CATALOG["default_form"]
        profile = CATALOG["forms"][actual_form]
        reference_paths = references or [self.primary(actual_form)]
        typed_references = []
        for index, path in enumerate(reference_paths):
            typed_references.append({
                "id": "canonical-identity" if index == 0 else f"reference-{index + 1}",
                "path": path,
                "roles": ["identity", "style", "costume", "proportion"]
                if index == 0 else ["pose_action", "composition"],
                "instruction": "Canonical Whale-chan identity anchor"
                if index == 0 else "Use pose and composition only",
            })
        return {
            "name": name,
            "subject": "one Whale-chan",
            "expression": "calm",
            "action": "stand",
            "composition": "full body",
            "props": [],
            "objects": [],
            "style": {"mode": "canonical", "description": manage_run.DEFAULT_STYLE},
            "costume": {"mode": "canonical", "description": manage_run.DEFAULT_COSTUME},
            "background": {"mode": "solid", "description": manage_run.DEFAULT_BACKGROUND},
            "text": None,
            "proportion": {
                "mode": "preset",
                "preset": actual_form,
                "target_head_ratio": profile["mean_head_ratio"],
                "acceptance_range": profile["acceptance_range"],
                "proportion_reference": profile["primary"],
            },
            "references": typed_references,
            "output": {
                "format": "png",
                "aspect_ratio": "1:1",
                "alpha": False,
                "resolution": {
                    "mode": "provider-native",
                    "width": None,
                    "height": None,
                },
            },
            "counterpart": None,
        }

    def assignment(self, images: list[dict]) -> dict:
        estimated = len(images) * 8
        return {
            "schema_version": 4,
            "confirmation": {"confirmed": True, "confirmed_at": "2026-08-13T00:00:00Z"},
            "input": {"type": "text", "content": "test"},
            "run_name": "test-run",
            "image_count": len(images),
            "images": images,
            "execution": {
                "mode": "sequential",
                "requested_parallelism": 1,
                "max_parallelism": 5,
                "commit_strategy": "coordinator-serial",
            },
            "budget": {
                "per_image_candidates": 8,
                "per_provider_candidates": 2,
                "run_candidates": estimated,
                "confirmed_over_24": estimated > 24,
            },
        }

    def validate(self, assignment: dict) -> dict:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assignment.json"
            path.write_text(json.dumps(assignment), encoding="utf-8")
            return manage_run.validate_assignment(path)

    def primary(self, form: str) -> str:
        return str(SKILL_ROOT / CATALOG["forms"][form]["primary"])

    def auxiliary(self, form: str) -> str:
        return str(SKILL_ROOT / CATALOG["forms"][form]["references"][1]["path"])

    def test_v4_requires_resolved_fields(self) -> None:
        image = self.image("sparse")
        del image["subject"]
        sparse = self.assignment([image])
        with self.assertRaisesRegex(manage_run.RunError, "missing required fields"):
            self.validate(sparse)

    def test_v4_rejects_null_resolved_values(self) -> None:
        cases = (
            ("subject", lambda image: image.__setitem__("subject", None)),
            (
                "preset target",
                lambda image: image["proportion"].__setitem__("target_head_ratio", None),
            ),
            (
                "preset target",
                lambda image: image["proportion"].__setitem__("acceptance_range", None),
            ),
            (
                "custom range",
                lambda image: image.__setitem__(
                    "proportion",
                    {
                        "mode": "custom",
                        "preset": None,
                        "target_head_ratio": 5.0,
                        "acceptance_range": None,
                        "proportion_reference": None,
                    },
                ),
            ),
        )
        for label, mutate in cases:
            with self.subTest(label=label):
                image = self.image("null_value")
                mutate(image)
                with self.assertRaises(manage_run.RunError):
                    self.validate(self.assignment([image]))

    def test_v4_rejects_run_budget_below_estimated_maximum(self) -> None:
        assignment = self.assignment([self.image("one")])
        assignment["budget"]["run_candidates"] = 1
        with self.assertRaisesRegex(manage_run.RunError, "estimated maximum 8"):
            self.validate(assignment)

    def test_v4_custom_pair_requires_explicit_shared_gap(self) -> None:
        expanded = self.image("custom_five", "standard")
        compact = self.image("custom_four_six", "standard")
        for image, ratio in ((expanded, 5.0), (compact, 4.6)):
            image["proportion"] = {
                "mode": "custom",
                "preset": None,
                "target_head_ratio": ratio,
                "acceptance_range": [ratio - 0.15, ratio + 0.15],
                "proportion_reference": None,
            }
            image["references"][0]["roles"] = ["identity", "style", "costume"]
        expanded["counterpart"] = compact["name"]
        compact["counterpart"] = expanded["name"]
        assignment = self.assignment([expanded, compact])
        with self.assertRaisesRegex(manage_run.RunError, "must be explicit"):
            self.validate(assignment)
        expanded["pairwise_minimum_head_ratio_gap"] = 0.0
        compact["pairwise_minimum_head_ratio_gap"] = 0.0
        with self.assertRaisesRegex(manage_run.RunError, "must be positive"):
            self.validate(assignment)
        expanded["pairwise_minimum_head_ratio_gap"] = 0.2
        compact["pairwise_minimum_head_ratio_gap"] = 0.2
        validated = self.validate(assignment)
        self.assertEqual(validated["images"][0]["pairwise_minimum_head_ratio_gap"], 0.2)

    def test_v4_shared_reference_role_requires_instructions(self) -> None:
        image = self.image("conflicting_refs")
        image["references"].append({
            "id": "second-style",
            "path": self.auxiliary("semi-chibi"),
            "roles": ["style"],
            "instruction": None,
        })
        with self.assertRaisesRegex(manage_run.RunError, "conflict-resolution instructions"):
            self.validate(self.assignment([image]))

    def test_rejects_unsupported_assignment_fields(self) -> None:
        image = self.image("unsupported_field", "standard")
        image["unexpected"] = True
        with self.assertRaisesRegex(manage_run.RunError, "unsupported fields"):
            self.validate(self.assignment([image]))

    def test_accepts_explicit_text(self) -> None:
        image = self.image("with_text")
        image["text"] = {
            "content": "加油！",
            "languages": ["zh-Hans"],
            "direction": "ltr",
            "placement": "above the character",
            "style": "rounded navy lettering",
        }
        validated = self.validate(self.assignment([image]))
        self.assertEqual(validated["images"][0]["text"]["content"], "加油！")
        self.assertEqual(validated["images"][0]["text"]["languages"], ["zh-Hans"])
        self.assertEqual(validated["images"][0]["text"]["direction"], "ltr")

    def test_accepts_multilingual_text(self) -> None:
        image = self.image("multilingual")
        image["text"] = {
            "content": "你好 / Hello",
            "languages": ["zh-Hans", "en"],
            "direction": "ltr",
            "placement": "above",
            "style": "rounded",
        }
        validated = self.validate(self.assignment([image]))
        self.assertEqual(validated["images"][0]["text"]["languages"], ["zh-Hans", "en"])

    def test_accepts_transparent_png(self) -> None:
        image = self.image("transparent")
        image["background"] = {"mode": "transparent", "description": "transparent background"}
        image["output"] = {
            "format": "png", "aspect_ratio": "1:1", "alpha": True,
            "resolution": {"mode": "provider-native", "width": None, "height": None},
        }
        validated = self.validate(self.assignment([image]))
        self.assertEqual(validated["images"][0]["background"]["mode"], "transparent")
        self.assertTrue(validated["images"][0]["output"]["alpha"])

    def test_defaults_to_provider_native_square_without_fixed_dimensions(self) -> None:
        validated = self.validate(self.assignment([self.image("native_square")]))
        output = validated["images"][0]["output"]
        self.assertEqual(output["aspect_ratio"], "1:1")
        self.assertEqual(output["resolution"], {
            "mode": "provider-native", "width": None, "height": None,
        })

    def test_accepts_arbitrary_output_aspect_ratios(self) -> None:
        cases = (("3:2", 1536, 1024), ("7:3", 1400, 600))
        for aspect_ratio, width, height in cases:
            with self.subTest(aspect_ratio=aspect_ratio):
                image = self.image("custom_canvas")
                image["output"].update({
                    "aspect_ratio": aspect_ratio,
                    "resolution": {"mode": "exact", "width": width, "height": height},
                })
                validated = self.validate(self.assignment([image]))
                self.assertEqual(validated["images"][0]["output"]["aspect_ratio"], aspect_ratio)

    def test_rejects_invalid_or_mismatched_output_aspect_ratio(self) -> None:
        for aspect_ratio in ("free", "0:1", "1:0", "1.5:1"):
            with self.subTest(aspect_ratio=aspect_ratio):
                image = self.image("invalid_canvas")
                image["output"]["aspect_ratio"] = aspect_ratio
                with self.assertRaisesRegex(manage_run.RunError, "positive WIDTH:HEIGHT"):
                    self.validate(self.assignment([image]))
        image = self.image("mismatched_canvas")
        image["output"]["aspect_ratio"] = "3:2"
        image["output"]["resolution"] = {
            "mode": "exact", "width": 1024, "height": 1024,
        }
        with self.assertRaisesRegex(manage_run.RunError, "dimensions do not match"):
            self.validate(self.assignment([image]))

    def test_rejects_dimensions_in_provider_native_mode(self) -> None:
        image = self.image("invalid_native_dimensions")
        image["output"]["resolution"] = {
            "mode": "provider-native", "width": 1024, "height": 1024,
        }
        with self.assertRaisesRegex(manage_run.RunError, "requires null width and height"):
            self.validate(self.assignment([image]))

    def test_rejects_missing_dimensions_in_exact_mode(self) -> None:
        image = self.image("invalid_exact_dimensions")
        image["output"]["resolution"] = {
            "mode": "exact", "width": None, "height": None,
        }
        with self.assertRaisesRegex(manage_run.RunError, "requires positive width and height"):
            self.validate(self.assignment([image]))

    def test_rejects_alpha_background_mismatch(self) -> None:
        image = self.image("bad_alpha")
        image["background"] = {"mode": "transparent", "description": "transparent background"}
        image["output"]["alpha"] = False
        with self.assertRaisesRegex(manage_run.RunError, "output.alpha must be true"):
            self.validate(self.assignment([image]))

    def test_accepts_custom_style_costume_and_scene(self) -> None:
        image = self.image("custom_visuals")
        image["style"] = {"mode": "custom", "description": "watercolor storybook"}
        image["costume"] = {"mode": "custom", "description": "white spacesuit"}
        image["background"] = {"mode": "custom", "description": "a complete observatory interior"}
        image["references"][0]["roles"] = ["identity", "proportion"]
        validated = self.validate(self.assignment([image]))
        result = validated["images"][0]
        self.assertEqual(result["style"]["mode"], "custom")
        self.assertEqual(result["costume"]["mode"], "custom")
        self.assertEqual(result["background"]["mode"], "custom")
        primary = result["references"][0]
        self.assertEqual(primary["roles"], ["identity", "proportion"])

    def test_rejects_custom_description_in_canonical_mode(self) -> None:
        image = self.image("conflicting_style")
        image["style"] = {"mode": "canonical", "description": "watercolor"}
        with self.assertRaisesRegex(manage_run.RunError, "must match the canonical default"):
            self.validate(self.assignment([image]))

    def test_accepts_custom_ratio_without_proportion_reference(self) -> None:
        image = self.image("five_heads", "standard")
        image["proportion"] = {
            "mode": "custom", "preset": None, "target_head_ratio": 5.0,
            "acceptance_range": [4.85, 5.15], "proportion_reference": None,
        }
        image["references"][0]["roles"].remove("proportion")
        validated = self.validate(self.assignment([image]))
        result = validated["images"][0]
        self.assertEqual(result["proportion"]["acceptance_range"], [4.85, 5.15])
        self.assertIsNone(result["proportion"]["proportion_reference"])
        self.assertNotIn("proportion", result["references"][0]["roles"])

    def test_rejects_non_image_external_reference(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".png") as handle:
            handle.write(b"not-an-image")
            handle.flush()
            image = self.image("invalid_external")
            image["references"].append({
                "id": "bad-reference",
                "path": handle.name,
                "roles": ["style"],
                "instruction": "Use style only",
            })
            with self.assertRaisesRegex(manage_run.RunError, "not decodable"):
                self.validate(self.assignment([image]))

    def test_rejects_text_without_exact_content(self) -> None:
        image = self.image("invalid_text")
        image["text"] = {
            "content": "", "languages": ["zh-Hans"], "direction": "ltr",
            "placement": "above", "style": "rounded",
        }
        with self.assertRaisesRegex(manage_run.RunError, "text.content"):
            self.validate(self.assignment([image]))

    def test_rejects_text_without_confirmed_placement_or_style(self) -> None:
        for missing in ("placement", "style"):
            with self.subTest(missing=missing):
                text = {
                    "content": "加油！",
                    "languages": ["zh-Hans"],
                    "direction": "ltr",
                    "placement": "above the character",
                    "style": "rounded navy lettering",
                }
                del text[missing]
                image = self.image(f"missing_{missing}")
                image["text"] = text
                with self.assertRaisesRegex(manage_run.RunError, f"missing required fields: {missing}"):
                    self.validate(self.assignment([image]))

    def test_rejects_unsupported_assignment_schema(self) -> None:
        assignment = self.assignment([self.image("unsupported_schema")])
        assignment["schema_version"] = 2
        with self.assertRaisesRegex(
            manage_run.RunError,
            "schema_version must be 4",
        ):
            self.validate(assignment)

    def test_rejects_cross_form_reference(self) -> None:
        image = self.image("cross_form", "standard", [self.primary("standard"), self.primary("chibi")])
        with self.assertRaisesRegex(manage_run.RunError, "bundled reference must use the standard"):
            self.validate(self.assignment([image]))


class RunInitializationTests(unittest.TestCase):
    def primary(self, form: str) -> str:
        return str(SKILL_ROOT / CATALOG["forms"][form]["primary"])

    def image(self, name: str) -> dict:
        profile = CATALOG["forms"]["semi-chibi"]
        return {
            "name": name,
            "subject": "one Whale-chan",
            "expression": "calm",
            "action": "stand",
            "composition": "full body",
            "props": [],
            "objects": [],
            "style": {"mode": "canonical", "description": manage_run.DEFAULT_STYLE},
            "costume": {"mode": "canonical", "description": manage_run.DEFAULT_COSTUME},
            "background": {"mode": "solid", "description": manage_run.DEFAULT_BACKGROUND},
            "text": None,
            "proportion": {
                "mode": "preset",
                "preset": "semi-chibi",
                "target_head_ratio": profile["mean_head_ratio"],
                "acceptance_range": profile["acceptance_range"],
                "proportion_reference": profile["primary"],
            },
            "references": [{
                "id": "canonical-identity",
                "path": self.primary("semi-chibi"),
                "roles": ["identity", "style", "costume", "proportion"],
                "instruction": "Canonical Whale-chan identity anchor",
            }],
            "output": {
                "format": "png", "aspect_ratio": "1:1", "alpha": False,
                "resolution": {"mode": "provider-native", "width": None, "height": None},
            },
            "counterpart": None,
        }

    def assignment(self, images: list[dict]) -> dict:
        estimated = len(images) * 8
        return {
            "schema_version": 4,
            "confirmation": {"confirmed": True, "confirmed_at": "2026-08-13T00:00:00Z"},
            "input": {"type": "text", "content": "test"},
            "run_name": "test-run",
            "image_count": len(images),
            "images": images,
            "execution": {
                "mode": "sequential",
                "requested_parallelism": 1,
                "max_parallelism": 5,
                "commit_strategy": "coordinator-serial",
            },
            "budget": {
                "per_image_candidates": 8,
                "per_provider_candidates": 2,
                "run_candidates": estimated,
                "confirmed_over_24": estimated > 24,
            },
        }

    def test_freezes_external_references_and_records_effective_parallelism(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "style.png"
            shutil.copy2(self.primary("semi-chibi"), external)
            image = self.image("parallel_custom")
            image["style"] = {"mode": "custom", "description": "watercolor"}
            image["references"][0]["roles"].remove("style")
            image["references"].append({
                "id": "style-reference",
                "path": str(external),
                "roles": ["style"],
                "instruction": "Use watercolor style only",
            })
            assignment = self.assignment([image, self.image("second")])
            assignment["execution"] = {
                "mode": "parallel",
                "requested_parallelism": 3,
                "max_parallelism": 5,
                "commit_strategy": "coordinator-serial",
            }
            assignment_path = root / "assignment.json"
            assignment_path.write_text(json.dumps(assignment), encoding="utf-8")
            result = manage_run.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=2,
            ))
            run_dir = Path(result["run_dir"])
            frozen = manage_run.read_json(run_dir / "assignment.json")
            external_refs = [
                item
                for item in frozen["images"][0]["references"]
                if item["source"] == "external"
            ]
            self.assertEqual(len(external_refs), 1)
            self.assertTrue(Path(external_refs[0]["path"]).is_file())
            self.assertTrue(Path(external_refs[0]["path"]).is_relative_to(run_dir))
            manifest = manage_run.read_json(run_dir / "manifest.json")
            self.assertEqual(manifest["execution"]["requested_parallelism"], 3)
            self.assertEqual(manifest["execution"]["effective_parallelism"], 2)
            self.assertTrue((run_dir / "staging" / "01_parallel_custom").is_dir())
            Path(external_refs[0]["path"]).write_bytes(b"tampered")
            with self.assertRaisesRegex(manage_run.RunError, "Frozen reference SHA-256 mismatch"):
                manage_run.load_run(str(run_dir))

    def test_detects_frozen_assignment_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment_path = root / "assignment.json"
            assignment_path.write_text(
                json.dumps(self.assignment([self.image("one")])), encoding="utf-8"
            )
            result = manage_run.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=1,
            ))
            run_dir = Path(result["run_dir"])
            manifest_path = run_dir / "manifest.json"
            manifest = manage_run.read_json(manifest_path)
            incomplete_manifest = dict(manifest)
            del incomplete_manifest["candidate_count"]
            manifest_path.write_text(json.dumps(incomplete_manifest), encoding="utf-8")
            with self.assertRaisesRegex(manage_run.RunError, "missing required fields: candidate_count"):
                manage_run.load_run(result["run_dir"])
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            frozen_path = run_dir / "assignment.json"
            frozen = manage_run.read_json(frozen_path)
            frozen["images"][0]["action"] = "tampered action"
            frozen_path.write_text(json.dumps(frozen), encoding="utf-8")
            with self.assertRaisesRegex(manage_run.RunError, "assignment SHA-256 mismatch"):
                manage_run.load_run(result["run_dir"])

    def test_safety_rejection_halts_the_whole_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment_path = root / "assignment.json"
            assignment_path.write_text(
                json.dumps(self.assignment([self.image("one"), self.image("two")])),
                encoding="utf-8",
            )
            result = manage_run.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=1,
            ))
            common = {
                "run_dir": result["run_dir"],
                "provider": "codex",
                "model": "gpt-image-2",
                "details": "blocked",
            }
            manage_run.cmd_record_error(argparse.Namespace(
                **common, image="01_one", category="safety_rejection"
            ))
            with self.assertRaisesRegex(manage_run.RunError, "Run is not open"):
                manage_run.cmd_record_error(argparse.Namespace(
                    **common, image="02_two", category="service"
                ))

    def test_initializes_five_ready_images_at_effective_parallelism_five(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = [self.image(f"image_{index}") for index in range(1, 6)]
            assignment = self.assignment(images)
            assignment["execution"] = {
                "mode": "parallel",
                "requested_parallelism": 5,
                "max_parallelism": 5,
                "commit_strategy": "coordinator-serial",
            }
            assignment["budget"] = {
                "per_image_candidates": 4,
                "per_provider_candidates": 1,
                "run_candidates": 20,
                "confirmed_over_24": False,
            }
            assignment_path = root / "assignment.json"
            assignment_path.write_text(json.dumps(assignment), encoding="utf-8")
            result = manage_run.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=5,
            ))
            self.assertEqual(result["execution"]["effective_parallelism"], 5)
            self.assertEqual(result["execution"]["initial_ready_image_count"], 5)

    def test_records_requested_provider_and_actual_output_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assignment_path = root / "assignment.json"
            assignment_path.write_text(
                json.dumps(self.assignment([self.image("native_output")])),
                encoding="utf-8",
            )
            initialized = manage_run.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=1,
            ))

            candidate = root / "candidate.png"
            subprocess.run(
                [
                    shutil.which("magick"),
                    "-size",
                    "1536x1536",
                    "xc:red",
                    "-define",
                    "png:color-type=2",
                    str(candidate),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            automatic_file = root / "automatic.json"
            subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts" / "validate-image.py"),
                    str(candidate),
                    "--write-json",
                    str(automatic_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            overlay = root / "measurement.png"
            overlay.write_bytes(b"measurement evidence")
            visual = visual_qa(
                "semi-chibi",
                CATALOG["forms"]["semi-chibi"]["mean_head_ratio"],
            )
            visual["candidate_sha256"] = manage_run.sha256(candidate)
            visual["form_evidence"]["measurement_overlay_sha256"] = manage_run.sha256(overlay)
            visual_file = root / "visual.json"
            visual_file.write_text(json.dumps(visual), encoding="utf-8")
            prompt_file = root / "prompt.txt"
            prompt_file.write_text("Generate one Whale-chan.", encoding="utf-8")

            manage_run.cmd_record_candidate(argparse.Namespace(
                run_dir=initialized["run_dir"],
                image="01_native_output",
                provider="codex",
                model="gpt-image-2",
                prompt_file=str(prompt_file),
                candidate=str(candidate),
                automatic_json=str(automatic_file),
                visual_json=str(visual_file),
                provider_size=None,
            ))
            promoted = manage_run.cmd_promote(argparse.Namespace(
                run_dir=initialized["run_dir"],
                image="01_native_output",
                attempt=1,
            ))

            _run_dir, frozen, manifest = manage_run.load_run(initialized["run_dir"])
            attempt = manifest["images"]["01_native_output"]["attempts"][0]
            self.assertEqual(attempt["requested_output"], frozen["images"][0]["output"])
            self.assertEqual(attempt["provider_output_request"], {
                "aspect_ratio": "1:1",
                "resolution_mode": "provider-native",
                "size": None,
            })
            self.assertEqual(attempt["actual_output"]["width"], 1536)
            self.assertEqual(attempt["actual_output"]["height"], 1536)
            self.assertEqual(promoted["output"], attempt["actual_output"])
            self.assertEqual(
                manifest["images"]["01_native_output"]["final_output"],
                attempt["actual_output"],
            )


class AutomaticQaTests(unittest.TestCase):
    def automatic(self, candidate: Path, alpha_policy: str = "forbidden") -> dict:
        result = subprocess.run(
            [
                sys.executable,
                str(SKILL_ROOT / "scripts" / "validate-image.py"),
                str(candidate),
                "--alpha",
                alpha_policy,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertIn(result.returncode, {0, 1})
        return json.loads(result.stdout)

    def create_candidate(self, path: Path) -> None:
        subprocess.run(
            [
                shutil.which("magick"),
                "-size",
                "1024x1024",
                "xc:red",
                "-define",
                "png:color-type=2",
                str(path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_rejects_automatic_qa_with_wrong_alpha_policy(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.png"
            self.create_candidate(candidate)
            image = {"output": {
                "format": "png", "aspect_ratio": "1:1", "alpha": True,
                "resolution": {"mode": "provider-native", "width": None, "height": None},
            }}
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            with self.assertRaisesRegex(manage_run.RunError, "alpha_policy must be required"):
                manage_run.validate_automatic_qa(
                    self.automatic(candidate), image, candidate, digest
                )

    def test_rejects_automatic_qa_for_another_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate.png"
            self.create_candidate(candidate)
            automatic = self.automatic(candidate)
            automatic["sha256"] = "0" * 64
            image = {"output": {
                "format": "png", "aspect_ratio": "1:1", "alpha": False,
                "resolution": {"mode": "provider-native", "width": None, "height": None},
            }}
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            with self.assertRaisesRegex(manage_run.RunError, "does not match the candidate"):
                manage_run.validate_automatic_qa(
                    automatic, image, candidate, digest
                )

    def test_provider_output_request_preserves_native_tier(self) -> None:
        output = {
            "format": "png",
            "aspect_ratio": "1:1",
            "alpha": False,
            "resolution": {"mode": "provider-native", "width": None, "height": None},
        }
        self.assertEqual(
            manage_run.provider_output_request(output, "1K")["size"],
            "1K",
        )

    def test_provider_output_request_rejects_wrong_exact_size(self) -> None:
        output = {
            "format": "png",
            "aspect_ratio": "3:2",
            "alpha": False,
            "resolution": {"mode": "exact", "width": 1536, "height": 1024},
        }
        with self.assertRaisesRegex(manage_run.RunError, "frozen exact resolution"):
            manage_run.provider_output_request(output, "1024x1024")

class CatalogTests(unittest.TestCase):
    def test_catalog_rejects_reference_hash_drift(self) -> None:
        original_sha256 = manage_run.sha256
        def drift_one_reference(path: Path) -> str:
            if path.name == "01_gentle_wave.webp":
                return "0" * 64
            return original_sha256(path)
        with mock.patch.object(manage_run, "sha256", side_effect=drift_one_reference):
            with self.assertRaisesRegex(manage_run.RunError, "SHA-256 mismatch"):
                manage_run.load_catalog()


if __name__ == "__main__":
    unittest.main()
