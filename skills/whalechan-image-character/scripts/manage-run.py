#!/usr/bin/env python3
"""Validate, initialize, audit, and finalize Whale-chan character runs."""

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROVIDERS = ["codex", "openai", "nano-banana", "seedream"]
FORM_ORDER = ("standard", "compact", "semi-chibi", "chibi", "super-deformed")
FORMS = set(FORM_ORDER)
CATALOG_SCHEMA_VERSION = 4
ASSIGNMENT_SCHEMA_VERSION = 4
MANIFEST_SCHEMA_VERSION = 3
AUTOMATIC_QA_SCHEMA_VERSION = 2
INPUT_TYPES = {"text", "screenshot", "chat-log", "dialogue"}
REFERENCE_ROLES = {
    "identity",
    "style",
    "pose_action",
    "composition",
    "costume",
    "background",
    "typography",
    "proportion",
}
STYLE_MODES = {"canonical", "custom"}
COSTUME_MODES = {"canonical", "custom"}
BACKGROUND_MODES = {"solid", "custom", "transparent"}
PROPORTION_MODES = {"preset", "custom"}
TEXT_DIRECTIONS = {"ltr", "rtl", "vertical"}
EXECUTION_MODES = {"sequential", "parallel"}
RESOLUTION_MODES = {"provider-native", "exact"}
MAX_PARALLELISM = 5
MAX_IMAGE_CANDIDATES = 8
NORMAL_RUN_CANDIDATES = 24
DEFAULT_BACKGROUND = "warm ivory-beige #F5EADD"
DEFAULT_STYLE = "canonical clean rounded cel-shaded Whale-chan style"
DEFAULT_COSTUME = "canonical navy-and-white ornate maid outfit"
EXHAUSTING_ERRORS = {"unavailable", "authentication", "quota", "capability"}
SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "reference-catalog.json"
REQUIRED_VISUAL_GATES = {
    "V1",
    "I1",
    "I2",
    "F1a",
    "F1b",
    "F1c",
    "F1d",
    "F1e",
    "P1",
    "A1",
    "O1",
    "C1",
    "X1",
    "S1",
}
FORM_EVIDENCE_TEXT_FIELDS = {
    "torso",
    "arms",
    "legs",
    "hands_feet",
}
MEASUREMENT_METHOD = "pose-neutralized-skeleton"
BODY_SEGMENT_NAMES = ("chin_to_pelvis", "pelvis_to_knee", "knee_to_sole")
PAIRWISE_BOOLEAN_FIELDS = {
    "head_ratio_clearly_different",
    "compact_form_torso_visibly_shorter",
    "compact_form_limbs_visibly_shorter",
    "apparent_age_unchanged",
}


class RunError(RuntimeError):
    """A deterministic run-state error."""


def utc_now() -> str:
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
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunError(f"{label} must be a non-empty string")
    return value.strip()


def require_exact_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunError(f"{label} must be a non-empty string")
    return value


def require_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    missing = sorted(fields - value.keys())
    if missing:
        raise RunError(f"{label} is missing required fields: {', '.join(missing)}")


def require_only_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    unexpected = sorted(value.keys() - fields)
    if unexpected:
        raise RunError(f"{label} contains unsupported fields: {', '.join(unexpected)}")


def require_iso8601(value: Any, label: str) -> str:
    value = require_string(value, label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RunError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise RunError(f"{label} must include a timezone")
    return value


def require_sha256(value: Any, label: str) -> str:
    value = require_string(value, label).lower()
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise RunError(f"{label} must be a SHA-256 hex digest")
    return value


def require_string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise RunError(f"{label} must be a non-empty list")
    return [require_string(item, f"{label} item") for item in value]


def identify_reference(path: Path) -> dict[str, Any]:
    magick = shutil.which("magick")
    if not magick:
        raise RunError("ImageMagick 'magick' is required to validate reference images")
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


def target_sha256(mode: str, preset: str | None, mean: float, acceptance_range: list[float]) -> str:
    value = {
        "mode": mode,
        "preset": preset,
        "target_head_ratio": float(mean),
        "acceptance_range": [float(item) for item in acceptance_range],
    }
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def nearest_form(catalog: dict[str, Any], mean: float) -> str:
    return min(
        FORM_ORDER,
        key=lambda form: abs(float(catalog["forms"][form]["mean_head_ratio"]) - mean),
    )


def load_catalog() -> tuple[dict[str, Any], str]:
    catalog = read_json(CATALOG_PATH)
    if catalog.get("schema_version") != CATALOG_SCHEMA_VERSION:
        raise RunError(
            f"reference catalog schema_version must be {CATALOG_SCHEMA_VERSION}"
        )
    forms = catalog.get("forms")
    if not isinstance(forms, dict) or set(forms) != FORMS:
        raise RunError(f"reference catalog must define: {', '.join(FORM_ORDER)}")
    if catalog.get("default_form") != "semi-chibi":
        raise RunError("reference catalog default_form must be semi-chibi")
    if catalog.get("aggregation") != "arithmetic_mean":
        raise RunError("reference catalog aggregation must be arithmetic_mean")
    if catalog.get("mean_precision_decimals") != 1:
        raise RunError("reference catalog mean_precision_decimals must be 1")
    tolerance = catalog.get("acceptance_tolerance")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or tolerance <= 0:
        raise RunError("reference catalog acceptance_tolerance must be positive")
    gap = catalog.get("pairwise_minimum_head_ratio_gap")
    if isinstance(gap, bool) or not isinstance(gap, (int, float)) or gap <= 0:
        raise RunError("reference catalog pairwise_minimum_head_ratio_gap must be positive")
    for form, profile in forms.items():
        if not isinstance(profile, dict):
            raise RunError(f"reference catalog {form} profile must be an object")
        references = profile.get("references")
        if not isinstance(references, list) or not references:
            raise RunError(f"reference catalog {form} requires references")
        primary_entries = [
            item for item in references
            if isinstance(item, dict) and item.get("primary") is True
        ]
        primary_count = len(primary_entries)
        if primary_count != 1:
            raise RunError(f"reference catalog {form} requires exactly one primary")
        paths = {item.get("path") for item in references if isinstance(item, dict)}
        if len(paths) != len(references):
            raise RunError(f"reference catalog {form} paths must be unique")
        if profile.get("primary") not in paths:
            raise RunError(f"reference catalog {form} primary must be listed")
        if primary_entries[0].get("path") != profile.get("primary"):
            raise RunError(f"reference catalog {form} primary flag must match primary path")
        mean_head_ratio = profile.get("mean_head_ratio")
        if isinstance(mean_head_ratio, bool) or not isinstance(mean_head_ratio, (int, float)):
            raise RunError(f"reference catalog {form} mean_head_ratio must be a number")
        acceptance_range = profile.get("acceptance_range")
        if (
            not isinstance(acceptance_range, list)
            or len(acceptance_range) != 2
            or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in acceptance_range)
            or acceptance_range[0] >= acceptance_range[1]
        ):
            raise RunError(f"reference catalog {form} acceptance_range is invalid")
        for entry in references:
            if not isinstance(entry, dict):
                raise RunError(f"reference catalog {form} entry must be an object")
            relative = Path(require_string(entry.get("path"), f"reference catalog {form} path"))
            if relative.is_absolute() or ".." in relative.parts:
                raise RunError(f"reference catalog {form} path must stay inside the skill")
            expected_parent = Path("assets") / "reference-images" / form
            if relative.parent != expected_parent:
                raise RunError(f"reference catalog {form} path is outside its form directory")
            reference_path = (SKILL_ROOT / relative).resolve()
            if not reference_path.is_file():
                raise RunError(f"Reference catalog image does not exist: {reference_path}")
            expected_sha256 = require_sha256(
                entry.get("sha256"), f"reference catalog {form} SHA-256"
            )
            if sha256(reference_path) != expected_sha256:
                raise RunError(f"Reference catalog image SHA-256 mismatch: {reference_path}")
            measured = entry.get("measured_head_ratio")
            if isinstance(measured, bool) or not isinstance(measured, (int, float)) or measured <= 0:
                raise RunError(f"reference catalog {form} measured_head_ratio must be positive")
        raw_mean = sum(
            float(item["measured_head_ratio"]) for item in references
        ) / len(references)
        calculated_mean = round(raw_mean, catalog["mean_precision_decimals"])
        if not math.isclose(float(mean_head_ratio), calculated_mean, abs_tol=0.0005):
            raise RunError(f"reference catalog {form} mean_head_ratio must equal its reference arithmetic mean")
        expected_range = [
            round(raw_mean - float(tolerance), 3),
            round(raw_mean + float(tolerance), 3),
        ]
        if acceptance_range != expected_range:
            raise RunError(
                f"reference catalog {form} acceptance_range must equal unrounded mean ± tolerance"
            )
        if any(
            not expected_range[0] <= float(item["measured_head_ratio"]) <= expected_range[1]
            for item in references
        ):
            raise RunError(
                f"reference catalog {form} contains a reference outside its acceptance_range"
            )
    actual_paths = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in (SKILL_ROOT / "assets" / "reference-images").glob("*/*.webp")
    }
    catalog_paths = {
        item["path"] for profile in forms.values() for item in profile["references"]
    }
    if actual_paths != catalog_paths:
        raise RunError("reference catalog paths must exactly match current reference images")
    return catalog, sha256(CATALOG_PATH)


