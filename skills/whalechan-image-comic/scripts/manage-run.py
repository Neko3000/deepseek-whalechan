#!/usr/bin/env python3
"""Validate, initialize, audit, and finalize Whale-chan comic runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "asset-catalog.json"
EXPRESSION_PRESETS_PATH = SKILL_ROOT / "references" / "expression-presets.json"
PROVIDERS = ("codex", "openai", "nano-banana", "seedream")
FORM_ORDER = ("standard", "compact", "semi-chibi", "chibi", "super-deformed")
FORMS = set(FORM_ORDER)
ASSET_CATALOG_SCHEMA_VERSION = 3
EXPRESSION_PRESETS_SCHEMA_VERSION = 1
ASSIGNMENT_SCHEMA_VERSION = 12
# Frozen runs from these versions may still be generated and finalized, never newly initialized.
RESUMABLE_SCHEMA_VERSIONS = {10, 11, ASSIGNMENT_SCHEMA_VERSION}
QA_CONTRACT_VERSION = 9
MANIFEST_SCHEMA_VERSION = 1
INPUT_TYPES = ("text", "image", "screenshot", "chat-log", "dialogue", "other")
TEXT_STYLES = {
    "01_shy-blue-sticker", "02_keyword-bubble", "03_blue-banner",
    "04_burst-command", "05_outline-poster", "06_top-bottom-punchline",
    "07_casual-dialogue", "08_confrontation-dialogue", "09_vertical-panic",
    "10_manga-impact",
}
FULL_GATES = {"J1", "K1", "I1", "C1", "P1", "T1", "A1", "V1"}
CONFIGURABLE_GATES = FULL_GATES | {"S1", "O1", "B1", "X1", "H1"}
COMPONENT_GATES = {"I1", "P1", "T1", "A1", "V1"}
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
DIRECTION_LABELS = {
    "reversal": "反转", "exposure": "暴露", "escalation": "升级",
    "recognition": "共鸣", "character": "角色梗",
}
RHYTHM_TYPES = {"triple", "pause", "callback", "deadpan"}
SAME_DIRECTION_LIMIT = 4
MAX_PARALLELISM = 5
IMAGE_FIELDS = {
    "name", "id", "idea_id", "source_rank", "execution", "execution_note",
    "composition", "proportion_check", "qa_contract_version",
    "fact_anchor", "premise", "punchline", "why_funny", "personality",
    "panel_count", "layout", "intensity", "output", "expression_plan",
    "action_plan", "style", "costume", "background", "core_text",
    "text_style", "text_style_reason", "dialogue_plan", "cast_plan",
    "proportion", "proportion_sha256", "identity_anchor_form", "references",
    "rhythm",
}
EXECUTION_MODES = {"sequential", "parallel"}
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


def proposal_options(proposal: Any, legacy: bool = False) -> dict[str, dict[str, Any]]:
    if not isinstance(proposal, dict):
        raise RunError("proposal must be an object")
    if type(proposal.get("revision")) is not int or proposal["revision"] < 1:
        raise RunError("proposal.revision must be a positive integer")
    text(proposal.get("fact_anchor"), "proposal.fact_anchor")
    options = proposal.get("options")
    if (not isinstance(options, list) or len(options) != 5
            or any(not isinstance(item, dict) for item in options)
            or [item.get("choice") for item in options] != list("ABCDE")):
        raise RunError("proposal.options must contain exactly five ordered choices A–E")
    ideas = set()
    for item in options:
        for field in ("title", "idea_id", "premise", "scene", "twist", "staging", "recommendation_reason"):
            text(item.get(field), f"proposal.{item['choice']}.{field}")
        if not re.fullmatch(r"idea_[0-9]{2}", item["idea_id"]) or item["idea_id"] in ideas:
            raise RunError("proposal options must reference five unique idea_NN ids")
        ideas.add(item["idea_id"])
        string_list(item.get("key_lines"), "proposal.key_lines")
        if type(item.get("rating")) is not int or item["rating"] not in {1, 2, 3}:
            raise RunError("proposal.rating must be 1, 2, or 3")
    recommended = string_list(proposal.get("recommended_choices"), "proposal.recommended_choices")
    if len(set(recommended)) != len(recommended) or any(item not in "ABCDE" or len(item) != 1 for item in recommended):
        raise RunError("proposal.recommended_choices must name unique choices A–E")
    text(proposal.get("recommendation_reason"), "proposal.recommendation_reason")
    if not legacy:
        validate_proposal_directions(proposal, options)
    return {item["choice"]: item for item in options}


def validate_proposal_directions(proposal: dict[str, Any], options: list[dict[str, Any]]) -> None:
    native = native_direction(proposal.get("native_direction"), "proposal.native_direction")["direction"]
    for item in options:
        if item.get("direction") not in DIRECTION_CARRIERS:
            raise RunError(f"proposal.{item['choice']}.direction must be one of {', '.join(DIRECTION_CARRIERS)}")
        if type(item.get("is_native")) is not bool:
            raise RunError(f"proposal.{item['choice']}.is_native must be true or false")
        if item["is_native"] and item["direction"] != native:
            raise RunError(f"proposal.{item['choice']} is marked native but does not use the source's native direction")
    if native is not None and not any(item["is_native"] for item in options):
        raise RunError("At least one proposal must keep the source's native direction (is_native: true)")
    if sum(item["direction"] == "character" for item in options) > 1:
        raise RunError("At most one proposal may be a pure character gag (direction: character)")
    counts = Counter(item["direction"] for item in options)
    warnings = [
        {"code": "same_direction",
         "message": f"{count} of 5 proposals use direction {direction}"}
        for direction, count in counts.items() if count >= SAME_DIRECTION_LIMIT
    ]
    resolve_warnings(warnings, proposal.get("warning_dispositions"), "proposal.warning_dispositions")


def is_legacy(value: dict[str, Any]) -> bool:
    return value.get("schema_version") == 10


def selection_summary(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") == 12:
        return plan_summary(value)
    proposal = value.get("proposal")
    options = proposal_options(proposal, legacy=is_legacy(value))
    selection = value.get("selection")
    if not isinstance(selection, dict):
        raise RunError("Gate 1 selection must be an object")
    text(selection.get("user_reply"), "selection.user_reply")
    if selection.get("proposal_sha256") != contract_hash(proposal):
        raise RunError("selection.proposal_sha256 is stale; repeat Gate 1 for the current proposal")
    choices = selection.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RunError("selection.choices must be non-empty")
    rows = []
    seen = set()
    for item in choices:
        if not isinstance(item, dict):
            raise RunError("selection choice must be an object")
        choice = item.get("choice")
        if not isinstance(choice, str) or choice not in options or choice in seen:
            raise RunError("selection must contain unique known choices")
        seen.add(choice)
        count = item.get("count", 5)
        if type(count) is not int or count < 1:
            raise RunError("selection count must be a positive integer")
        rows.append({"choice": choice, "title": options[choice]["title"],
                     "idea_id": options[choice]["idea_id"], "count": count})
    adjustments = selection.get("adjustments")
    if not isinstance(adjustments, list) or any(not isinstance(item, str) or not item.strip() for item in adjustments):
        raise RunError("selection.adjustments must be a list of explicit user changes")
    total = sum(item["count"] for item in rows)
    return {"proposal_count": len(rows), "image_count": total, "choices": rows,
            "adjustments": adjustments,
            "summary_sha256": contract_hash({"proposal": proposal, "selection": selection})}


def validate_approval(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema_version") == 12:
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
            raise RunError("images must contain five selected ideas exactly once each")
        options = {item["idea_id"]: item for item in value["proposal"]["options"]}
        for image in images:
            option = options[image["idea_id"]]
            if (image.get("execution") != 1 or image.get("premise") != option["premise"]
                    or image.get("panel_count") != option["panel_count"]
                    or image.get("core_text") != option["key_lines"]):
                raise RunError("Each image must preserve its confirmed premise, panel_count and key_lines, execution=1")
        return summary
    summary = selection_summary(value)
    confirmation = value.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("status") != "confirmed":
        raise RunError("Gate 2 confirmation is required before generation")
    text(confirmation.get("user_reply"), "confirmation.user_reply")
    if confirmation.get("summary_sha256") != summary["summary_sha256"]:
        raise RunError("Gate 2 confirmation is stale; show the updated summary and wait again")
    if value.get("input", {}).get("fact_anchor") != value["proposal"]["fact_anchor"]:
        raise RunError("proposal.fact_anchor must match the assignment")
    expected = {item["idea_id"]: item["count"] for item in summary["choices"]}
    if set(value.get("ranked_ideas", [])) != set(expected):
        raise RunError("ranked_ideas must match the user-selected proposal ideas")
    images = value.get("images")
    if (not isinstance(images, list) or any(not isinstance(item, dict) for item in images)
            or Counter(item.get("idea_id") for item in images) != expected):
        raise RunError("images must match the confirmed counts for every selected proposal")
    return summary


def markdown_cell(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", "<br>")


def proposal_markdown(proposal: dict[str, Any], legacy: bool = False) -> str:
    options = proposal_options(proposal, legacy=legacy)
    humor_header = "笑点与反转" if legacy else "方向｜笑点"
    lines = [f"| 选择 | 方案 | 核心场景 | {humor_header} | 分镜／构图 | 关键台词 | 推荐程度与理由 |",
             "|---|---|---|---|---|---|---|"]
    for choice, item in options.items():
        rating = item["rating"]
        recommendation = "★" * rating + "☆" * (3 - rating)
        recommendation += " " + {3: "首推", 2: "推荐", 1: "可选"}[rating] + "：" + item["recommendation_reason"]
        humor = item["twist"]
        if not legacy:
            humor = DIRECTION_LABELS[item["direction"]] + ("（原）" if item["is_native"] else "") + "｜" + humor
        cells = [choice, item["title"], item["scene"], humor, item["staging"],
                 "\n".join(item["key_lines"]), recommendation]
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in cells) + " |")
    if not legacy and any(item["is_native"] for item in options.values()):
        lines.extend(["", "标注“（原）”的方案保留了原素材本来的笑点方向。"])
    lines.extend(["", "**你想生成哪些方案？** 可选一个或多个。推荐 **"
                  + "＋".join(proposal["recommended_choices"]) + "**，"
                  + markdown_cell(proposal["recommendation_reason"]) + "。", "",
                  "**生成策略：**每个入选方案默认生成 **5 张**，围绕该创意展开不同演绎。选一个共 5 张，选两个共 10 张，全选共 25 张；也可以指定“五种方案各一张”，共 5 张。选择后，我会汇总方案和张数，请你确认后再开始生成。"])
    return "\n".join(lines) + "\n"


def selection_markdown(summary: dict[str, Any]) -> str:
    if "worker_plan" in summary:
        return plan_markdown({"proposal": {"options": summary["options"]},
                              "panel_policy": summary["panel_policy"]}, summary)
    lines = [f"已选择 **{summary['proposal_count']} 个方案，共 {summary['image_count']} 张图片**：", ""]
    for item in summary["choices"]:
        lines.append(f"- **{item['choice']}｜{markdown_cell(item['title'])}**：{item['count']} 张")
    if summary["adjustments"]:
        lines.extend(["", "同步落实以下修改：", ""])
        lines.extend("- " + markdown_cell(item) for item in summary["adjustments"])
    lines.extend(["", "每个方案围绕已选创意展开不同演绎，生成后进行质量验证。",
                  "生图通道：优先 Codex ImageGen（不在 Codex 中运行时，通过本机 Codex CLI 调用，消耗 ChatGPT 订阅额度）→ OpenAI → Nano Banana → Seedream。", "",
                  "**确认按以上方案和数量开始生成吗？** 回复“确认”即可开始，也可以调整方案或数量。"])
    return "\n".join(lines) + "\n"


def cmd_render_proposal(args: argparse.Namespace) -> dict[str, Any]:
    value = read_json(Path(args.draft).resolve())
    if value.get("schema_version") == 12:
        summary = plan_summary(value)
        return {**summary, "markdown": plan_markdown(value, summary)}
    proposal = value.get("proposal")
    return {"markdown": proposal_markdown(proposal), "proposal_sha256": contract_hash(proposal)}


def cmd_summarize_selection(args: argparse.Namespace) -> dict[str, Any]:
    value = read_json(Path(args.draft).resolve())
    summary = selection_summary(value)
    if value.get("schema_version") == 12:
        return {**summary, "markdown": plan_markdown(value, summary)}
    return {**summary, "markdown": selection_markdown(summary)}


def cmd_rank_ideas(args: argparse.Namespace) -> dict[str, Any]:
    value = read_json(Path(args.draft).resolve())
    standings = tournament_results(value)
    return {"standings": standings, "ranked_ideas": [row["idea_id"] for row in standings[:5]]}


def tournament_results(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Count authored comparisons; never judge the creative merits ourselves."""
    pool = value.get("creative_pool")
    if not isinstance(pool, list) or len(pool) != 10 or any(not isinstance(i, dict) for i in pool):
        raise RunError("creative_pool must contain exactly 10 ideas")
    ids = [i.get("id") for i in pool]
    if any(not isinstance(i, str) or not re.fullmatch(r"idea_[0-9]{2}", i) for i in ids) or len(set(ids)) != 10:
        raise RunError("creative_pool must contain 10 unique idea_NN ids")
    points = dict.fromkeys(ids, 0)
    matches = value.get("duels")
    if not isinstance(matches, list) or len(matches) != 45:
        raise RunError("duels must contain exactly 45 unique pairs")
    seen = set()
    for match in matches:
        if not isinstance(match, dict):
            raise RunError("Each duel must be an object")
        a, b, winner = match.get("a"), match.get("b"), match.get("winner")
        if (not isinstance(a, str) or not isinstance(b, str) or a not in points or b not in points
                or a == b or "winner" not in match or winner not in (a, b, None)):
            raise RunError("duel requires two different known ideas and winner=a, b or null")
        pair = frozenset((a, b))
        if pair in seen:
            raise RunError("duels must contain 45 unique pairs without repeats")
        seen.add(pair)
        text(match.get("reason"), "duel.reason")
        points[a] += 1 if winner is None else 2 if winner == a else 0
        points[b] += 1 if winner is None else 2 if winner == b else 0
    head = dict.fromkeys(ids, 0)
    for match in matches:
        a, b, winner = match["a"], match["b"], match["winner"]
        if points[a] == points[b]:
            head[a] += 1 if winner is None else 2 if winner == a else 0
            head[b] += 1 if winner is None else 2 if winner == b else 0
    groups: dict[tuple[int, int], list[str]] = {}
    for idea in ids:
        groups.setdefault((points[idea], head[idea]), []).append(idea)
    breaks = value.get("tie_breaks", [])
    if not isinstance(breaks, list):
        raise RunError("tie_breaks must be a list")
    authored = {}
    for item in breaks:
        if not isinstance(item, dict):
            raise RunError("tie_breaks entries must be objects")
        order = string_list(item.get("ideas"), "tie_breaks.ideas", 2)
        key = frozenset(order)
        if len(key) != len(order) or key in authored:
            raise RunError("tie_breaks must name each tied group once without duplicate ids")
        text(item.get("reason"), "tie_breaks.reason")
        authored[key] = order
    expected = {frozenset(group) for group in groups.values() if len(group) > 1}
    if set(authored) != expected:
        raise RunError("tie_breaks must resolve exactly the remaining tied groups with an authored reason")
    ranking = []
    for key in sorted(groups, reverse=True):
        group = groups[key]
        order = authored[frozenset(group)] if len(group) > 1 else group
        ranking.extend({"idea_id": i, "points": points[i], "head_to_head": head[i]} for i in order)
    return ranking


