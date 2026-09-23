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
ASSIGNMENT_SCHEMA_VERSION = 9
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
MAX_PARALLELISM = 5
IMAGE_FIELDS = {
    "name", "id", "idea_id", "source_rank", "execution", "execution_note",
    "composition", "proportion_check", "qa_contract_version",
    "fact_anchor", "premise", "punchline", "why_funny", "personality",
    "panel_count", "layout", "intensity", "output", "expression_plan",
    "action_plan", "style", "costume", "background", "core_text",
    "text_style", "text_style_reason", "dialogue_plan", "cast_plan",
    "proportion", "proportion_sha256", "identity_anchor_form", "references",
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
            "instruction": "Preserve only the declared canonical Whale-chan roles",
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
        if line.get("delivery") not in {"speech", "thought", "caption"}:
            raise RunError(f"{label}.dialogue_plan.delivery is invalid")
        if speaker == "narrator" and line["delivery"] != "caption":
            raise RunError(f"{label}.narrator must use caption delivery")
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
                "panel_count": image["panel_count"], "layout": image["layout"],
                "shot": composition["shot"], "staging": composition["staging"],
                "text_placement": composition["text_placement"],
                "template": image["text_style"],
                "beats": [item["action"] for item in image["action_plan"]],
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
            for field in ("mechanism", "beats", "staging"):
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
    return {
        "structurally_valid": True,
        "creative_review_required": len(assignments) > 1 or bool(warnings),
        "creative_approval": None,
        "matrix": matrix,
        "warnings": warnings,
        "image_count": len(images),
        "text_styles": dict(sorted(Counter(image["text_style"] for image in images).items())),
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
    source["language"] = text(source.get("language"), "input.language")
    anchor = text(source.get("fact_anchor"), "input.fact_anchor")
    participants = validate_participants(source)
    analysis = source.get("source_analysis")
    if not isinstance(analysis, dict):
        raise RunError("input.source_analysis must be an object")
    for field in ("source_event", "expectation", "actual_turn", "comic_target", "tone", "language_notes"):
        text(analysis.get(field), f"input.source_analysis.{field}")
    constraints = analysis.get("user_constraints")
    if not isinstance(constraints, list) or any(not isinstance(item, str) for item in constraints):
        raise RunError("input.source_analysis.user_constraints must be a list of strings")
    text(assignment.get("selection_reason"), "selection_reason")

    pool = assignment.get("creative_pool")
    if not isinstance(pool, list) or not pool:
        raise RunError("creative_pool must contain at least one idea")
    ideas: dict[str, dict[str, Any]] = {}
    required_idea = ("premise", "expectation", "reversal", "punchline", "fact_anchor", "scene", "mechanism", "gate_reason")
    for index, idea in enumerate(pool):
        if not isinstance(idea, dict):
            raise RunError(f"creative_pool[{index}] must be an object")
        idea_id = text(idea.get("id"), f"creative_pool[{index}].id")
        if not re.fullmatch(r"idea_[0-9]{2}", idea_id) or idea_id in ideas:
            raise RunError("idea ids must be unique idea_NN values")
        for field in required_idea:
            text(idea.get(field), f"{idea_id}.{field}")
        if idea["fact_anchor"] != anchor:
            raise RunError(f"{idea_id}.fact_anchor must equal input.fact_anchor")
        traits = string_list(idea.get("personality"), f"{idea_id}.personality", 2)
        if len(traits) != 2:
            raise RunError(f"{idea_id}.personality must contain exactly 2 traits")
        if idea.get("gate") not in {"PASS", "FAIL"}:
            raise RunError(f"{idea_id}.gate must be PASS or FAIL")
        if idea["gate"] == "FAIL":
            text(idea.get("rejection_reason"), f"{idea_id}.rejection_reason")
        ideas[idea_id] = idea
    ranked = assignment.get("ranked_ideas")
    if (not isinstance(ranked, list) or not 1 <= len(ranked) <= 5
            or any(not isinstance(item, str) for item in ranked) or len(set(ranked)) != len(ranked)):
        raise RunError("ranked_ideas must contain 1 through 5 unique ids")
    if any(item not in ideas or ideas[item]["gate"] != "PASS" for item in ranked):
        raise RunError("ranked_ideas must reference passing creative_pool ideas")
    duels = assignment.setdefault("duels", [])
    if not isinstance(duels, list):
        raise RunError("duels must be a list; use [] when no duels were held")
    for index, duel in enumerate(duels):
        if not isinstance(duel, dict) or duel.get("winner") not in ideas or duel.get("loser") not in ideas:
            raise RunError(f"duels[{index}] has unknown ideas")
        if duel["winner"] == duel["loser"]:
            raise RunError(f"duels[{index}] winner and loser must differ")
        text(duel.get("reason"), f"duels[{index}].reason")

    assignment["execution"] = normalize_execution(assignment.get("execution"))

    images = assignment.get("images")
    if not isinstance(images, list) or len(images) != 5:
        raise RunError("images must contain exactly 5 tasks")
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
    budget = assignment.get("budget", {})
    if not isinstance(budget, dict) or budget.get("per_image_candidates", MAX_CANDIDATES) != MAX_CANDIDATES:
        raise RunError("budget.per_image_candidates must be 3")
    assignment["budget"] = {"per_image_candidates": MAX_CANDIDATES, "maximum_total": 15}
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
    if assignment.get("schema_version") != ASSIGNMENT_SCHEMA_VERSION:
        raise RunError(f"Run assignment schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise RunError(f"Manifest schema_version must be {MANIFEST_SCHEMA_VERSION}")
    _assets, _forms, current_hash = catalog()
    if assignment.get("asset_catalog_sha256") != current_hash or manifest.get("asset_catalog_sha256") != current_hash:
        raise RunError("Run asset catalog no longer matches this Skill")
    expected_assignment_hash = require_sha256(manifest.get("assignment_sha256"), "manifest.assignment_sha256")
    if sha256(run_dir / "assignment.json") != expected_assignment_hash:
        raise RunError("Frozen assignment SHA-256 mismatch")
    images = assignment.get("images")
    if not isinstance(images, list) or len(images) != 5:
        raise RunError("Frozen assignment must contain five images")
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
    for item in (candidate, prompt_file, automatic_path, visual_path):
        if not item.is_file():
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
    verdict = "PASS" if automatic["overall"] == "PASS" and visual["verdict"] == "PASS" else "FAIL"
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
        "consumes_candidate_budget": True,
    }
    state["attempts"].append(record)
    state["status"] = "component_ready" if component and verdict == "PASS" else "candidate_pass" if verdict == "PASS" else "pending"
    save_manifest(run_dir, manifest)
    return record


def creative_markdown(assignment: dict[str, Any]) -> str:
    lines = [f"# {assignment['run_name']}", "", f"Fact anchor: {assignment['input']['fact_anchor']}", ""]
    lines.extend([
        "## Source analysis", "", "```json",
        json.dumps(assignment["input"]["source_analysis"], ensure_ascii=False, indent=2),
        "```", "", f"Selection reason: {assignment['selection_reason']}", "",
    ])
    lines.extend(["## Creative pool", ""])
    for idea in assignment["creative_pool"]:
        lines.extend([f"### {idea['id']} — {idea['gate']}", "", f"- Premise: {idea['premise']}", f"- Expectation: {idea['expectation']}", f"- Reversal: {idea['reversal']}", f"- Punchline: {idea['punchline']}", f"- Personality: {', '.join(idea['personality'])}", f"- Scene: {idea['scene']}"])
        lines.extend([f"- Mechanism: {idea['mechanism']}", f"- Gate reason: {idea['gate_reason']}"])
        if idea["gate"] == "FAIL":
            lines.append(f"- Rejected: {idea['rejection_reason']}")
        lines.append("")
    lines.extend(["## Pairwise duels", ""])
    for duel in assignment["duels"]:
        lines.append(f"- {duel['winner']} beat {duel['loser']}: {duel['reason']}")
    summary = design_summary([assignment])
    lines.extend([
        "", "## Design decisions", "",
        f"- Typography policy: {assignment['text_style_policy']}",
        f"- Template distribution: {summary['text_styles']}",
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
        "", "## Five tasks", "",
    ])
    for image in assignment["images"]:
        lines.append(f"- `{image['id']}`: rank {image['source_rank']}, execution {image['execution']}, {image['panel_count']} panel(s), {image['intensity']}, {image['punchline']}")
        lines.extend([
            f"  - Idea: {image['idea_id']}; execution note: {image['execution_note']}",
            "  - Composition: " + json.dumps(image["composition"], ensure_ascii=False),
            f"  - Proportion check: {image['proportion_check']}",
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
        "maximum_total": 15,
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
    run_dir, _assignment, manifest = load_run(args.run_dir)
    passed = [key for key, value in manifest["images"].items() if value["status"] == "passed"]
    if len(passed) != 5 and not args.allow_partial:
        raise RunError(f"Only {len(passed)}/5 tasks passed; use --allow-partial to finalize honestly")
    if len(passed) != 5:
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
    manifest["status"] = "complete" if len(passed) == 5 else "partial"
    manifest["completed_at"] = now()
    save_manifest(run_dir, manifest)
    return {
        "status": manifest["status"],
        "passed": len(passed),
        "final_paths": [manifest["images"][key]["final_path"] for key in passed],
        "execution": manifest.get("execution"),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
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
