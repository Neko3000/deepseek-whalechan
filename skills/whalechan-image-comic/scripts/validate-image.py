#!/usr/bin/env python3
"""Validate comic PNG format, dimensions, colorspace, and alpha state."""

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
from pathlib import Path
from typing import Any


class ValidationError(RuntimeError):
    pass


def inspect(path: Path) -> dict[str, Any]:
    executable = shutil.which("magick")
    if not executable:
        raise ValidationError("ImageMagick 'magick' is required")
    try:
        result = subprocess.run(
            [executable, "identify", "-quiet", "-format", "%m|%w|%h|%[colorspace]|%[channels]", str(path)],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ValidationError((getattr(exc, "stderr", "") or str(exc)).strip()) from exc
    parts = result.stdout.strip().split("|", 4)
    if len(parts) != 5:
        raise ValidationError(f"Unexpected identify output: {result.stdout.strip()}")
    return {
        "format": parts[0],
        "width": int(parts[1]),
        "height": int(parts[2]),
        "colorspace": parts[3],
        "channels": parts[4],
    }


def canonical_ratio(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("aspect_ratio must use positive integers as W:H")
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", value.strip())
    if match is None:
        raise ValidationError("aspect_ratio must use positive integers as W:H")
    width, height = (int(item) for item in match.groups())
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def normalize_output(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        return {
            "format": "png",
            "aspect_ratio": "1:1",
            "resolution": {"mode": "auto", "recommended": "1024x1024"},
        }
    if (
        not isinstance(value, dict)
        or set(value) != {"format", "aspect_ratio", "resolution"}
        or value.get("format") != "png"
    ):
        raise ValidationError("output must be a PNG output object")
    ratio = canonical_ratio(value.get("aspect_ratio"))
    resolution = value.get("resolution")
    if not isinstance(resolution, dict):
        raise ValidationError("output.resolution must be an object")
    mode = resolution.get("mode")
    if mode == "auto":
        if set(resolution) != {"mode", "recommended"}:
            raise ValidationError("automatic resolution requires mode and recommended")
        recommended = resolution.get("recommended")
        if recommended is not None:
            match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", str(recommended))
            if match is None:
                raise ValidationError("recommended resolution must use WIDTHxHEIGHT or null")
            width, height = (int(item) for item in match.groups())
            if canonical_ratio(f"{width}:{height}") != ratio:
                raise ValidationError("recommended resolution does not match aspect_ratio")
        normalized_resolution = {
            "mode": "auto",
            "recommended": recommended,
        }
    elif mode == "explicit":
        if set(resolution) != {"mode", "width", "height"}:
            raise ValidationError("explicit resolution requires mode, width, and height")
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
            raise ValidationError("explicit output requires positive width and height")
        if canonical_ratio(f"{width}:{height}") != ratio:
            raise ValidationError("aspect_ratio does not match explicit resolution")
        normalized_resolution = {"mode": "explicit", "width": width, "height": height}
    else:
        raise ValidationError("resolution.mode must be auto or explicit")
    return {"format": "png", "aspect_ratio": ratio, "resolution": normalized_resolution}


def ratio_matches(width: int, height: int, ratio: str) -> bool:
    ratio_width, ratio_height = (int(item) for item in ratio.split(":"))
    if ratio_width == ratio_height:
        return width == height
    return math.isclose(width / height, ratio_width / ratio_height, rel_tol=0.02)


def validate(path: Path, output: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.is_file() or path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError("Image must be a decodable PNG file")
    expected = normalize_output(output)
    metadata = inspect(path)
    channels = metadata["channels"].lower().replace(" ", "")
    has_alpha = "alpha" in channels or channels.startswith(("rgba", "srgba", "graya", "cmyka"))
    resolution = expected["resolution"]
    if resolution["mode"] == "explicit":
        dimensions_pass = (
            metadata["width"] == resolution["width"]
            and metadata["height"] == resolution["height"]
        )
        dimensions_expected = f"exactly {resolution['width']}x{resolution['height']}"
    else:
        dimensions_pass = ratio_matches(
            metadata["width"], metadata["height"], expected["aspect_ratio"]
        )
        dimensions_expected = f"aspect ratio {expected['aspect_ratio']} at provider-native resolution"
    gates = {
        "F1": {
            "verdict": "PASS" if metadata["format"].upper() == "PNG" and dimensions_pass else "FAIL",
            "detail": f"{metadata['format']} {metadata['width']}x{metadata['height']}; expected PNG {dimensions_expected}",
        },
        "F2": {
            "verdict": "PASS" if metadata["colorspace"].lower() in {"rgb", "srgb"} and not has_alpha else "FAIL",
            "detail": f"colorspace={metadata['colorspace']}, channels={metadata['channels']}",
        },
    }
    return {
        "schema_version": 2,
        "path": str(path.resolve()),
        "candidate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "expected_output": expected,
        "overall": "PASS" if all(item["verdict"] == "PASS" for item in gates.values()) else "FAIL",
        "gates": gates,
        "metrics": metadata,
    }


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--resolution-mode", choices=("auto", "explicit"), default="auto")
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    recommendation = parser.add_mutually_exclusive_group()
    recommendation.add_argument("--recommended")
    recommendation.add_argument("--no-recommendation", action="store_true")
    parser.add_argument("--write-json")
    args = parser.parse_args()
    try:
        if args.resolution_mode == "explicit":
            if args.width is None or args.height is None:
                raise ValidationError("explicit mode requires --width and --height")
            if args.recommended is not None or args.no_recommendation:
                raise ValidationError("recommendation flags require automatic mode")
            resolution = {
                "mode": "explicit",
                "width": args.width,
                "height": args.height,
            }
        else:
            if args.width is not None or args.height is not None:
                raise ValidationError("--width and --height require explicit mode")
            recommended = None if args.no_recommendation else args.recommended
            if (
                recommended is None
                and not args.no_recommendation
                and canonical_ratio(args.aspect_ratio) == "1:1"
            ):
                recommended = "1024x1024"
            resolution = {"mode": "auto", "recommended": recommended}
        output = {
            "format": "png",
            "aspect_ratio": args.aspect_ratio,
            "resolution": resolution,
        }
        result = validate(Path(args.image).resolve(), output)
        if args.write_json:
            write_json(Path(args.write_json).resolve(), result)
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