def validate_measurement_target(
    evidence: dict[str, Any], image_spec: dict[str, Any]
) -> None:
    _catalog, catalog_sha256 = load_catalog()
    proportion = image_spec["proportion"]
    if evidence.get("catalog_sha256") != catalog_sha256:
        raise RunError("form_evidence.catalog_sha256 does not match the reference catalog")
    if evidence.get("mean_head_ratio") != proportion["target_head_ratio"]:
        raise RunError("form_evidence.mean_head_ratio does not match the frozen assignment")
    if evidence.get("acceptance_range") != proportion["acceptance_range"]:
        raise RunError("form_evidence.acceptance_range does not match the frozen assignment")
    if evidence.get("target_source") != proportion["mode"]:
        raise RunError("form_evidence.target_source does not match the frozen assignment")
    if evidence.get("target_sha256") != image_spec["proportion_sha256"]:
        raise RunError("form_evidence.target_sha256 does not match the frozen assignment")


def normalize_named_mode(
    value: Any,
    modes: set[str],
    default_description: str,
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    require_fields(value, {"mode", "description"}, label)
    require_only_fields(value, {"mode", "description"}, label)
    mode = value.get("mode")
    if mode not in modes:
        raise RunError(f"{label}.mode must be one of: {', '.join(sorted(modes))}")
    supplied_description = value.get("description")
    description = require_string(supplied_description, f"{label}.description")
    if mode == "custom":
        return {"mode": mode, "description": description}
    else:
        if description != default_description:
            raise RunError(f"{label}.description must match the canonical default")
        description = default_description
    return {"mode": mode, "description": description}


def normalize_background(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    require_fields(value, {"mode", "description"}, label)
    require_only_fields(value, {"mode", "description"}, label)
    mode = value.get("mode")
    if mode not in BACKGROUND_MODES:
        raise RunError(f"{label}.mode must be one of: {', '.join(sorted(BACKGROUND_MODES))}")
    description = require_string(value.get("description"), f"{label}.description")
    return {"mode": mode, "description": description}


def normalize_output(
    value: Any,
    background: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object")
    fields = {"format", "alpha", "aspect_ratio", "resolution"}
    require_fields(value, fields, label)
    require_only_fields(value, fields, label)
    if value.get("format") != "png":
        raise RunError(f"{label}.format must be png")
    alpha = value.get("alpha")
    if not isinstance(alpha, bool):
        raise RunError(f"{label}.alpha must be boolean")
    expected_alpha = background["mode"] == "transparent"
    if alpha != expected_alpha:
        raise RunError(
            f"{label}.alpha must be {str(expected_alpha).lower()} "
            f"for {background['mode']} background"
        )

    aspect_ratio = value.get("aspect_ratio")
    ratio_match = (
        re.fullmatch(r"([1-9]\d*):([1-9]\d*)", aspect_ratio)
        if isinstance(aspect_ratio, str)
        else None
    )
    if ratio_match is None:
        raise RunError(f"{label}.aspect_ratio must be a positive WIDTH:HEIGHT ratio")
    ratio_width, ratio_height = (int(item) for item in ratio_match.groups())

    resolution = value.get("resolution")
    if not isinstance(resolution, dict):
        raise RunError(f"{label}.resolution must be an object")
    resolution_fields = {"mode", "width", "height"}
    require_fields(resolution, resolution_fields, f"{label}.resolution")
    require_only_fields(resolution, resolution_fields, f"{label}.resolution")
    mode = resolution.get("mode")
    if mode not in RESOLUTION_MODES:
        raise RunError(
            f"{label}.resolution.mode must be one of: "
            f"{', '.join(sorted(RESOLUTION_MODES))}"
        )
    width = resolution.get("width")
    height = resolution.get("height")
    if mode == "provider-native":
        if width is not None or height is not None:
            raise RunError(
                f"{label}.resolution provider-native mode requires null width and height"
            )
    else:
        if (
            isinstance(width, bool)
            or not isinstance(width, int)
            or width < 1
            or isinstance(height, bool)
            or not isinstance(height, int)
            or height < 1
        ):
            raise RunError(
                f"{label}.resolution exact mode requires positive width and height"
            )
        if not math.isclose(
            width / height,
            ratio_width / ratio_height,
            rel_tol=0.02,
        ):
            raise RunError(f"{label}.resolution dimensions do not match aspect_ratio")
    return {
        "format": "png",
        "alpha": alpha,
        "aspect_ratio": aspect_ratio,
        "resolution": {"mode": mode, "width": width, "height": height},
    }


def normalize_text(value: Any, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise RunError(f"{label} must be null or an object")
    require_fields(value, {"content", "languages", "direction", "placement", "style"}, label)
    require_only_fields(value, {"content", "languages", "direction", "placement", "style"}, label)
    languages = value.get("languages")
    languages = require_string_list(languages, f"{label}.languages")
    if len(set(languages)) != len(languages) or any(
        not re.fullmatch(r"[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*", language)
        for language in languages
    ):
        raise RunError(f"{label}.languages must contain unique BCP-47 language tags")
    direction = value.get("direction")
    if direction not in TEXT_DIRECTIONS:
        raise RunError(f"{label}.direction must be one of: {', '.join(sorted(TEXT_DIRECTIONS))}")
    return {
        "content": require_exact_string(value.get("content"), f"{label}.content"),
        "languages": languages,
        "direction": direction,
        "placement": require_string(value.get("placement"), f"{label}.placement"),
        "style": require_string(value.get("style"), f"{label}.style"),
    }


def normalize_proportion(
    image: dict[str, Any], catalog: dict[str, Any], label: str
) -> tuple[dict[str, Any], str]:
    value = image.get("proportion")
    if not isinstance(value, dict):
        raise RunError(f"{label}.proportion must be an object")
    require_fields(
        value,
        {"mode", "preset", "target_head_ratio", "acceptance_range", "proportion_reference"},
        f"{label}.proportion",
    )
    require_only_fields(
        value,
        {"mode", "preset", "target_head_ratio", "acceptance_range", "proportion_reference"},
        f"{label}.proportion",
    )
    mode = value.get("mode")
    if mode not in PROPORTION_MODES:
        raise RunError(
            f"{label}.proportion.mode must be one of: {', '.join(sorted(PROPORTION_MODES))}"
        )
    if mode == "preset":
        preset = value.get("preset")
        if preset not in FORMS:
            raise RunError(f"{label}.proportion.preset must be one of: {', '.join(FORM_ORDER)}")
        profile = catalog["forms"][preset]
        mean = float(profile["mean_head_ratio"])
        acceptance_range = list(profile["acceptance_range"])
        supplied_mean = value.get("target_head_ratio")
        supplied_range = value.get("acceptance_range")
        if supplied_mean is None or supplied_range is None:
            raise RunError(f"{label}.proportion preset target and range must be explicit")
        if supplied_mean is not None:
            if (
                isinstance(supplied_mean, bool)
                or not isinstance(supplied_mean, (int, float))
                or not math.isfinite(supplied_mean)
                or not math.isclose(float(supplied_mean), mean, abs_tol=1e-9)
            ):
                raise RunError(f"{label}.proportion target does not match preset {preset}")
        if supplied_range is not None and supplied_range != acceptance_range:
            raise RunError(f"{label}.proportion range does not match preset {preset}")
        anchor_form = preset
        reference = catalog["forms"][preset]["primary"]
        supplied_reference = value.get("proportion_reference")
        if supplied_reference != reference:
            raise RunError(f"{label}.proportion_reference must match preset {preset}")
    else:
        if value.get("preset") is not None:
            raise RunError(f"{label}.proportion.preset must be null in custom mode")
        preset = None
        mean = value.get("target_head_ratio")
        if (
            isinstance(mean, bool)
            or not isinstance(mean, (int, float))
            or not math.isfinite(mean)
            or mean <= 1
        ):
            raise RunError(f"{label}.proportion.target_head_ratio must be greater than 1")
        mean = float(mean)
        acceptance_range = value.get("acceptance_range")
        if acceptance_range is None:
            raise RunError(f"{label}.proportion.acceptance_range must be explicit in custom mode")
        if (
            not isinstance(acceptance_range, list)
            or len(acceptance_range) != 2
            or any(
                isinstance(item, bool)
                or not isinstance(item, (int, float))
                or not math.isfinite(item)
                for item in acceptance_range
            )
            or acceptance_range[0] <= 1
            or acceptance_range[0] >= acceptance_range[1]
            or not acceptance_range[0] <= mean <= acceptance_range[1]
        ):
            raise RunError(f"{label}.proportion.acceptance_range must contain a target greater than 1")
        acceptance_range = [float(item) for item in acceptance_range]
        anchor_form = nearest_form(catalog, mean)
        reference = None
        if value.get("proportion_reference") is not None:
            raise RunError(f"{label}.proportion.proportion_reference must be null in custom mode")
    normalized = {
        "mode": mode,
        "preset": preset,
        "target_head_ratio": mean,
        "acceptance_range": acceptance_range,
        "proportion_reference": reference,
    }
    return normalized, anchor_form


def default_primary_roles(
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


def normalize_references(
    image: dict[str, Any],
    assignment_path: Path,
    catalog: dict[str, Any],
    anchor_form: str,
    default_roles: list[str],
    label: str,
) -> list[dict[str, Any]]:
    raw = image.get("references")
    if not isinstance(raw, list) or not raw:
        raise RunError(f"{label}.references must be a non-empty list")

    profile = catalog["forms"][anchor_form]
    primary = str((SKILL_ROOT / profile["primary"]).resolve())
    has_primary = any(
        isinstance(item, dict)
        and str((assignment_path.parent / str(item.get("path", ""))).resolve()) == primary
        for item in raw
    )
    if not has_primary:
        raise RunError(f"{label}.references requires an explicit canonical {anchor_form} identity anchor")

    all_catalog_paths = {
        str((SKILL_ROOT / entry["path"]).resolve()): (form, entry)
        for form, form_profile in catalog["forms"].items()
        for entry in form_profile["references"]
    }
    normalized: list[dict[str, Any]] = []
    ids: set[str] = set()
    paths: set[str] = set()
    for index, item in enumerate(raw, start=1):
        ref_label = f"{label}.references[{index - 1}]"
        if not isinstance(item, dict):
            raise RunError(f"{ref_label} must be an object")
        require_fields(item, {"id", "path", "roles", "instruction"}, ref_label)
        require_only_fields(
            item,
            {
                "id", "path", "roles", "instruction", "source", "sha256", "format",
                "width", "height", "colorspace",
            },
            ref_label,
        )
        ref_id = require_string(item.get("id"), f"{ref_label}.id")
        if not re.fullmatch(r"[a-z0-9]+(?:[-_][a-z0-9]+)*", ref_id):
            raise RunError(f"{ref_label}.id must use lowercase letters, digits, hyphens, or underscores")
        if ref_id in ids:
            raise RunError(f"Duplicate reference id: {ref_id}")
        ids.add(ref_id)
        ref_path = Path(require_string(item.get("path"), f"{ref_label}.path"))
        if not ref_path.is_absolute():
            ref_path = (assignment_path.parent / ref_path).resolve()
        else:
            ref_path = ref_path.resolve()
        if not ref_path.is_file():
            raise RunError(f"Reference image does not exist: {ref_path}")
        resolved = str(ref_path)
        if resolved in paths:
            raise RunError(f"Duplicate reference path: {ref_path}")
        paths.add(resolved)
        roles = require_string_list(item.get("roles"), f"{ref_label}.roles")
        if len(set(roles)) != len(roles) or not set(roles) <= REFERENCE_ROLES:
            raise RunError(f"{ref_label}.roles contains an invalid or duplicate role")
        catalog_entry = all_catalog_paths.get(resolved)
        if catalog_entry:
            form, entry = catalog_entry
            if form != anchor_form:
                raise RunError(f"{ref_label} bundled reference must use the {anchor_form} anchor form")
            if sha256(ref_path) != entry["sha256"]:
                raise RunError(f"Reference image SHA-256 mismatch: {ref_path}")
            metadata = identify_reference(ref_path)
            source = "bundled"
        else:
            metadata = identify_reference(ref_path)
            source = "external"
        supplied_sha256 = item.get("sha256")
        actual_sha256 = sha256(ref_path)
        if supplied_sha256 is not None and require_sha256(
            supplied_sha256, f"{ref_label}.sha256"
        ) != actual_sha256:
            raise RunError(f"Reference image SHA-256 mismatch: {ref_path}")
        instruction = item.get("instruction")
        if instruction is not None:
            instruction = require_string(instruction, f"{ref_label}.instruction")
        normalized.append({
            "id": ref_id,
            "path": resolved,
            "roles": roles,
            "instruction": instruction,
            "source": source,
            "sha256": actual_sha256,
            **metadata,
        })

    primary_refs = [item for item in normalized if item["path"] == primary]
    if len(primary_refs) != 1 or "identity" not in primary_refs[0]["roles"]:
        raise RunError(f"{label}.references requires one canonical {anchor_form} identity anchor")
    forbidden_primary_roles = set()
    if "style" not in default_roles:
        forbidden_primary_roles.add("style")
    if "costume" not in default_roles:
        forbidden_primary_roles.add("costume")
    if "proportion" not in default_roles:
        forbidden_primary_roles.add("proportion")
    if forbidden_primary_roles & set(primary_refs[0]["roles"]):
        raise RunError(
            f"{label} canonical identity anchor cannot control overridden roles: "
            f"{', '.join(sorted(forbidden_primary_roles & set(primary_refs[0]['roles'])))}"
        )
    for role in REFERENCE_ROLES:
        owners = [item for item in normalized if role in item["roles"]]
        if len(owners) > 1 and any(not item.get("instruction") for item in owners):
            raise RunError(
                f"{label}.references with shared role {role} require conflict-resolution instructions"
            )
    return normalized


def normalize_execution(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RunError("execution must be an object")
    require_fields(
        value,
        {"mode", "requested_parallelism", "max_parallelism", "commit_strategy"},
        "execution",
    )
    require_only_fields(
        value,
        {"mode", "requested_parallelism", "max_parallelism", "commit_strategy"},
        "execution",
    )
    requested = value.get("requested_parallelism")
    if not isinstance(requested, int) or isinstance(requested, bool) or not 1 <= requested <= MAX_PARALLELISM:
        raise RunError(f"execution.requested_parallelism must be between 1 and {MAX_PARALLELISM}")
    if value.get("max_parallelism") != MAX_PARALLELISM:
        raise RunError(f"execution.max_parallelism must be {MAX_PARALLELISM}")
    mode = value.get("mode")
    if mode not in EXECUTION_MODES:
        raise RunError(f"execution.mode must be one of: {', '.join(sorted(EXECUTION_MODES))}")
    if mode == "sequential" and requested != 1:
        raise RunError("sequential execution requires requested_parallelism=1")
    if mode == "parallel" and requested == 1:
        raise RunError("parallel execution requires requested_parallelism greater than 1")
    strategy = value.get("commit_strategy")
    if strategy != "coordinator-serial":
        raise RunError("execution.commit_strategy must be coordinator-serial")
    return {
        "mode": mode,
        "requested_parallelism": requested,
        "max_parallelism": MAX_PARALLELISM,
        "commit_strategy": strategy,
    }


def require_point(value: Any, label: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) != 2:
        raise RunError(f"{label} must be a two-number [x, y] point")
    if any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value):
        raise RunError(f"{label} must be a two-number [x, y] point")
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
        raise RunError("form_evidence.body_segments must contain the three required segments")
    found: dict[str, float] = {}
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise RunError(f"form_evidence.body_segments[{index}] must be an object")
        name = segment.get("name")
        if name not in BODY_SEGMENT_NAMES or name in found:
            raise RunError("form_evidence.body_segments has an invalid or duplicate name")
        start = require_point(segment.get("start"), f"form_evidence.body_segments[{index}].start")
        end = require_point(segment.get("end"), f"form_evidence.body_segments[{index}].end")
        length = point_distance(start, end)
        if length <= 0:
            raise RunError(f"form_evidence.body_segments[{index}] must have positive length")
        found[name] = length
    if set(found) != set(BODY_SEGMENT_NAMES):
        raise RunError("form_evidence.body_segments must contain each required segment once")
    return (head_height + sum(found.values())) / head_height


def validate_visual_qa(
    visual: dict[str, Any],
    image_spec: dict[str, Any],
    expected_candidate_sha256: str | None = None,
    overlay_root: Path | None = None,
    counterpart_ratio: float | None = None,
    compact_pair: bool = False,
) -> None:
    verdict = visual.get("verdict")
    if verdict not in {"PASS", "FAIL"}:
        raise RunError("visual QA verdict must be PASS or FAIL")

    gates = visual.get("gates")
    if not isinstance(gates, dict):
        raise RunError("visual QA gates must be an object")
    missing = sorted(REQUIRED_VISUAL_GATES - gates.keys())
    if missing:
        raise RunError(f"visual QA is missing gates: {', '.join(missing)}")
    unexpected = sorted(gates.keys() - REQUIRED_VISUAL_GATES)
    if unexpected:
        raise RunError(f"visual QA has unexpected gates: {', '.join(unexpected)}")
    invalid = sorted(key for key in REQUIRED_VISUAL_GATES if gates.get(key) not in {"PASS", "FAIL"})
    if invalid:
        raise RunError(f"visual QA gates must be PASS or FAIL: {', '.join(invalid)}")
    all_pass = all(gates[key] == "PASS" for key in REQUIRED_VISUAL_GATES)
    if verdict == "PASS" and not all_pass:
        raise RunError("visual QA verdict PASS requires every gate to PASS")
    if verdict == "FAIL" and all_pass:
        raise RunError("visual QA verdict FAIL requires at least one failed gate")

    candidate_sha256 = require_sha256(visual.get("candidate_sha256"), "visual QA candidate_sha256")
    if expected_candidate_sha256 and candidate_sha256 != expected_candidate_sha256:
        raise RunError("visual QA candidate_sha256 does not match the candidate")

    evidence = visual.get("form_evidence")
    if not isinstance(evidence, dict):
        raise RunError("visual QA requires form_evidence")
    ratio = calculated_head_ratio(evidence)
    validate_measurement_target(evidence, image_spec)
    reported_ratio = evidence.get("calculated_head_ratio")
    if isinstance(reported_ratio, bool) or not isinstance(reported_ratio, (int, float)):
        raise RunError("form_evidence.calculated_head_ratio must be a number")
    if not math.isclose(float(reported_ratio), ratio, abs_tol=0.01):
        raise RunError("form_evidence.calculated_head_ratio does not match the landmarks")
    overlay_path = Path(require_string(evidence.get("measurement_overlay"), "form_evidence.measurement_overlay"))
    overlay_sha256 = require_sha256(
        evidence.get("measurement_overlay_sha256"),
        "form_evidence.measurement_overlay_sha256",
    )
    if overlay_sha256 == candidate_sha256:
        raise RunError("measurement overlay must differ from the unmodified candidate")
    if overlay_root is not None:
        resolved_overlay = overlay_path if overlay_path.is_absolute() else overlay_root / overlay_path
        if not resolved_overlay.is_file():
            raise RunError(f"Missing measurement overlay: {resolved_overlay}")
        if sha256(resolved_overlay) != overlay_sha256:
            raise RunError("measurement overlay SHA-256 does not match")
    for field in sorted(FORM_EVIDENCE_TEXT_FIELDS):
        require_string(evidence.get(field), f"form_evidence.{field}")
    if not isinstance(evidence.get("pose_retargeted"), bool):
        raise RunError("form_evidence.pose_retargeted must be boolean")
    if verdict == "PASS":
        minimum, maximum = image_spec["proportion"]["acceptance_range"]
        if ratio < minimum - 1e-9 or ratio > maximum + 1e-9:
            raise RunError(
                f"target head ratio must be between {minimum:g} and {maximum:g}"
            )
        if evidence["pose_retargeted"] is not True:
            raise RunError("PASS requires form_evidence.pose_retargeted=true")

    counterpart = image_spec.get("counterpart")
    pairwise = visual.get("pairwise_evidence")
    is_more_compact = bool(counterpart and compact_pair)
    if is_more_compact and verdict == "PASS":
        if not isinstance(pairwise, dict):
            raise RunError("paired compact-form PASS requires pairwise_evidence")
    if pairwise is not None:
        if not counterpart:
            raise RunError("pairwise_evidence requires a frozen counterpart")
        if not isinstance(pairwise, dict):
            raise RunError("pairwise_evidence must be an object")
        if pairwise.get("counterpart") != counterpart:
            raise RunError("pairwise_evidence.counterpart must match the frozen assignment")
        for field in sorted(PAIRWISE_BOOLEAN_FIELDS):
            if not isinstance(pairwise.get(field), bool):
                raise RunError(f"pairwise_evidence.{field} must be boolean")
        if verdict == "PASS" and not all(pairwise[field] for field in PAIRWISE_BOOLEAN_FIELDS):
            raise RunError("paired PASS requires every pairwise comparison to be true")
        for field in ("expanded_form_head_ratio", "compact_form_head_ratio"):
            value = pairwise.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise RunError(f"pairwise_evidence.{field} must be a number")
        if is_more_compact and not math.isclose(
            float(pairwise["compact_form_head_ratio"]), ratio, abs_tol=0.01
        ):
            raise RunError("pairwise_evidence.compact_form_head_ratio must match form evidence")
        expanded_ratio = float(pairwise["expanded_form_head_ratio"])
        if counterpart_ratio is not None and not math.isclose(
            expanded_ratio, counterpart_ratio, abs_tol=0.01
        ):
            raise RunError("pairwise_evidence.expanded_form_head_ratio must match the counterpart")
        if "pairwise_minimum_head_ratio_gap" not in image_spec:
            raise RunError("paired QA requires frozen pairwise_minimum_head_ratio_gap")
        minimum_gap = image_spec["pairwise_minimum_head_ratio_gap"]
        minimum_gap = float(minimum_gap)
        if verdict == "PASS" and expanded_ratio - float(pairwise["compact_form_head_ratio"]) < minimum_gap:
            raise RunError(f"paired PASS requires a head-ratio gap of at least {minimum_gap:g}")

    defects = visual.get("defects")
    if not isinstance(defects, list) or any(not isinstance(item, str) for item in defects):
        raise RunError("visual QA defects must be a list of strings")
    if verdict == "FAIL":
        if not any(item.strip() for item in defects):
            raise RunError("visual QA FAIL requires at least one defect")
        require_string(visual.get("targeted_retry"), "visual QA targeted_retry")
    else:
        if defects:
            raise RunError("visual QA PASS requires an empty defects list")
        if visual.get("targeted_retry") is not None:
            raise RunError("visual QA PASS requires targeted_retry=null")


def inspect_automatic_candidate(
    candidate: Path,
    output: dict[str, Any],
    alpha_policy: str,
) -> dict[str, Any]:
    resolution = output["resolution"]
    arguments = [
        sys.executable,
        str(SKILL_ROOT / "scripts" / "validate-image.py"),
        str(candidate),
        "--aspect-ratio",
        output["aspect_ratio"],
        "--resolution-mode",
        resolution["mode"],
        "--alpha",
        alpha_policy,
    ]
    if resolution["mode"] == "exact":
        arguments.extend([
            "--width",
            str(resolution["width"]),
            "--height",
            str(resolution["height"]),
        ])
    completed = subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        inspected = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RunError(f"Cannot re-inspect automatic QA candidate: {completed.stderr.strip()}") from exc
    if completed.returncode not in {0, 1}:
        raise RunError(f"Cannot re-inspect automatic QA candidate: {completed.stderr.strip()}")
    return inspected


def validate_automatic_qa(
    automatic: dict[str, Any],
    image_spec: dict[str, Any],
    candidate: Path,
    candidate_sha256: str,
    *,
    require_matching_path: bool = True,
) -> None:
    output = image_spec["output"]
    resolution = output["resolution"]
    expected_alpha = "required" if output["alpha"] else "forbidden"
    if automatic.get("schema_version") != AUTOMATIC_QA_SCHEMA_VERSION:
        raise RunError(
            f"automatic QA schema_version must be {AUTOMATIC_QA_SCHEMA_VERSION}"
        )
    gates = automatic.get("gates")
    if not isinstance(gates, dict) or set(gates) != {"T1", "T2"}:
        raise RunError("automatic QA gates must contain exactly T1 and T2")
    verdicts = []
    for gate in ("T1", "T2"):
        value = gates[gate]
        if not isinstance(value, dict) or value.get("verdict") not in {"PASS", "FAIL"}:
            raise RunError(f"automatic QA {gate}.verdict must be PASS or FAIL")
        verdicts.append(value["verdict"])
    expected_overall = "PASS" if all(value == "PASS" for value in verdicts) else "FAIL"
    if automatic.get("overall") != expected_overall:
        raise RunError("automatic QA overall does not match its gates")
    if require_sha256(automatic.get("sha256"), "automatic QA sha256") != candidate_sha256:
        raise RunError("automatic QA sha256 does not match the candidate")
    if require_matching_path:
        reported_path = Path(require_string(automatic.get("path"), "automatic QA path")).resolve()
        if reported_path != candidate.resolve():
            raise RunError("automatic QA path does not match the candidate")

    metrics = automatic.get("metrics")
    if not isinstance(metrics, dict):
        raise RunError("automatic QA metrics must be an object")
    if metrics.get("alpha_policy") != expected_alpha:
        raise RunError(f"automatic QA alpha_policy must be {expected_alpha}")
    if metrics.get("resolution_mode") != resolution["mode"]:
        raise RunError(
            f"automatic QA resolution_mode must be {resolution['mode']}"
        )
    if metrics.get("expected_aspect_ratio") != output["aspect_ratio"]:
        raise RunError(
            f"automatic QA expected_aspect_ratio must be {output['aspect_ratio']}"
        )
    if metrics.get("expected_width") != resolution["width"]:
        raise RunError("automatic QA expected_width does not match the assignment")
    if metrics.get("expected_height") != resolution["height"]:
        raise RunError("automatic QA expected_height does not match the assignment")
    if str(metrics.get("format", "")).upper() != "PNG":
        raise RunError("automatic QA format must be PNG")
    width = metrics.get("width")
    height = metrics.get("height")
    if (
        isinstance(width, bool)
        or not isinstance(width, int)
        or width < 1
        or isinstance(height, bool)
        or not isinstance(height, int)
        or height < 1
    ):
        raise RunError("automatic QA width and height must be positive integers")
    if resolution["mode"] == "exact" and (
        width != resolution["width"] or height != resolution["height"]
    ):
        raise RunError("automatic QA dimensions do not match the frozen exact resolution")
    inspected = inspect_automatic_candidate(candidate, output, expected_alpha)
    for field in ("schema_version", "sha256", "overall", "gates", "metrics"):
        if automatic.get(field) != inspected.get(field):
            raise RunError(f"automatic QA {field} does not match fresh candidate inspection")


def actual_output_from_automatic(
    automatic: dict[str, Any],
    alpha: bool,
) -> dict[str, Any]:
    metrics = automatic["metrics"]
    width = int(metrics["width"])
    height = int(metrics["height"])
    divisor = math.gcd(width, height)
    return {
        "format": "png",
        "alpha": alpha,
        "width": width,
        "height": height,
        "aspect_ratio": f"{width // divisor}:{height // divisor}",
    }


def provider_output_request(
    output: dict[str, Any],
    provider_size: str | None,
) -> dict[str, Any]:
    resolution = output["resolution"]
    if resolution["mode"] == "exact":
        exact_size = f"{resolution['width']}x{resolution['height']}"
        if provider_size is None:
            provider_size = exact_size
        elif provider_size != exact_size:
            raise RunError("provider size must match the frozen exact resolution")
    elif provider_size is not None:
        provider_size = require_string(provider_size, "provider size")
        size_match = re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", provider_size)
        if size_match is not None:
            width, height = (int(item) for item in size_match.groups())
            ratio_width, ratio_height = (
                int(item) for item in output["aspect_ratio"].split(":", 1)
            )
            if not math.isclose(
                width / height,
                ratio_width / ratio_height,
                rel_tol=0.02,
            ):
                raise RunError("provider size does not match the frozen aspect ratio")
    return {
        "aspect_ratio": output["aspect_ratio"],
        "resolution_mode": resolution["mode"],
        "size": provider_size,
    }


def validate_assignment(path: Path) -> dict[str, Any]:
    assignment = read_json(path)
    catalog, catalog_sha256 = load_catalog()
    if assignment.get("schema_version") != ASSIGNMENT_SCHEMA_VERSION:
        raise RunError(f"assignment schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
    require_fields(
        assignment,
        {"confirmation", "input", "run_name", "image_count", "images", "execution", "budget"},
        "assignment",
    )
    require_only_fields(
        assignment,
        {"schema_version", "confirmation", "input", "run_name", "image_count", "images", "execution", "budget"},
        "assignment",
    )

    confirmation = assignment.get("confirmation")
    if not isinstance(confirmation, dict) or confirmation.get("confirmed") is not True:
        raise RunError("assignment requires confirmation.confirmed=true")
    require_iso8601(confirmation.get("confirmed_at"), "confirmation.confirmed_at")

    source = assignment.get("input")
    if not isinstance(source, dict) or source.get("type") not in INPUT_TYPES:
        raise RunError(f"input.type must be one of: {', '.join(sorted(INPUT_TYPES))}")
    content = source.get("content")
    if not isinstance(content, (str, list)) or not content:
        raise RunError("input.content must be a non-empty string or list")

    run_name = require_string(assignment.get("run_name"), "run_name")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", run_name):
        raise RunError("run_name must be lowercase kebab-case")

    images = assignment.get("images")
    if not isinstance(images, list) or not images:
        raise RunError("images must be a non-empty list")
    image_count = assignment.get("image_count")
    if (
        isinstance(image_count, bool)
        or not isinstance(image_count, int)
        or image_count < 1
        or image_count != len(images)
    ):
        raise RunError("image_count must equal the number of images")

    names: set[str] = set()
    image_by_name: dict[str, dict[str, Any]] = {}
    for index, image in enumerate(images, start=1):
        label = f"images[{index - 1}]"
        if not isinstance(image, dict):
            raise RunError(f"{label} must be an object")
        require_fields(
            image,
            {
                "name", "subject", "expression", "action", "composition", "props", "objects",
                "style", "costume", "background", "text", "proportion", "references", "output",
                "counterpart",
            },
            label,
        )
        require_only_fields(
            image,
            {
                "name", "subject", "expression", "action", "composition", "props", "objects",
                "style", "costume", "background", "text", "proportion", "references", "output",
                "counterpart", "pairwise_minimum_head_ratio_gap",
            },
            label,
        )
        name = require_string(image.get("name"), f"{label}.name")
        if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", name):
            raise RunError(f"{label}.name must be lowercase snake_case")
        if name in names:
            raise RunError(f"Duplicate image name: {name}")
        names.add(name)
        image_by_name[name] = image
        for field in ("expression", "action", "composition"):
            image[field] = require_string(image.get(field), f"{label}.{field}")
        image["subject"] = require_string(image.get("subject"), f"{label}.subject")
        for field in ("props", "objects"):
            if not isinstance(image.get(field), list):
                raise RunError(f"{label}.{field} must be a list")

        style = normalize_named_mode(
            image.get("style"), STYLE_MODES, DEFAULT_STYLE, f"{label}.style",
        )
        costume = normalize_named_mode(
            image.get("costume"),
            COSTUME_MODES,
            DEFAULT_COSTUME,
            f"{label}.costume",
        )
        background = normalize_background(image.get("background"), f"{label}.background")
        text_spec = normalize_text(image.get("text"), f"{label}.text")
        proportion, anchor_form = normalize_proportion(image, catalog, label)

        output = normalize_output(image["output"], background, f"{label}.output")

        roles = default_primary_roles(style, costume, proportion)
        references = normalize_references(
            image, path, catalog, anchor_form, roles, label
        )

        image["style"] = style
        image["costume"] = costume
        image["background"] = background
        image["text"] = text_spec
        image["proportion"] = proportion
        image["proportion_sha256"] = target_sha256(
            proportion["mode"],
            proportion["preset"],
            proportion["target_head_ratio"],
            proportion["acceptance_range"],
        )
        image["identity_anchor_form"] = anchor_form
        image["references"] = references
        image["output"] = output
        image["id"] = f"{index:02d}_{name}"

    for name, image in image_by_name.items():
        counterpart = image.get("counterpart")
        if counterpart is None:
            continue
        counterpart = require_string(counterpart, f"{name}.counterpart")
        other = image_by_name.get(counterpart)
        if other is None:
            raise RunError(f"Unknown counterpart for {name}: {counterpart}")
        image_ratio = float(image["proportion"]["target_head_ratio"])
        other_ratio = float(other["proportion"]["target_head_ratio"])
        if other is image or math.isclose(other_ratio, image_ratio, abs_tol=1e-9):
            raise RunError(f"Counterpart for {name} must use a different target head ratio")
        if other.get("counterpart") != name:
            raise RunError(f"Counterpart link must be mutual: {name} <-> {counterpart}")
        image["counterpart"] = counterpart
        configured_gap = image.get("pairwise_minimum_head_ratio_gap")
        if configured_gap is None:
            both_presets = image["proportion"]["mode"] == other["proportion"]["mode"] == "preset"
            if not both_presets:
                raise RunError(
                    f"{name}.pairwise_minimum_head_ratio_gap must be explicit for custom pairs"
                )
            configured_gap = catalog["pairwise_minimum_head_ratio_gap"]
        if (
            isinstance(configured_gap, bool)
            or not isinstance(configured_gap, (int, float))
            or configured_gap < 0
            or configured_gap == 0
        ):
            raise RunError(f"{name}.pairwise_minimum_head_ratio_gap must be positive")
        image["pairwise_minimum_head_ratio_gap"] = float(configured_gap)
        other_gap = other.get("pairwise_minimum_head_ratio_gap")
        if other_gap is not None and not math.isclose(float(other_gap), float(configured_gap), abs_tol=1e-9):
            raise RunError(f"Counterpart pair must use one pairwise_minimum_head_ratio_gap: {name}")

    budget = assignment.get("budget")
    if not isinstance(budget, dict):
        raise RunError("budget must be an object")
    require_fields(
        budget,
        {"per_image_candidates", "per_provider_candidates", "run_candidates", "confirmed_over_24"},
        "budget",
    )
    require_only_fields(
        budget,
        {"per_image_candidates", "per_provider_candidates", "run_candidates", "confirmed_over_24"},
        "budget",
    )
    per_image = budget.get("per_image_candidates")
    per_provider = budget.get("per_provider_candidates")
    run_candidates = budget.get("run_candidates")
    for value, label in (
        (per_image, "per_image_candidates"),
        (per_provider, "per_provider_candidates"),
        (run_candidates, "run_candidates"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise RunError(f"budget.{label} must be a positive integer")
    if per_image > MAX_IMAGE_CANDIDATES:
        raise RunError(f"budget.per_image_candidates cannot exceed {MAX_IMAGE_CANDIDATES}")
    if per_provider > per_image:
        raise RunError("budget.per_provider_candidates cannot exceed per-image budget")
    expected = image_count * per_image
    confirmed_over_24 = budget.get("confirmed_over_24")
    if not isinstance(confirmed_over_24, bool):
        raise RunError("budget.confirmed_over_24 must be boolean")
    if run_candidates < expected:
        raise RunError(f"Run budget must be at least the estimated maximum {expected}")
    if expected > NORMAL_RUN_CANDIDATES:
        if confirmed_over_24 is not True:
            raise RunError(
                f"Estimated maximum is {expected}; set budget.confirmed_over_24=true after confirmation"
            )
    elif run_candidates > NORMAL_RUN_CANDIDATES and confirmed_over_24 is not True:
        raise RunError("A run budget above 24 requires budget.confirmed_over_24=true")
    budget.update(
        {
            "per_image_candidates": per_image,
            "per_provider_candidates": per_provider,
            "run_candidates": run_candidates,
            "estimated_maximum": expected,
            "confirmed_over_24": confirmed_over_24,
        }
    )
    assignment["budget"] = budget
    assignment["execution"] = normalize_execution(assignment.get("execution"))
    assignment["reference_catalog"] = {
        "schema_version": catalog["schema_version"],
        "sha256": catalog_sha256,
    }
    assignment["image_count"] = image_count
    return assignment


def unique_run_dir(root: Path, run_name: str) -> Path:
    candidate = root / run_name
    suffix = 2
    while candidate.exists():
        candidate = root / f"{run_name}-{suffix:02d}"
        suffix += 1
    return candidate


def validate_frozen_assignment_structure(assignment: dict[str, Any]) -> None:
    root_fields = {
        "schema_version", "confirmation", "input", "run_name", "image_count", "images",
        "execution", "budget", "reference_catalog", "source_assignment", "run_dir", "frozen_at",
    }
    require_fields(assignment, root_fields, "frozen assignment")
    require_only_fields(assignment, root_fields, "frozen assignment")
    if assignment["schema_version"] != ASSIGNMENT_SCHEMA_VERSION:
        raise RunError(f"Frozen assignment schema_version must be {ASSIGNMENT_SCHEMA_VERSION}")
    images = assignment["images"]
    if not isinstance(images, list) or not images or assignment["image_count"] != len(images):
        raise RunError("Frozen assignment image_count must equal a non-empty images list")
    require_iso8601(assignment["frozen_at"], "frozen assignment frozen_at")

    execution_fields = {"mode", "requested_parallelism", "max_parallelism", "commit_strategy"}
    execution = assignment["execution"]
    if not isinstance(execution, dict):
        raise RunError("Frozen assignment execution must be an object")
    require_fields(execution, execution_fields, "frozen assignment execution")
    require_only_fields(execution, execution_fields, "frozen assignment execution")

    budget_fields = {
        "per_image_candidates", "per_provider_candidates", "run_candidates",
        "confirmed_over_24", "estimated_maximum",
    }
    budget = assignment["budget"]
    if not isinstance(budget, dict):
        raise RunError("Frozen assignment budget must be an object")
    require_fields(budget, budget_fields, "frozen assignment budget")
    require_only_fields(budget, budget_fields, "frozen assignment budget")

    image_fields = {
        "name", "subject", "expression", "action", "composition", "props", "objects",
        "style", "costume", "background", "text", "proportion", "references", "output",
        "counterpart", "proportion_sha256", "identity_anchor_form", "id",
    }
    reference_fields = {
        "id", "path", "roles", "instruction", "source", "sha256", "format",
        "width", "height", "colorspace",
    }
    output_fields = {"format", "alpha", "aspect_ratio", "resolution"}
    resolution_fields = {"mode", "width", "height"}
    proportion_fields = {
        "mode", "preset", "target_head_ratio", "acceptance_range", "proportion_reference",
    }
    ids: set[str] = set()
    for index, image in enumerate(images):
        label = f"frozen assignment images[{index}]"
        if not isinstance(image, dict):
            raise RunError(f"{label} must be an object")
        allowed_image_fields = image_fields | {"pairwise_minimum_head_ratio_gap"}
        require_fields(image, image_fields, label)
        require_only_fields(image, allowed_image_fields, label)
        if image["counterpart"] is not None and "pairwise_minimum_head_ratio_gap" not in image:
            raise RunError(f"{label} requires pairwise_minimum_head_ratio_gap")
        image_id = require_string(image["id"], f"{label}.id")
        if image_id in ids:
            raise RunError(f"Duplicate frozen image id: {image_id}")
        ids.add(image_id)
        for field, fields in (("output", output_fields), ("proportion", proportion_fields)):
            value = image[field]
            if not isinstance(value, dict):
                raise RunError(f"{label}.{field} must be an object")
            require_fields(value, fields, f"{label}.{field}")
            require_only_fields(value, fields, f"{label}.{field}")
        resolution = image["output"]["resolution"]
        if not isinstance(resolution, dict):
            raise RunError(f"{label}.output.resolution must be an object")
        require_fields(resolution, resolution_fields, f"{label}.output.resolution")
        require_only_fields(resolution, resolution_fields, f"{label}.output.resolution")
        references = image["references"]
        if not isinstance(references, list) or not references:
            raise RunError(f"{label}.references must be a non-empty list")
        for ref_index, reference in enumerate(references):
            ref_label = f"{label}.references[{ref_index}]"
            if not isinstance(reference, dict):
                raise RunError(f"{ref_label} must be an object")
            require_fields(reference, reference_fields, ref_label)
            require_only_fields(reference, reference_fields, ref_label)


def validate_manifest_structure(
    manifest: dict[str, Any], assignment: dict[str, Any]
) -> None:
    root_fields = {
        "schema_version", "status", "assignment_sha256", "reference_catalog",
        "provider_order", "candidate_count", "budget", "execution", "created_at",
        "updated_at", "images",
    }
    allowed_root_fields = root_fields | {"safety_halt", "finalized_at"}
    require_fields(manifest, root_fields, "manifest")
    require_only_fields(manifest, allowed_root_fields, "manifest")
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise RunError(f"manifest schema_version must be {MANIFEST_SCHEMA_VERSION}")
    if manifest["status"] not in {
        "in_progress", "safety_blocked", "complete", "complete_with_failures",
    }:
        raise RunError("manifest status is invalid")
    require_sha256(manifest["assignment_sha256"], "manifest.assignment_sha256")
    require_iso8601(manifest["created_at"], "manifest.created_at")
    require_iso8601(manifest["updated_at"], "manifest.updated_at")
    if "finalized_at" in manifest:
        require_iso8601(manifest["finalized_at"], "manifest.finalized_at")
    if manifest["provider_order"] != PROVIDERS:
        raise RunError("manifest provider_order does not match the current provider order")
    candidate_count = manifest["candidate_count"]
    if isinstance(candidate_count, bool) or not isinstance(candidate_count, int) or candidate_count < 0:
        raise RunError("manifest candidate_count must be a non-negative integer")
    if manifest["budget"] != assignment["budget"]:
        raise RunError("manifest budget does not match the frozen assignment")

    execution_fields = {
        "mode", "requested_parallelism", "max_parallelism", "commit_strategy",
        "effective_parallelism", "initial_ready_image_count",
    }
    execution = manifest["execution"]
    if not isinstance(execution, dict):
        raise RunError("manifest execution must be an object")
    require_fields(execution, execution_fields, "manifest execution")
    require_only_fields(execution, execution_fields, "manifest execution")
    for field in ("mode", "requested_parallelism", "max_parallelism", "commit_strategy"):
        if execution[field] != assignment["execution"][field]:
            raise RunError(f"manifest execution.{field} does not match the frozen assignment")

    images = manifest["images"]
    expected_ids = {image["id"] for image in assignment["images"]}
    image_specs = {image["id"]: image for image in assignment["images"]}
    if not isinstance(images, dict) or set(images) != expected_ids:
        raise RunError("manifest images must exactly match the frozen assignment image ids")
    state_fields = {
        "status", "attempts", "provider_errors", "final_path", "final_sha256",
        "final_measured_head_ratio", "final_output",
    }
    attempt_fields = {
        "candidate_attempt", "provider", "model", "created_at", "assignment_sha256",
        "prompt", "prompt_sha256", "references", "candidate_path", "candidate_sha256",
        "proportion", "identity_anchor_form", "measured_head_ratio", "automatic_qa",
        "requested_output", "provider_output_request", "actual_output", "visual_qa",
        "verdict", "consumes_candidate_budget",
    }
    error_fields = {
        "error_id", "provider", "model", "category", "details", "created_at",
        "consumes_candidate_budget",
    }
    for image_id, state in images.items():
        label = f"manifest images.{image_id}"
        if not isinstance(state, dict):
            raise RunError(f"{label} must be an object")
        require_fields(state, state_fields, label)
        require_only_fields(state, state_fields, label)
        if state["status"] not in {"pending", "generating", "candidate_pass", "passed", "safety_blocked"}:
            raise RunError(f"{label}.status is invalid")
        final_output = state["final_output"]
        if final_output is not None and not isinstance(final_output, dict):
            raise RunError(f"{label}.final_output must be null or an object")
        if isinstance(final_output, dict) and set(final_output) != {
            "format", "alpha", "width", "height", "aspect_ratio"
        }:
            raise RunError(f"{label}.final_output is invalid")
        for field, fields in (("attempts", attempt_fields), ("provider_errors", error_fields)):
            records = state[field]
            if not isinstance(records, list):
                raise RunError(f"{label}.{field} must be a list")
            for index, record in enumerate(records):
                record_label = f"{label}.{field}[{index}]"
                if not isinstance(record, dict):
                    raise RunError(f"{record_label} must be an object")
                require_fields(record, fields, record_label)
                require_only_fields(record, fields, record_label)
                if field == "attempts":
                    if record["requested_output"] != image_specs[image_id]["output"]:
                        raise RunError(
                            f"{record_label}.requested_output does not match the assignment"
                        )
                    provider_request = record["provider_output_request"]
                    if not isinstance(provider_request, dict) or set(provider_request) != {
                        "aspect_ratio", "resolution_mode", "size"
                    }:
                        raise RunError(
                            f"{record_label}.provider_output_request is invalid"
                        )
                    actual_output = record["actual_output"]
                    if not isinstance(actual_output, dict) or set(actual_output) != {
                        "format", "alpha", "width", "height", "aspect_ratio"
                    }:
                        raise RunError(f"{record_label}.actual_output is invalid")


def load_run(value: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    run_dir = Path(value).resolve()
    assignment_path = run_dir / "assignment.json"
    assignment = read_json(assignment_path)
    manifest = read_json(run_dir / "manifest.json")
    validate_frozen_assignment_structure(assignment)
    validate_manifest_structure(manifest, assignment)
    if manifest["assignment_sha256"] != sha256(assignment_path):
        raise RunError("Frozen assignment SHA-256 mismatch")
    _catalog, catalog_sha256 = load_catalog()
    expected = {"schema_version": CATALOG_SCHEMA_VERSION, "sha256": catalog_sha256}
    if assignment["reference_catalog"] != expected:
        raise RunError("Run reference catalog no longer matches the current skill catalog")
    if manifest["reference_catalog"] != expected:
        raise RunError("Manifest reference catalog does not match the frozen assignment")
    for image in assignment["images"]:
        for reference in image["references"]:
            reference_path = Path(reference["path"])
            if not reference_path.is_file() or sha256(reference_path) != reference.get("sha256"):
                raise RunError(f"Frozen reference SHA-256 mismatch: {reference_path}")
    return run_dir, assignment, manifest


def image_state(manifest: dict[str, Any], image_id: str) -> dict[str, Any]:
    images = manifest["images"]
    if not isinstance(images, dict) or image_id not in images:
        raise RunError(f"Unknown image id: {image_id}")
    state = images[image_id]
    if not isinstance(state, dict):
        raise RunError(f"Invalid image state: {image_id}")
    return state


def paired_expanded_ratio(
    assignment: dict[str, Any], manifest: dict[str, Any], image_spec: dict[str, Any]
) -> float | None:
    counterpart_name = image_spec.get("counterpart")
    if not counterpart_name:
        return None
    counterpart = next(
        (item for item in assignment["images"] if item["name"] == counterpart_name), None
    )
    image_ratio = float(image_spec["proportion"]["target_head_ratio"])
    if counterpart is None:
        raise RunError("Paired image is missing its frozen counterpart")
    counterpart_ratio = float(counterpart["proportion"]["target_head_ratio"])
    if image_ratio >= counterpart_ratio:
        return None
    state = image_state(manifest, counterpart["id"])
    passed = [item for item in state["attempts"] if item["verdict"] == "PASS"]
    if not passed:
        raise RunError("Paired compact-form PASS requires the measured expanded counterpart first")
    ratio = passed[-1].get("measured_head_ratio")
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
        raise RunError("Expanded counterpart is missing measured_head_ratio")
    return float(ratio)


def is_compact_pair(assignment: dict[str, Any], image_spec: dict[str, Any]) -> bool:
    counterpart_name = image_spec.get("counterpart")
    if not counterpart_name:
        return False
    counterpart = next(
        (item for item in assignment["images"] if item["name"] == counterpart_name), None
    )
    if counterpart is None:
        raise RunError("Paired image is missing its frozen counterpart")
    return float(image_spec["proportion"]["target_head_ratio"]) < float(
        counterpart["proportion"]["target_head_ratio"]
    )


def save_manifest(run_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now()
    write_json(run_dir / "manifest.json", manifest)


def provider_is_exhausted(state: dict[str, Any], provider: str, cap: int) -> bool:
    count = sum(item["provider"] == provider for item in state["attempts"])
    if count >= cap:
        return True
    return any(
        error["provider"] == provider and error["category"] in EXHAUSTING_ERRORS
        for error in state["provider_errors"]
    )


def enforce_provider_order(
    state: dict[str, Any], provider: str, per_provider_candidates: int
) -> None:
    if provider not in PROVIDERS:
        raise RunError(f"Unsupported provider: {provider}")
    used = [item["provider"] for item in state["attempts"]]
    used.extend(item["provider"] for item in state["provider_errors"])
    ranks = [PROVIDERS.index(item) for item in used if item in PROVIDERS]
    rank = PROVIDERS.index(provider)
    if ranks and rank < max(ranks):
        raise RunError("Provider order cannot move backward")
    for earlier in PROVIDERS[:rank]:
        if not provider_is_exhausted(state, earlier, per_provider_candidates):
            raise RunError(f"Earlier provider is not exhausted or unavailable: {earlier}")


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    assignment = validate_assignment(Path(args.assignment).resolve())
    return {
        "valid": True,
        "run_name": assignment["run_name"],
        "image_count": assignment["image_count"],
        "estimated_maximum": assignment["budget"]["estimated_maximum"],
    }


def cmd_init(args: argparse.Namespace) -> dict[str, Any]:
    assignment_path = Path(args.assignment).resolve()
    assignment = validate_assignment(assignment_path)
    requested_parallelism = assignment["execution"]["requested_parallelism"]
    effective_parallelism = args.effective_parallelism
    if effective_parallelism is None:
        effective_parallelism = 1
    image_by_name = {image["name"]: image for image in assignment["images"]}
    ready_image_count = sum(
        1
        for image in assignment["images"]
        if image.get("counterpart") is None
        or image["proportion"]["target_head_ratio"]
        > image_by_name[image["counterpart"]]["proportion"]["target_head_ratio"]
    )
    if not 1 <= effective_parallelism <= min(requested_parallelism, ready_image_count):
        raise RunError(
            "effective parallelism must be between 1 and the current requested/ready-image limit"
        )
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    run_dir = unique_run_dir(root, assignment["run_name"])
    run_dir.mkdir()
    (run_dir / "final").mkdir()
    (run_dir / "staging").mkdir()
    frozen_references = run_dir / "inputs" / "references"
    frozen_references.mkdir(parents=True)

    copied: dict[tuple[str, str], str] = {}
    for image in assignment["images"]:
        for reference in image["references"]:
            if reference["source"] != "external":
                continue
            source = Path(reference["path"])
            key = (reference["sha256"], source.suffix.lower())
            if key not in copied:
                destination = frozen_references / f"{reference['sha256'][:16]}{source.suffix.lower()}"
                if destination.exists():
                    raise RunError(f"Frozen reference already exists: {destination}")
                shutil.copy2(source, destination)
                if sha256(destination) != reference["sha256"]:
                    raise RunError(f"Frozen reference SHA-256 mismatch: {destination}")
                copied[key] = str(destination)
            reference["path"] = copied[key]

    states: dict[str, Any] = {}
    for image in assignment["images"]:
        image_id = image["id"]
        (run_dir / "attempts" / image_id).mkdir(parents=True)
        (run_dir / "staging" / image_id).mkdir(parents=True)
        states[image_id] = {
            "status": "pending",
            "attempts": [],
            "provider_errors": [],
            "final_path": None,
            "final_sha256": None,
            "final_measured_head_ratio": None,
            "final_output": None,
        }
    assignment["source_assignment"] = str(assignment_path)
    assignment["run_dir"] = str(run_dir)
    assignment["frozen_at"] = utc_now()
    frozen_assignment_path = run_dir / "assignment.json"
    write_json(frozen_assignment_path, assignment)
    assignment_sha256 = sha256(frozen_assignment_path)
    created = utc_now()
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "status": "in_progress",
        "assignment_sha256": assignment_sha256,
        "reference_catalog": assignment["reference_catalog"],
        "provider_order": PROVIDERS,
        "candidate_count": 0,
        "budget": assignment["budget"],
        "execution": {
            **assignment["execution"],
            "effective_parallelism": effective_parallelism,
            "initial_ready_image_count": ready_image_count,
        },
        "created_at": created,
        "updated_at": created,
        "images": states,
    }
    write_json(run_dir / "manifest.json", manifest)
    return {
        "run_dir": str(run_dir),
        "images": list(states),
        "budget": assignment["budget"],
        "execution": manifest["execution"],
    }


def cmd_record_error(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    if manifest["status"] != "in_progress":
        raise RunError("Run is not open")
    state = image_state(manifest, args.image)
    if state["status"] not in {"pending", "generating"}:
        raise RunError(f"Image is not open for provider errors: {args.image}")
    per_provider = assignment["budget"]["per_provider_candidates"]
    enforce_provider_order(state, args.provider, per_provider)
    if args.category == "safety_rejection":
        state["status"] = "safety_blocked"
        manifest["status"] = "safety_blocked"
        manifest["safety_halt"] = {
            "image": args.image,
            "provider": args.provider,
            "created_at": utc_now(),
            "uncommitted_results": "quarantine",
        }
    error_number = len(state["provider_errors"]) + 1
    record = {
        "error_id": f"error-{error_number:02d}",
        "provider": args.provider,
        "model": args.model,
        "category": args.category,
        "details": args.details,
        "created_at": utc_now(),
        "consumes_candidate_budget": False,
    }
    state["provider_errors"].append(record)
    error_path = run_dir / "attempts" / args.image / f"error_{error_number:02d}_{args.provider}.json"
    write_json(error_path, record)
    save_manifest(run_dir, manifest)
    return {"recorded": str(error_path), "candidate_count": manifest["candidate_count"]}


def cmd_record_candidate(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    if manifest["status"] != "in_progress":
        raise RunError("Run is not open")
    state = image_state(manifest, args.image)
    if state["status"] in {"candidate_pass", "passed", "safety_blocked"}:
        raise RunError(f"Image is not open for candidates: {args.image}")

    budget = assignment["budget"]
    attempts = state["attempts"]
    if len(attempts) >= budget["per_image_candidates"]:
        raise RunError("Per-image candidate budget is exhausted")
    if manifest["candidate_count"] >= budget["run_candidates"]:
        raise RunError("Run candidate budget is exhausted")
    enforce_provider_order(state, args.provider, budget["per_provider_candidates"])
    provider_count = sum(item["provider"] == args.provider for item in attempts)
    if provider_count >= budget["per_provider_candidates"]:
        raise RunError("Per-provider candidate budget is exhausted")

    candidate = Path(args.candidate).resolve()
    prompt_file = Path(args.prompt_file).resolve()
    automatic_file = Path(args.automatic_json).resolve()
    visual_file = Path(args.visual_json).resolve()
    for path, label in (
        (candidate, "candidate"),
        (prompt_file, "prompt file"),
        (automatic_file, "automatic QA"),
        (visual_file, "visual QA"),
    ):
        if not path.is_file():
            raise RunError(f"Missing {label}: {path}")
    automatic = read_json(automatic_file)
    visual = read_json(visual_file)
    prompt = prompt_file.read_text(encoding="utf-8").strip()
    if not prompt:
        raise RunError("Prompt file is empty")

    image_spec = next(item for item in assignment["images"] if item["id"] == args.image)
    candidate_sha256 = sha256(candidate)
    validate_automatic_qa(
        automatic,
        image_spec,
        candidate,
        candidate_sha256,
    )
    validate_visual_qa(
        visual,
        image_spec,
        expected_candidate_sha256=candidate_sha256,
        overlay_root=visual_file.parent,
        counterpart_ratio=(
            paired_expanded_ratio(assignment, manifest, image_spec)
            if visual.get("verdict") == "PASS"
            else None
        ),
        compact_pair=is_compact_pair(assignment, image_spec),
    )

    attempt_number = len(attempts) + 1
    base = f"{attempt_number:02d}_{args.provider}"
    attempt_dir = run_dir / "attempts" / args.image
    stored_candidate = attempt_dir / f"{base}.png"
    record_path = attempt_dir / f"{base}.json"
    if stored_candidate.exists() or record_path.exists():
        raise RunError(f"Attempt path already exists: {base}")
    shutil.copy2(candidate, stored_candidate)
    stored_overlay = attempt_dir / f"{base}_measurement.png"
    source_overlay_path = Path(visual["form_evidence"]["measurement_overlay"])
    source_overlay = (
        source_overlay_path
        if source_overlay_path.is_absolute()
        else visual_file.parent / source_overlay_path
    )
    if stored_overlay.exists():
        raise RunError(f"Attempt measurement path already exists: {stored_overlay}")
    shutil.copy2(source_overlay, stored_overlay)
    stored_visual = copy.deepcopy(visual)
    stored_visual["form_evidence"]["measurement_overlay"] = str(
        stored_overlay.relative_to(run_dir)
    )

    references = copy.deepcopy(image_spec["references"])
    passed = automatic.get("overall") == "PASS" and visual.get("verdict") == "PASS"
    record = {
        "candidate_attempt": attempt_number,
        "provider": args.provider,
        "model": args.model,
        "created_at": utc_now(),
        "assignment_sha256": manifest["assignment_sha256"],
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "references": references,
        "candidate_path": str(stored_candidate.relative_to(run_dir)),
        "candidate_sha256": candidate_sha256,
        "proportion": copy.deepcopy(image_spec["proportion"]),
        "identity_anchor_form": image_spec["identity_anchor_form"],
        "measured_head_ratio": stored_visual["form_evidence"]["calculated_head_ratio"],
        "automatic_qa": automatic,
        "requested_output": copy.deepcopy(image_spec["output"]),
        "provider_output_request": provider_output_request(
            image_spec["output"], args.provider_size
        ),
        "actual_output": actual_output_from_automatic(
            automatic, image_spec["output"]["alpha"]
        ),
        "visual_qa": stored_visual,
        "verdict": "PASS" if passed else "FAIL",
        "consumes_candidate_budget": True,
    }
    write_json(record_path, record)
    attempts.append(record)
    state["attempts"] = attempts
    state["status"] = "candidate_pass" if passed else "generating"
    manifest["candidate_count"] += 1
    save_manifest(run_dir, manifest)
    return {
        "recorded": str(record_path),
        "verdict": record["verdict"],
        "image_candidates": len(attempts),
        "run_candidates": manifest["candidate_count"],
    }


def cmd_promote(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, assignment, manifest = load_run(args.run_dir)
    if manifest["status"] != "in_progress":
        raise RunError("Run is not open")
    state = image_state(manifest, args.image)
    matches = [
        item for item in state["attempts"] if item["candidate_attempt"] == args.attempt
    ]
    if len(matches) != 1 or matches[0]["verdict"] != "PASS":
        raise RunError("Only one recorded PASS candidate can be promoted")
    image_spec = next(item for item in assignment["images"] if item["id"] == args.image)
    validate_visual_qa(
        matches[0]["visual_qa"],
        image_spec,
        expected_candidate_sha256=matches[0]["candidate_sha256"],
        overlay_root=run_dir,
        counterpart_ratio=paired_expanded_ratio(assignment, manifest, image_spec),
        compact_pair=is_compact_pair(assignment, image_spec),
    )
    source = run_dir / matches[0]["candidate_path"]
    if sha256(source) != matches[0]["candidate_sha256"]:
        raise RunError("Recorded candidate SHA-256 mismatch")
    validate_automatic_qa(
        matches[0]["automatic_qa"],
        image_spec,
        source,
        matches[0]["candidate_sha256"],
        require_matching_path=False,
    )
    destination = run_dir / "final" / f"{args.image}.png"
    if destination.exists():
        raise RunError(f"Final file already exists: {destination}")
    shutil.copy2(source, destination)
    state["status"] = "passed"
    state["final_path"] = str(destination.relative_to(run_dir))
    state["final_sha256"] = sha256(destination)
    state["final_measured_head_ratio"] = matches[0]["measured_head_ratio"]
    state["final_output"] = copy.deepcopy(matches[0]["actual_output"])
    save_manifest(run_dir, manifest)
    return {
        "final": str(destination),
        "sha256": state["final_sha256"],
        "output": state["final_output"],
    }


def cmd_finalize(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, _assignment, manifest = load_run(args.run_dir)
    if manifest["status"] != "in_progress":
        raise RunError("Run is already finalized")
    states = list(manifest["images"].values())
    complete = all(item["status"] == "passed" for item in states)
    if not complete and not args.allow_failures:
        raise RunError("Not every image passed; use --allow-failures to close with gaps")
    manifest["status"] = "complete" if complete else "complete_with_failures"
    manifest["finalized_at"] = utc_now()
    save_manifest(run_dir, manifest)
    return {
        "status": manifest["status"],
        "passed": sum(item["status"] == "passed" for item in states),
        "total": len(states),
        "candidate_count": manifest["candidate_count"],
    }


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    run_dir, _assignment, manifest = load_run(args.run_dir)
    return {
        "run_dir": str(run_dir),
        "status": manifest["status"],
        "candidate_count": manifest["candidate_count"],
        "execution": manifest["execution"],
        "images": {
            key: {
                "status": value["status"],
                "candidates": len(value["attempts"]),
                "provider_errors": len(value["provider_errors"]),
                "final_path": value["final_path"],
                "final_measured_head_ratio": value["final_measured_head_ratio"],
                "final_output": value["final_output"],
            }
            for key, value in manifest["images"].items()
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-assignment", help="Validate a confirmed assignment")
    validate.add_argument("--assignment", required=True)
    validate.set_defaults(func=cmd_validate)

    init = commands.add_parser("init", help="Create a non-overwriting run directory")
    init.add_argument("--assignment", required=True)
    init.add_argument("--root", default="artifacts/whalechan-image-character")
    init.add_argument("--effective-parallelism", type=int)
    init.set_defaults(func=cmd_init)

    error = commands.add_parser("record-error", help="Record a provider error without budget use")
    error.add_argument("--run-dir", required=True)
    error.add_argument("--image", required=True)
    error.add_argument("--provider", choices=PROVIDERS, required=True)
    error.add_argument("--model", required=True)
    error.add_argument(
        "--category",
        choices=[
            "unavailable",
            "authentication",
            "quota",
            "rate_limit",
            "timeout",
            "service",
            "capability",
            "safety_rejection",
        ],
        required=True,
    )
    error.add_argument("--details", required=True)
    error.set_defaults(func=cmd_record_error)

    candidate = commands.add_parser("record-candidate", help="Store one candidate and its QA")
    candidate.add_argument("--run-dir", required=True)
    candidate.add_argument("--image", required=True)
    candidate.add_argument("--provider", choices=PROVIDERS, required=True)
    candidate.add_argument("--model", required=True)
    candidate.add_argument("--prompt-file", required=True)
    candidate.add_argument("--candidate", required=True)
    candidate.add_argument("--automatic-json", required=True)
    candidate.add_argument("--visual-json", required=True)
    candidate.add_argument("--provider-size")
    candidate.set_defaults(func=cmd_record_candidate)

    promote = commands.add_parser("promote", help="Copy one PASS candidate into final")
    promote.add_argument("--run-dir", required=True)
    promote.add_argument("--image", required=True)
    promote.add_argument("--attempt", type=int, required=True)
    promote.set_defaults(func=cmd_promote)

    finalize = commands.add_parser("finalize", help="Close a run and preserve any numbering gaps")
    finalize.add_argument("--run-dir", required=True)
    finalize.add_argument("--allow-failures", action="store_true")
    finalize.set_defaults(func=cmd_finalize)

    status = commands.add_parser("status", help="Print a compact run summary")
    status.add_argument("--run-dir", required=True)
    status.set_defaults(func=cmd_status)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        output = args.func(args)
    except RunError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **output}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