def plan_summary(value: dict[str, Any]) -> dict[str, Any]:
    ranking = tournament_results(value)
    selected = [item["idea_id"] for item in ranking[:5]]
    if value.get("ranked_ideas") != selected:
        raise RunError("ranked_ideas must be the five tournament winners in ranking order")
    if "selection" in value:
        raise RunError("v12 has one confirmation, not a user selection record")
    text(value.get("selection_reason"), "selection_reason")
    source = value.get("input", {})
    anchor = text(source.get("fact_anchor"), "input.fact_anchor")
    native = native_direction(source.get("source_analysis", {}).get("native_direction"), "input.source_analysis.native_direction")
    ideas = {item["id"]: item for item in value["creative_pool"]}
    for idea in ideas.values():
        for field in ("premise", "punchline", "scene", "mechanism"):
            text(idea.get(field), f"{idea['id']}.{field}")
        if any(field in idea for field in ("gate", "gate_reason", "rejection_reason")):
            raise RunError("v12 creative ideas have no PASS/FAIL gate or rejection_reason")
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
        raise RunError("v12 proposal is informational; recommendations are not choices")
    options = proposal.get("options")
    if (not isinstance(options, list) or any(not isinstance(i, dict) for i in options)
            or [i.get("idea_id") for i in options] != selected):
        raise RunError("proposal.options must contain the five ranked ideas in order")
    for option in options:
        idea = ideas[option["idea_id"]]
        for field in ("title", "premise", "scene", "twist", "staging", "selection_reason"):
            text(option.get(field), f"proposal.{field}")
        if any(k in option for k in ("choice", "rating", "recommendation_reason")):
            raise RunError("v12 proposal has no user choice or rating")
        if (option["premise"] != idea["premise"] or option["scene"] != idea["scene"]
                or option["twist"] != idea["punchline"] or option.get("direction") != idea["direction"]):
            raise RunError("proposal premise, scene, twist/punchline and direction must match its idea")
        if type(option.get("is_native")) is not bool or option["is_native"] != (idea["direction"] == native["direction"]):
            raise RunError("proposal.is_native must accurately match the source direction")
        string_list(option.get("key_lines"), "proposal.key_lines")
        if type(option.get("panel_count")) is not int or option["panel_count"] not in {1, 2, 4}:
            raise RunError("proposal.panel_count must be 1, 2, or 4")
    policy = value.get("panel_policy", {"mode": "narrative"})
    if not isinstance(policy, dict) or policy.get("mode") not in {"narrative", "user-override"}:
        raise RunError("panel_policy.mode must be narrative or user-override")
    if policy["mode"] == "user-override":
        text(policy.get("user_instruction"), "panel_policy.user_instruction")
    elif {option["panel_count"] for option in options} != {1, 2, 4}:
        raise RunError("Five comics must cover three panel counts: 1, 2 and 4")
    if "images" in value:
        images = value["images"]
        if (not isinstance(images, list) or any(not isinstance(i, dict) for i in images)
                or Counter(i.get("idea_id") for i in images) != Counter(selected)):
            raise RunError("images must contain five selected ideas exactly once each")
    return worker_summary(value, selected, ranking, policy)


