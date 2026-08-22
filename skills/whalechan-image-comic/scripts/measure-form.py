#!/usr/bin/env python3
"""Create candidate-bound Whale-chan head-ratio evidence from reviewed landmarks."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = SKILL_ROOT / "references" / "asset-catalog.json"
CATALOG_SCHEMA_VERSION = 3


class MeasurementError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog() -> dict[str, Any]:
    try:
        value = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MeasurementError(f"Cannot read asset catalog: {exc}") from exc
    forms = value.get("character_forms") if isinstance(value, dict) else None
    if value.get("schema_version") != CATALOG_SCHEMA_VERSION or not isinstance(forms, dict):
        raise MeasurementError("Invalid asset catalog")
    return value


def distance(start: list[float], end: list[float]) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


def target_sha256(
    mode: str,
    preset: str | None,
    mean: float,
    acceptance_range: list[float],
) -> str:
    payload = json.dumps(
        {
            "mode": mode,
            "preset": preset,
            "target_head_ratio": float(mean),
            "acceptance_range": [float(item) for item in acceptance_range],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def resolve_target(
    profile: dict[str, Any],
    override_mean: float | None,
    override_range: list[float] | None,
) -> tuple[str, float, list[float]]:
    if (override_mean is None) != (override_range is None):
        raise MeasurementError("Confirmed mean and acceptance range must be provided together")
    if override_mean is None:
        return "preset", float(profile["mean_head_ratio"]), list(profile["acceptance_range"])
    if (
        not math.isfinite(override_mean)
        or override_mean <= 1
        or not isinstance(override_range, list)
        or len(override_range) != 2
        or any(not math.isfinite(item) for item in override_range)
        or override_range[0] <= 1
        or override_range[0] >= override_range[1]
        or not override_range[0] <= override_mean <= override_range[1]
    ):
        raise MeasurementError("Invalid confirmed proportion target")
    return "custom", float(override_mean), [float(item) for item in override_range]


def draw_line(start: list[float], end: list[float]) -> str:
    return f"line {start[0]:g},{start[1]:g} {end[0]:g},{end[1]:g}"


def draw_circle(point: list[float], radius: int = 7) -> str:
    return f"circle {point[0]:g},{point[1]:g} {point[0] + radius:g},{point[1]:g}"


def render_overlay(
    image: Path,
    overlay: Path,
    head_top: list[float],
    chin: list[float],
    pelvis: list[float],
    knee: list[float],
    sole: list[float],
) -> None:
    magick = shutil.which("magick")
    if not magick:
        raise MeasurementError("ImageMagick 'magick' is required")
    overlay.parent.mkdir(parents=True, exist_ok=True)
    body_points = [chin, pelvis, knee, sole]
    command = [
        magick,
        str(image),
        "-stroke", "#E5484D", "-strokewidth", "5", "-fill", "none",
        "-draw", draw_line(head_top, chin),
        "-stroke", "#1677FF",
        "-draw", " ".join(
            draw_line(start, end) for start, end in zip(body_points, body_points[1:])
        ),
        "-fill", "#FFD60A", "-stroke", "#111827", "-strokewidth", "2",
        "-draw", " ".join(draw_circle(point) for point in [head_top, *body_points]),
        str(overlay),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=30)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise MeasurementError(f"Cannot render measurement overlay: {detail.strip()}") from exc


def build_result(
    image: Path,
    form: str,
    overlay: Path,
    head_top: list[float],
    chin: list[float],
    pelvis: list[float],
    knee: list[float],
    sole: list[float],
    override_mean: float | None = None,
    override_range: list[float] | None = None,
) -> dict[str, Any]:
    head_height = distance(head_top, chin)
    if head_height <= 0:
        raise MeasurementError("Head top and chin must not be the same point")
    segments = [
        {"name": "chin_to_pelvis", "start": chin, "end": pelvis},
        {"name": "pelvis_to_knee", "start": pelvis, "end": knee},
        {"name": "knee_to_sole", "start": knee, "end": sole},
    ]
    if any(distance(item["start"], item["end"]) <= 0 for item in segments):
        raise MeasurementError("Every body segment must have positive length")
    ratio = (head_height + sum(distance(item["start"], item["end"]) for item in segments)) / head_height
    catalog = load_catalog()
    profile = catalog["character_forms"][form]
    source, mean, acceptance = resolve_target(profile, override_mean, override_range)
    preset = form if source == "preset" else None
    evidence = {
        "candidate_sha256": sha256(image),
        "measurement_method": "pose-neutralized-skeleton",
        "target_source": source,
        "target_sha256": target_sha256(source, preset, mean, acceptance),
        "mean_head_ratio": mean,
        "acceptance_range": acceptance,
        "head_axis": {"top": head_top, "chin": chin},
        "body_segments": segments,
        "calculated_head_ratio": round(ratio, 3),
        "measurement_overlay": str(overlay.resolve()),
        "measurement_overlay_sha256": sha256(overlay),
    }
    return {
        "candidate_sha256": sha256(image),
        "form_evidence": evidence,
        "within_range": acceptance[0] <= ratio <= acceptance[1],
    }


def main() -> int:
    catalog = load_catalog()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--form", choices=sorted(catalog["character_forms"]), required=True)
    for name in ("head-top", "chin", "pelvis", "knee", "sole"):
        parser.add_argument(f"--{name}", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--confirmed-mean-head-ratio", type=float)
    parser.add_argument("--confirmed-acceptance-range", nargs=2, type=float, metavar=("MIN", "MAX"))
    parser.add_argument("--write-overlay", required=True)
    parser.add_argument("--write-json", required=True)
    args = parser.parse_args()
    image = Path(args.image).resolve()
    overlay = Path(args.write_overlay).resolve()
    output = Path(args.write_json).resolve()
    if not image.is_file():
        print(json.dumps({"ok": False, "error": f"Image does not exist: {image}"}), file=sys.stderr)
        return 2
    try:
        render_overlay(image, overlay, args.head_top, args.chin, args.pelvis, args.knee, args.sole)
        result = build_result(
            image, args.form, overlay, args.head_top, args.chin, args.pelvis,
            args.knee, args.sole, args.confirmed_mean_head_ratio,
            args.confirmed_acceptance_range,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except MeasurementError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
    return 0 if result["within_range"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
