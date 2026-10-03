"""Synthetic assignments and visual evidence, never real approval or image review."""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SKILL_ROOT / "scripts" / "manage-run.py"
SPEC = importlib.util.spec_from_file_location("whalechan_manage_run", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {MODULE_PATH}")
manage_run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage_run)
CATALOG, CATALOG_SHA256 = manage_run.load_catalog()


def confirm_fixture(value: dict, path: Path | None = None) -> dict:
    """Synthetic decisions for tests only; never actual user authorization."""
    value["proposal"] = {
        "revision": 1, "mode": "direct", "request": "Synthetic specified scenes",
        "options": [], "recommended_choices": ["A"],
    }
    value["selection"] = {"user_reply": "Synthetic Gate 1", "choices": [], "adjustments": []}
    value["scope"] = {"configurations": []}
    for index, image in enumerate(value["images"]):
        choice = chr(65 + index)
        image.update(proposal_choice=choice, configuration_id=f"config_{index}", execution_note="Confirmed scene execution")
        value["proposal"]["options"].append({
            "choice": choice, "title": image["name"], "scene": "A specified scene",
            "action_expression": "Calm standing", "composition": "Full body",
            "visual_text": "Canonical, no text", "rating": 2,
            "recommendation_reason": "Matches the specified scene",
        })
        value["selection"]["choices"].append({"choice": choice, "count": 1})
        value["scope"]["configurations"].append({
            "id": image["configuration_id"], "choice": choice, "count": 1,
            "variation": "Use the specified scene",
            "requirements": {key: copy.deepcopy(image[key]) for key in manage_run.SCOPE_FIELDS if key in image},
        })
    value["selection"]["proposal_sha256"] = manage_run.contract_hash(value["proposal"])
    summary = manage_run.selection_summary(value, path or SKILL_ROOT / "assignment.json")
    value["confirmation"] = {"status": "confirmed", "user_reply": "Synthetic Gate 2",
                             "confirmed_at": "2026-08-13T00:00:00Z", "summary_sha256": summary["summary_sha256"]}
    return value


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


class FixtureCase(unittest.TestCase):
    def image(self, name: str, form: str = "semi-chibi") -> dict:
        profile = CATALOG["forms"][form]
        typed_references = [{
            "id": "canonical-identity", "path": self.primary(form),
            "roles": ["identity", "style", "costume", "proportion"],
            "instruction": "Canonical Whale-chan identity anchor",
        }]
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
                "preset": form,
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

    def raw_assignment(self, images: list[dict]) -> dict:
        estimated = len(images) * 8
        return {
            "schema_version": manage_run.ASSIGNMENT_SCHEMA_VERSION,
            "input": {"type": "text", "content": "test"},
            "run_name": "test-run",
            "image_count": len(images),
            "images": images,
            "execution": {
                "mode": "sequential",
                "requested_parallelism": 1,
                "max_parallelism": 10,
                "subagent_count": 0,
                "commit_strategy": "coordinator-serial",
            },
            "budget": {
                "per_image_candidates": 8,
                "per_provider_candidates": 2,
                "run_candidates": estimated,
                "confirmed_over_24": estimated > 24,
            },
        }

    def primary(self, form: str) -> str:
        return str(SKILL_ROOT / CATALOG["forms"][form]["primary"])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.serial = 0

    def assignment(self, images=None, count=1):
        if images is None:
            images = [self.image(f"scene_{index}") for index in range(count)]
        return confirm_fixture(self.raw_assignment(images))

    def validate(self, value):
        path = self.root / "assignment.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return manage_run.validate_assignment(path)

    def initialize(self, value=None, effective_parallelism=1):
        path = self.root / "assignment.json"
        path.write_text(json.dumps(self.assignment() if value is None else value), encoding="utf-8")
        result = manage_run.cmd_init(argparse.Namespace(
            assignment=str(path), root=str(self.root / "runs"),
            effective_parallelism=effective_parallelism,
        ))
        return Path(result["run_dir"])

    def png(self, name, size="64x64", color="red", alpha=False):
        path = self.root / name
        subprocess.run(["magick", "-size", size, f"xc:{color}", "-define",
                        f"png:color-type={6 if alpha else 2}", str(path)],
                       check=True, capture_output=True, text=True)
        return path

    def candidate(self, run, *, provider="codex", visual_pass=True, size="64x64"):
        self.serial += 1
        prefix = f"candidate_{self.serial}"
        candidate = self.png(f"{prefix}.png", size=size)
        automatic = self.root / f"{prefix}_automatic.json"
        inspected = subprocess.run([sys.executable, "-B", str(SKILL_ROOT / "scripts/validate-image.py"),
                        str(candidate), "--write-json", str(automatic)],
                       check=False, capture_output=True, text=True)
        self.assertIn(inspected.returncode, (0, 1), inspected.stderr)
        overlay = self.png(f"{prefix}_overlay.png", color="blue")
        visual = visual_qa("semi-chibi", CATALOG["forms"]["semi-chibi"]["mean_head_ratio"])
        visual["candidate_sha256"] = manage_run.sha256(candidate)
        visual["form_evidence"].update(measurement_overlay=str(overlay),
                                     measurement_overlay_sha256=manage_run.sha256(overlay))
        if not visual_pass:
            visual.update(verdict="FAIL", defects=["Synthetic identity defect"],
                          targeted_retry="Restore the fin ears")
            visual["gates"]["I1"] = "FAIL"
        visual_path = self.root / f"{prefix}_visual.json"
        manage_run.write_json(visual_path, visual)
        prompt = self.root / f"{prefix}.txt"
        prompt.write_text("Synthetic Whale-chan prompt.", encoding="utf-8")
        return argparse.Namespace(run_dir=str(run), image="01_scene_0", provider=provider,
            model="synthetic-model", candidate=str(candidate), prompt_file=str(prompt),
            automatic_json=str(automatic), visual_json=str(visual_path), provider_size=None,
            transport="builtin" if provider == "codex" else None)
