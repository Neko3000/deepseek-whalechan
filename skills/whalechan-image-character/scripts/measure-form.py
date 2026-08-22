#!/usr/bin/env python3
"""Create image-bound Whale-chan proportion evidence from reviewed landmarks."""

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
CATALOG_PATH = SKILL_ROOT / "references" / "reference-catalog.json"
CATALOG_SCHEMA_VERSION = 4


class MeasurementError(RuntimeError):
    """Invalid input or unavailable overlay renderer."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_catalog() -> tuple[dict[str, Any], str]:
    try:
        value = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MeasurementError(f"Cannot read reference catalog: {exc}") from exc
    if not isinstance(value, dict):
        raise MeasurementError("Invalid reference catalog")
    forms = value.get("forms")
    if (
        value.get("schema_version") != CATALOG_SCHEMA_VERSION
        or not isinstance(forms, dict)
        or not forms
    ):
        raise MeasurementError("Invalid reference catalog")
    for profile in forms.values():
        if not isinstance(profile, dict):
            raise MeasurementError("Invalid reference catalog")
        mean = profile.get("mean_head_ratio")
        acceptance_range = profile.get("acceptance_range")
        if (
            not isinstance(mean, (int, float))
            or isinstance(mean, bool)
            or not math.isfinite(mean)
            or mean <= 0
            or not isinstance(acceptance_range, list)
            or len(acceptance_range) != 2
            or any(
                not isinstance(item, (int, float))
                or isinstance(item, bool)
                or not math.isfinite(item)
                for item in acceptance_range
            )
            or not acceptance_range[0] <= mean <= acceptance_range[1]
        ):
            raise MeasurementError("Invalid reference catalog")
    return value, sha256(CATALOG_PATH)


def distance(start: list[float], end: list[float]) -> float:
    return math.hypot(end[0] - start[0], end[1] - start[1])


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


def resolve_target(
    profile: dict[str, Any],
    override_mean: float | None,
    override_range: list[float] | None,
) -> tuple[float, list[float]]:
    if (override_mean is None) != (override_range is None):
        raise MeasurementError(
            "Confirmed mean and acceptance range must be provided together"
        )
    if override_mean is None:
        return float(profile["mean_head_ratio"]), list(profile["acceptance_range"])
    if (
        isinstance(override_mean, bool)
        or not isinstance(override_mean, (int, float))
        or not math.isfinite(override_mean)
        or override_mean <= 1
        or not isinstance(override_range, list)
        or len(override_range) != 2
        or any(
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            for item in override_range
        )
        or override_range[0] >= override_range[1]
        or not override_range[0] <= override_mean <= override_range[1]
    ):
        raise MeasurementError("Invalid confirmed proportion target")
    return float(override_mean), [float(item) for item in override_range]


def draw_line(start: list[float], end: list[float]) -> str:
    return f"line {start[0]:g},{start[1]:g} {end[0]:g},{end[1]:g}"


def draw_circle(point: list[float], radius: int = 7) -> str:
    return (
        f"circle {point[0]:g},{point[1]:g} "
        f"{point[0] + radius:g},{point[1]:g}"
    )


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
    body_lines = " ".join(
        draw_line(start, end) for start, end in zip(body_points, body_points[1:])
    )
    points = " ".join(draw_circle(point) for point in [head_top, *body_points])
    command = [
        magick,
        str(image),
        "-stroke",
        "#E5484D",
        "-strokewidth",
        "5",
        "-fill",
        "none",
        "-draw",
        draw_line(head_top, chin),
        "-stroke",
        "#1677FF",
        "-draw",
        body_lines,
        "-fill",
        "#FFD60A",
        "-stroke",
        "#111827",
        "-strokewidth",
        "2",
        "-draw",
        points,
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
    catalog, catalog_sha256 = load_catalog()
    profile = catalog["forms"][form]
    mean_head_ratio, acceptance_range = resolve_target(
        profile, override_mean, override_range
    )
    target_source = "custom" if override_mean is not None else "preset"
    target_preset = None if override_mean is not None else form
    target_digest = target_sha256(
        target_source, target_preset, mean_head_ratio, acceptance_range
    )
    minimum, maximum = acceptance_range
    return {
        "candidate_sha256": sha256(image),
        "form_evidence": {
            "measurement_method": "pose-neutralized-skeleton",
            "head_axis": {"top": head_top, "chin": chin},
            "body_segments": segments,
            "calculated_head_ratio": round(ratio, 3),
            "measurement_overlay": str(overlay.resolve()),
            "measurement_overlay_sha256": sha256(overlay),
            "catalog_sha256": catalog_sha256,
            "target_source": target_source,
            "target_sha256": target_digest,
            "mean_head_ratio": mean_head_ratio,
            "acceptance_range": acceptance_range,
        },
        "form": form,
        "catalog_sha256": catalog_sha256,
        "target_source": target_source,
        "target_sha256": target_digest,
        "mean_head_ratio": mean_head_ratio,
        "acceptance_range": acceptance_range,
        "within_range": minimum <= ratio <= maximum,
    }


def main() -> int:
    catalog, _catalog_sha256 = load_catalog()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--form", choices=sorted(catalog["forms"]), required=True)
    parser.add_argument("--head-top", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--chin", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--pelvis", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--knee", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--sole", nargs=2, type=float, required=True, metavar=("X", "Y"))
    parser.add_argument("--confirmed-mean-head-ratio", type=float)
    parser.add_argument(
        "--confirmed-acceptance-range", nargs=2, type=float, metavar=("MIN", "MAX")
    )
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
            image,
            args.form,
            overlay,
            args.head_top,
            args.chin,
            args.pelvis,
            args.knee,
            args.sole,
            args.confirmed_mean_head_ratio,
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
