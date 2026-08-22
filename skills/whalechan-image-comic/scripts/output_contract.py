"""Validate the v5 image output contract used by provider adapters."""

from __future__ import annotations

import math
import re
from typing import Any, Callable


def canonical_ratio(value: Any, fail: Callable[[str], Exception]) -> str:
    if not isinstance(value, str):
        raise fail("request.output.aspect_ratio must use W:H")
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", value.strip())
    if match is None:
        raise fail("request.output.aspect_ratio must use positive integers as W:H")
    width, height = (int(item) for item in match.groups())
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def parse_output(spec: dict[str, Any], fail: Callable[[str], Exception]) -> dict[str, Any]:
    value = spec.get("output")
    if not isinstance(value, dict):
        raise fail("request.output must be a v5 output object")
    if set(value) != {"format", "aspect_ratio", "resolution"}:
        raise fail("request.output must contain exactly format, aspect_ratio, and resolution")
    if value.get("format") != "png":
        raise fail("request.output.format must be png")
    ratio = canonical_ratio(value.get("aspect_ratio"), fail)
    resolution = value.get("resolution")
    if not isinstance(resolution, dict):
        raise fail("request.output.resolution must be an object")
    mode = resolution.get("mode")
    if mode == "auto":
        if set(resolution) != {"mode", "recommended"}:
            raise fail("automatic resolution must contain exactly mode and recommended")
        recommended = resolution.get("recommended")
        if recommended is not None and not re.fullmatch(
            r"[1-9][0-9]*x[1-9][0-9]*", str(recommended)
        ):
            raise fail("request.output.resolution.recommended must use WIDTHxHEIGHT or null")
        if recommended is not None:
            width, height = dimensions(str(recommended))
            if canonical_ratio(f"{width}:{height}", fail) != ratio:
                raise fail(
                    "request.output.resolution.recommended does not match aspect_ratio"
                )
        normalized_resolution = {"mode": "auto", "recommended": recommended}
    elif mode == "explicit":
        if set(resolution) != {"mode", "width", "height"}:
            raise fail("explicit resolution must contain exactly mode, width, and height")
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
            raise fail("explicit resolution requires positive integer width and height")
        expected = canonical_ratio(f"{width}:{height}", fail)
        if ratio != expected:
            raise fail("request.output.aspect_ratio does not match explicit resolution")
        normalized_resolution = {"mode": "explicit", "width": width, "height": height}
    else:
        raise fail("request.output.resolution.mode must be auto or explicit")
    return {"format": "png", "aspect_ratio": ratio, "resolution": normalized_resolution}


def dimensions(value: str) -> tuple[int, int]:
    width, height = value.split("x", 1)
    return int(width), int(height)
