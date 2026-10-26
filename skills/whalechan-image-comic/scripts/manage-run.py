#!/usr/bin/env python3
"""Validate, initialize, audit, and finalize Whale-chan comic runs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "asset-catalog.json"
EXPRESSION_PRESETS_PATH = SKILL_ROOT / "references" / "expression-presets.json"
EXAGGERATION_TIERS_PATH = SKILL_ROOT / "references" / "exaggeration-tiers.json"
PROVIDERS = ("codex", "openai", "nano-banana", "seedream")
FORM_ORDER = ("standard", "compact", "semi-chibi", "chibi", "super-deformed")
FORMS = set(FORM_ORDER)
ASSET_CATALOG_SCHEMA_VERSION = 4
EXPRESSION_PRESETS_SCHEMA_VERSION = 2
EXAGGERATION_TIERS_SCHEMA_VERSION = 1
ASSIGNMENT_SCHEMA_VERSION = 20
SUPPORTED_ASSIGNMENT_VERSIONS = (19, 20)
QA_CONTRACT_VERSION = 11
MANIFEST_SCHEMA_VERSION = 1
INPUT_TYPES = ("text", "image", "screenshot", "chat-log", "dialogue", "other")
TEXT_STYLES = {
    "01_shy-blue-sticker", "02_keyword-bubble", "03_blue-banner",
    "04_burst-command", "05_outline-poster", "06_top-bottom-punchline",
    "07_casual-dialogue", "08_confrontation-dialogue", "09_vertical-panic",
    "10_manga-impact",
}
FULL_GATES = {"J1", "K1", "I1", "C1", "P1", "T1", "A1", "V1"}
CONFIGURABLE_GATES = FULL_GATES | {"S1", "O1", "B1", "X1", "H1", "E1"}
ADVANCE_ERRORS = {"unavailable", "authentication", "quota", "rate_limit", "timeout", "service", "capability"}
MAX_CANDIDATES = 3
# Each comedy direction names the fields that carry its laugh; only reversal needs expectation/reversal.
DIRECTION_CARRIERS = {
    "reversal": ("expectation", "reversal"),
    "exposure": ("surface", "truth", "exposure"),
    "escalation": ("steps",),
    "recognition": ("situation", "recognition"),
    "character": ("trait", "trigger"),
}
# Legacy UI renderings; new assignments use saved locale packs.
DIRECTION_LABELS = {
    "zh": {"reversal": "反转", "exposure": "暴露", "escalation": "升级",
           "recognition": "共鸣", "character": "角色梗"},
    "en": {"reversal": "Reversal", "exposure": "Exposure", "escalation": "Escalation",
           "recognition": "Recognition", "character": "Character gag"},
}
TIER_LABELS = {
    "zh": {"A": "A-日漫冲击", "B": "B-漫画爆发", "C": "C-克制冷幽默"},
    "en": {"A": "A-Manga impact", "B": "B-Comic outburst", "C": "C-Restrained deadpan"},
}
FORM_LABELS = {
    "standard": "标准版", "compact": "紧凑版", "semi-chibi": "半 Q 版",
    "chibi": "Q 版", "super-deformed": "超 Q 版",
}
PLAN_TEXT = {
    "zh": {
        "tiered_header": "| 序号 | 创意 | 方向 | 格数 | 档位 | 场景／分镜 | 关键台词 | 入选理由 |",
        "colon": "：", "list": "、", "override": "（用户指定）",
        "panels": "> 格数分布：", "panel_item": "{count} 格 ×{n}", "tiers": " ｜ 档位分布：",
        "legend": "档位：A-日漫冲击 · B-漫画爆发 · C-克制冷幽默；括号内为刻意压低的维度。",
        "proportion": "> 本次目标头身比：",
        "panel_override": "格数按用户指定覆盖默认三种格数：",
        "tier_override": "档位按用户指定覆盖默认 A/B/C 覆盖：",
        "question": "**确认按以上创意、张数和 sub-agent 分配开始生成吗？**",
    },
    "en": {
        "tiered_header": "| # | Idea | Direction | Panels | Tier | Scene / staging | Key lines | Why selected |",
        "colon": ": ", "list": ", ", "override": "(user override)",
        "panels": "> Panels: ", "panel_item": "{count}-panel ×{n}", "tiers": " | Tiers: ",
        "legend": "Tiers: A-Manga impact · B-Comic outburst · C-Restrained deadpan; parentheses name deliberately lowered axes.",
        "proportion": "> Target head-to-body ratio: ",
        "panel_override": "Panel counts follow the user's override of the default 1/2/4 coverage: ",
        "tier_override": "Tiers follow the user's override of the default A/B/C coverage: ",
        "question": "**Start generating with the ideas, image count and sub-agent allocation above?**",
    },
}
RHYTHM_TYPES = {"triple", "pause", "callback", "deadpan"}
# Lowest to highest; the order compares a panel tier with the landing tier.
TIER_ORDER = ("C", "B", "A")
DEFAULT_TIER_POLICY = {"mode": "target-ratio", "ratio": {"A": 3, "B": 1, "C": 1}}
PERFORMANCE_LEVELS = ("grounded", "heightened", "punchline_peak", "manga_burst")
DELIVERIES = {"speech", "thought", "caption", "label", "sfx"}
IMAGE_FIELDS = {
    "name", "id", "idea_id", "source_rank", "execution", "execution_note",
    "composition", "proportion_check", "qa_contract_version",
    "fact_anchor", "premise", "punchline", "why_funny", "personality",
    "panel_count", "layout", "exaggeration", "landing_panel",
    "contrast", "effects_plan", "output", "expression_plan",
    "action_plan", "style", "costume", "background", "core_text",
    "text_style", "text_style_reason", "dialogue_plan", "cast_plan",
    "proportion", "proportion_sha256", "identity_anchor_form", "references",
    "rhythm", "lettering_description",
}
REFERENCE_ROLES = {
    "identity", "style", "pose_action", "composition", "costume",
    "background", "typography", "proportion",
}
STYLE_MODES = {"canonical", "custom"}
COSTUME_MODES = {"canonical", "custom"}
BACKGROUND_MODES = {"solid", "custom"}
PROPORTION_MODES = {"preset", "custom"}
DEFAULT_STYLE = "canonical clean rounded cel-shaded Whale-chan style"
DEFAULT_COSTUME = "canonical navy-and-white ornate maid outfit"
DEFAULT_BACKGROUND = "pure white #FFFFFF"
DEFAULT_FORM = "semi-chibi"
MEASUREMENT_METHOD = "pose-neutralized-skeleton"
BODY_SEGMENT_NAMES = ("chin_to_pelvis", "pelvis_to_knee", "knee_to_sole")
OUTPUT_FORMAT = "png"
DEFAULT_ASPECT_RATIO = "1:1"
DEFAULT_RECOMMENDED_RESOLUTION = "1024x1024"


class RunError(RuntimeError):
    pass


def contract_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def native_direction(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"direction", "reason"}:
        raise RunError(f"{label} must be {{direction, reason}}")
    if value["direction"] is not None and value["direction"] not in DIRECTION_CARRIERS:
        raise RunError(f"{label}.direction must be one of {', '.join(DIRECTION_CARRIERS)} or null")
    text(value["reason"], f"{label}.reason")
    return value


def direction_carriers(item: dict[str, Any], label: str) -> str:
    direction = item.get("direction")
    if direction not in DIRECTION_CARRIERS:
        raise RunError(f"{label}.direction must be one of {', '.join(DIRECTION_CARRIERS)}")
    for field in DIRECTION_CARRIERS[direction]:
        if field == "steps":
            steps = string_list(item.get("steps"), f"{label}.steps", 3)
            if len(steps) < 3:
                raise RunError(f"{label}.steps must contain at least 3 escalating steps")
        else:
            text(item.get(field), f"{label}.{field}")
    return direction


def resolve_warnings(found: list[dict[str, Any]], dispositions: Any, label: str) -> None:
    """Soft warnings never block a justified choice, but each needs a written disposition."""
    if dispositions is None:
        dispositions = []
    if not isinstance(dispositions, list) or any(not isinstance(item, dict) for item in dispositions):
        raise RunError(f"{label} must be a list of {{code, reason}} objects")
    resolved = {item.get("code") for item in dispositions if isinstance(item.get("reason"), str) and item["reason"].strip()}
    for warning in found:
        if warning["code"] not in resolved:
            raise RunError(f"{warning['message']}; revise it or add {label} "
                           f"{{\"code\": \"{warning['code']}\", \"reason\": <source-grounded reason>}}")


def language_policy():
    import importlib.util
    spec = importlib.util.spec_from_file_location("task_language_policy", Path(__file__).with_name("language_policy.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def language_contract(value, images=True):
    if value.get("schema_version") != ASSIGNMENT_SCHEMA_VERSION:
        return {}
    try:
        return language_policy().validate(value, comic=True, images=images)
    except ValueError as error:
        raise RunError(str(error)) from error


def selection_summary(value):
    return plan_summary(value)


def validate_approval(value: dict[str, Any]) -> dict[str, Any]:
    summary = plan_summary(value)
    confirmation = value.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("status") != "confirmed":
        raise RunError("Single gate confirmation is required before generation")
    text(confirmation.get("user_reply"), "confirmation.user_reply")
    if confirmation.get("summary_sha256") != summary["summary_sha256"]:
        raise RunError("Single gate confirmation is stale; display the updated plan and wait again")
    images = value.get("images")
    expected = {item["idea_id"] for item in summary["choices"]}
    if (not isinstance(images, list) or any(not isinstance(item, dict) for item in images)
            or Counter(item.get("idea_id") for item in images) != Counter(expected)):
        raise RunError("images must contain the selected ideas exactly once each")
    options = {item["idea_id"]: item for item in value["proposal"]["options"]}
    for image in images:
        option = options[image["idea_id"]]
        if (image.get("execution") != 1 or image.get("premise") != option["premise"]
                or image.get("panel_count") != option["panel_count"]
                or image.get("core_text") != option["key_lines"]):
            raise RunError("Each image must preserve its confirmed premise, panel_count and key_lines, execution=1")
        contrast = image.get("contrast")
        planned = None if not isinstance(contrast, dict) else {
            "axes": contrast.get("axes"), "lowered_to": contrast.get("lowered_to")}
        if image.get("exaggeration") != option["exaggeration"] or planned != option.get("contrast"):
            raise RunError("Each image must preserve its confirmed exaggeration tier and contrast")
    return summary


def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def planning_draft(value: dict[str, Any], label: str = "Planning draft") -> dict[str, Any]:
    if value.get("schema_version") not in SUPPORTED_ASSIGNMENT_VERSIONS:
        raise RunError(f"{label} must use schema_version {ASSIGNMENT_SCHEMA_VERSION}")
    return value


def cmd_render_proposal(args: argparse.Namespace) -> dict[str, Any]:
    value = planning_draft(read_json(Path(args.draft).resolve()))
    summary = plan_summary(value)
    return {**summary, "markdown": plan_markdown(value, summary, getattr(args, "language", "zh"))}


def cmd_summarize_selection(args: argparse.Namespace) -> dict[str, Any]:
    return cmd_render_proposal(args)


def target_images(value):
    try:
        return extension_module("selection_contract").count(value.get("target_images"))
    except ValueError as exc:
        raise RunError(str(exc)) from exc


def priority_results(value):
    try:
        from types import SimpleNamespace
        return extension_module("selection_contract").ranking(SimpleNamespace(**globals()), value)
    except ValueError as exc:
        raise RunError(str(exc)) from exc


def plan_summary(value: dict[str, Any]) -> dict[str, Any]:
    planning_draft(value)
    language_contract(value)
    ranking = priority_results(value)
    n = target_images(value)
    selected = [item["idea_id"] for item in ranking[:n]]
    if value.get("ranked_ideas") != selected:
        raise RunError("ranked_ideas must follow the selected ranking order")
    if "selection" in value:
        raise RunError("The ranked plan has one confirmation, not a user selection record")
    text(value.get("selection_reason"), "selection_reason")
    source = value.get("input", {})
    anchor = text(source.get("fact_anchor"), "input.fact_anchor")
    native = native_direction(source.get("source_analysis", {}).get("native_direction"), "input.source_analysis.native_direction")
    ideas = {item["id"]: item for item in value["creative_pool"]}
    for idea in ideas.values():
        for field in ("premise", "punchline", "scene", "mechanism"):
            text(idea.get(field), f"{idea['id']}.{field}")
        if any(field in idea for field in ("gate", "gate_reason", "rejection_reason")):
            raise RunError("Candidate ideas have no PASS/FAIL gate or rejection_reason")
        if idea.get("fact_anchor") != anchor:
            raise RunError("idea.fact_anchor must match input.fact_anchor")
        direction_carriers(idea, idea["id"])
        if len(string_list(idea.get("personality"), "idea.personality", 2)) != 2:
            raise RunError("idea.personality must contain exactly two traits")
        string_list(idea.get("key_lines"), "idea.key_lines")
    proposal = value.get("proposal")
    if not isinstance(proposal, dict) or type(proposal.get("revision")) is not int or proposal["revision"] < 1:
        raise RunError("proposal requires a positive integer revision")
    if proposal.get("fact_anchor") != anchor or proposal.get("native_direction") != native:
        raise RunError("proposal fact_anchor/native_direction must match input.source_analysis")
    if any(k in proposal for k in ("recommended_choices", "recommendation_reason")):
        raise RunError("The ranked proposal is informational; recommendations are not choices")
    options = proposal.get("options")
    if (not isinstance(options, list) or any(not isinstance(i, dict) for i in options)
            or [i.get("idea_id") for i in options] != selected):
        raise RunError("proposal.options must contain the selected ranked ideas in order")
    for option in options:
        idea = ideas[option["idea_id"]]
        for field in ("title", "premise", "scene", "twist", "staging", "selection_reason"):
            text(option.get(field), f"proposal.{field}")
        if any(k in option for k in ("choice", "rating", "recommendation_reason")):
            raise RunError("The ranked proposal has no user choice or rating")
        if (option["premise"] != idea["premise"] or option["scene"] != idea["scene"]
                or option["twist"] != idea["punchline"] or option.get("direction") != idea["direction"]):
            raise RunError("proposal premise, scene, twist/punchline and direction must match its idea")
        if type(option.get("is_native")) is not bool or option["is_native"] != (idea["direction"] == native["direction"]):
            raise RunError("proposal.is_native must accurately match the source direction")
        string_list(option.get("key_lines"), "proposal.key_lines")
        if (option["key_lines"] != idea["key_lines"]):
            raise RunError("Selected candidate key lines are frozen")
        if type(option.get("panel_count")) is not int or option["panel_count"] not in {1, 2, 4}:
            raise RunError("proposal.panel_count must be 1, 2, or 4")
    policy = value.get("panel_policy", {"mode": "narrative"})
    if not isinstance(policy, dict) or policy.get("mode") not in {"narrative", "user-override"}:
        raise RunError("panel_policy.mode must be narrative or user-override")
    if policy["mode"] == "user-override":
        text(policy.get("user_instruction"), "panel_policy.user_instruction")
    elif n >= 3 and {option["panel_count"] for option in options} != {1, 2, 4}:
        raise RunError("The selected comics must cover three panel counts: 1, 2 and 4")
    tier_policy = exaggeration_policy(value, options)
    if "images" in value:
        images = value["images"]
        if (not isinstance(images, list) or any(not isinstance(i, dict) for i in images)
                or Counter(i.get("idea_id") for i in images) != Counter(selected)):
            raise RunError("images must contain the selected ideas exactly once each")
    if ("images" in value):
        if [i["idea_id"] for i in value["images"]] != selected:
            raise RunError("images must follow the selected priority order")
        for image, option in zip(value["images"], options, strict=True):
            if image.get("execution") != 1 or any(image.get(a) != option.get(b) for a, b in (
                ("premise", "premise"), ("core_text", "key_lines"),
                ("panel_count", "panel_count"), ("exaggeration", "exaggeration"))):
                raise RunError("Detailed images must preserve selected premise, exact key lines, panels and tier")
    proportions = []
    form_profiles = read_json(CATALOG_PATH)["character_forms"]
    for option in options:
        if not isinstance(option.get("proportion"), dict):
            raise RunError("Every proposal option must record proportion")
        proportion, _anchor = normalize_proportion(option, form_profiles, "proposal")
        proportions.append(proportion)
        for image in value.get("images", []):
            if image["idea_id"] == option["idea_id"]:
                actual, _anchor = normalize_proportion(image, form_profiles, "image")
                if actual != proportion:
                    raise RunError("Each image must preserve its confirmed proportion")
    summary = worker_summary(value, selected, ranking, policy, tier_policy)
    summary["proportions"] = proportions
    return summary


def normalize_tier_policy(policy):
    if not isinstance(policy, dict) or policy.get("mode") not in {"target-ratio", "user-override"}:
        raise RunError("exaggeration_policy.mode must be target-ratio or user-override")
    if policy["mode"] == "user-override":
        text(policy.get("user_instruction"), "exaggeration_policy.user_instruction")
    elif policy["mode"] == "target-ratio":
        ratio = policy.get("ratio")
        if (policy != DEFAULT_TIER_POLICY or not isinstance(ratio, dict)
                or any(type(n) is not int for n in ratio.values())):
            raise RunError("target-ratio requires ratio A=3, B=1, C=1")
    return copy.deepcopy(policy)


def exaggeration_policy(value: dict[str, Any], options: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate the current source tier policy."""
    tiers = exaggeration_tiers()
    for option in options:
        tier = option.get("exaggeration")
        if tier not in TIER_ORDER:
            raise RunError("proposal.exaggeration must be A, B or C")
        contrast = option.get("contrast")
        if contrast is not None:
            if not isinstance(contrast, dict) or set(contrast) != {"axes", "lowered_to"}:
                raise RunError("proposal.contrast must be null or {axes, lowered_to}")
            contrast_axes(contrast["axes"], tiers, "proposal.contrast.axes")
            if contrast["lowered_to"] not in TIER_ORDER or tier_rank(contrast["lowered_to"]) >= tier_rank(tier):
                raise RunError("proposal.contrast.lowered_to must be below the option's tier")
    policy = normalize_tier_policy(value.get("exaggeration_policy"))
    if policy["mode"] == "user-override":
        return policy
    counts = Counter(option["exaggeration"] for option in options)
    if policy["mode"] == "target-ratio" and target_images(value) == 5 and counts != policy["ratio"]:
        difference = {tier: policy["ratio"][tier] - counts[tier] for tier in "ABC"}
        raise RunError(f"Five-image target requires A=3, B=1, C=1; actual={dict(counts)}; target-minus-actual={difference}")
    if target_images(value) >= 3 and set(counts) != set(TIER_ORDER):
        raise RunError("The selected comics must cover exaggeration tiers A, B and C")
    return policy


