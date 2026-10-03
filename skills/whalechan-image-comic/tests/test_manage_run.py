from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
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


TEXT_STYLE = "06_top-bottom-punchline"


def text_style_reference(style: str = TEXT_STYLE) -> dict:
    return {
        "id": "text-style",
        "path": str(SKILL_ROOT / f"assets/text-style-templates/{style}/reference.webp"),
        "roles": ["typography"],
        "instruction": "Apply typography treatment only",
    }



def confirm_fixture_selection(value: dict, choices: list[dict] | None = None) -> dict:
    """Synthetic two-turn approval for tests only; never user authorization."""
    if choices is None:
        counts = {}
        for image in value["images"]:
            counts[image["idea_id"]] = counts.get(image["idea_id"], 0) + 1
        choices = [{"choice": option["choice"], "count": counts[option["idea_id"]]}
                   for option in value["proposal"]["options"] if option["idea_id"] in counts]
    value["selection"] = {"proposal_sha256": manage.contract_hash(value["proposal"]),
                          "user_reply": "Synthetic Gate 1 choice", "choices": choices, "adjustments": []}
    value["confirmation"] = {"status": "confirmed", "user_reply": "Synthetic Gate 2 confirmation",
                             "summary_sha256": manage.selection_summary(value)["summary_sha256"]}
    return value



# One passing idea per comedy direction, so the fixture exercises every carrier.
DIRECTION_FIXTURES = [
    ("reversal", {"expectation": "Fix the punctuation", "reversal": "She builds a factory instead"}),
    ("exposure", {"surface": "Calm expert pose", "truth": "She never found the comma", "exposure": "The factory log shows zero commas"}),
    ("escalation", {"steps": ["She checks one line", "She audits the chapter", "She builds a comma factory"]}),
    ("recognition", {"situation": "Proofreading late at night", "recognition": "The missing comma was in the title all along"}),
    ("character", {"trait": "rice as compute currency", "trigger": "The comma hunt drains her compute"}),
]


