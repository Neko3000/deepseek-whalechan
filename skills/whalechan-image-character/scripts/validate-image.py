#!/usr/bin/env python3
"""Validate Whale-chan PNG geometry and color mode."""

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
    """A file inspection failure."""


def run_magick(arguments: list[str]) -> str:
    executable = shutil.which("magick")
    if not executable:
        raise ValidationError("ImageMagick 'magick' is required")
    try:
        completed = subprocess.run(
            [executable, *arguments],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        detail = getattr(exc, "stderr", "") or str(exc)
        raise ValidationError(f"ImageMagick failed: {detail.strip()}") from exc
    return completed.stdout.strip()


def inspect_header(path: Path) -> dict[str, Any]:
    value = run_magick(
        ["identify", "-quiet", "-format", "%m|%w|%h|%[colorspace]|%[channels]", str(path)]
    )
    parts = value.split("|", 4)
    if len(parts) != 5:
        raise ValidationError(f"Unexpected identify output: {value}")
    return {
        "format": parts[0],
        "width": int(parts[1]),
        "height": int(parts[2]),
        "colorspace": parts[3],
        "channels": parts[4],
    }


def inspect_alpha_minimum(path: Path) -> float:
    value = run_magick(
        [str(path), "-alpha", "extract", "-format", "%[fx:minima]", "info:"]
    )
    try:
        return float(value)
    except ValueError as exc:
        raise ValidationError(f"Unexpected alpha inspection output: {value}") from exc


def inspect_transparent_fraction(path: Path) -> float:
    value = run_magick(
        [
            str(path),
            "-alpha",
            "extract",
            "-threshold",
            "5%",
            "-format",
            "%[fx:1-mean]",
            "info:",
        ]
    )
    try:
        return float(value)
    except ValueError as exc:
        raise ValidationError(f"Unexpected transparency inspection output: {value}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(
    path: Path,
    aspect_ratio: str = "1:1",
    resolution_mode: str = "provider-native",
    width: int | None = None,
    height: int | None = None,
    alpha: str = "forbidden",
) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationError(f"Image does not exist: {path}")
    if path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValidationError("File does not have a PNG signature")

    ratio_match = re.fullmatch(r"([1-9]\d*):([1-9]\d*)", aspect_ratio)
    if ratio_match is None:
        raise ValidationError("aspect_ratio must be a positive WIDTH:HEIGHT ratio")
    ratio_width, ratio_height = (int(item) for item in ratio_match.groups())
    if resolution_mode not in {"provider-native", "exact"}:
        raise ValidationError("resolution_mode must be provider-native or exact")
    if resolution_mode == "provider-native":
        if width is not None or height is not None:
            raise ValidationError("provider-native resolution must not specify width or height")
    elif (
        isinstance(width, bool)
        or not isinstance(width, int)
        or width < 1
        or isinstance(height, bool)
        or not isinstance(height, int)
        or height < 1
    ):
        raise ValidationError("exact resolution requires positive width and height")

    header = inspect_header(path)
    ratio_pass = math.isclose(
        header["width"] / header["height"],
        ratio_width / ratio_height,
        rel_tol=0.02,
    )
    size_pass = resolution_mode == "provider-native" or (
        header["width"] == width and header["height"] == height
    )
    t1_pass = (
        header["format"].upper() == "PNG"
        and header["width"] > 0
        and header["height"] > 0
        and ratio_pass
        and size_pass
    )
    channels = header["channels"].lower().replace(" ", "")
    has_alpha = "alpha" in channels or channels.startswith(("rgba", "srgba", "graya", "cmyka"))
    alpha_minimum = inspect_alpha_minimum(path) if has_alpha else None
    transparent_fraction = inspect_transparent_fraction(path) if has_alpha else None
    alpha_pass = (
        not has_alpha
        if alpha == "forbidden"
        else has_alpha
        and alpha_minimum is not None
        and alpha_minimum <= 0.05
        and transparent_fraction is not None
        and transparent_fraction >= 0.01
    )
    t2_pass = header["colorspace"].lower() in {"rgb", "srgb"} and alpha_pass
    gates = {
        "T1": {
            "verdict": "PASS" if t1_pass else "FAIL",
            "detail": (
                f"{header['format']} {header['width']}x{header['height']}; "
                f"expected PNG aspect_ratio={aspect_ratio}, "
                f"resolution={resolution_mode}"
                + (f" {width}x{height}" if resolution_mode == "exact" else "")
            ),
        },
        "T2": {
            "verdict": "PASS" if t2_pass else "FAIL",
            "detail": (
                f"colorspace={header['colorspace']}, channels={header['channels']}, "
                f"alpha={alpha}, alpha_minimum={alpha_minimum}, "
                f"transparent_fraction={transparent_fraction}"
            ),
        },
    }
    overall = "PASS" if all(item["verdict"] == "PASS" for item in gates.values()) else "FAIL"
    return {
        "schema_version": 2,
        "path": str(path.resolve()),
        "sha256": sha256(path),
        "overall": overall,
        "gates": gates,
        "metrics": {
            **header,
            "alpha_policy": alpha,
            "resolution_mode": resolution_mode,
            "expected_aspect_ratio": aspect_ratio,
            "expected_width": width,
            "expected_height": height,
            "alpha_minimum": alpha_minimum,
            "transparent_fraction": transparent_fraction,
        },
    }


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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument(
        "--resolution-mode",
        choices=("provider-native", "exact"),
        default="provider-native",
    )
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--alpha", choices=("forbidden", "required"), default="forbidden")
    parser.add_argument("--write-json")
    args = parser.parse_args()
    try:
        result = validate(
            Path(args.image).resolve(),
            args.aspect_ratio,
            args.resolution_mode,
            args.width,
            args.height,
            args.alpha,
        )
        if args.write_json:
            write_json(Path(args.write_json).resolve(), result)
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