def worker_summary(value: dict[str, Any], selected: list[str], ranking: list[dict[str, Any]],
                   policy: dict[str, Any], tier_policy: dict[str, Any]) -> dict[str, Any]:
    plan = value.get("worker_plan")
    if not isinstance(plan, dict) or plan.get("coordinator") != "main":
        raise RunError("worker_plan requires coordinator=main")
    execution = role_execution(value.get("execution"))
    extension_module("provider_policy").validate(execution.get("tool"))
    if plan != {"coordinator": "main", "allocation": "dynamic"}:
        raise RunError("worker_plan requires dynamic allocation")
    proposal = value["proposal"]
    rows = [{"choice": str(n), "title": item["title"], "idea_id": item["idea_id"], "count": 1}
            for n, item in enumerate(proposal["options"], 1)]
    keys = ("proposal", "creative_pool", "ranked_ideas", "selection_reason", "worker_plan",
            "target_images", "source_id", "author_agent_ids", "concept_task_id", "pool_sha256", "selection_review")
    payload = {key: value[key] for key in keys}
    if value.get("schema_version") == 20:
        payload["language_contract"] = language_contract(value)
        payload["image_titles"] = [i["title"] for i in value["images"]]
        payload["prompt_templates"] = language_policy().locale(value, language_policy().effective(value, "prompt"), "prompt")
    payload.update(panel_policy=policy, execution=execution, input=value["input"])
    payload["exaggeration_policy"] = tier_policy
    payload["review_workflow"] = {"version": 1, "candidate_reviews": 1,
                                  "minor_tolerance": True, "collection_repair_rounds": 1,
                                  "regeneration_sources": ["single_image_qa", "collection_review"]}
    payload["visual_plan"] = visual_prompt().contract(value)
    return {"proposal_count": len(selected), "image_count": len(selected), "choices": rows, "adjustments": [],
            "worker_plan": plan, "maximum_total": len(selected) * MAX_CANDIDATES, "standings": ranking,
            "execution": execution,
            "options": proposal["options"], "panel_policy": policy,
            "exaggeration_policy": tier_policy,
            "visual_plan": payload["visual_plan"],
            "summary_sha256": contract_hash(payload)}


def distribution_line(options: list[dict[str, Any]], panel_policy: dict[str, Any],
                      tier_policy: dict[str, Any], language: str = "zh") -> str:
    words = PLAN_TEXT[language]
    panels = Counter(item["panel_count"] for item in options)
    tiers = Counter(item["exaggeration"] for item in options)

    def mark(policy: dict[str, Any]) -> str:
        return " " + (words["override"] if policy.get("mode") == "user-override" else "✓")

    line = (words["panels"] + " · ".join(words["panel_item"].format(count=count, n=panels[count]) for count in (1, 2, 4))
            + mark(panel_policy) + words["tiers"]
            + " · ".join(f"{TIER_LABELS[language][tier]} ×{tiers[tier]}" for tier in reversed(TIER_ORDER)) + mark(tier_policy))
    if tier_policy.get("mode") == "target-ratio":
        actual = " / ".join(f"{100 * tiers[t] / len(options):.1f}%" for t in "ABC")
        deviation = " / ".join(f"{100 * tiers[t] / len(options) - 20 * tier_policy['ratio'][t]:+.1f}" for t in "ABC")
        line += (f"\n\n档位目标 A:B:C＝3:1:1（60% / 20% / 20%）；实际占比 {actual}；偏差 {deviation} 个百分点。" if language == "zh" else
                 f"\n\nTier target A:B:C=3:1:1 (60% / 20% / 20%); actual {actual}; deviation {deviation} percentage points.")
        line += (" 五张配比已满足。" if language == "zh" else " Five-image ratio satisfied.") if len(options) == 5 else (
            " 按内容自主分配，接近目标的合理性由策划审查。" if language == "zh" else " Author allocates by content and reviews closeness to the target.")
    return line


def proportion_line(proportions: list[dict[str, Any]], language: str) -> str:
    words = PLAN_TEXT[language]
    groups: dict[str, list[str]] = {}
    for index, proportion in enumerate(proportions, 1):
        ratio = str(proportion["target_head_ratio"])
        preset = proportion["preset"]
        if language == "zh":
            name = f"{FORM_LABELS[preset]}，{preset}" if preset else "自定义"
            label = f"{ratio} 头身（{name}）"
        else:
            label = f"{ratio} heads ({preset or 'custom'})"
        groups.setdefault(label, []).append(str(index))
    if len(groups) == 1:
        label = next(iter(groups))
        return words["proportion"] + (f"{label}，适用于全部 {len(proportions)} 张。" if language == "zh"
                                      else f"{label}, for all {len(proportions)} images.")
    if language == "zh":
        return words["proportion"] + "；".join(f"第 {'、'.join(indices)} 张为 {label}"
                                               for label, indices in groups.items()) + "。"
    return words["proportion"] + "; ".join(f"Images {', '.join(indices)}: {label}"
                                           for label, indices in groups.items()) + "."