def worker_summary(value: dict[str, Any], selected: list[str], ranking: list[dict[str, Any]],
                   policy: dict[str, Any]) -> dict[str, Any]:
    plan = value.get("worker_plan")
    if not isinstance(plan, dict) or plan.get("coordinator") != "main":
        raise RunError("worker_plan requires coordinator=main")
    workers = plan.get("workers")
    capacity = plan.get("max_parallelism")
    if (type(capacity) is not int or not 1 <= capacity <= MAX_PARALLELISM
            or not isinstance(workers, list) or len(workers) != capacity):
        raise RunError("worker_plan requires 1 through 5 workers matching max_parallelism")
    names, assigned = set(), []
    for worker in workers:
        if not isinstance(worker, dict):
            raise RunError("worker_plan workers must be objects")
        name = text(worker.get("id"), "worker.id")
        if name == "main" or name in names:
            raise RunError("worker ids must be unique and different from main")
        names.add(name)
        assigned.extend(string_list(worker.get("idea_ids"), "worker.idea_ids"))
    if Counter(assigned) != Counter(selected):
        raise RunError("worker_plan must assign each selected idea exactly once")
    execution = normalize_execution(value.get("execution"))
    if execution["requested_parallelism"] != capacity:
        raise RunError("execution.requested_parallelism must match worker_plan.max_parallelism")
    proposal = value["proposal"]
    rows = [{"choice": str(n), "title": item["title"], "idea_id": item["idea_id"], "count": 1}
            for n, item in enumerate(proposal["options"], 1)]
    payload = {key: value[key] for key in ("proposal", "creative_pool", "duels", "ranked_ideas",
                                          "selection_reason", "worker_plan")}
    payload.update(tie_breaks=value.get("tie_breaks", []), panel_policy=policy,
                   execution=execution, input=value["input"])
    return {"proposal_count": 5, "image_count": 5, "choices": rows, "adjustments": [],
            "worker_plan": plan, "maximum_total": 15, "standings": ranking,
            "options": proposal["options"], "panel_policy": policy,
            "summary_sha256": contract_hash(payload)}