def legacy_assignment() -> dict:
    pool = []
    for number in range(1, 9):
        direction, carrier = DIRECTION_FIXTURES[(number - 1) % len(DIRECTION_FIXTURES)]
        item = {
            "id": f"idea_{number:02d}",
            "premise": f"premise {number}",
            "direction": direction,
            **copy.deepcopy(carrier),
            "punchline": f"punchline {number}",
            "personality": ["serious", "malicious"],
            "fact_anchor": "missing comma",
            "scene": f"scene {number}",
            "mechanism": f"mechanism {number}",
            "gate_reason": "The reversal is visible and source-specific.",
            "gate": "PASS" if number <= 5 else "FAIL",
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
        style = TEXT_STYLE if index % 2 == 0 else "03_blue-banner"
        images.append(
            {
                "name": f"comic_{index + 1}",
                "source_rank": rank,
                "idea_id": f"idea_{rank:02d}",
                "execution": execution,
                "execution_note": f"Distinct consequence {index + 1}",
                "composition": {
                    "shot": "wide action view", "staging": f"factory position {index + 1}",
                    "text_placement": "above the action", "reason": "Keeps the punctuation visible",
                },
                "proportion_check": "measured",
                "fact_anchor": "missing comma",
                "premise": f"premise {rank}",
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
                "text_style": style,
                "text_style_reason": "Separate the setup from the oversized factory-service boast.",
                "references": [text_style_reference(style)],
                "dialogue_plan": [
                    {"text_index": line, "panel": min(line + 1, panels),
                     "speaker": "whalechan", "delivery": "speech"}
                    for line in range(2)
                ],
                "cast_plan": [],
            }
        )
    value = {
        "schema_version": 11,
        "run_name": "comma-factory",
        "input": {
            "type": "text", "content": "input", "language": "zh-CN", "fact_anchor": "missing comma", "participants": [],
            "source_analysis": {
                "source_event": "A comma is missing", "comic_target": "Disproportionate effort",
                "tone": "playful", "language_notes": "Simplified Chinese", "user_constraints": [],
                "native_direction": {"direction": "reversal", "reason": "The source turns a tiny fix into a factory."},
            },
        },
        "selection_reason": "These premises expose the disproportionate response.",
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
    value["proposal"] = {
        "revision": 1, "fact_anchor": "missing comma",
        "native_direction": copy.deepcopy(value["input"]["source_analysis"]["native_direction"]),
        "recommended_choices": ["A"], "recommendation_reason": "The factory reveal is clearest",
        "options": [
            {"choice": choice, "title": f"Proposal {choice}", "idea_id": idea["id"],
             "premise": idea["premise"], "scene": idea["scene"], "twist": f"twist {idea['id']}",
             "direction": idea["direction"], "is_native": idea["direction"] == "reversal",
             "staging": "Wide shot with the comma visible", "key_lines": ["缺了个逗号。"],
             "rating": 3, "recommendation_reason": "The visual consequence reveals the mistake"}
            for choice, idea in zip("ABCDE", pool[:5])
        ],
    }
    return confirm_fixture_selection(value)



def confirm_fixture_plan(value: dict) -> dict:
    """Synthetic single approval for tests only; never user authorization."""
    value["confirmation"] = {"status": "confirmed", "user_reply": "Synthetic plan confirmation",
                             "summary_sha256": manage.selection_summary(value)["summary_sha256"]}
    return value


def assignment() -> dict:
    value = legacy_assignment()
    value["schema_version"] = 12
    value.pop("selection")
    value.pop("confirmation")
    pool = value["creative_pool"]
    for number in (9, 10):
        idea = copy.deepcopy(pool[number - 6])
        idea.update(id=f"idea_{number:02d}", premise=f"premise {number}", scene=f"scene {number}")
        pool.append(idea)
    for index, idea in enumerate(pool, 1):
        for field in ("gate", "gate_reason", "rejection_reason"):
            idea.pop(field, None)
        idea["key_lines"] = [f"任务 {index} 已完成", f"独有结果 {index}。"]
    value["duels"] = [{"a": first["id"], "b": second["id"], "winner": first["id"],
                       "reason": f"{first['id']} has the more immediate visual payoff than {second['id']}."}
                      for index, first in enumerate(pool) for second in pool[index + 1:]]
    value["ranked_ideas"] = [idea["id"] for idea in pool[:5]]
    proposal = value["proposal"]
    proposal.pop("recommended_choices")
    proposal.pop("recommendation_reason")
    for index, (option, image, idea) in enumerate(zip(proposal["options"], value["images"], pool), 1):
        for field in ("choice", "rating", "recommendation_reason"):
            option.pop(field)
        option.update(key_lines=list(idea["key_lines"]), panel_count=image["panel_count"], twist=idea["punchline"],
                      selection_reason=f"Rank {index}: a distinct visible consequence.")
        image.update(source_rank=index, idea_id=idea["id"], premise=idea["premise"], execution=1,
                     core_text=list(idea["key_lines"]))
    value["worker_plan"] = {"coordinator": "main", "max_parallelism": 3,
                            "workers": [{"id": "worker-1", "idea_ids": ["idea_01", "idea_04"]},
                                        {"id": "worker-2", "idea_ids": ["idea_02", "idea_05"]},
                                        {"id": "worker-3", "idea_ids": ["idea_03"]}]}
    value["execution"].update(mode="parallel", requested_parallelism=3)
    return confirm_fixture_plan(value)


def design_evidence(image: dict) -> dict:
    """Synthetic protocol evidence for unit tests, not an image review."""
    return {
        "text_style_match": {"template": image["text_style"], "observed_cues": ["assigned lettering hierarchy and frame"]},
        "dialogue_match": [dict(line, observed_cues=["connector reaches the assigned speaker"]) for line in image["dialogue_plan"]],
        "cast_match": [
            {**{key: member[key] for key in ("participant", "representation", "panels")},
             "observed_cues": ["assigned representation and role contribution"]}
            for member in image["cast_plan"]
        ],
    }



def reviewed_observation(image: dict, candidate_hash: str) -> dict:
    """Synthetic review protocol fixture; never production image evidence."""
    return {
        "review_status": "reviewed",
        "observation": {
            "candidate_sha256": candidate_hash, "reviewer": "unit-test fixture",
            "method": "direct-image-inspection",
            "panels": [{"panel": panel, "observed_scene": "Synthetic factory scene"}
                       for panel in range(1, image["panel_count"] + 1)],
            "text_transcription": list(image["core_text"]),
        },
    }



def selected_assignment(choices):
    value = legacy_assignment()
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
    return confirm_fixture_selection(value, choices)


class RunStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.magick = shutil.which("magick")
        if self.magick is None:
            self.skipTest("ImageMagick is required")
        self.initialize()

    def initialize(self, choices=None):
        root = Path(self.temporary.name)
        assignment_path = root / "assignment.json"
        value = assignment() if choices is None else selected_assignment(choices)
        assignment_path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        result = manage.cmd_init(argparse.Namespace(
            assignment=str(assignment_path), root=str(root / "runs"), effective_parallelism=None,
        ))
        self.run_dir = Path(result["run_dir"])
        frozen = manage.read_json(self.run_dir / "assignment.json")
        self.image_spec = frozen["images"][0]
        self.image = self.image_spec["id"]
        return frozen

    def files(self, number: int, verdict: str = "FAIL") -> argparse.Namespace:
        root = self.run_dir / f"test-input-{number}"
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
            **design_evidence(self.image_spec),
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
                "acceptance_range": [2.695, 2.995],
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
            "expression_match": [dict(plan, observed_cues=["synthetic assigned expression"],
                                      forbidden_cues_present=[])
                                 for plan in self.image_spec["expression_plan"]],
        }
        if verdict == "FAIL":
            gates["J1"] = "FAIL"
            defects = ["The punchline is flat"]
            targeted = "Replace the punchline"
        visual.write_text(json.dumps({**reviewed_observation(self.image_spec, candidate_hash), "verdict": verdict, "candidate_sha256": candidate_hash, "gates": gates, "evidence": evidence, "defects": defects, "targeted_retry": targeted}), encoding="utf-8")
        return argparse.Namespace(run_dir=str(self.run_dir), image=self.image, provider="codex", model="test", candidate=str(candidate), prompt_file=str(prompt), automatic_json=str(automatic), visual_json=str(visual), transport="builtin")

    def test_budget_is_per_image_and_stops_at_three(self) -> None:
        for number in range(1, 4):
            manage.record_image(self.files(number), component=False)
        with self.assertRaisesRegex(manage.RunError, "budget is exhausted"):
            manage.record_image(self.files(4), component=False)
        _run, _assignment, manifest = manage.load_run(str(self.run_dir))
        self.assertEqual(len(manifest["images"][self.image]["attempts"]), 3)
        self.assertEqual(len(manifest["images"]["02_comic_2"]["attempts"]), 0)


    def test_frozen_assignment_and_existing_prompt_are_protected(self):
        command = [sys.executable, "-B", str(SKILL_ROOT / "scripts/build-prompt.py"),
                   "--run-dir", str(self.run_dir), "--image", self.image]
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        prompt = Path(json.loads(first.stdout)["prompt_file"])
        original = prompt.read_bytes()
        repeated = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(repeated.returncode, 2)
        self.assertEqual(prompt.read_bytes(), original)
        frozen_path = self.run_dir / "assignment.json"
        frozen = manage.read_json(frozen_path)
        frozen["images"][0]["core_text"] = ["Changed after confirmation"]
        manage.write_json(frozen_path, frozen)
        with self.assertRaisesRegex(manage.RunError, "Frozen assignment SHA-256"):
            manage.load_run(str(self.run_dir))

    def test_complete_and_partial_delivery_group_by_idea(self):
        frozen = manage.read_json(self.run_dir / "assignment.json")
        for number, image in enumerate(frozen["images"], 1):
            self.image_spec, self.image = image, image["id"]
            manage.record_image(self.files(number, "PASS"), component=False)
            manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=False))
        self.assertEqual((result["status"], result["passed"], result["expected"]), ("complete", 5, 5))
        self.assertEqual([len(item["final_paths"]) for item in result["proposals"]], [1] * 5)
        self.assertTrue(all(not item["missing"] for item in result["proposals"]))
        self.assertEqual(result["unverified_provider_audits"], [])
        frozen = self.initialize()
        manage.record_image(self.files(1, "PASS"), component=False)
        manage.cmd_promote(argparse.Namespace(run_dir=str(self.run_dir), image=self.image))
        with self.assertRaisesRegex(manage.RunError, "viable attempt"):
            manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        for image in frozen["images"][1:]:
            for provider in manage.PROVIDERS:
                manage.cmd_record_error(argparse.Namespace(run_dir=str(self.run_dir), image=image["id"],
                                                            provider=provider, model="test", category="unavailable", details="offline test"))
        result = manage.cmd_finalize(argparse.Namespace(run_dir=str(self.run_dir), allow_partial=True))
        self.assertEqual((result["status"], result["passed"], result["expected"]), ("partial", 1, 5))
        self.assertEqual(sum(len(item["missing"]) for item in result["proposals"]), 4)



if __name__ == "__main__":
    unittest.main()