def plan_markdown(value: dict[str, Any], summary: dict[str, Any] | None = None, language: str = "zh") -> str:
    summary = summary or plan_summary(value)
    if value.get("schema_version") == 20:
        return extension_module("localized_plan").render(__import__("types").SimpleNamespace(**globals()), value, summary)
    language = language or "zh"
    words = dict(PLAN_TEXT[language])
    n = target_images(value)
    words["totals"] = f"总计 {n} 张；最多 {3*n} 次出图。" if language == "zh" else f"{n} images; at most {3*n} image-producing calls."
    words["route"] = "从冻结的2N候选中独立排序选N个；筛选不是生图授权。" if language == "zh" else "Independent priority selection from 2N candidates; selection is not generation consent."
    directions = DIRECTION_LABELS[language]
    options = value["proposal"]["options"]
    tier_policy = summary.get("exaggeration_policy")
    tiers = exaggeration_tiers()
    lines = [words["tiered_header"], "|---|---|---|---|---|---|---|---|"]
    has_cast = any(c.get('character_id') for image in summary['visual_plan'] for c in image['cast'])
    if has_cast:
        code = language_policy().tag(language)
        cast_words = language_policy().locale(value, code, 'cast')
        lines[0] = lines[0].rstrip(' |') + ' | ' + cast_words['heading'] + ' |'
        lines[1] += '---|'
    for index, item in enumerate(options, 1):
        staging = item["scene"] + "\n" + item["staging"]
        visual = next(v for v in summary["visual_plan"] if v["idea_id"] == item["idea_id"])
        staging = "\n".join(f"{action['panel']}: {action['action']} {expression['visual_description']}"
                            for action, expression in zip(visual["actions"], visual["expressions"], strict=True))
        cells = [str(index), item["title"] + words["colon"] + item["premise"],
                 directions[item["direction"]] + words["colon"] + item["twist"], str(item["panel_count"]),
                 tier_label(item, tiers, language), staging,
                 "\n".join(item["key_lines"]), item["selection_reason"]]
        if has_cast:
            cells.append(model_cast().plan_text(visual["cast"], cast_words, value, code))
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in cells) + " |")
    lines.extend(["", distribution_line(options, value.get("panel_policy", {"mode": "narrative"}), tier_policy, language),
                  "", proportion_line(summary["proportions"], language), "", words["legend"]])
    limits = summary["execution"]["role_limits"]
    detail = (f"分类 sub-agent 上限：策划 {limits['planning']}；生图 {limits['generation']} / Codex {limits['codex_generation']}；集合 {limits['collection']}；交付 {limits['delivery']}。主代理只编排；实际启动受运行时槽位和整批上限约束。" if language == "zh" else
              f"Independent sub-agent limits: {limits}. Main coordinates only; runtime slots and batch cap constrain actual dispatch.")
    detail += f" 创意筛选上限：{limits['selection']}。" if language == "zh" else f" Selection limit: {limits['selection']}."
    lines.extend(["", words["totals"], "", words["route"], "", detail])
    if value.get("panel_policy", {}).get("mode") == "user-override":
        lines.extend(["", words["panel_override"] + markdown_cell(value["panel_policy"]["user_instruction"])])
    if (tier_policy or {}).get("mode") == "user-override":
        lines.extend(["", words["tier_override"] + markdown_cell(tier_policy["user_instruction"])])
    review_note = ("审阅：每个候选看图一次；轻微瑕疵可接受；每组五图拼图审阅一次。"
                   "集合最多返工一轮并复验一次，与单图 QA 共用每张三次产图预算。"
                   "主代理不重复看图复核，技术检查失败不触发生图。" if language == "zh" else
                   "Review: inspect each candidate once; accept minor issues; review one five-image contact sheet. "
                   "At most one collection repair round and focused recheck share each image's three-call budget. "
                   "No coordinator visual rereview; technical checks never trigger regeneration.")
    review_note = review_note.replace("每组五图", f"每组{target_images(value)}图").replace("five-image", f"{target_images(value)}-image")
    if target_images(value) < 3:
        lines.append("少量方案按内容选择格数和档位，不强制三类覆盖。" if language == "zh" else "Small sets choose panels and tiers by content; full coverage is not required.")
    lines.extend(["", review_note])
    lines.extend(["", words["question"]])
    tool = summary["execution"]["tool"]
    label = "本批工具：" if language == "zh" else "Batch tool: "
    policy = "；服务错误即暂停，不自动重试或切换。" if language == "zh" else "; service errors pause; no automatic retry or switch."
    lines.append("\n" + label + tool["provider"] + " / " + tool["transport"] + " / " + tool["model"] + policy)
    return "\n".join(lines) + "\n"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RunError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RunError(f"Expected a JSON object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunError(f"{label} must be a non-empty string")
    return value.strip()


def canonical_aspect_ratio(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise RunError(f"{label} must use positive integers as W:H")
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", value.strip())
    if match is None:
        raise RunError(f"{label} must use positive integers as W:H")
    width, height = (int(item) for item in match.groups())
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def aspect_matches(width: int, height: int, ratio: str) -> bool:
    ratio_width, ratio_height = (int(item) for item in ratio.split(":"))
    return width * ratio_height == height * ratio_width


def normalize_output(image: dict[str, Any], label: str) -> dict[str, Any]:
    value = image.get("output")
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise RunError(f"{label}.output must be an object")
    unknown = set(value) - {"format", "aspect_ratio", "resolution"}
    if unknown:
        raise RunError(f"{label}.output has unsupported fields: {', '.join(sorted(unknown))}")
    if value.get("format", OUTPUT_FORMAT) != OUTPUT_FORMAT:
        raise RunError(f"{label}.output.format must be png")
    raw_ratio = value.get("aspect_ratio")
    resolution = value.get("resolution", {"mode": "auto"})
    if not isinstance(resolution, dict):
        raise RunError(f"{label}.output.resolution must be an object")
    mode = resolution.get("mode", "auto")
    if mode == "auto":
        unknown_resolution = set(resolution) - {"mode", "recommended"}
        if unknown_resolution:
            raise RunError(
                f"{label}.output.resolution has unsupported auto fields: "
                + ", ".join(sorted(unknown_resolution))
            )
        ratio = canonical_aspect_ratio(
            raw_ratio or DEFAULT_ASPECT_RATIO, f"{label}.output.aspect_ratio"
        )
        default_recommendation = (
            DEFAULT_RECOMMENDED_RESOLUTION if ratio == DEFAULT_ASPECT_RATIO else None
        )
        recommended = resolution.get("recommended", default_recommendation)
        if recommended is not None:
            match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", str(recommended))
            if match is None:
                raise RunError(
                    f"{label}.output.resolution.recommended must use WIDTHxHEIGHT or null"
                )
            width, height = (int(item) for item in match.groups())
            if not aspect_matches(width, height, ratio):
                raise RunError(
                    f"{label}.output.resolution.recommended does not match aspect_ratio"
                )
        normalized_resolution = {"mode": "auto", "recommended": recommended}
    elif mode == "explicit":
        unknown_resolution = set(resolution) - {"mode", "width", "height"}
        if unknown_resolution:
            raise RunError(
                f"{label}.output.resolution has unsupported explicit fields: "
                + ", ".join(sorted(unknown_resolution))
            )
        width = resolution.get("width")
        height = resolution.get("height")
        if (
            isinstance(width, bool)
            or isinstance(height, bool)
            or not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            raise RunError(
                f"{label}.output explicit resolution requires positive integer width and height"
            )
        inferred_ratio = canonical_aspect_ratio(
            f"{width}:{height}", f"{label}.output.aspect_ratio"
        )
        ratio = canonical_aspect_ratio(
            raw_ratio or inferred_ratio, f"{label}.output.aspect_ratio"
        )
        if ratio != inferred_ratio:
            raise RunError(
                f"{label}.output.aspect_ratio does not match explicit resolution"
            )
        normalized_resolution = {"mode": "explicit", "width": width, "height": height}
    else:
        raise RunError(f"{label}.output.resolution.mode must be auto or explicit")
    return {
        "format": OUTPUT_FORMAT,
        "aspect_ratio": ratio,
        "resolution": normalized_resolution,
    }


def string_list(value: Any, label: str, minimum: int = 1) -> list[str]:
    if not isinstance(value, list) or len(value) < minimum:
        raise RunError(f"{label} must contain at least {minimum} strings")
    return [text(item, f"{label} item") for item in value]


def require_sha256(value: Any, label: str) -> str:
    value = text(value, label).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise RunError(f"{label} must be a SHA-256 hex digest")
    return value


def identify_reference(path: Path) -> dict[str, Any]:
    magick = shutil.which("magick")
    if not magick:
        raise RunError("ImageMagick 'magick' is required to inspect reference images")
    try:
        output = subprocess.run(
            [magick, "identify", "-quiet", "-format", "%m|%w|%h|%[colorspace]", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout
        image_format, width, height, colorspace = output.split("|", 3)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise RunError(f"Reference image is not decodable: {path}: {detail.strip()}") from exc
    return {
        "format": image_format,
        "width": int(width),
        "height": int(height),
        "colorspace": colorspace,
    }


def target_sha256(
    mode: str,
    preset: str | None,
    mean: float,
    acceptance_range: list[float],
) -> str:
    value = {
        "mode": mode,
        "preset": preset,
        "target_head_ratio": float(mean),
        "acceptance_range": [float(item) for item in acceptance_range],
    }
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_named_mode(
    value: Any,
    modes: set[str],
    default_mode: str,
    default_description: str,
    label: str,
) -> dict[str, Any]:
    if value is None:
        value = {"mode": default_mode, "description": default_description}
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    mode = value.get("mode", default_mode)
    if mode not in modes:
        raise RunError(f"{label}.mode must be one of: {', '.join(sorted(modes))}")
    supplied = value.get("description")
    if mode == "custom":
        description = text(supplied, f"{label}.description")
    else:
        if supplied is not None and text(supplied, f"{label}.description") != default_description:
            raise RunError(f"{label}.description must match the canonical default")
        description = default_description
    return {"mode": mode, "description": description}


def normalize_background(value: Any, label: str, tier: str, tiers: dict[str, Any]) -> dict[str, Any]:
    """An unresolved background follows the tier; a user-resolved one always wins."""
    default = tiers["tiers"][tier]["default_background"]
    if value is None:
        value = {"mode": "solid" if tier == "C" else "custom", "description": default, "origin": "tier"}
    if isinstance(value, str):
        value = {"mode": "custom", "description": value, "origin": "user"}
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    mode = value.get("mode", "solid")
    if mode not in BACKGROUND_MODES:
        raise RunError(f"{label}.mode must be one of: {', '.join(sorted(BACKGROUND_MODES))}")
    origin = value.get("origin")
    if origin not in {"tier", "user"}:
        raise RunError(f"{label}.origin must be tier or user")
    description = text(value.get("description", default), f"{label}.description")
    if origin == "tier" and tier == "C" and (mode, description) != ("solid", DEFAULT_BACKGROUND):
        raise RunError(f"{label} from tier C must be the solid {DEFAULT_BACKGROUND} default")
    return {"mode": mode, "description": description, "origin": origin}


def effective_subagents(execution: dict[str, Any], parallelism: int, count: int) -> int:
    approved = execution["batch_limit"]
    if type(parallelism) is not int or parallelism < 1:
        raise RunError("effective parallelism must be a positive integer")
    if type(count) is not int or not 0 <= count <= approved:
        raise RunError("effective subagent count exceeds the confirmed limit")
    if parallelism != max(1, count):
        raise RunError("effective parallelism must equal max(1, effective subagent count)")
    return count


def expression_presets() -> tuple[dict[str, dict[str, Any]], set[str]]:
    value = read_json(EXPRESSION_PRESETS_PATH)
    entries = value.get("expressions")
    performance_levels = value.get("performance_levels")
    if (
        value.get("schema_version") != EXPRESSION_PRESETS_SCHEMA_VERSION
        or not isinstance(entries, list)
        or not entries
        or not isinstance(performance_levels, list)
        or tuple(performance_levels) != PERFORMANCE_LEVELS
    ):
        raise RunError("Invalid expression presets")
    presets: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RunError(f"expression preset {index} must be an object")
        preset_id = text(entry.get("id"), f"expression preset {index}.id")
        if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", preset_id) or preset_id in presets:
            raise RunError("expression preset ids must be unique lowercase snake_case")
        string_list(entry.get("face_cues"), f"{preset_id}.face_cues")
        string_list(entry.get("manga_accents"), f"{preset_id}.manga_accents", 0)
        string_list(entry.get("heightened_cues"), f"{preset_id}.heightened_cues")
        string_list(entry.get("forbidden_cues"), f"{preset_id}.forbidden_cues")
        presets[preset_id] = entry
    return presets, set(performance_levels)


def exaggeration_tiers() -> dict[str, Any]:
    value = read_json(EXAGGERATION_TIERS_PATH)
    axes, tiers, anchors = value.get("axes"), value.get("tiers"), value.get("identity_anchors")
    if (
        value.get("schema_version") != EXAGGERATION_TIERS_SCHEMA_VERSION
        or tuple(value.get("order", ())) != TIER_ORDER
        or not isinstance(axes, list) or not isinstance(tiers, dict) or set(tiers) != set(TIER_ORDER)
        or not isinstance(anchors, list) or type(value.get("identity_anchor_minimum")) is not int
    ):
        raise RunError("Invalid exaggeration tiers")
    axis_ids = [item.get("id") for item in axes if isinstance(item, dict)]
    if len(set(axis_ids)) != len(axes) or any(not isinstance(item.get("label_zh"), str) for item in axes):
        raise RunError("Exaggeration axes need unique ids and labels")
    for tier, spec in tiers.items():
        if not isinstance(spec, dict) or set(spec.get("axes", {})) != set(axis_ids):
            raise RunError(f"Exaggeration tier {tier} must describe every axis")
        markers = spec.get("markers")
        if not isinstance(markers, list) or not markers or any(
                not isinstance(marker, dict) or not set(marker.get("axes", [])) <= set(axis_ids) for marker in markers):
            raise RunError(f"Exaggeration tier {tier} has invalid markers")
        if not set(spec.get("allowed_performance", [])) <= set(PERFORMANCE_LEVELS):
            raise RunError(f"Exaggeration tier {tier} allows an unknown performance level")
    return value


def tier_rank(tier: str) -> int:
    return TIER_ORDER.index(tier)


def contrast_axes(value: Any, tiers: dict[str, Any], label: str) -> list[str]:
    axes = string_list(value, label)
    if len(set(axes)) != len(axes) or not set(axes) <= {item["id"] for item in tiers["axes"]}:
        raise RunError(f"{label} must name distinct exaggeration axes")
    return axes


def tier_label(item: dict[str, Any], tiers: dict[str, Any], language: str = "zh") -> str:
    """Render a fixed descriptive tier label and any deliberately lowered axes."""
    label = TIER_LABELS[language][item["exaggeration"]]
    contrast = item.get("contrast")
    if not contrast:
        return label
    key = "label_zh" if language == "zh" else "label"
    labels = {axis["id"]: axis[key] for axis in tiers["axes"]}
    axes = PLAN_TEXT[language]["list"].join(labels[axis] for axis in contrast["axes"])
    if language == "zh":
        return f"{label}（{axes}→{contrast['lowered_to']}）"
    return f"{label} ({axes}→{contrast['lowered_to']})"


def axis_tier(image: dict[str, Any], panel: int, panel_tier: str, axis: str) -> str:
    contrast = image.get("contrast")
    if contrast and panel == image["landing_panel"] and axis in contrast["axes"]:
        return contrast["lowered_to"]
    return panel_tier


def visible_characters(value: str) -> int:
    # Dashes, punctuation and spaces stretch a sound effect without adding characters.
    return sum(not unicodedata.category(char).startswith(("P", "Z")) for char in value)


def normalize_exaggeration(image: dict[str, Any], tiers: dict[str, Any], label: str) -> None:
    tier = image["exaggeration"]
    panels = image["panel_count"]
    landing = image.get("landing_panel", panels)
    if type(landing) is not int or not 1 <= landing <= panels:
        raise RunError(f"{label}.landing_panel must name a panel")
    image["landing_panel"] = landing
    contrast = image.get("contrast")
    if contrast is not None:
        if not isinstance(contrast, dict) or set(contrast) != {"panel", "axes", "lowered_to", "reason"}:
            raise RunError(f"{label}.contrast must be null or {{panel, axes, lowered_to, reason}}")
        if contrast["panel"] != landing:
            raise RunError(f"{label}.contrast.panel must be the landing panel")
        contrast_axes(contrast["axes"], tiers, f"{label}.contrast.axes")
        if contrast["lowered_to"] not in TIER_ORDER or tier_rank(contrast["lowered_to"]) >= tier_rank(tier):
            raise RunError(f"{label}.contrast.lowered_to must be below the image tier")
        text(contrast["reason"], f"{label}.contrast.reason")
    image["contrast"] = contrast
    panel_tiers = {}
    for entry in image["expression_plan"]:
        panel_tier = entry.get("tier")
        if panel_tier not in TIER_ORDER:
            raise RunError(f"{label}.expression_plan.tier must be A, B or C")
        if tier_rank(panel_tier) > tier_rank(tier):
            raise RunError(f"{label}.expression_plan setup panels cannot exceed the landing tier")
        if entry["panel"] == landing and panel_tier != tier:
            raise RunError(f"{label}.expression_plan landing panel tier must equal exaggeration")
        face_tier = axis_tier(image, entry["panel"], panel_tier, "expression")
        if entry["performance"] not in tiers["tiers"][face_tier]["allowed_performance"]:
            raise RunError(f"{label}.expression_plan performance {entry['performance']} exceeds tier {face_tier}")
        panel_tiers[entry["panel"]] = panel_tier
    if panels == 1 and image["expression_plan"][0]["performance"] == "manga_burst" \
            and image["proportion_check"] != "visible-only":
        raise RunError(f"{label} single-panel manga_burst deformation requires visible-only proportion review")
    effects = image.get("effects_plan", [])
    if not isinstance(effects, list):
        raise RunError(f"{label}.effects_plan must be a list")
    axis_ids = {item["id"] for item in tiers["axes"]}
    for effect in effects:
        if not isinstance(effect, dict) or set(effect) != {"axis", "effect"} or effect["axis"] not in axis_ids:
            raise RunError(f"{label}.effects_plan entries must be {{axis, effect}} on a known axis")
        text(effect["effect"], f"{label}.effects_plan.effect")
    if tier != "C" and not effects:
        raise RunError(f"{label}.effects_plan must declare the landing panel's key effects")
    image["effects_plan"] = effects
    for panel, panel_tier in panel_tiers.items():
        sound = [image["core_text"][line["text_index"]] for line in image["dialogue_plan"]
                 if line["delivery"] == "sfx" and line["panel"] == panel]
        limit = tiers["tiers"][axis_tier(image, panel, panel_tier, "sfx")]["sfx_limit"]
        if len(sound) > limit["count"] or any(visible_characters(item) > limit["max_characters"] for item in sound):
            raise RunError(f"{label} panel {panel} exceeds its tier's drawn sound-effect limit")


def catalog() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    value = read_json(CATALOG_PATH)
    entries = value.get("assets")
    forms = value.get("character_forms")
    if (
        value.get("schema_version") != ASSET_CATALOG_SCHEMA_VERSION
        or not isinstance(entries, list)
        or not isinstance(forms, dict)
        or tuple(forms) != FORM_ORDER
    ):
        raise RunError("Invalid asset catalog")
    mapping: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise RunError("Invalid asset catalog entry")
        relative = text(entry.get("path"), "asset path")
        path = (SKILL_ROOT / relative).resolve()
        if not path.is_file() or not path.is_relative_to(SKILL_ROOT.resolve()):
            raise RunError(f"Missing or unsafe catalog asset: {relative}")
        if sha256(path) != entry.get("sha256"):
            raise RunError(f"Asset hash mismatch: {relative}")
        mapping[str(path)] = entry
    if len(mapping) != value.get("asset_count"):
        raise RunError("Asset catalog count mismatch")
    if sum(entry.get("kind") == "character" for entry in mapping.values()) != 15:
        raise RunError("Asset catalog must contain exactly 15 character references")
    for form, profile in forms.items():
        if not isinstance(profile, dict):
            raise RunError(f"Invalid character form profile: {form}")
        primary = profile.get("primary")
        mean = profile.get("mean_head_ratio")
        acceptance = profile.get("acceptance_range")
        primary_path = (SKILL_ROOT / primary).resolve() if isinstance(primary, str) else None
        primary_entry = mapping.get(str(primary_path)) if primary_path else None
        form_entries = [
            entry
            for entry in mapping.values()
            if entry.get("kind") == "character" and entry.get("variant") == form
        ]
        if (
            primary_entry is None
            or primary_entry.get("kind") != "character"
            or primary_entry.get("variant") != form
            or len(form_entries) != 3
            or isinstance(mean, bool)
            or not isinstance(mean, (int, float))
            or not isinstance(acceptance, list)
            or len(acceptance) != 2
            or any(
                isinstance(item, bool) or not isinstance(item, (int, float))
                for item in acceptance
            )
            or not acceptance[0] <= mean <= acceptance[1]
        ):
            raise RunError(f"Invalid character form authority: {form}")
    return mapping, forms, sha256(CATALOG_PATH)


def resolve_reference(value: str, assignment_path: Path) -> str:
    path = Path(value)
    if not path.is_absolute():
        bundled = (SKILL_ROOT / path).resolve()
        path = bundled if bundled.is_file() else (assignment_path.parent / path).resolve()
    return str(path.resolve())


def nearest_form(form_profiles: dict[str, dict[str, Any]], mean: float) -> str:
    return min(
        FORM_ORDER,
        key=lambda form: abs(float(form_profiles[form]["mean_head_ratio"]) - mean),
    )


def normalize_proportion(
    image: dict[str, Any],
    form_profiles: dict[str, dict[str, Any]],
    label: str,
) -> tuple[dict[str, Any], str]:
    value = image.get("proportion")
    if value is None:
        value = {"mode": "preset", "preset": DEFAULT_FORM}
    if not isinstance(value, dict):
        raise RunError(f"{label}.proportion must be an object")
    mode = value.get("mode", "preset")
    if mode not in PROPORTION_MODES:
        raise RunError(f"{label}.proportion.mode must be preset or custom")
    if mode == "preset":
        preset = value.get("preset", DEFAULT_FORM)
        if preset not in FORMS:
            raise RunError(f"{label}.proportion.preset must be a supported form")
        profile = form_profiles[preset]
        mean = float(profile["mean_head_ratio"])
        acceptance = [float(item) for item in profile["acceptance_range"]]
        supplied_mean = value.get("target_head_ratio")
        supplied_acceptance = value.get("acceptance_range")
        if supplied_mean is not None and supplied_mean != mean:
            raise RunError(f"{label}.proportion target does not match preset {preset}")
        if supplied_acceptance is not None and supplied_acceptance != acceptance:
            raise RunError(f"{label}.proportion range does not match preset {preset}")
        expected_reference = profile["primary"]
        if value.get("proportion_reference", expected_reference) != expected_reference:
            raise RunError(f"{label}.proportion_reference must match preset {preset}")
        anchor_form = preset
        reference = expected_reference
    else:
        if value.get("preset") is not None:
            raise RunError(f"{label}.proportion.preset must be null in custom mode")
        mean = value.get("target_head_ratio")
        if (
            isinstance(mean, bool)
            or not isinstance(mean, (int, float))
            or not math.isfinite(mean)
            or mean <= 1
        ):
            raise RunError(f"{label}.proportion.target_head_ratio must be finite and greater than 1")
        mean = float(mean)
        acceptance = value.get("acceptance_range")
        if acceptance is None:
            acceptance = [round(max(1.001, mean - 0.15), 3), round(mean + 0.15, 3)]
        if (
            not isinstance(acceptance, list)
            or len(acceptance) != 2
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                for item in acceptance
            )
            or acceptance[0] <= 1
            or acceptance[0] >= acceptance[1]
            or not acceptance[0] <= mean <= acceptance[1]
        ):
            raise RunError(f"{label}.proportion.acceptance_range must contain the custom target")
        acceptance = [float(item) for item in acceptance]
        if value.get("proportion_reference") is not None:
            raise RunError(f"{label}.proportion.proportion_reference must be null in custom mode")
        preset = None
        reference = None
        anchor_form = image.get("identity_anchor_form", nearest_form(form_profiles, mean))
        if anchor_form not in FORMS:
            raise RunError(f"{label}.identity_anchor_form must be a supported form")
    normalized = {
        "mode": mode,
        "preset": preset,
        "target_head_ratio": mean,
        "acceptance_range": acceptance,
        "proportion_reference": reference,
    }
    return normalized, anchor_form


def default_identity_roles(
    style: dict[str, Any], costume: dict[str, Any], proportion: dict[str, Any]
) -> list[str]:
    roles = ["identity"]
    if style["mode"] == "canonical":
        roles.append("style")
    if costume["mode"] == "canonical":
        roles.append("costume")
    if proportion["mode"] == "preset":
        roles.append("proportion")
    return roles


def normalize_typed_references(
    image: dict[str, Any],
    assignment_path: Path,
    assets: dict[str, dict[str, Any]],
    form_profiles: dict[str, dict[str, Any]],
    anchor_form: str,
    identity_roles: list[str],
    label: str,
) -> list[dict[str, Any]]:
    raw = image.get("references")
    if raw is None:
        raw = []
    if not isinstance(raw, list):
        raise RunError(f"{label}.references must be a list")
    primary = str((SKILL_ROOT / form_profiles[anchor_form]["primary"]).resolve())
    raw_paths = []
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            raw_paths.append(resolve_reference(item["path"], assignment_path))
    if primary not in raw_paths:
        raw.insert(0, {
            "id": "canonical-identity",
            "path": primary,
            "roles": identity_roles,
            "instruction": "Preserve only the declared canonical Whale-chan roles; never copy its facial expression",
        })
    if not 1 <= len(raw) <= 5:
        raise RunError(f"{label}.references must contain 1 to 5 images")
    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(raw):
        ref_label = f"{label}.references[{index}]"
        if not isinstance(item, dict):
            raise RunError(f"{ref_label} must be an object")
        ref_id = text(item.get("id"), f"{ref_label}.id")
        if not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", ref_id) or ref_id in ids:
            raise RunError(f"{ref_label}.id must be unique lowercase kebab/snake case")
        ids.add(ref_id)
        resolved = resolve_reference(text(item.get("path"), f"{ref_label}.path"), assignment_path)
        if resolved in paths:
            raise RunError(f"{ref_label}.path is duplicated")
        paths.add(resolved)
        path = Path(resolved)
        if not path.is_file():
            raise RunError(f"Reference image does not exist: {path}")
        roles = string_list(item.get("roles"), f"{ref_label}.roles")
        if len(set(roles)) != len(roles) or not set(roles) <= REFERENCE_ROLES:
            raise RunError(f"{ref_label}.roles contains an invalid or duplicate role")
        actual_hash = sha256(path)
        supplied_hash = item.get("sha256")
        if supplied_hash is not None and require_sha256(supplied_hash, f"{ref_label}.sha256") != actual_hash:
            raise RunError(f"Reference SHA-256 mismatch: {path}")
        instruction = item.get("instruction")
        if instruction is not None:
            instruction = text(instruction, f"{ref_label}.instruction")
        normalized.append({
            "id": ref_id,
            "path": resolved,
            "roles": roles,
            "instruction": instruction,
            "source": "bundled" if resolved in assets else "external",
            "sha256": actual_hash,
            **identify_reference(path),
        })
    primary_refs = [item for item in normalized if item["path"] == primary]
    if len(primary_refs) != 1 or "identity" not in primary_refs[0]["roles"]:
        raise RunError(f"{label}.references requires one canonical {anchor_form} identity anchor")
    forbidden = {role for role in ("style", "costume", "proportion") if role not in identity_roles}
    if forbidden & set(primary_refs[0]["roles"]):
        raise RunError(f"{label} identity anchor cannot control overridden roles")
    for role in REFERENCE_ROLES:
        owners = [item for item in normalized if role in item["roles"]]
        if len(owners) > 1 and any(not item.get("instruction") for item in owners):
            raise RunError(f"{label}.references sharing role {role} require instructions")
    return normalized


def normalize_rhythm(value: Any, panels: int, label: str) -> dict[str, Any] | None:
    """Rhythm is an optional delivery layer; declaring one requires a reason it is needed."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"type", "panel", "reason"}:
        raise RunError(f"{label}.rhythm must be null or {{type, panel, reason}}")
    if value["type"] not in RHYTHM_TYPES:
        raise RunError(f"{label}.rhythm.type must be one of {', '.join(sorted(RHYTHM_TYPES))}")
    if type(value["panel"]) is not int or not 1 <= value["panel"] <= panels:
        raise RunError(f"{label}.rhythm.panel must name the panel where the rhythm lands")
    text(value["reason"], f"{label}.rhythm.reason")
    return value


def validate_participants(source: dict[str, Any]) -> set[str]:
    participants = source.get("participants")
    if not isinstance(participants, list):
        raise RunError("input.participants must list the supporting roles, or be [] for a solo source")
    ids: set[str] = set()
    for participant in participants:
        if not isinstance(participant, dict):
            raise RunError("input.participants entries must be objects")
        identifier = text(participant.get("id"), "participant.id")
        if (
            not re.fullmatch(r"[a-z][a-z0-9_]*", identifier)
            or identifier in ids | {"whalechan", "narrator", "device"}
        ):
            raise RunError("participant.id must be unique and must not use a reserved speaker")
        text(participant.get("role"), "participant.role")
        text(participant.get("source_evidence"), "participant.source_evidence")
        if "character_id" in participant and participant["character_id"] not in {"abstract-user", *model_cast().characters}:
            raise RunError("participant.character_id is unknown")
        ids.add(identifier)
    return ids


def validate_design(image: dict[str, Any], participants: set[str], label: str) -> None:
    text(image.get("text_style_reason"), f"{label}.text_style_reason")
    cast = image.get("cast_plan")
    if not isinstance(cast, list):
        raise RunError(f"{label}.cast_plan must account for every input participant")
    members: dict[str, dict[str, Any]] = {}
    for item in cast:
        if not isinstance(item, dict):
            raise RunError(f"{label}.cast_plan entries must be objects")
        participant = text(item.get("participant"), f"{label}.cast_plan.participant")
        if participant not in participants or participant in members:
            raise RunError(f"{label}.cast_plan has an unknown or duplicate participant")
        representation = item.get("representation")
        if representation not in {"physical", "avatar", "offscreen", "absent"}:
            raise RunError(f"{label}.cast_plan.representation is invalid")
        panels = item.get("panels")
        if (
            not isinstance(panels, list)
            or any(type(panel) is not int or not 1 <= panel <= image["panel_count"] for panel in panels)
            or len(set(panels)) != len(panels)
            or (representation == "absent") != (len(panels) == 0)
        ):
            raise RunError(f"{label}.cast_plan.panels must name visible/audible panels; absent requires []")
        text(item.get("reason"), f"{label}.cast_plan.{participant}.reason")
        if representation in {"physical", "avatar"}:
            text(item.get("staging"), f"{label}.cast_plan.{participant}.staging")
        elif item.get("staging") not in {None, ""}:
            raise RunError(f"{label}.cast_plan nonvisual participants must have staging=null")
        members[participant] = item
    if set(members) != participants:
        raise RunError(f"{label}.cast_plan must account for every input participant")
    dialogue = image.get("dialogue_plan")
    if not isinstance(dialogue, list) or len(dialogue) != len(image["core_text"]):
        raise RunError(f"{label}.dialogue_plan must attribute every core_text entry")
    previous_panel = 1
    for index, line in enumerate(dialogue):
        if not isinstance(line, dict) or type(line.get("text_index")) is not int or line["text_index"] != index:
            raise RunError(f"{label}.dialogue_plan text_index must be consecutive from 0")
        panel = line.get("panel")
        if type(panel) is not int or not previous_panel <= panel <= image["panel_count"]:
            raise RunError(f"{label}.dialogue_plan panels must follow reading order")
        previous_panel = panel
        speaker = text(line.get("speaker"), f"{label}.dialogue_plan.speaker")
        if speaker not in participants | {"whalechan", "narrator", "device"}:
            raise RunError(f"{label}.dialogue_plan has an unknown speaker")
        if line.get("delivery") not in DELIVERIES:
            raise RunError(f"{label}.dialogue_plan.delivery is invalid")
        if line["delivery"] == "label":
            # Writing that belongs to an object (a tag, a sign, a poem scroll) is drawn on that prop.
            text(line.get("prop"), f"{label}.dialogue_plan.prop")
        # The narrator owns captions, printed writing that belongs to no character, and drawn sound effects.
        if speaker == "narrator" and line["delivery"] not in {"caption", "label", "sfx"}:
            raise RunError(f"{label}.narrator must use caption, label or sfx delivery")
        if line["delivery"] == "sfx" and speaker != "narrator":
            raise RunError(f"{label}.dialogue_plan sound effects belong to the narrator")
        if speaker in members and panel not in members[speaker]["panels"]:
            raise RunError(f"{label}.dialogue_plan speaker is absent from its declared panel")


def validate_text_style_policy(assignment: dict[str, Any]) -> None:
    policy = assignment.get("text_style_policy", {"mode": "semantic"})
    if not isinstance(policy, dict) or policy.get("mode") not in {"semantic", "uniform"}:
        raise RunError("text_style_policy.mode must be semantic or uniform")
    styles = {image["text_style"] for image in assignment["images"]}
    if policy["mode"] == "semantic":
        if set(policy) != {"mode"}:
            raise RunError("semantic text_style_policy only accepts mode")
    else:
        text(policy.get("user_instruction"), "text_style_policy.user_instruction")
        if policy.get("template") not in TEXT_STYLES or styles != {policy["template"]}:
            raise RunError("uniform text_style_policy requires its explicitly selected template on all images")
    assignment["text_style_policy"] = policy


def sequence_warnings(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Signals that cases share a panel or tier recipe, by position and regardless of order."""
    grouped: dict[tuple, list[str]] = {}
    for row in matrix:
        columns = row["columns"]
        grouped.setdefault(("repeated_panel_sequence", tuple(c["panel_count"] for c in columns)), []).append(row["case"])
        if all(c["exaggeration"] for c in columns):
            grouped.setdefault(("repeated_tier_sequence", tuple(c["exaggeration"] for c in columns)), []).append(row["case"])
            # Order-free pairing: shuffling images must not hide the same panel-by-tier recipe.
            pairing = tuple(sorted(f"{c['panel_count']}:{c['exaggeration']}" for c in columns))
            grouped.setdefault(("repeated_panel_tier_sequence", pairing), []).append(row["case"])
    return [{"code": code, "sequence": list(value), "cases": cases}
            for (code, value), cases in grouped.items() if len(cases) >= 2]


def line_warnings(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    repeated: dict[str, list[dict[str, Any]]] = {}
    for row in matrix:
        for column in row["columns"]:
            for line in set(column["dialogue"]):
                repeated.setdefault(line, []).append({"case": row["case"], "index": column["index"]})
    return [{"code": "repeated_line", "value": line, "positions": positions}
            for line, positions in repeated.items() if len(positions) > 1]


def draft_summary(paths: list[Path]) -> dict[str, Any]:
    """Cross-case signals from planning drafts, available before the single confirmation."""
    matrix = []
    for path in paths:
        value = planning_draft(read_json(path), path.name)
        summary = plan_summary(value)
        tiers = exaggeration_tiers() if summary["exaggeration_policy"] is not None else None
        ideas = {idea["id"]: idea for idea in value["creative_pool"]}
        matrix.append({"case": value.get("run_name") or path.stem, "columns": [
            {"index": index, "idea_id": option["idea_id"], "direction": option["direction"],
             "mechanism": ideas[option["idea_id"]]["mechanism"], "panel_count": option["panel_count"],
             "exaggeration": option.get("exaggeration"),
             "tier": tier_label(option, tiers) if tiers else None,
             "staging": option["staging"], "dialogue": option["key_lines"]}
            for index, option in enumerate(value["proposal"]["options"], 1)]})
    cases = [row["case"] for row in matrix]
    if len(set(cases)) != len(cases):
        raise RunError("batch drafts need distinct run_name values")
    warnings = sequence_warnings(matrix) + line_warnings(matrix)
    columns = [column for row in matrix for column in row["columns"]]
    return {
        "structurally_valid": True, "creative_review_required": True, "creative_approval": None,
        "matrix": matrix, "warnings": warnings, "image_count": len(columns),
        "directions": dict(sorted(Counter(column["direction"] for column in columns).items())),
        "exaggerations": dict(sorted(Counter(column["exaggeration"] for column in columns if column["exaggeration"]).items())),
    }


def design_summary(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    images = [image for assignment in assignments for image in assignment["images"]]
    matrix = []
    for assignment in assignments:
        ideas = {idea["id"]: idea for idea in assignment["creative_pool"]}
        columns = []
        for index, image in enumerate(assignment["images"], 1):
            composition = image.get("composition", {})
            columns.append({
                "index": index,
                "idea_id": image["idea_id"],
                "mechanism": ideas[image["idea_id"]]["mechanism"],
                "direction": ideas[image["idea_id"]]["direction"],
                "rhythm": (image.get("rhythm") or {}).get("type"),
                "exaggeration": image.get("exaggeration"),
                "panel_count": image["panel_count"], "layout": image["layout"],
                "shot": composition.get("shot", ""), "staging": composition.get("staging", ""),
                "text_placement": composition.get("text_placement", ""),
                "template": image["text_style"],
                "beats": [item["action"] for item in image["action_plan"]],
                "dialogue": image["core_text"],
            })
        matrix.append({"case": assignment["run_name"], "columns": columns})
    warnings = sequence_warnings(matrix)
    slots: dict[tuple, list[str]] = {}
    repetitions: dict[tuple, list[dict[str, Any]]] = {}
    for row in matrix:
        for column in row["columns"]:
            slot = (column["index"], column["layout"], column["template"])
            slots.setdefault(slot, []).append(row["case"])
            for field in ("mechanism", "beats", "staging", "dialogue"):
                value = column[field]
                if value:
                    key = (field, json.dumps(value, ensure_ascii=False, sort_keys=True))
                    repetitions.setdefault(key, []).append({"case": row["case"], "index": column["index"]})
    for (index, layout, template), cases in slots.items():
        if len(cases) >= 2:
            warnings.append({"code": "same_index_layout_template", "index": index,
                             "layout": layout, "template": template, "cases": cases})
    for (field, value), positions in repetitions.items():
        if len(positions) >= 2:
            warnings.append({"code": f"repeated_{field}", "value": json.loads(value), "positions": positions})
    warnings.extend(line_warnings(matrix))
    return {
        "structurally_valid": True,
        "creative_review_required": len(assignments) > 1 or bool(warnings),
        "creative_approval": None,
        "matrix": matrix,
        "warnings": warnings,
        "image_count": len(images),
        "text_styles": dict(sorted(Counter(image["text_style"] for image in images).items())),
        "directions": dict(sorted(Counter(column["direction"] for row in matrix for column in row["columns"]).items())),
        "rhythm_images": sum(image.get("rhythm") is not None for image in images),
        "exaggerations": dict(sorted(Counter(image["exaggeration"] for image in images if image.get("exaggeration")).items())),
        "cast_images": {
            representation: sum(any(item["representation"] == representation for item in image["cast_plan"]) for image in images)
            for representation in ("physical", "avatar", "offscreen", "absent")
        },
    }


def validate_assignment(path: Path, require_approval: bool = True) -> dict[str, Any]:
    assignment = read_json(path)
    assets, form_profiles, catalog_hash = catalog()
    presets, performance_levels = expression_presets()
    tiers = exaggeration_tiers()
    if assignment.get("schema_version") not in SUPPORTED_ASSIGNMENT_VERSIONS:
        raise RunError(f"schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
    language_contract(assignment)
    run_name = text(assignment.get("run_name"), "run_name")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", run_name):
        raise RunError("run_name must be lowercase kebab-case")
    source = assignment.get("input")
    if not isinstance(source, dict) or source.get("type") not in INPUT_TYPES:
        raise RunError(f"input.type must be one of: {', '.join(INPUT_TYPES)}")
    if not isinstance(source.get("content"), (str, list)) or not source["content"]:
        raise RunError("input.content must be non-empty")
    if source["type"] in {"image", "screenshot"}:
        # Image sources are frozen into the run, so content must name the files, not describe them.
        for item in source["content"] if isinstance(source["content"], list) else [source["content"]]:
            source_path = Path(text(item, "input.content"))
            if not source_path.is_absolute():
                source_path = (path.parent / source_path).resolve()
            if not source_path.is_file():
                raise RunError("input.content for image/screenshot sources must list existing source file paths; "
                               "put the transcription in input.source_analysis.source_event")
    source["language"] = text(source.get("language"), "input.language")
    anchor = text(source.get("fact_anchor"), "input.fact_anchor")
    participants = validate_participants(source)
    analysis = source.get("source_analysis")
    if not isinstance(analysis, dict):
        raise RunError("input.source_analysis must be an object")
    for field in ("source_event", "comic_target", "tone", "language_notes"):
        text(analysis.get(field), f"input.source_analysis.{field}")
    native = native_direction(analysis.get("native_direction"), "input.source_analysis.native_direction")
    constraints = analysis.get("user_constraints")
    if not isinstance(constraints, list) or any(not isinstance(item, str) for item in constraints):
        raise RunError("input.source_analysis.user_constraints must be a list of strings")
    text(assignment.get("selection_reason"), "selection_reason")

    plan_summary(assignment)
    ideas = {idea["id"]: idea for idea in assignment["creative_pool"]}
    ranked = assignment["ranked_ideas"]

    assignment["execution"] = role_execution(assignment.get("execution"))

    images = assignment.get("images")
    if not isinstance(images, list) or not images:
        raise RunError("images must contain the confirmed tasks")
    names: set[str] = set()
    executions: set[tuple[str, int]] = set()
    execution_notes: set[tuple[str, str]] = set()
    for index, image in enumerate(images, 1):
        label = f"images[{index - 1}]"
        if not isinstance(image, dict):
            raise RunError(f"{label} must be an object")
        unknown = set(image) - (IMAGE_FIELDS | {"title"})
        if unknown:
            raise RunError(f"{label} has unsupported fields: {', '.join(sorted(unknown))}")
        if "qa_contract_version" in image and image["qa_contract_version"] != QA_CONTRACT_VERSION:
            raise RunError(f"{label}.qa_contract_version must be {QA_CONTRACT_VERSION}")
        name = text(image.get("name"), f"{label}.name")
        if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", name) or name in names:
            raise RunError("image names must be unique lowercase snake_case")
        names.add(name)
        idea_id = text(image.get("idea_id"), f"{label}.idea_id")
        if idea_id not in ranked:
            raise RunError(f"{label}.idea_id must belong to ranked_ideas")
        rank = ranked.index(idea_id) + 1
        if "source_rank" in image and (type(image["source_rank"]) is not int or image["source_rank"] != rank):
            raise RunError(f"{label}.source_rank contradicts idea_id and ranked_ideas")
        image["source_rank"] = rank
        image["qa_contract_version"] = QA_CONTRACT_VERSION
        execution = image.get("execution")
        if type(execution) is not int or execution < 1:
            raise RunError(f"{label}.execution must be positive")
        if (idea_id, execution) in executions:
            raise RunError(f"{label}.execution must be unique within its idea")
        executions.add((idea_id, execution))
        note = text(image.get("execution_note"), f"{label}.execution_note")
        if (idea_id, note.casefold()) in execution_notes:
            raise RunError(f"{label}.execution_note must differentiate executions of the same idea")
        execution_notes.add((idea_id, note.casefold()))
        composition = image.setdefault("composition", {})
        if not isinstance(composition, dict):
            raise RunError(f"{label}.composition must be an object")
        for field in ("shot", "staging", "text_placement", "reason"):
            if field in composition:
                text(composition[field], f"{label}.composition.{field}")
        if image.get("proportion_check") not in {"measured", "visible-only"}:
            raise RunError(f"{label}.proportion_check must be measured or visible-only")
        # Whether the framing supports landmarks is a visual-review judgment,
        # not a shot-name/full-body keyword requirement.
        for field in ("fact_anchor", "premise", "punchline", "why_funny"):
            text(image.get(field), f"{label}.{field}")
        if image["fact_anchor"] != anchor:
            raise RunError(f"{label}.fact_anchor must equal input.fact_anchor")
        if image["premise"] != ideas[idea_id]["premise"]:
            raise RunError(f"{label}.premise must match its idea_id premise")
        traits = string_list(image.get("personality"), f"{label}.personality", 2)
        if len(traits) != 2:
            raise RunError(f"{label}.personality must contain exactly 2 traits")
        panels = image.get("panel_count")
        if panels not in {1, 2, 4}:
            raise RunError(f"{label}.panel_count must be 1, 2, or 4")
        expression_plan = image.get("expression_plan")
        if not isinstance(expression_plan, list) or len(expression_plan) != panels:
            raise RunError(f"{label}.expression_plan must contain one entry per panel")
        for panel_number, expression in enumerate(expression_plan, 1):
            expression_label = f"{label}.expression_plan[{panel_number - 1}]"
            if not isinstance(expression, dict):
                raise RunError(f"{expression_label} must be an object")
            if expression.get("panel") != panel_number:
                raise RunError(f"{label}.expression_plan panels must be consecutive from 1")
            preset = text(expression.get("preset"), f"{expression_label}.preset")
            if preset not in presets:
                raise RunError(f"{expression_label}.preset is unknown")
            if expression.get("performance") not in performance_levels:
                raise RunError(f"{expression_label}.performance is invalid")
        action_plan = image.get("action_plan")
        if not isinstance(action_plan, list) or len(action_plan) != panels:
            raise RunError(f"{label}.action_plan must contain one action per panel")
        for panel_number, action in enumerate(action_plan, 1):
            action_label = f"{label}.action_plan[{panel_number - 1}]"
            if not isinstance(action, dict) or action.get("panel") != panel_number:
                raise RunError(f"{label}.action_plan panels must be consecutive from 1")
            action["action"] = text(action.get("action"), f"{action_label}.action")
        image["rhythm"] = normalize_rhythm(image.get("rhythm"), panels, label)
        layout = image.get("layout")
        allowed_layouts = {1: {"single"}, 2: {"top-bottom", "left-right"}, 4: {"2x2"}}
        if layout not in allowed_layouts[panels]:
            raise RunError(f"{label}.layout is invalid for {panels} panels")
        if image.get("exaggeration") not in TIER_ORDER:
            raise RunError(f"{label}.exaggeration must be A, B or C")
        image["output"] = normalize_output(image, label)
        image["style"] = normalize_named_mode(
            image.get("style"), STYLE_MODES, "canonical", DEFAULT_STYLE, f"{label}.style"
        )
        image["costume"] = normalize_named_mode(
            image.get("costume"), COSTUME_MODES, "canonical", DEFAULT_COSTUME, f"{label}.costume"
        )
        image["background"] = normalize_background(
            image.get("background"), f"{label}.background", image["exaggeration"], tiers)
        image["core_text"] = string_list(image.get("core_text"), f"{label}.core_text")
        text_style = image.get("text_style")
        if text_style not in TEXT_STYLES:
            raise RunError(f"{label}.text_style is invalid")
        image["text_style"] = text_style
        validate_design(image, participants, label)
        normalize_exaggeration(image, tiers, label)
        proportion, anchor_form = normalize_proportion(image, form_profiles, label)
        image["cast_plan"] = model_cast().normalize(image, source["participants"], proportion)
        image["proportion"] = proportion
        image["identity_anchor_form"] = anchor_form
        image["proportion_sha256"] = target_sha256(
            proportion["mode"],
            proportion["preset"],
            proportion["target_head_ratio"],
            proportion["acceptance_range"],
        )
        identity_roles = default_identity_roles(
            image["style"], image["costume"], proportion
        )
        image["references"] = normalize_typed_references(
            image,
            path,
            assets,
            form_profiles,
            anchor_form,
            identity_roles,
            label,
        )
        typography_refs = [
            item for item in image["references"] if "typography" in item["roles"]
        ]
        text_style_refs = [
            item for item in image["references"]
            if assets.get(item["path"], {}).get("kind") == "text-style"
        ]
        if len(typography_refs) != 1 or len(text_style_refs) != 1:
            raise RunError(f"{label} requires exactly one selected text-style typography reference")
        typography_ref = typography_refs[0]
        text_style_ref = text_style_refs[0]
        text_style_entry = assets[text_style_ref["path"]]
        if (
            typography_ref["path"] != text_style_ref["path"]
            or typography_ref["roles"] != ["typography"]
            or text_style_entry.get("variant") != text_style
            or not text_style_entry["path"].endswith("/reference.webp")
        ):
            raise RunError(f"{label} requires the selected text-style reference.webp as sole typography")
        model_cast().validate_references(image["cast_plan"], image["references"])
        image["id"] = f"{index:02d}_{name}"
    validate_text_style_policy(assignment)
    if require_approval:
        validate_approval(assignment)
    rhythmic = sum(image["rhythm"] is not None for image in images)
    rhythm_warnings = []
    if len(images) >= 2 and rhythmic * 2 > len(images):
        rhythm_warnings.append({"code": "rhythm_majority",
                                "message": f"{rhythmic} of {len(images)} images declare a rhythm layer"})
    resolve_warnings(rhythm_warnings, assignment.get("warning_dispositions"), "warning_dispositions")
    budget = assignment.get("budget", {})
    if not isinstance(budget, dict) or budget.get("per_image_candidates", MAX_CANDIDATES) != MAX_CANDIDATES:
        raise RunError("budget.per_image_candidates must be 3")
    assignment["budget"] = {"per_image_candidates": MAX_CANDIDATES, "maximum_total": len(images) * MAX_CANDIDATES}
    assignment["asset_catalog_sha256"] = catalog_hash
    return assignment


def state_for(manifest: dict[str, Any], image_id: str) -> dict[str, Any]:
    try:
        state = manifest["images"][image_id]
    except (KeyError, TypeError) as exc:
        raise RunError(f"Unknown image id: {image_id}") from exc
    return state


def load_run(value: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(value).resolve()
    assignment = read_json(run_dir / "assignment.json")
    manifest = read_json(run_dir / "manifest.json")
    if assignment.get("schema_version") not in SUPPORTED_ASSIGNMENT_VERSIONS:
        raise RunError(f"Run assignment schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
    if (manifest.get("review_workflow_version") != 1 or not isinstance(manifest.get("collection"), dict)):
        raise RunError("QA11 requires its collection review workflow")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise RunError(f"Manifest schema_version must be {MANIFEST_SCHEMA_VERSION}")
    _assets, _forms, current_hash = catalog()
    if assignment.get("asset_catalog_sha256") != current_hash or manifest.get("asset_catalog_sha256") != current_hash:
        raise RunError("Run asset catalog no longer matches this Skill")
    expected_assignment_hash = require_sha256(manifest.get("assignment_sha256"), "manifest.assignment_sha256")
    if sha256(run_dir / "assignment.json") != expected_assignment_hash:
        raise RunError("Frozen assignment SHA-256 mismatch")
    images = assignment.get("images")
    validate_approval(assignment)
    if set(manifest.get("images", {})) != {item.get("id") for item in images}:
        raise RunError("Manifest images must match the frozen assignment")
    for image in images:
        if not isinstance(image, dict) or set(image) - (IMAGE_FIELDS | {"title"}):
            raise RunError("Frozen image specification has unsupported fields")
        if image.get("qa_contract_version") != QA_CONTRACT_VERSION:
            raise RunError(f"Frozen image qa_contract_version must be {QA_CONTRACT_VERSION}")
        references = image.get("references")
        if not isinstance(references, list) or not references:
            raise RunError("Frozen image references must be a non-empty list")
        for reference in references:
            reference_path = Path(reference["path"])
            if not reference_path.is_file() or sha256(reference_path) != reference.get("sha256"):
                raise RunError(f"Frozen reference SHA-256 mismatch: {reference_path}")
    return run_dir, assignment, manifest


def save_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now()
    write_json(run_dir / "manifest.json", manifest)


def provider_allowed(state, provider, assignment):
    tool = extension_module("provider_policy").validate(assignment["execution"].get("tool"))
    if provider != tool["provider"]:
        raise RunError("Batch tool is locked; provider switching is forbidden")


def require_point(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise RunError(f"{label} must be a two-number point")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise RunError(f"{label} must be a two-number point")
    return float(value[0]), float(value[1])


def point_distance(start: tuple[float, float], end: tuple[float, float]) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def calculated_head_ratio(evidence: dict[str, Any]) -> float:
    if evidence.get("measurement_method") != MEASUREMENT_METHOD:
        raise RunError(f"form_evidence.measurement_method must be {MEASUREMENT_METHOD}")
    head_axis = evidence.get("head_axis")
    if not isinstance(head_axis, dict):
        raise RunError("form_evidence.head_axis must be an object")
    head_top = require_point(head_axis.get("top"), "form_evidence.head_axis.top")
    chin = require_point(head_axis.get("chin"), "form_evidence.head_axis.chin")
    head_height = point_distance(head_top, chin)
    if head_height <= 0:
        raise RunError("form_evidence head axis must have positive length")
    segments = evidence.get("body_segments")
    if not isinstance(segments, list) or len(segments) != len(BODY_SEGMENT_NAMES):
        raise RunError("form_evidence.body_segments must contain three segments")
    found: dict[str, float] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict) or segment.get("name") not in BODY_SEGMENT_NAMES:
            raise RunError("form_evidence.body_segments has an invalid name")
        name = segment["name"]
        if name in found:
            raise RunError("form_evidence.body_segments has a duplicate name")
        start = require_point(segment.get("start"), f"form_evidence.body_segments[{index}].start")
        end = require_point(segment.get("end"), f"form_evidence.body_segments[{index}].end")
        length = point_distance(start, end)
        if length <= 0:
            raise RunError("form_evidence body segments must have positive length")
        found[name] = length
    if set(found) != set(BODY_SEGMENT_NAMES):
        raise RunError("form_evidence.body_segments is incomplete")
    return (head_height + sum(found.values())) / head_height


def validate_form_evidence(
    evidence: Any, image_spec: dict[str, Any], expected_hash: str
) -> None:
    if not isinstance(evidence, dict):
        raise RunError("PASS requires form_evidence")
    proportion = image_spec["proportion"]
    if evidence.get("candidate_sha256") != expected_hash:
        raise RunError("form_evidence.candidate_sha256 does not match the candidate")
    if evidence.get("target_source") != proportion["mode"]:
        raise RunError("form_evidence.target_source does not match the assignment")
    if evidence.get("target_sha256") != image_spec["proportion_sha256"]:
        raise RunError("form_evidence.target_sha256 does not match the assignment")
    if evidence.get("mean_head_ratio") != proportion["target_head_ratio"]:
        raise RunError("form_evidence.mean_head_ratio does not match the assignment")
    if evidence.get("acceptance_range") != proportion["acceptance_range"]:
        raise RunError("form_evidence.acceptance_range does not match the assignment")
    calculated = round(calculated_head_ratio(evidence), 3)
    if evidence.get("calculated_head_ratio") != calculated:
        raise RunError("form_evidence.calculated_head_ratio was not recomputed from landmarks")
    minimum, maximum = proportion["acceptance_range"]
    if not minimum <= calculated <= maximum:
        raise RunError("measured head ratio is outside the frozen acceptance range")
    overlay = Path(text(evidence.get("measurement_overlay"), "form_evidence.measurement_overlay"))
    if not overlay.is_file():
        raise RunError("form_evidence measurement overlay does not exist")
    if sha256(overlay) != require_sha256(
        evidence.get("measurement_overlay_sha256"),
        "form_evidence.measurement_overlay_sha256",
    ):
        raise RunError("form_evidence measurement overlay SHA-256 mismatch")


def extension_module(name):
    import importlib.util
    scripts = str(Path(__file__).parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def role_execution(value):
    try:
        return extension_module("agent_orchestration").execution(value)
    except ValueError as exc:
        raise RunError(str(exc)) from exc


def image_tasks():
    from types import SimpleNamespace
    return extension_module("image_task").ImageTasks(SimpleNamespace(**globals()))


def model_cast():
    return extension_module("model_cast").ModelCast(__import__("types").SimpleNamespace(**globals()))


def visual_prompt():
    import importlib.util
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location("comic_visual_prompt", Path(__file__).with_name("visual_prompt.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VisualPrompt(SimpleNamespace(**globals()))


def review_workflow():
    import importlib.util
    from types import SimpleNamespace
    spec = importlib.util.spec_from_file_location("comic_review_workflow", Path(__file__).with_name("review_workflow.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ReviewWorkflow(SimpleNamespace(**globals()))


def validate_compact_qa(value, expected_hash, image_spec):
    return review_workflow().validate_qa(value, expected_hash, image_spec)


def register_review_commands(commands):
    review_workflow().register(commands)


def validate_qa(path, expected_hash, image_spec):
    if image_spec.get("qa_contract_version") != QA_CONTRACT_VERSION:
        raise RunError(f"Image qa_contract_version must be {QA_CONTRACT_VERSION}")
    return validate_compact_qa(read_json(path), expected_hash, image_spec)


def validate_automatic(
    path: Path, expected_hash: str, expected_output: dict[str, Any]
) -> dict[str, Any]:
    value = read_json(path)
    if value.get("schema_version") != 2:
        raise RunError("Automatic QA schema_version must be 2")
    if value.get("overall") not in {"PASS", "FAIL"}:
        raise RunError("Automatic QA overall must be PASS or FAIL")
    if value.get("candidate_sha256") != expected_hash:
        raise RunError("Automatic QA candidate_sha256 does not match")
    if value.get("expected_output") != expected_output:
        raise RunError("Automatic QA expected_output does not match the assignment")
    gates = value.get("gates")
    if not isinstance(gates, dict) or set(gates) != {"F1", "F2"}:
        raise RunError("Automatic QA must contain F1 and F2")
    if any(
        not isinstance(gates[key], dict)
        or gates[key].get("verdict") not in {"PASS", "FAIL"}
        for key in gates
    ):
        raise RunError("Automatic QA gates must have PASS or FAIL verdicts")
    metrics = value.get("metrics")
    if (
        not isinstance(metrics, dict)
        or not isinstance(metrics.get("format"), str)
        or isinstance(metrics.get("width"), bool)
        or not isinstance(metrics.get("width"), int)
        or isinstance(metrics.get("height"), bool)
        or not isinstance(metrics.get("height"), int)
        or metrics["width"] <= 0
        or metrics["height"] <= 0
    ):
        raise RunError("Automatic QA metrics must contain actual format, width, and height")
    return value


def copy_once(source: Path, destination: Path) -> None:
    if destination.exists():
        raise RunError(f"Refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def load_provider_audit(path: Path, provider: str, candidate_hash: str) -> dict[str, Any]:
    audit = read_json(path)
    if audit.get("provider") != provider:
        raise RunError("Provider audit belongs to a different provider")
    if audit.get("output_sha256") != candidate_hash:
        raise RunError("Provider audit does not match the candidate image")
    # usable is true (verified), false (prompt rewritten or references dropped) or null (unverifiable).
    if audit.get("usable") not in (True, False, None) or "usable" not in audit:
        raise RunError("Provider audit must state usable as true, false or null")
    return audit


def resolve_transport(args: argparse.Namespace, audit_path: Path | None) -> str | None:
    """Codex through the CLI must bring its audit; built-in Codex calls have none."""
    transport = getattr(args, "transport", None)
    if args.provider != "codex":
        if transport is not None:
            raise RunError("--transport only applies to codex candidates")
        return None
    if transport not in {"cli", "builtin"}:
        raise RunError("codex candidates require --transport cli or --transport builtin")
    if transport == "cli" and audit_path is None:
        raise RunError("Codex CLI candidates require --provider-audit from generate-codex.py")
    if transport == "builtin" and audit_path is not None:
        raise RunError("Built-in Codex calls have no provider audit; use --transport cli for generate-codex.py output")
    return transport


def creative_markdown(assignment: dict[str, Any]) -> str:
    if assignment.get("schema_version") == 20:
        policy = language_policy()
        words = policy.locale(assignment, policy.effective(assignment, "communication"), "plan")
        return (plan_markdown(assignment) + "\n" + words["source_anchor"] + ": " + assignment["input"]["fact_anchor"]
                + "\n\n" + words["selection_record"] + "\n```json\n"
                + json.dumps(assignment["selection_review"], ensure_ascii=False, indent=2) + "\n```\n")
    lines = [f"# {assignment['run_name']}", "", f"Fact anchor: {assignment['input']['fact_anchor']}", ""]
    lines.extend(["## Confirmed plan", "", plan_markdown(assignment), "```json",
                  json.dumps(assignment["confirmation"], ensure_ascii=False, indent=2), "```", ""])
    lines.extend(["## Independent priority selection", "", "```json",
                  json.dumps(assignment["selection_review"], ensure_ascii=False, indent=2), "```", ""])
    native = assignment["input"]["source_analysis"]["native_direction"]
    lines.extend([
        f"Native direction: {native['direction'] or 'none'} — {native['reason']}", "",
        "## Source analysis", "", "```json",
        json.dumps(assignment["input"]["source_analysis"], ensure_ascii=False, indent=2),
        "```", "", f"Selection reason: {assignment['selection_reason']}", "",
    ])
    lines.extend(["## Creative pool", ""])
    for idea in assignment["creative_pool"]:
        lines.extend([f"### {idea['id']}", "", f"- Premise: {idea['premise']}",
                      f"- Direction: {idea['direction']} ({DIRECTION_LABELS['zh'][idea['direction']]})"])
        for field in DIRECTION_CARRIERS[idea["direction"]]:
            value = idea[field]
            lines.append(f"- {field.capitalize()}: {' → '.join(value) if isinstance(value, list) else value}")
        lines.extend([f"- Punchline: {idea['punchline']}", f"- Personality: {', '.join(idea['personality'])}", f"- Scene: {idea['scene']}"])
        lines.append(f"- Mechanism: {idea['mechanism']}")
        lines.append("- Key lines: " + json.dumps(idea["key_lines"], ensure_ascii=False))
        lines.append("")
    summary = design_summary([assignment])
    lines.extend([
        "", "## Design decisions", "",
        f"- Typography policy: {assignment['text_style_policy']}",
        f"- Template distribution: {summary['text_styles']}",
        f"- Direction distribution: {summary['directions']}",
        f"- Images with a rhythm layer: {summary['rhythm_images']} of {summary['image_count']}",
        f"- Exaggeration distribution: {summary['exaggerations']}",
        f"- Exaggeration policy: {assignment['exaggeration_policy']}",
        f"- Images by cast representation (may overlap): {summary['cast_images']}",
        "- Pre-generation review: verify each template fits its joke and every omitted/offscreen role has a narrative reason. Counts alone do not establish design quality.",
    ])
    for participant in assignment["input"]["participants"]:
        lines.append(f"- Source role `{participant['id']}` ({participant['role']}): {participant['source_evidence']}")
    lines.extend([
        "", f"Final ranking: {' > '.join(assignment['ranked_ideas'])}",
        "", "## Execution", "",
        f"- Mode: {assignment['execution'].get('mode', 'role-queues')}",
        (f"- Execution: {assignment['execution']}"),
        f"- Commit strategy: {assignment['execution']['commit_strategy']}",
        "", f"## {len(assignment['images'])} tasks", "",
    ])
    for image in assignment["images"]:
        performance = f"tier {tier_label(image, exaggeration_tiers())}, landing panel {image['landing_panel']}"
        lines.append(f"- `{image['id']}`: rank {image['source_rank']}, execution {image['execution']}, {image['panel_count']} panel(s), {performance}, {image['punchline']}")
        lines.extend([
            f"  - Idea: {image['idea_id']}; execution note: {image['execution_note']}",
            "  - Composition: " + json.dumps(image["composition"], ensure_ascii=False),
            f"  - Proportion check: {image['proportion_check']}",
            "  - Rhythm: " + (json.dumps(image["rhythm"], ensure_ascii=False) if image["rhythm"] else "none"),
        ])
        lines.append("  - Panel tiers: " + ", ".join(f"{entry['panel']}={entry['tier']}" for entry in image["expression_plan"]))
        lines.append("  - Landing effects: " + json.dumps(image["effects_plan"], ensure_ascii=False))
        if image["contrast"]:
            lines.append("  - Contrast: " + json.dumps(image["contrast"], ensure_ascii=False))
        lines.append(f"  - Background origin: {image['background']['origin']}")
        lines.append(
            "  - Render: "
            f"style={image['style']['mode']}; costume={image['costume']['mode']}; "
            f"background={image['background']['description']}; "
            f"text_style={image['text_style']}; core_text={image['core_text']}; "
            f"proportion={image['proportion']['mode']}:"
            f"{image['proportion']['target_head_ratio']}"
        )
        lines.append(
            "  - Output: "
            f"{image['output']['format']} {image['output']['aspect_ratio']} "
            f"{image['output']['resolution']}"
        )
        lines.append(f"  - Typography decision: {image['text_style_reason']}")
        for item in image["cast_plan"]:
            lines.append(f"  - Cast `{item['participant']}`: {item['representation']} in panels {item['panels']}; reason: {item['reason']}; staging: {item['staging']}")
        for line in image["dialogue_plan"]:
            lines.append(f"  - Text {line['text_index']}, panel {line['panel']}: {line['speaker']} / {line['delivery']} — {image['core_text'][line['text_index']]}")
    return "\n".join(lines) + "\n"


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    assignment = validate_assignment(Path(args.assignment).resolve())
    return {
        "valid": True,
        "structurally_valid": True,
        "creative_approval": None,
        "run_name": assignment["run_name"],
        "images": len(assignment["images"]),
        "maximum_total": assignment["budget"]["maximum_total"],
        "selection_summary": selection_summary(assignment),
        "execution": assignment["execution"],
        "design_summary": design_summary([assignment]),
    }


def cmd_validate_batch(args: argparse.Namespace) -> dict[str, Any]:
    drafts = getattr(args, "draft", None) or []
    if bool(drafts) == bool(args.assignment):
        raise RunError("validate-batch takes either --draft planning drafts or --assignment files, not both")
    if drafts:
        summary = draft_summary([Path(path).resolve() for path in drafts])
        return {"valid": True, "stage": "planning", "structurally_valid": True, "creative_approval": None,
                "creative_review_required": True, "runs": [row["case"] for row in summary["matrix"]],
                "design_summary": summary}
    assignments = [validate_assignment(Path(path).resolve()) for path in args.assignment]
    names = [assignment["run_name"] for assignment in assignments]
    if len(set(names)) != len(names):
        raise RunError("batch run_name values must be unique")
    summary = design_summary(assignments)
    return {"valid": True, "structurally_valid": True, "creative_approval": None,
            "creative_review_required": summary["creative_review_required"],
            "runs": names, "design_summary": summary}


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    assignment_path = Path(args.assignment).resolve()
    assignment = validate_assignment(assignment_path)
    requested_parallelism = assignment["execution"]["role_limits"]["generation"]
    effective_parallelism = 1 if args.effective_parallelism is None else args.effective_parallelism
    if not 1 <= effective_parallelism <= min(requested_parallelism, len(assignment["images"])):
        raise RunError("effective parallelism exceeds the requested or ready-image limit")
    actual_count = getattr(args, "effective_subagents", None)
    if actual_count is None:
        actual_count = min(requested_parallelism, effective_parallelism)
    subagents = effective_subagents(assignment["execution"], effective_parallelism, actual_count)
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / assignment["run_name"]
    checkpoint = None
    if (getattr(args, "batch", None)):
        identity = contract_hash({"assignment": assignment, "batch": str(Path(args.batch).resolve())})
        checkpoint_path = run_dir / "init-checkpoint.json"
        if run_dir.exists():
            if not checkpoint_path.is_file() or read_json(checkpoint_path)["identity"] != identity:
                raise RunError("Run path belongs to another initialization")
            checkpoint = read_json(checkpoint_path)
            if (run_dir / "manifest.json").is_file():
                _, frozen, existing = load_run(str(run_dir))
                return {"run_dir": str(run_dir), "images": list(existing["images"]), "execution": existing["execution"]}
        else:
            checkpoint = {"identity": identity, "frozen_at": now()}
            write_json(checkpoint_path, checkpoint)
    else:
        suffix = 2
        while run_dir.exists():
            run_dir = root / f"{assignment['run_name']}-{suffix:02d}"
            suffix += 1
    def init_copy(source, destination):
        if checkpoint and destination.exists():
            if sha256(source) != sha256(destination):
                raise RunError("Interrupted initialization bytes differ")
        else:
            copy_once(source, destination)
    for folder in ("source", "prompts", "candidates", "qa", "logs", "final", "staging", "inputs/references"):
        (run_dir / folder).mkdir(parents=True, exist_ok=True)
    copied: dict[tuple[str, str], str] = {}
    for image in assignment["images"]:
        for reference in image["references"]:
            if reference.get("source") != "external":
                continue
            source = Path(reference["path"])
            key = (reference["sha256"], source.suffix.lower())
            if key not in copied:
                destination = run_dir / "inputs" / "references" / f"{reference['sha256'][:16]}{source.suffix.lower()}"
                init_copy(source, destination)
                if sha256(destination) != reference["sha256"]:
                    raise RunError(f"Frozen reference SHA-256 mismatch: {destination}")
                copied[key] = str(destination)
            reference["path"] = copied[key]
        (run_dir / "staging" / image["id"]).mkdir(parents=True, exist_ok=True)
    assignment["run_dir"] = str(run_dir)
    assignment["frozen_at"] = checkpoint["frozen_at"] if checkpoint else now()
    write_json(run_dir / "assignment.json", assignment)
    assignment_hash = sha256(run_dir / "assignment.json")
    (run_dir / "creative-record.md").write_text(creative_markdown(assignment), encoding="utf-8")
    write_json(run_dir / "source" / "input.json", assignment["input"])
    if assignment["input"]["type"] in {"image", "screenshot"}:
        source_items = assignment["input"]["content"]
        if isinstance(source_items, str):
            source_items = [source_items]
        for index, item in enumerate(source_items, 1):
            source_path = Path(item)
            if not source_path.is_absolute():
                source_path = (assignment_path.parent / source_path).resolve()
            if source_path.is_file():
                init_copy(
                    source_path,
                    run_dir / "source" / f"original-{index:02d}{source_path.suffix.lower()}",
                )
    states = {
        image["id"]: {
            "status": "pending", "attempts": [],
            "provider_errors": [],
            "final_path": None, "final_sha256": None,
        }
        for image in assignment["images"]
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "status": "in_progress",
        "assignment_sha256": assignment_hash,
        "asset_catalog_sha256": assignment["asset_catalog_sha256"],
        "provider_order": list(PROVIDERS),
        "execution": {
            **assignment["execution"],
            "effective_parallelism": effective_parallelism,
            "effective_subagent_count": subagents,
            "initial_ready_image_count": len(assignment["images"]),
        },
        "created_at": now(), "updated_at": now(), "images": states,
    }
    manifest["review_workflow_version"] = 1
    manifest["collection"] = {"status": "pending", "reviews": [], "sheets": [], "repair_rounds": 0}
    manifest["events"] = []
    from types import SimpleNamespace
    extension_module("batch_workflow").BatchWorkflow(SimpleNamespace(**globals())).attach(args, run_dir, assignment, manifest)
    write_json(run_dir / "manifest.json", manifest)
    return {
        "run_dir": str(run_dir),
        "images": list(states),
        "execution": manifest["execution"],
    }


def cmd_promote(args):
    run_dir, assignment, manifest = load_run(args.run_dir)
    return review_workflow().promote(args, run_dir, assignment, manifest)


def cmd_finalize(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    review_workflow().before_finalize(run_dir, assignment, manifest)
    expected = len(assignment["images"])
    passed = [key for key, value in manifest["images"].items() if value["status"] == "passed"]
    if len(passed) != expected and not args.allow_partial:
        raise RunError(f"Only {len(passed)}/{expected} tasks passed; use --allow-partial to finalize honestly")
    manifest["status"] = "complete" if len(passed) == expected else "partial"
    manifest["completed_at"] = now()
    save_manifest(run_dir, manifest)
    return {
        "status": manifest["status"],
        "passed": len(passed),
        "expected": expected,
        "proposals": [
            {**item,
             "final_paths": [manifest["images"][image["id"]]["final_path"]
                             for image in assignment["images"]
                             if image["idea_id"] == item["idea_id"] and image["id"] in passed],
             "missing": [image["id"] for image in assignment["images"]
                         if image["idea_id"] == item["idea_id"] and image["id"] not in passed]}
            for item in selection_summary(assignment)["choices"]
        ],
        "final_paths": [manifest["images"][key]["final_path"] for key in passed],
        # Tier coverage binds the plan; a tier lost to an exhausted budget is reported, never reassigned.
        "missing_tiers": sorted(
            {image["exaggeration"] for image in assignment["images"] if image.get("exaggeration")}
            - {image["exaggeration"] for image in assignment["images"] if image.get("exaggeration") and image["id"] in passed},
            key=tier_rank, reverse=True),
        "unverified_provider_audits": [
            key for key in passed
            if any(item.get("verdict") == "PASS" and (item.get("provider_audit") or {}).get("usable", True) is None
                   for item in manifest["images"][key]["attempts"])
        ],
        "execution": manifest.get("execution"),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name, handler in (("render-proposal", cmd_render_proposal),
                          ("summarize-selection", cmd_summarize_selection)):
        command = commands.add_parser(name)
        command.add_argument("--draft", required=True)
        command.add_argument("--language", default=None,
                                 help="Legacy rendering language; new assignments use their saved communication language")
        command.set_defaults(handler=handler)
    validate = commands.add_parser("validate-assignment")
    validate.add_argument("--assignment", required=True)
    validate.set_defaults(handler=cmd_validate)
    batch = commands.add_parser("validate-batch")
    batch.add_argument("--assignment", action="append", help="Confirmed assignment; repeat for each source")
    batch.add_argument("--draft", action="append", help="Planning draft before the confirmation; repeat for each source")
    batch.set_defaults(handler=cmd_validate_batch)
    init = commands.add_parser("init")
    init.add_argument("--assignment", required=True)
    init.add_argument("--batch")
    init.add_argument("--root", default="artifacts/whalechan-image-comic")
    init.add_argument("--effective-subagents", type=int, help="Actual worker count, including 0 for main-agent fallback")
    init.add_argument("--effective-parallelism", type=int)
    init.set_defaults(handler=cmd_init)
    promote = commands.add_parser("promote")
    promote.add_argument("--run-dir", required=True); promote.add_argument("--image", required=True)
    promote.set_defaults(handler=cmd_promote)
    finalize = commands.add_parser("finalize")
    finalize.add_argument("--run-dir", required=True); finalize.add_argument("--allow-partial", action="store_true")
    finalize.set_defaults(handler=cmd_finalize)
    register_review_commands(commands)
    from types import SimpleNamespace
    extension_module("agent_orchestration").Orchestration(SimpleNamespace(**globals())).register(commands)
    image_tasks().register(commands)
    extension_module("batch_workflow").BatchWorkflow(SimpleNamespace(**globals())).register(commands)
    return root


def invoke(args):
    shared = {"build-review-sheet", "record-collection-review", "promote", "finalize"}
    if args.command in shared:
        return image_tasks().shared(args, args.handler)
    return args.handler(args)


def main() -> int:
    args = parser().parse_args()
    try:
        result = invoke(args)
    except (RunError, ValueError, OSError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