def plan_markdown(value: dict[str, Any], summary: dict[str, Any] | None = None) -> str:
    summary = summary or plan_summary(value)
    lines = ["| 序号 | 创意描述 | 核心场景 | 方向｜笑点 | 格数／分镜 | 关键台词 | 入选理由 |",
             "|---|---|---|---|---|---|---|"]
    for index, item in enumerate(value["proposal"]["options"], 1):
        cells = [str(index), item["title"] + "：" + item["premise"], item["scene"],
                 DIRECTION_LABELS[item["direction"]] + "：" + item["twist"],
                 f"{item['panel_count']} 格：{item['staging']}", "\n".join(item["key_lines"]), item["selection_reason"]]
        lines.append("| " + " | ".join(markdown_cell(cell) for cell in cells) + " |")
    lines.extend(["", "共 **5 个创意，各 1 张，共 5 张图片**。每张最多 3 次产图调用，共最多 15 次。", "",
                  "生图通道：Codex ImageGen → OpenAI → Nano Banana → Seedream。", "",
                  "**sub-agent 分配**（并发上限 " + str(summary["worker_plan"]["max_parallelism"]) + "）：", "",
                  "- main：协调、验收、串行记录及交付。"])
    titles = {i["idea_id"]: i["title"] for i in summary["choices"]}
    for worker in summary["worker_plan"]["workers"]:
        lines.append("- " + markdown_cell(worker["id"]) + "：" + "、".join(markdown_cell(titles[i]) for i in worker["idea_ids"]) + "；依次执行。")
    if value.get("panel_policy", {}).get("mode") == "user-override":
        lines.extend(["", "格数按用户指定覆盖默认三种格数：" + markdown_cell(value["panel_policy"]["user_instruction"])])
    lines.extend(["", "**确认按以上创意、张数和 sub-agent 分配开始生成吗？**"])
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


def normalize_background(value: Any, label: str) -> dict[str, Any]:
    if value is None:
        value = {"mode": "solid", "description": DEFAULT_BACKGROUND}
    if isinstance(value, str):
        value = {"mode": "custom", "description": value}
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    mode = value.get("mode", "solid")
    if mode not in BACKGROUND_MODES:
        raise RunError(f"{label}.mode must be one of: {', '.join(sorted(BACKGROUND_MODES))}")
    description = text(value.get("description", DEFAULT_BACKGROUND), f"{label}.description")
    return {"mode": mode, "description": description}


def normalize_execution(value: Any) -> dict[str, Any]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise RunError("execution must be an object")
    requested = value.get("requested_parallelism", 1)
    if (
        not isinstance(requested, int)
        or isinstance(requested, bool)
        or not 1 <= requested <= MAX_PARALLELISM
    ):
        raise RunError(f"execution.requested_parallelism must be between 1 and {MAX_PARALLELISM}")
    mode = value.get("mode", "parallel" if requested > 1 else "sequential")
    if mode not in EXECUTION_MODES:
        raise RunError(f"execution.mode must be one of: {', '.join(sorted(EXECUTION_MODES))}")
    if (mode == "sequential") != (requested == 1):
        raise RunError("execution mode and requested_parallelism are inconsistent")
    if value.get("max_parallelism", MAX_PARALLELISM) != MAX_PARALLELISM:
        raise RunError(f"execution.max_parallelism must be {MAX_PARALLELISM}")
    strategy = value.get("commit_strategy", "coordinator-serial")
    if strategy != "coordinator-serial":
        raise RunError("execution.commit_strategy must be coordinator-serial")
    return {
        "mode": mode,
        "requested_parallelism": requested,
        "max_parallelism": MAX_PARALLELISM,
        "commit_strategy": strategy,
    }


