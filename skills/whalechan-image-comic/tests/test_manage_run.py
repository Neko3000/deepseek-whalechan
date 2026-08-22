from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "manage-run.py"
SPEC = importlib.util.spec_from_file_location("comic_manage_run", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


FORM_PROFILES = {
    "standard": ("01_gentle_wave.webp", 4.0, [3.846, 4.146]),
    "compact": (
        "0102_intimate_relationship_question_rendered_isolated.webp",
        3.3,
        [3.105, 3.405],
    ),
    "semi-chibi": (
        "0092_enduring_release_delay_rendered_isolated.webp",
        2.8,
        [2.689, 2.989],
    ),
    "chibi": (
        "0067_angry_you_are_silly_reply_rendered_isolated.webp",
        2.5,
        [2.372, 2.672],
    ),
    "super-deformed": (
        "0019_literal_love_reply_rendered_isolated.webp",
        2.1,
        [1.931, 2.231],
    ),
}
TEXT_STYLE = "06_top-bottom-punchline"
TEXT_STYLE_REFERENCE = (
    SKILL_ROOT / f"assets/text-style-templates/{TEXT_STYLE}/reference.webp"
)


def text_style_reference() -> dict:
    return {
        "id": "text-style",
        "path": str(TEXT_STYLE_REFERENCE),
        "roles": ["typography"],
        "instruction": "Apply typography treatment only",
    }


def assignment() -> dict:
    pool = []
    for number in range(1, 9):
        item = {
            "id": f"idea_{number:02d}",
            "premise": f"premise {number}",
            "expectation": f"expectation {number}",
            "reversal": f"reversal {number}",
            "punchline": f"punchline {number}",
            "personality": ["serious", "malicious"],
            "fact_anchor": "missing comma",
            "scene": f"scene {number}",
            "gate": "PASS" if number <= 4 else "FAIL",
        }
        if item["gate"] == "FAIL":
            item["rejection_reason"] = "too flat"
        pool.append(item)
    layouts = [(1, "single"), (2, "top-bottom"), (4, "2x2"), (1, "single"), (2, "left-right")]
    ranks = [(1, 1), (1, 2), (1, 3), (2, 1), (3, 1)]
    intensities = ["C", "C", "B", "C", "B"]
    images = []
    for index in range(5):
        panels, layout = layouts[index]
        rank, execution = ranks[index]
        images.append(
            {
                "name": f"comic_{index + 1}",
                "source_rank": rank,
                "execution": execution,
                "fact_anchor": "missing comma",
                "premise": "factory produces punctuation" if rank == 1 else f"independent {rank}",
                "punchline": f"knife {index + 1}",
                "why_funny": "huge effort produces punctuation",
                "personality": ["serious", "malicious"],
                "panel_count": panels,
                "expression_plan": [
                    {
                        "panel": panel,
                        "preset": "procedural" if panel == 1 else "smug",
                        "performance": "grounded" if panel == 1 else "heightened",
                    }
                    for panel in range(1, panels + 1)
                ],
                "action_plan": [
                    {
                        "panel": panel,
                        "action": f"perform requested action in panel {panel}",
                    }
                    for panel in range(1, panels + 1)
                ],
                "layout": layout,
                "intensity": intensities[index],
                "core_text": ["全厂推理完毕", "缺了个逗号。"],
                "text_style": TEXT_STYLE,
                "references": [text_style_reference()],
                "supporting_character": {"present": False, "interaction": None},
            }
        )
    return {
        "schema_version": 6,
        "run_name": "comma-factory",
        "input": {"type": "text", "content": "input", "language": "zh-CN", "fact_anchor": "missing comma"},
        "creative_pool": pool,
        "duels": [
            {"winner": "idea_01", "loser": "idea_04", "reason": "harder"},
            {"winner": "idea_02", "loser": "idea_04", "reason": "clearer"},
            {"winner": "idea_03", "loser": "idea_04", "reason": "sharper"},
        ],
        "ranked_ideas": ["idea_01", "idea_02", "idea_03"],
        "images": images,
        "execution": {
            "mode": "sequential",
            "requested_parallelism": 1,
            "max_parallelism": 5,
            "commit_strategy": "coordinator-serial",
        },
        "budget": {"per_image_candidates": 3},
    }


class AssignmentTests(unittest.TestCase):
    def write(self, directory: str, value: dict) -> Path:
        path = Path(directory) / "assignment.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_valid_assignment_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            value = manage.validate_assignment(self.write(directory, assignment()))
            self.assertEqual(value["budget"]["maximum_total"], 15)
            self.assertEqual([item["source_rank"] for item in value["images"]].count(1), 3)
            self.assertTrue(all(item["references"][0]["path"].endswith("0092_enduring_release_delay_rendered_isolated.webp") for item in value["images"]))
            self.assertTrue(all(item["proportion"]["target_head_ratio"] == 2.8 for item in value["images"]))
            self.assertTrue(
                all(item["proportion"]["acceptance_range"] == [2.689, 2.989] for item in value["images"])
            )
            self.assertTrue(all(item["output"] == {
                "format": "png",
                "aspect_ratio": "1:1",
                "resolution": {"mode": "auto", "recommended": "1024x1024"},
            } for item in value["images"]))

    def test_v6_requires_exact_text_style_and_preserves_visual_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(
                self.write(directory, assignment())
            )
        self.assertEqual(manage.DEFAULT_BACKGROUND, "pure white #FFFFFF")
        for image in normalized["images"]:
            self.assertEqual(image["core_text"], ["全厂推理完毕", "缺了个逗号。"])
            self.assertEqual(image["text_style"], TEXT_STYLE)
            self.assertEqual(image["background"], {
                "mode": "solid", "description": manage.DEFAULT_BACKGROUND
            })
            self.assertEqual(image["style"]["mode"], "canonical")
            self.assertEqual(image["costume"]["mode"], "canonical")
            self.assertEqual(image["proportion"]["preset"], "semi-chibi")
            self.assertEqual(image["references"][0]["roles"], [
                "identity", "style", "costume", "proportion"
            ])
            self.assertEqual(image["references"][1]["roles"], ["typography"])
            self.assertEqual(Path(image["references"][1]["path"]), TEXT_STYLE_REFERENCE)

    def test_v6_accepts_custom_visuals_and_ratio(self) -> None:
        value = assignment()
        image = value["images"][0]
        image["style"] = {"mode": "custom", "description": "loose watercolor"}
        image["costume"] = {"mode": "custom", "description": "navy astronaut suit"}
        image["background"] = {"mode": "custom", "description": "moonlit city rooftop"}
        image["proportion"] = {
            "mode": "custom",
            "preset": None,
            "target_head_ratio": 5.0,
            "acceptance_range": [4.85, 5.15],
            "proportion_reference": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(self.write(directory, value))
        result = normalized["images"][0]
        self.assertEqual(result["background"], {
            "mode": "custom", "description": "moonlit city rooftop"
        })
        self.assertEqual(result["proportion"]["target_head_ratio"], 5.0)
        self.assertIsNone(result["proportion"]["proportion_reference"])
        self.assertEqual(result["references"][0]["roles"], ["identity"])

    def test_v6_requires_input_language(self) -> None:
        value = assignment()
        value["input"].pop("language")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "input.language"):
                manage.validate_assignment(self.write(directory, value))

    def test_v6_requires_core_text_and_text_style(self) -> None:
        value = assignment()
        value["images"][0].pop("core_text")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "core_text"):
                manage.validate_assignment(self.write(directory, value))
        value = assignment()
        value["images"][0]["core_text"] = []
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "core_text"):
                manage.validate_assignment(self.write(directory, value))
        value = assignment()
        value["images"][0].pop("text_style")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "text_style"):
                manage.validate_assignment(self.write(directory, value))
        value = assignment()
        value["images"][0]["text_style"] = "unknown-style"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "text_style"):
                manage.validate_assignment(self.write(directory, value))

    def test_v6_requires_matching_text_style_typography_reference(self) -> None:
        value = assignment()
        value["images"][0]["references"] = []
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "exactly one selected text-style"):
                manage.validate_assignment(self.write(directory, value))
        value = assignment()
        value["images"][0]["text_style"] = "03_blue-banner"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "selected text-style reference"):
                manage.validate_assignment(self.write(directory, value))

    def test_v6_accepts_external_role_scoped_reference(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "style.png"
            shutil.copy2(
                SKILL_ROOT / "assets/character-references/semi-chibi/0015_data_still_in_brain_rendered_isolated.webp",
                external,
            )
            value = assignment()
            value["images"][0]["style"] = {
                "mode": "custom", "description": "inherit watercolor texture"
            }
            value["images"][0]["references"].append({
                "id": "user-style",
                "path": str(external),
                "roles": ["style"],
                "instruction": "inherit style only",
            })
            assignment_path = self.write(directory, value)
            normalized = manage.validate_assignment(assignment_path)
            references = normalized["images"][0]["references"]
            self.assertEqual(len(references), 3)
            self.assertEqual(references[2]["source"], "external")
            self.assertEqual(references[2]["roles"], ["style"])
            result = manage.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=1,
            ))
            frozen = manage.read_json(Path(result["run_dir"]) / "assignment.json")
            frozen_external = frozen["images"][0]["references"][2]
            self.assertTrue(Path(frozen_external["path"]).is_relative_to(Path(result["run_dir"])))
            self.assertEqual(
                hashlib.sha256(Path(frozen_external["path"]).read_bytes()).hexdigest(),
                frozen_external["sha256"],
            )

    def test_execution_accepts_five_and_rejects_six(self) -> None:
        value = assignment()
        value["execution"] = {"mode": "parallel", "requested_parallelism": 5}
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(self.write(directory, value))
        self.assertEqual(normalized["execution"]["requested_parallelism"], 5)
        value["execution"] = {"mode": "parallel", "requested_parallelism": 6}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "between 1 and 5"):
                manage.validate_assignment(self.write(directory, value))

    def test_parallel_init_records_effective_capacity_and_staging(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            value = assignment()
            value["execution"] = {"mode": "parallel", "requested_parallelism": 5}
            assignment_path = self.write(directory, value)
            result = manage.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=3,
            ))
            self.assertEqual(result["execution"]["requested_parallelism"], 5)
            self.assertEqual(result["execution"]["effective_parallelism"], 3)
            for image_id in result["images"]:
                self.assertTrue((Path(result["run_dir"]) / "staging" / image_id).is_dir())
            five_way = manage.cmd_init(argparse.Namespace(
                assignment=str(assignment_path),
                root=str(root / "runs"),
                effective_parallelism=5,
            ))
            self.assertEqual(five_way["execution"]["effective_parallelism"], 5)

    def test_v6_pass_requires_candidate_bound_ratio_and_config_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            normalized = manage.validate_assignment(
                self.write(directory, assignment())
            )
            image = normalized["images"][0]
            candidate = SKILL_ROOT / "assets/character-references/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp"
            candidate_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            overlay = root / "measurement.png"
            shutil.copy2(candidate, overlay)
            visual = {
                "verdict": "PASS",
                "candidate_sha256": candidate_hash,
                "gates": {key: "PASS" for key in manage.CONFIGURABLE_GATES},
                "evidence": {
                    "why_funny": "The user expects punctuation work, but Whale-chan reclassifies the tiny output as a completed factory service.",
                    "fact_anchor_visible_as": "a visible missing comma consequence",
                    "text_transcription": image["core_text"],
                    "style_match": "canonical rounded cel shading is visible",
                    "costume_match": "the complete canonical maid outfit is visible",
                    "background_match": "the background is pure white",
                    "action_match": "panel one performs the frozen action",
                    "form_evidence": {
                        "candidate_sha256": candidate_hash,
                        "measurement_method": "pose-neutralized-skeleton",
                        "target_source": "preset",
                        "target_sha256": image["proportion_sha256"],
                        "mean_head_ratio": 2.8,
                        "acceptance_range": [2.689, 2.989],
                        "head_axis": {"top": [100, 0], "chin": [100, 100]},
                        "body_segments": [
                            {"name": "chin_to_pelvis", "start": [100, 100], "end": [100, 160]},
                            {"name": "pelvis_to_knee", "start": [100, 160], "end": [100, 220]},
                            {"name": "knee_to_sole", "start": [100, 220], "end": [100, 280]},
                        ],
                        "calculated_head_ratio": 2.8,
                        "measurement_overlay": str(overlay),
                        "measurement_overlay_sha256": hashlib.sha256(overlay.read_bytes()).hexdigest(),
                    },
                    "form_consistency": "the frozen ratio is consistent",
                    "crop_status": "the full body is intentionally visible",
                    "expression_match": [{
                        "panel": 1,
                        "preset": "procedural",
                        "performance": "grounded",
                        "observed_cues": ["level eyebrows", "straight mouth"],
                        "forbidden_cues_present": [],
                    }],
                },
                "defects": [],
                "targeted_retry": None,
            }
            visual_path = root / "visual.json"
            visual_path.write_text(json.dumps(visual), encoding="utf-8")
            result = manage.validate_qa(
                visual_path, candidate_hash, image_spec=image
            )
            self.assertEqual(result["verdict"], "PASS")
            visual["evidence"]["text_transcription"] = ["错误文字"]
            visual_path.write_text(json.dumps(visual), encoding="utf-8")
            with self.assertRaisesRegex(manage.RunError, "does not match"):
                manage.validate_qa(visual_path, candidate_hash, image_spec=image)
            visual["evidence"]["text_transcription"] = image["core_text"]
            visual["evidence"]["form_evidence"]["calculated_head_ratio"] = 3.1
            visual_path.write_text(json.dumps(visual), encoding="utf-8")
            with self.assertRaisesRegex(manage.RunError, "recomputed"):
                manage.validate_qa(visual_path, candidate_hash, image_spec=image)

    def test_catalog_has_five_authoritative_forms(self) -> None:
        assets, profiles, _catalog_hash = manage.catalog()
        character_assets = [
            item for item in assets.values() if item["kind"] == "character"
        ]
        self.assertEqual(tuple(profiles), manage.FORM_ORDER)
        self.assertEqual(len(character_assets), 15)
        for form, (primary, mean, acceptance) in FORM_PROFILES.items():
            with self.subTest(form=form):
                self.assertEqual(
                    profiles[form]["primary"],
                    f"assets/character-references/{form}/{primary}",
                )
                self.assertEqual(profiles[form]["mean_head_ratio"], mean)
                self.assertEqual(profiles[form]["acceptance_range"], acceptance)
                self.assertEqual(
                    sum(item.get("variant") == form for item in character_assets), 3
                )

    def test_expression_presets_cover_existing_and_new_performances(self) -> None:
        presets, performance_levels = manage.expression_presets()
        self.assertEqual(
            set(presets),
            {
                "innocent",
                "smug",
                "shy",
                "aggrieved",
                "procedural",
                "clinical_sweetness",
                "cheerful_wink",
                "relaxed",
                "exhausted",
                "panic",
                "proud",
                "sly_coaxing",
                "aloof_disdain",
                "puffed_innocence",
                "awkward_deflection",
                "explosive_rage",
                "meltdown_panic",
            },
        )
        self.assertEqual(
            performance_levels,
            {"grounded", "heightened", "punchline_peak"},
        )

    def test_accepts_all_five_forms_with_their_primary_reference(self) -> None:
        for form, (primary, mean, acceptance) in FORM_PROFILES.items():
            with self.subTest(form=form), tempfile.TemporaryDirectory() as directory:
                value = assignment()
                for image in value["images"]:
                    image["proportion"] = {"mode": "preset", "preset": form}
                normalized = manage.validate_assignment(self.write(directory, value))
                self.assertTrue(
                    all(item["proportion"]["target_head_ratio"] == mean for item in normalized["images"])
                )
                self.assertTrue(
                    all(item["proportion"]["acceptance_range"] == acceptance for item in normalized["images"])
                )
                self.assertTrue(
                    all(item["references"][0]["path"].endswith(primary) for item in normalized["images"])
                )

    def test_requires_assignment_schema_v6(self) -> None:
        for version in (5, manage.ASSIGNMENT_SCHEMA_VERSION + 1):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                value = assignment()
                value["schema_version"] = version
                with self.assertRaisesRegex(
                    manage.RunError,
                    f"schema_version must be {manage.ASSIGNMENT_SCHEMA_VERSION}",
                ):
                    manage.validate_assignment(self.write(directory, value))

    def test_output_accepts_explicit_resolution_and_infers_ratio(self) -> None:
        value = assignment()
        value["images"][0]["output"] = {
            "format": "png",
            "resolution": {"mode": "explicit", "width": 1920, "height": 1080},
        }
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(self.write(directory, value))
        self.assertEqual(normalized["images"][0]["output"], {
            "format": "png",
            "aspect_ratio": "16:9",
            "resolution": {"mode": "explicit", "width": 1920, "height": 1080},
        })

    def test_output_accepts_aspect_ratio_with_auto_resolution(self) -> None:
        value = assignment()
        value["images"][0]["output"] = {
            "format": "png",
            "aspect_ratio": "16:9",
            "resolution": {"mode": "auto"},
        }
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(self.write(directory, value))
        self.assertEqual(normalized["images"][0]["output"], {
            "format": "png",
            "aspect_ratio": "16:9",
            "resolution": {"mode": "auto", "recommended": None},
        })

    def test_output_rejects_conflicting_ratio_and_explicit_resolution(self) -> None:
        value = assignment()
        value["images"][0]["output"] = {
            "format": "png",
            "aspect_ratio": "1:1",
            "resolution": {"mode": "explicit", "width": 1920, "height": 1080},
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "does not match"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_wrong_intensity_mix(self) -> None:
        value = assignment()
        value["images"][0]["intensity"] = "B"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "3 C and 2 B"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_one_panel_count_for_entire_set(self) -> None:
        value = assignment()
        for image in value["images"]:
            image["panel_count"] = 1
            image["layout"] = "single"
            image["expression_plan"] = image["expression_plan"][:1]
            image["action_plan"] = image["action_plan"][:1]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "at least two panel counts"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_expression_plan_with_wrong_panel_count(self) -> None:
        value = assignment()
        value["images"][1]["expression_plan"] = value["images"][1]["expression_plan"][:1]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "one entry per panel"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_nonconsecutive_expression_panels(self) -> None:
        value = assignment()
        value["images"][1]["expression_plan"][1]["panel"] = 1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "consecutive from 1"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_unknown_expression_preset(self) -> None:
        value = assignment()
        value["images"][0]["expression_plan"][0]["preset"] = "unknown_face"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "preset is unknown"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_invalid_expression_performance(self) -> None:
        value = assignment()
        value["images"][0]["expression_plan"][0]["performance"] = "extreme"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "performance is invalid"):
                manage.validate_assignment(self.write(directory, value))

    def test_rejects_supporting_reference_without_character(self) -> None:
        value = assignment()
        value["images"][0]["references"].append({
            "id": "abstract-user",
            "path": str(
                SKILL_ROOT
                / "assets/supporting-character-references/abstract-user-pose-sheet.webp"
            ),
            "roles": ["pose_action"],
            "instruction": "Use only for the supporting character pose",
        })
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "must not load"):
                manage.validate_assignment(self.write(directory, value))

    def test_requires_pose_sheet_and_text_for_supporting_character(self) -> None:
        value = assignment()
        value["images"][0]["supporting_character"] = {
            "present": True,
            "interaction": "The abstract user kneels on the left and points upward.",
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(manage.RunError, "must load only"):
                manage.validate_assignment(self.write(directory, value))
        value["images"][0]["references"].append({
            "id": "abstract-user",
            "path": str(
                SKILL_ROOT
                / "assets/supporting-character-references/abstract-user-pose-sheet.webp"
            ),
            "roles": ["pose_action"],
            "instruction": "Use only for the supporting character pose",
        })
        with tempfile.TemporaryDirectory() as directory:
            normalized = manage.validate_assignment(self.write(directory, value))
            self.assertTrue(normalized["images"][0]["supporting_character"]["present"])


class RunStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        assignment_path = root / "assignment.json"
        assignment_path.write_text(json.dumps(assignment(), ensure_ascii=False), encoding="utf-8")
        result = manage.cmd_init(argparse.Namespace(
            assignment=str(assignment_path),
            root=str(root / "runs"),
            effective_parallelism=None,
        ))
        self.run_dir = Path(result["run_dir"])
        self.image = "01_comic_1"
        frozen = manage.read_json(self.run_dir / "assignment.json")
        self.image_spec = frozen["images"][0]
        self.magick = shutil.which("magick")
        if self.magick is None:
            self.skipTest("ImageMagick is required")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def files(self, number: int, verdict: str = "FAIL") -> argparse.Namespace:
        root = Path(self.temporary.name) / f"input-{number}"
        root.mkdir()
        candidate = root / "candidate.png"
        subprocess.run([self.magick, "-size", "1024x1024", "xc:white", str(candidate)], check=True)
        prompt = root / "prompt.txt"
        prompt.write_text("test prompt", encoding="utf-8")
        candidate_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
        overlay = root / "measurement.png"
        shutil.copy2(candidate, overlay)
        automatic = root / "automatic.json"
        automatic.write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "overall": "PASS",
                    "candidate_sha256": candidate_hash,
                    "expected_output": self.image_spec["output"],
                    "metrics": {
                        "format": "PNG",
                        "width": 1024,
                        "height": 1024,
                        "colorspace": "sRGB",
                        "channels": "srgb",
                    },
                    "gates": {
                        "F1": {"verdict": "PASS"},
                        "F2": {"verdict": "PASS"},
                    },
                }
            ),
            encoding="utf-8",
        )
        visual = root / "visual.json"
        gates = {key: "PASS" for key in manage.CONFIGURABLE_GATES}
        defects = []
        targeted = None
        evidence = {
            "why_funny": "contrast",
            "fact_anchor_visible_as": "comma",
            "text_transcription": self.image_spec["core_text"],
            "style_match": "canonical rounded cel shading is visible",
            "costume_match": "the canonical maid outfit is visible",
            "background_match": "the pure white background is visible",
            "action_match": "panel one performs the frozen action",
            "form_evidence": {
                "candidate_sha256": candidate_hash,
                "measurement_method": "pose-neutralized-skeleton",
                "target_source": "preset",
                "target_sha256": self.image_spec["proportion_sha256"],
                "mean_head_ratio": 2.8,
                "acceptance_range": [2.689, 2.989],
                "head_axis": {"top": [100, 0], "chin": [100, 100]},
                "body_segments": [
                    {"name": "chin_to_pelvis", "start": [100, 100], "end": [100, 160]},
                    {"name": "pelvis_to_knee", "start": [100, 160], "end": [100, 220]},
                    {"name": "knee_to_sole", "start": [100, 220], "end": [100, 280]},
                ],
                "calculated_head_ratio": 2.8,
                "measurement_overlay": str(overlay),
                "measurement_overlay_sha256": hashlib.sha256(overlay.read_bytes()).hexdigest(),
            },
            "form_consistency": "Every panel preserves the same body form.",
            "crop_status": "Every crop is intentional and complete for its shot.",
            "expression_match": [
                {
                    "panel": 1,
                    "preset": "procedural",
                    "performance": "grounded",
                    "observed_cues": ["level eyebrows", "small straight mouth"],
                    "forbidden_cues_present": [],
                }
            ],
        }
        if verdict == "FAIL":
            gates["J1"] = "FAIL"
            defects = ["The punchline is flat"]
            targeted = "Replace the punchline"
        visual.write_text(json.dumps({"verdict": verdict, "candidate_sha256": candidate_hash, "gates": gates, "evidence": evidence, "defects": defects, "targeted_retry": targeted}), encoding="utf-8")
        return argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="codex", model="test", candidate=str(candidate), prompt_file=str(prompt), automatic_json=str(automatic), visual_json=str(visual))

    def test_budget_is_per_image_and_stops_at_three(self) -> None:
        for number in range(1, 4):
            manage.record_image(self.files(number), component=False)
        with self.assertRaisesRegex(manage.RunError, "budget is exhausted"):
            manage.record_image(self.files(4), component=False)
        _run, _assignment, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 3)
        self.assertEqual(len(manifest["images"]["02_comic_2"]["attempts"]), 0)

    def test_provider_cannot_skip(self) -> None:
        with self.assertRaisesRegex(manage.RunError, "first provider"):
            manage.cmd_record_error(argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="openai", model="x", category="service", details="down"))
        manage.cmd_record_error(argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="codex", model="x", category="service", details="down"))
        with self.assertRaisesRegex(manage.RunError, "skip"):
            manage.cmd_record_error(argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="nano-banana", model="x", category="service", details="down"))

    def test_pass_can_promote_without_spending_other_budget(self) -> None:
        record = manage.record_image(self.files(1, verdict="PASS"), component=False)
        self.assertEqual(record["output"]["requested"], self.image_spec["output"])
        self.assertEqual(record["output"]["actual"]["width"], 1024)
        with self.assertRaisesRegex(manage.RunError, "task is closed"):
            manage.record_image(self.files(2), component=False)
        result = manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        self.assertTrue(Path(result["final"]).is_file())
        _run, _assignment, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(manifest["images"][self.image]["status"], "passed")
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 1)

    def test_pass_requires_current_form_evidence(self) -> None:
        args = self.files(1, verdict="PASS")
        visual_path = Path(args.visual_json)
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        del visual["evidence"]["form_consistency"]
        visual_path.write_text(json.dumps(visual), encoding="utf-8")
        with self.assertRaisesRegex(manage.RunError, "form_consistency"):
            manage.record_image(args, component=False)

    def test_pass_requires_expression_evidence_for_each_panel(self) -> None:
        args = self.files(1, verdict="PASS")
        visual_path = Path(args.visual_json)
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        visual["evidence"]["expression_match"] = []
        visual_path.write_text(json.dumps(visual), encoding="utf-8")
        with self.assertRaisesRegex(manage.RunError, "one entry per panel"):
            manage.record_image(args, component=False)

    def test_pass_expression_evidence_must_match_assignment(self) -> None:
        args = self.files(1, verdict="PASS")
        visual_path = Path(args.visual_json)
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        visual["evidence"]["expression_match"][0]["preset"] = "smug"
        visual_path.write_text(json.dumps(visual), encoding="utf-8")
        with self.assertRaisesRegex(manage.RunError, "does not match"):
            manage.record_image(args, component=False)

    def test_pass_rejects_forbidden_expression_cues(self) -> None:
        args = self.files(1, verdict="PASS")
        visual_path = Path(args.visual_json)
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        visual["evidence"]["expression_match"][0]["forbidden_cues_present"] = ["crying"]
        visual_path.write_text(json.dumps(visual), encoding="utf-8")
        with self.assertRaisesRegex(manage.RunError, "must be empty"):
            manage.record_image(args, component=False)

    def test_partial_finalize_rejects_viable_tasks(self) -> None:
        with self.assertRaisesRegex(manage.RunError, "still have a viable attempt"):
            manage.cmd_finalize(
                argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True)
            )


if __name__ == "__main__":
    unittest.main()