def expression_presets() -> tuple[dict[str, dict[str, Any]], set[str]]:
    value = read_json(EXPRESSION_PRESETS_PATH)
    entries = value.get("expressions")
    performance_levels = value.get("performance_levels")
    if (
        value.get("schema_version") != EXPRESSION_PRESETS_SCHEMA_VERSION
        or not isinstance(entries, list)
        or not entries
        or not isinstance(performance_levels, list)
        or set(performance_levels) != {"grounded", "heightened", "punchline_peak"}
        or len(performance_levels) != 3
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
        if line.get("delivery") not in {"speech", "thought", "caption", "label"}:
            raise RunError(f"{label}.dialogue_plan.delivery is invalid")
        if line["delivery"] == "label":
            # Writing that belongs to an object (a tag, a sign, a poem scroll) is drawn on that prop.
            text(line.get("prop"), f"{label}.dialogue_plan.prop")
        # The narrator owns captions and printed writing that belongs to no character.
        if speaker == "narrator" and line["delivery"] not in {"caption", "label"}:
            raise RunError(f"{label}.narrator must use caption or label delivery")
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


def design_summary(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    images = [image for assignment in assignments for image in assignment["images"]]
    matrix = []
    for assignment in assignments:
        ideas = {idea["id"]: idea for idea in assignment["creative_pool"]}
        columns = []
        for index, image in enumerate(assignment["images"], 1):
            composition = image["composition"]
            columns.append({
                "index": index,
                "idea_id": image["idea_id"],
                "mechanism": ideas[image["idea_id"]]["mechanism"],
                "direction": ideas[image["idea_id"]]["direction"],
                "rhythm": (image.get("rhythm") or {}).get("type"),
                "panel_count": image["panel_count"], "layout": image["layout"],
                "shot": composition["shot"], "staging": composition["staging"],
                "text_placement": composition["text_placement"],
                "template": image["text_style"],
                "beats": [item["action"] for item in image["action_plan"]],
                "dialogue": image["core_text"],
            })
        matrix.append({"case": assignment["run_name"], "columns": columns})
    warnings = []
    slots: dict[tuple, list[str]] = {}
    sequences: dict[tuple, list[str]] = {}
    repetitions: dict[tuple, list[dict[str, Any]]] = {}
    for row in matrix:
        sequence = tuple(column["panel_count"] for column in row["columns"])
        sequences.setdefault(sequence, []).append(row["case"])
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
    for sequence, cases in sequences.items():
        if len(cases) >= 2:
            warnings.append({"code": "repeated_panel_sequence", "sequence": list(sequence), "cases": cases})
    for (field, value), positions in repetitions.items():
        if len(positions) >= 2:
            warnings.append({"code": f"repeated_{field}", "value": json.loads(value), "positions": positions})
    repeated_lines: dict[str, list[dict[str, Any]]] = {}
    for row in matrix:
        for column in row["columns"]:
            for line in set(column["dialogue"]):
                repeated_lines.setdefault(line, []).append({"case": row["case"], "index": column["index"]})
    for line, positions in repeated_lines.items():
        if len(positions) > 1:
            warnings.append({"code": "repeated_line", "value": line, "positions": positions})
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
        "cast_images": {
            representation: sum(any(item["representation"] == representation for item in image["cast_plan"]) for image in images)
            for representation in ("physical", "avatar", "offscreen", "absent")
        },
    }


def validate_assignment(path: Path) -> dict[str, Any]:
    assignment = read_json(path)
    assets, form_profiles, catalog_hash = catalog()
    presets, performance_levels = expression_presets()
    if assignment.get("schema_version") != ASSIGNMENT_SCHEMA_VERSION:
        raise RunError(f"schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
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

    assignment["execution"] = normalize_execution(assignment.get("execution"))

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
        unknown = set(image) - IMAGE_FIELDS
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
        composition = image.get("composition")
        if not isinstance(composition, dict):
            raise RunError(f"{label}.composition must be an object")
        for field in ("shot", "staging", "text_placement", "reason"):
            text(composition.get(field), f"{label}.composition.{field}")
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
        intensity = image.get("intensity")
        if intensity not in {"B", "C"}:
            raise RunError(f"{label}.intensity must be B or C")
        image["output"] = normalize_output(image, label)
        image["style"] = normalize_named_mode(
            image.get("style"), STYLE_MODES, "canonical", DEFAULT_STYLE, f"{label}.style"
        )
        image["costume"] = normalize_named_mode(
            image.get("costume"), COSTUME_MODES, "canonical", DEFAULT_COSTUME, f"{label}.costume"
        )
        image["background"] = normalize_background(image.get("background"), f"{label}.background")
        image["core_text"] = string_list(image.get("core_text"), f"{label}.core_text")
        text_style = image.get("text_style")
        if text_style not in TEXT_STYLES:
            raise RunError(f"{label}.text_style is invalid")
        image["text_style"] = text_style
        validate_design(image, participants, label)
        proportion, anchor_form = normalize_proportion(image, form_profiles, label)
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
        supporting_entries = [
            item for item in image["references"]
            if assets.get(item["path"], {}).get("kind") == "supporting-character"
        ]
        pose_sheet = "assets/supporting-character-references/abstract-user-pose-sheet.webp"
        if any(member["representation"] in {"physical", "avatar"} for member in image["cast_plan"]):
            supporting_paths = {
                assets.get(item["path"], item).get("path") for item in supporting_entries
            }
            if len(supporting_entries) != 1 or pose_sheet not in supporting_paths:
                raise RunError(
                    f"{label} with a supporting character must load only abstract-user-pose-sheet.webp"
                )
        else:
            if supporting_entries:
                raise RunError(
                    f"{label} without a supporting character must not load its reference"
                )
        image["id"] = f"{index:02d}_{name}"
    validate_text_style_policy(assignment)
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
    assignment["schema_version"] = ASSIGNMENT_SCHEMA_VERSION
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
    if assignment.get("schema_version") not in RESUMABLE_SCHEMA_VERSIONS:
        raise RunError(f"Run assignment schema_version must be one of {sorted(RESUMABLE_SCHEMA_VERSIONS)}")
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
        if not isinstance(image, dict) or set(image) - IMAGE_FIELDS:
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


def provider_allowed(state: dict[str, Any], provider: str) -> None:
    if provider not in PROVIDERS:
        raise RunError(f"Unsupported provider: {provider}")
    events = state.get("attempts", []) + state.get("provider_errors", [])
    if not events:
        if provider != "codex":
            raise RunError("The first provider must be codex")
        return
    highest = max(PROVIDERS.index(item["provider"]) for item in events)
    rank = PROVIDERS.index(provider)
    if rank < highest or rank > highest + 1:
        raise RunError("Provider order cannot move backward or skip an untouched provider")
    if rank == highest + 1:
        previous = PROVIDERS[highest]
        prior = [item for item in events if item["provider"] == previous]
        if not any(item.get("verdict") == "FAIL" or item.get("category") in ADVANCE_ERRORS for item in prior):
            raise RunError(f"Cannot advance past provider {previous}")


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


def validate_design_evidence(evidence: dict[str, Any], image: dict[str, Any]) -> None:
    typography = evidence.get("text_style_match")
    if not isinstance(typography, dict) or typography.get("template") != image["text_style"]:
        raise RunError("evidence.text_style_match must name the selected template")
    string_list(typography.get("observed_cues"), "text_style_match.observed_cues")
    for key, plan, fields in (
        ("dialogue_match", image["dialogue_plan"], ("text_index", "panel", "speaker", "delivery")),
        ("cast_match", image["cast_plan"], ("participant", "representation", "panels")),
    ):
        observed = evidence.get(key)
        if not isinstance(observed, list) or len(observed) != len(plan):
            raise RunError(f"evidence.{key} must cover the complete frozen plan")
        for actual, expected in zip(observed, plan, strict=True):
            if not isinstance(actual, dict) or any(actual.get(field) != expected[field] for field in fields):
                raise RunError(f"evidence.{key} does not match the assignment")
            string_list(actual.get("observed_cues"), f"{key}.observed_cues")


def validate_qa(
    path: Path,
    expected_hash: str,
    component: bool = False,
    image_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(image_spec, dict):
        raise RunError("Visual QA requires the frozen image specification")
    if image_spec.get("qa_contract_version") != QA_CONTRACT_VERSION:
        raise RunError(f"Image qa_contract_version must be {QA_CONTRACT_VERSION}")
    required = {"core_text", "dialogue_plan", "panel_count", "expression_plan",
                "cast_plan", "text_style", "proportion_check", "proportion", "proportion_sha256"}
    missing = required - set(image_spec)
    if missing:
        raise RunError("Frozen image specification is missing: " + ", ".join(sorted(missing)))
    if image_spec["proportion_check"] not in {"measured", "visible-only"}:
        raise RunError("Frozen image proportion_check must be measured or visible-only")
    expressions = image_spec["expression_plan"]
    if not isinstance(expressions, list) or len(expressions) != image_spec["panel_count"]:
        raise RunError("Frozen image expression_plan must cover every panel")
    if value.get("review_status") != "reviewed":
        raise RunError("Visual QA review_status must be reviewed; pending drafts cannot be recorded or promoted")
    observation = value.get("observation")
    if not isinstance(observation, dict):
        raise RunError("Visual QA requires observation independent of planned evidence")
    if observation.get("candidate_sha256") != expected_hash:
        raise RunError("observation.candidate_sha256 does not match")
    text(observation.get("reviewer"), "observation.reviewer")
    if observation.get("method") != "direct-image-inspection":
        raise RunError("observation.method must be direct-image-inspection")
    panels = observation.get("panels")
    if not isinstance(panels, list) or not panels:
        raise RunError("observation.panels must contain observed scenes")
    panel_numbers = []
    for panel in panels:
        if (not isinstance(panel, dict) or type(panel.get("panel")) is not int
                or panel["panel"] < 1):
            raise RunError("observation.panels has an invalid panel")
        panel_numbers.append(panel["panel"])
        text(panel.get("observed_scene"), "observation.panels.observed_scene")
    if panel_numbers != sorted(set(panel_numbers)):
        raise RunError("observation.panels must cover reviewed panels once in reading order")
    if value.get("verdict") == "PASS" and (
        (component and max(panel_numbers) > image_spec["panel_count"])
        or (not component and panel_numbers != list(range(1, image_spec["panel_count"] + 1)))
    ):
        raise RunError("PASS observation.panels must match the assignment")
    transcript = observation.get("text_transcription")
    if not isinstance(transcript, list) or any(not isinstance(line, str) for line in transcript):
        raise RunError("observation.text_transcription must be a list of strings")
    expected_text = image_spec["core_text"]
    if component:
        expected_text = [image_spec["core_text"][line["text_index"]]
                         for line in image_spec["dialogue_plan"] if line["panel"] in panel_numbers]
    if value.get("verdict") == "PASS" and transcript != expected_text:
        raise RunError("observation.text_transcription does not match the assignment")
    gates_required = COMPONENT_GATES if component else CONFIGURABLE_GATES
    verdict = value.get("verdict")
    gates = value.get("gates")
    if verdict not in {"PASS", "FAIL"} or not isinstance(gates, dict) or set(gates) != gates_required:
        raise RunError("Visual QA has an invalid verdict or gate set")
    na_proportion = not component and gates.get("H1") == "NA"
    if any(gates[key] not in ({"PASS", "FAIL", "NA"} if key == "H1" else {"PASS", "FAIL"}) for key in gates_required):
        raise RunError("Visual QA gates must be PASS or FAIL; only H1 permits NA")
    if (not component and image_spec.get("proportion_check") == "visible-only"
            and gates["H1"] == "PASS"):
        raise RunError("visible-only proportion_check requires H1 NA or FAIL, not a measured PASS")
    evidence = value.get("evidence")
    form = evidence.get("form_evidence") if isinstance(evidence, dict) else None
    if (isinstance(form, dict)
            and (form.get("mode") == "visible-only" or image_spec.get("proportion_check") == "visible-only")
            and any(field in form for field in ("calculated_head_ratio", "head_axis", "body_segments"))):
        raise RunError("visible-only form_evidence must not claim calculated_head_ratio, head_axis, or body_segments")
    if na_proportion:
        if image_spec.get("proportion_check") != "visible-only":
            raise RunError("H1 NA requires proportion_check=visible-only")
        if not isinstance(form, dict) or form.get("mode") != "visible-only":
            raise RunError("H1 NA requires visible-only form_evidence")
        if form.get("candidate_sha256") != expected_hash:
            raise RunError("form_evidence.candidate_sha256 does not match the candidate")
        text(form.get("reason"), "form_evidence.reason")
        string_list(form.get("observed_cues"), "form_evidence.observed_cues")
    all_pass = all(gates[key] == "PASS" or (key == "H1" and na_proportion) for key in gates_required)
    if (verdict == "PASS") != all_pass:
        raise RunError("Visual QA verdict must agree with all gates")
    if value.get("candidate_sha256") != expected_hash:
        raise RunError("Visual QA candidate_sha256 does not match")
    defects = value.get("defects")
    if not isinstance(defects, list) or any(not isinstance(item, str) for item in defects):
        raise RunError("Visual QA defects must be a list of strings")
    if verdict == "PASS":
        if defects or value.get("targeted_retry") is not None:
            raise RunError("PASS requires no defects and targeted_retry=null")
        if not component:
            evidence = value.get("evidence")
            if not isinstance(evidence, dict):
                raise RunError("PASS requires evidence")
            text(evidence.get("why_funny"), "evidence.why_funny")
            text(evidence.get("fact_anchor_visible_as"), "evidence.fact_anchor_visible_as")
            transcription = evidence.get("text_transcription")
            if not isinstance(transcription, list) or any(not isinstance(item, str) for item in transcription):
                raise RunError("evidence.text_transcription must be a list of strings")
            expected_text = image_spec["core_text"]
            if transcription != expected_text:
                raise RunError("evidence.text_transcription does not match the assignment")
            validate_design_evidence(evidence, image_spec)
            for field in ("style_match", "costume_match", "background_match", "action_match"):
                text(evidence.get(field), f"evidence.{field}")
            if not na_proportion:
                validate_form_evidence(
                    evidence.get("form_evidence"), image_spec, expected_hash
                )
            text(evidence.get("form_consistency"), "evidence.form_consistency")
            text(evidence.get("crop_status"), "evidence.crop_status")
            expected_expressions = image_spec["expression_plan"]
            expression_match = evidence.get("expression_match")
            if not isinstance(expression_match, list) or len(expression_match) != len(expected_expressions):
                raise RunError("evidence.expression_match must contain one entry per panel")
            for expected, observed in zip(expected_expressions, expression_match, strict=True):
                if not isinstance(observed, dict):
                    raise RunError("evidence.expression_match entries must be objects")
                if (
                    observed.get("panel") != expected["panel"]
                    or observed.get("preset") != expected["preset"]
                    or observed.get("performance") != expected["performance"]
                ):
                    raise RunError("evidence.expression_match does not match the assignment")
                string_list(observed.get("observed_cues"), "expression_match.observed_cues")
                forbidden = observed.get("forbidden_cues_present")
                if forbidden != []:
                    raise RunError("expression_match.forbidden_cues_present must be empty for PASS")
    else:
        if not any(item.strip() for item in defects):
            raise RunError("FAIL requires concrete defects")
        text(value.get("targeted_retry"), "targeted_retry")
    return value


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


def record_image(args: argparse.Namespace, component: bool) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    if manifest.get("status") != "in_progress":
        raise RunError("Run is not open")
    state = state_for(manifest, args.image)
    image_spec = next(item for item in assignment["images"] if item["id"] == args.image)
    if state.get("status") in {"candidate_pass", "passed", "safety_blocked"}:
        raise RunError("Image task is closed")
    if len(state["attempts"]) >= MAX_CANDIDATES:
        raise RunError("Per-image candidate budget is exhausted")
    provider_allowed(state, args.provider)
    candidate = Path(args.candidate).resolve()
    prompt_file = Path(args.prompt_file).resolve()
    automatic_path = Path(args.automatic_json).resolve()
    visual_path = Path(args.visual_json).resolve()
    audit_path = Path(args.provider_audit).resolve() if getattr(args, "provider_audit", None) else None
    for item in (candidate, prompt_file, automatic_path, visual_path, audit_path):
        if item is not None and not item.is_file():
            raise RunError(f"Missing required file: {item}")
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    if not prompt:
        raise RunError("Prompt file is empty")
    candidate_hash = sha256(candidate)
    automatic = validate_automatic(automatic_path, candidate_hash, image_spec["output"])
    visual = validate_qa(
        visual_path,
        candidate_hash,
        component=component,
        image_spec=image_spec,
    )
    transport = resolve_transport(args, audit_path)
    audit = load_provider_audit(audit_path, args.provider, candidate_hash) if audit_path else None
    number = len(state["attempts"]) + 1
    role = "component" if component else "candidate"
    stem = f"{number:02d}_{role}_{args.provider}"
    attempt_dir = run_dir / "candidates" / args.image
    saved_image = attempt_dir / f"{stem}.png"
    saved_prompt = run_dir / "prompts" / args.image / f"{stem}.txt"
    saved_auto = run_dir / "qa" / args.image / f"{stem}_automatic.json"
    saved_visual = run_dir / "qa" / args.image / f"{stem}_visual.json"
    copy_once(candidate, saved_image)
    copy_once(prompt_file, saved_prompt)
    copy_once(automatic_path, saved_auto)
    copy_once(visual_path, saved_visual)
    provider_audit = None
    if audit is not None:
        saved_audit = run_dir / "logs" / args.image / f"{stem}_provider_audit.json"
        copy_once(audit_path, saved_audit)
        provider_audit = {
            "path": str(saved_audit), "sha256": sha256(saved_audit),
            **{key: audit.get(key) for key in ("thread_id", "prompt_verbatim", "usable")},
            "verified": audit["usable"] is True,
        }
    # A provider that rewrote the prompt or dropped references cannot yield a PASS;
    # an unverifiable audit may pass but stays flagged in the record and the final report.
    usable = audit is None or audit["usable"] is not False
    verdict = "PASS" if usable and automatic["overall"] == "PASS" and visual["verdict"] == "PASS" else "FAIL"
    record = {
        "attempt_id": f"attempt-{number:02d}", "role": role,
        "provider": args.provider, "model": args.model, "verdict": verdict,
        "candidate": str(saved_image), "candidate_sha256": candidate_hash,
        "prompt": str(saved_prompt), "automatic_qa": str(saved_auto),
        "visual_qa": str(saved_visual), "created_at": now(),
        "output": {
            "requested": image_spec["output"],
            "effective": automatic["expected_output"],
            "actual": automatic.get("metrics"),
        },
        "transport": transport,
        "provider_audit": provider_audit,
        "consumes_candidate_budget": True,
    }
    state["attempts"].append(record)
    state["status"] = "component_ready" if component and verdict == "PASS" else "candidate_pass" if verdict == "PASS" else "pending"
    save_manifest(run_dir, manifest)
    return record


def creative_markdown(assignment: dict[str, Any]) -> str:
    lines = [f"# {assignment['run_name']}", "", f"Fact anchor: {assignment['input']['fact_anchor']}", ""]
    if assignment.get("schema_version") == 12:
        lines.extend(["## Confirmed plan", "", plan_markdown(assignment), "```json",
                      json.dumps(assignment["confirmation"], ensure_ascii=False, indent=2), "```", "",
                      "## Tournament standings", "", "```json",
                      json.dumps(tournament_results(assignment), ensure_ascii=False, indent=2), "```", "",
                      "Tie decisions: " + json.dumps(assignment.get("tie_breaks", []), ensure_ascii=False), ""])
    else:
        lines.extend(["## Proposal selection and confirmation", "", proposal_markdown(assignment["proposal"]),
                      "```json", json.dumps({key: assignment[key] for key in ("selection", "confirmation")}, ensure_ascii=False, indent=2),
                      "```", "", selection_markdown(selection_summary(assignment)), ""])
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
                      f"- Direction: {idea['direction']} ({DIRECTION_LABELS[idea['direction']]})"])
        for field in DIRECTION_CARRIERS[idea["direction"]]:
            value = idea[field]
            lines.append(f"- {field.capitalize()}: {' → '.join(value) if isinstance(value, list) else value}")
        lines.extend([f"- Punchline: {idea['punchline']}", f"- Personality: {', '.join(idea['personality'])}", f"- Scene: {idea['scene']}"])
        lines.append(f"- Mechanism: {idea['mechanism']}")
        if "gate" in idea:
            lines.extend([f"- Gate: {idea['gate']}", f"- Gate reason: {idea['gate_reason']}"])
            if idea["gate"] == "FAIL":
                lines.append(f"- Rejected: {idea['rejection_reason']}")
        else:
            lines.append("- Key lines: " + json.dumps(idea["key_lines"], ensure_ascii=False))
        lines.append("")
    lines.extend(["## Pairwise duels", ""])
    for duel in assignment["duels"]:
        if "a" in duel:
            lines.append(f"- {duel['a']} vs {duel['b']}: {duel['winner'] or 'draw'} — {duel['reason']}")
        else:
            lines.append(f"- {duel['winner']} beat {duel['loser']}: {duel['reason']}")
    summary = design_summary([assignment])
    lines.extend([
        "", "## Design decisions", "",
        f"- Typography policy: {assignment['text_style_policy']}",
        f"- Template distribution: {summary['text_styles']}",
        f"- Direction distribution: {summary['directions']}",
        f"- Images with a rhythm layer: {summary['rhythm_images']} of {summary['image_count']}",
        f"- Images by cast representation (may overlap): {summary['cast_images']}",
        "- Pre-generation review: verify each template fits its joke and every omitted/offscreen role has a narrative reason. Counts alone do not establish design quality.",
    ])
    for participant in assignment["input"]["participants"]:
        lines.append(f"- Source role `{participant['id']}` ({participant['role']}): {participant['source_evidence']}")
    lines.extend([
        "", f"Final ranking: {' > '.join(assignment['ranked_ideas'])}",
        "", "## Execution", "",
        f"- Mode: {assignment['execution']['mode']}",
        f"- Requested parallelism: {assignment['execution']['requested_parallelism']}",
        "- Commit strategy: coordinator-serial",
        "", f"## {len(assignment['images'])} tasks", "",
    ])
    for image in assignment["images"]:
        lines.append(f"- `{image['id']}`: rank {image['source_rank']}, execution {image['execution']}, {image['panel_count']} panel(s), {image['intensity']}, {image['punchline']}")
        lines.extend([
            f"  - Idea: {image['idea_id']}; execution note: {image['execution_note']}",
            "  - Composition: " + json.dumps(image["composition"], ensure_ascii=False),
            f"  - Proportion check: {image['proportion_check']}",
            "  - Rhythm: " + (json.dumps(image["rhythm"], ensure_ascii=False) if image["rhythm"] else "none"),
        ])
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
    requested_parallelism = assignment["execution"]["requested_parallelism"]
    effective_parallelism = args.effective_parallelism or 1
    if not 1 <= effective_parallelism <= min(requested_parallelism, len(assignment["images"])):
        raise RunError("effective parallelism exceeds the requested or ready-image limit")
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = root / assignment["run_name"]
    suffix = 2
    while run_dir.exists():
        run_dir = root / f"{assignment['run_name']}-{suffix:02d}"
        suffix += 1
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
                copy_once(source, destination)
                if sha256(destination) != reference["sha256"]:
                    raise RunError(f"Frozen reference SHA-256 mismatch: {destination}")
                copied[key] = str(destination)
            reference["path"] = copied[key]
        (run_dir / "staging" / image["id"]).mkdir(parents=True, exist_ok=True)
    assignment["run_dir"] = str(run_dir)
    assignment["frozen_at"] = now()
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
                copy_once(
                    source_path,
                    run_dir / "source" / f"original-{index:02d}{source_path.suffix.lower()}",
                )
    states = {
        image["id"]: {
            "status": "pending", "attempts": [], "derived": [],
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
            "initial_ready_image_count": len(assignment["images"]),
        },
        "created_at": now(), "updated_at": now(), "images": states,
    }
    write_json(run_dir / "manifest.json", manifest)
    return {
        "run_dir": str(run_dir),
        "images": list(states),
        "execution": manifest["execution"],
    }


def cmd_record_error(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, _assignment, manifest = load_run(args.run_dir)
    if manifest.get("status") != "in_progress":
        raise RunError("Run is not open")
    state = state_for(manifest, args.image)
    if state.get("status") in {"candidate_pass", "passed", "safety_blocked"}:
        raise RunError("Image task is closed")
    provider_allowed(state, args.provider)
    if args.category not in ADVANCE_ERRORS | {"safety_rejection"}:
        raise RunError("Unsupported provider error category")
    record = {"error_id": f"error-{len(state['provider_errors']) + 1:02d}", "provider": args.provider, "model": args.model, "category": args.category, "details": args.details, "created_at": now(), "consumes_candidate_budget": False}
    state["provider_errors"].append(record)
    if args.category == "safety_rejection":
        state["status"] = "safety_blocked"
    path = run_dir / "logs" / args.image / f"{record['error_id']}_{args.provider}.json"
    write_json(path, record)
    save_manifest(run_dir, manifest)
    return {"recorded": str(path), "attempts": len(state["attempts"])}


def cmd_record_composite(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    state = state_for(manifest, args.image)
    image_spec = next(item for item in assignment["images"] if item["id"] == args.image)
    source_ids = args.source_attempt
    expected = image_spec["panel_count"]
    if expected not in {2, 4} or len(source_ids) != expected:
        raise RunError("Composite source count must equal a 2- or 4-panel assignment")
    if len(set(source_ids)) != len(source_ids):
        raise RunError("Composite source attempts must be unique")
    sources = []
    for attempt_id in source_ids:
        match = next((item for item in state["attempts"] if item["attempt_id"] == attempt_id and item["role"] == "component" and item["verdict"] == "PASS"), None)
        if match is None:
            raise RunError(f"Composite source is not a passing component: {attempt_id}")
        sources.append(match)
    candidate = Path(args.candidate).resolve()
    automatic_path = Path(args.automatic_json).resolve()
    visual_path = Path(args.visual_json).resolve()
    for item in (candidate, automatic_path, visual_path):
        if not item.is_file():
            raise RunError(f"Missing required file: {item}")
    candidate_hash = sha256(candidate)
    automatic = validate_automatic(automatic_path, candidate_hash, image_spec["output"])
    visual = validate_qa(visual_path, candidate_hash, image_spec=image_spec)
    verdict = "PASS" if automatic["overall"] == "PASS" and visual["verdict"] == "PASS" else "FAIL"
    number = len(state["derived"]) + 1
    stem = f"composite-{number:02d}"
    saved_image = run_dir / "candidates" / args.image / f"{stem}.png"
    saved_auto = run_dir / "qa" / args.image / f"{stem}_automatic.json"
    saved_visual = run_dir / "qa" / args.image / f"{stem}_visual.json"
    copy_once(candidate, saved_image)
    copy_once(automatic_path, saved_auto)
    copy_once(visual_path, saved_visual)
    record = {"derived_id": stem, "role": "composite", "verdict": verdict, "candidate": str(saved_image), "candidate_sha256": candidate_hash, "source_attempts": source_ids, "source_sha256": [item["candidate_sha256"] for item in sources], "automatic_qa": str(saved_auto), "visual_qa": str(saved_visual), "output": {"requested": image_spec["output"], "effective": automatic["expected_output"], "actual": automatic.get("metrics")}, "created_at": now(), "consumes_candidate_budget": False}
    state["derived"].append(record)
    state["status"] = "candidate_pass" if verdict == "PASS" else "pending"
    save_manifest(run_dir, manifest)
    return record


def cmd_promote(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    state = state_for(manifest, args.image)
    passing = [item for item in state["attempts"] + state["derived"] if item.get("verdict") == "PASS" and item.get("role") != "component"]
    if not passing:
        raise RunError("No passing full comic is available")
    selected = passing[-1]
    source = Path(selected["candidate"])
    image_spec = next(item for item in assignment["images"] if item["id"] == args.image)
    candidate_hash = sha256(source)
    if candidate_hash != selected["candidate_sha256"]:
        raise RunError("Candidate SHA-256 mismatch before promotion")
    visual = validate_qa(Path(selected["visual_qa"]), candidate_hash, image_spec=image_spec)
    automatic = validate_automatic(Path(selected["automatic_qa"]), candidate_hash, image_spec["output"])
    if visual["verdict"] != "PASS" or automatic["overall"] != "PASS":
        raise RunError("Promotion requires current PASS QA")
    destination = run_dir / "final" / f"{args.image}.png"
    copy_once(source, destination)
    state["status"] = "passed"
    state["final_path"] = str(destination)
    state["final_sha256"] = sha256(destination)
    save_manifest(run_dir, manifest)
    return {"final": str(destination), "sha256": state["final_sha256"]}


def cmd_finalize(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    expected = len(assignment["images"])
    passed = [key for key, value in manifest["images"].items() if value["status"] == "passed"]
    if len(passed) != expected and not args.allow_partial:
        raise RunError(f"Only {len(passed)}/{expected} tasks passed; use --allow-partial to finalize honestly")
    if len(passed) != expected:
        unresolved = []
        for key, state in manifest["images"].items():
            if state["status"] == "passed":
                continue
            all_providers_failed = {
                item["provider"]
                for item in state["provider_errors"]
                if item.get("category") in ADVANCE_ERRORS
            } == set(PROVIDERS)
            if (
                state["status"] != "safety_blocked"
                and len(state["attempts"]) < MAX_CANDIDATES
                and not all_providers_failed
            ):
                unresolved.append(key)
        if unresolved:
            raise RunError(
                "Cannot finalize while tasks still have a viable attempt: "
                + ", ".join(unresolved)
            )
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
                          ("summarize-selection", cmd_summarize_selection),
                          ("rank-ideas", cmd_rank_ideas)):
        command = commands.add_parser(name)
        command.add_argument("--draft", required=True)
        command.set_defaults(handler=handler)
    validate = commands.add_parser("validate-assignment")
    validate.add_argument("--assignment", required=True)
    validate.set_defaults(handler=cmd_validate)
    batch = commands.add_parser("validate-batch")
    batch.add_argument("--assignment", action="append", required=True)
    batch.set_defaults(handler=cmd_validate_batch)
    init = commands.add_parser("init")
    init.add_argument("--assignment", required=True)
    init.add_argument("--root", default="artifacts/whalechan-image-comic")
    init.add_argument("--effective-parallelism", type=int)
    init.set_defaults(handler=cmd_init)
    error = commands.add_parser("record-error")
    error.add_argument("--run-dir", required=True); error.add_argument("--image", required=True)
    error.add_argument("--provider", choices=PROVIDERS, required=True); error.add_argument("--model", required=True)
    error.add_argument("--category", required=True); error.add_argument("--details", required=True)
    error.set_defaults(handler=cmd_record_error)
    for command, component in (("record-candidate", False), ("record-component", True)):
        item = commands.add_parser(command)
        item.add_argument("--run-dir", required=True); item.add_argument("--image", required=True)
        item.add_argument("--provider", choices=PROVIDERS, required=True); item.add_argument("--model", required=True)
        item.add_argument("--candidate", required=True); item.add_argument("--prompt-file", required=True)
        item.add_argument("--automatic-json", required=True); item.add_argument("--visual-json", required=True)
        item.add_argument("--provider-audit", help="Adapter audit JSON, e.g. generate-codex.py's <output>.codex.json")
        item.add_argument("--transport", choices=("cli", "builtin"),
                          help="How a codex candidate was produced: generate-codex.py (cli) or the built-in tool")
        item.set_defaults(handler=lambda args, component=component: record_image(args, component))
    composite = commands.add_parser("record-composite")
    composite.add_argument("--run-dir", required=True); composite.add_argument("--image", required=True)
    composite.add_argument("--candidate", required=True); composite.add_argument("--automatic-json", required=True)
    composite.add_argument("--visual-json", required=True); composite.add_argument("--source-attempt", action="append", required=True)
    composite.set_defaults(handler=cmd_record_composite)
    promote = commands.add_parser("promote")
    promote.add_argument("--run-dir", required=True); promote.add_argument("--image", required=True)
    promote.set_defaults(handler=cmd_promote)
    finalize = commands.add_parser("finalize")
    finalize.add_argument("--run-dir", required=True); finalize.add_argument("--allow-partial", action="store_true")
    finalize.set_defaults(handler=cmd_finalize)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = args.handler(args)
    except RunError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
