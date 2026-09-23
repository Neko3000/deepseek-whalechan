#!/usr/bin/env python3
"""Compose existing panel images using the requested output aspect and resolution."""

from __future__ import annotations

import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_ratio(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([1-9][0-9]*):([1-9][0-9]*)", value.strip())
    if match is None:
        raise ValueError("aspect ratio must use positive integers as W:H")
    width, height = (int(item) for item in match.groups())
    divisor = math.gcd(width, height)
    return width // divisor, height // divisor


def image_dimensions(executable: str, path: Path) -> tuple[int, int]:
    result = subprocess.run(
        [executable, "identify", "-quiet", "-format", "%w|%h", str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    width, height = result.stdout.split("|", 1)
    return int(width), int(height)


def cells(layout: str, width: int, height: int, gutter: int) -> list[tuple[int, int, int, int]]:
    if layout == "left-right":
        first = (width - gutter) // 2
        return [(0, 0, first, height), (first + gutter, 0, width - gutter - first, height)]
    if layout == "top-bottom":
        first = (height - gutter) // 2
        return [(0, 0, width, first), (0, first + gutter, width, height - gutter - first)]
    first_width = (width - gutter) // 2
    first_height = (height - gutter) // 2
    widths = (first_width, width - gutter - first_width)
    heights = (first_height, height - gutter - first_height)
    return [
        (0, 0, widths[0], heights[0]),
        (widths[0] + gutter, 0, widths[1], heights[0]),
        (0, heights[0] + gutter, widths[0], heights[1]),
        (widths[0] + gutter, heights[0] + gutter, widths[1], heights[1]),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", choices=("top-bottom", "left-right", "2x2"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gutter", type=int, default=12)
    parser.add_argument("--resolution-mode", choices=("auto", "explicit"), default="auto")
    parser.add_argument("--aspect-ratio", default="1:1")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("panels", nargs="+")
    args = parser.parse_args()
    required = 4 if args.layout == "2x2" else 2
    if len(args.panels) != required:
        parser.error(f"{args.layout} requires exactly {required} panels")
    executable = shutil.which("magick")
    if not executable:
        print("ImageMagick 'magick' is required", file=sys.stderr)
        return 2
    output = Path(args.output).resolve()
    if output.exists():
        print(f"Output already exists: {output}", file=sys.stderr)
        return 2
    inputs = [Path(item).resolve() for item in args.panels]
    if any(not item.is_file() for item in inputs):
        print("Every panel path must exist", file=sys.stderr)
        return 2
    try:
        ratio_width, ratio_height = parse_ratio(args.aspect_ratio)
        if args.resolution_mode == "explicit":
            if args.width is None or args.height is None or args.width <= 0 or args.height <= 0:
                raise ValueError("explicit mode requires positive --width and --height")
            if args.width * ratio_height != args.height * ratio_width:
                raise ValueError("explicit dimensions do not match --aspect-ratio")
            width, height = args.width, args.height
        else:
            if args.width is not None or args.height is not None:
                raise ValueError("--width and --height require explicit mode")
            source_width, _source_height = image_dimensions(executable, inputs[0])
            width = source_width
            height = max(1, round(width * ratio_height / ratio_width))
        if args.gutter < 0 or args.gutter >= min(width, height):
            raise ValueError("gutter must be non-negative and smaller than the canvas")
        placements = cells(args.layout, width, height, args.gutter)
        if any(cell_width <= 0 or cell_height <= 0 for _, _, cell_width, cell_height in placements):
            raise ValueError("canvas is too small for the requested gutter")
    except (ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    command = [executable, "-size", f"{width}x{height}", "xc:white"]
    for item, (x, y, cell_width, cell_height) in zip(inputs, placements, strict=True):
        command.extend([
            "(", str(item), "-resize", f"{cell_width}x{cell_height}^",
            "-gravity", "center", "-extent", f"{cell_width}x{cell_height}", ")",
            "-geometry", f"+{x}+{y}", "-composite",
        ])
    command.extend(["-colorspace", "sRGB", "-alpha", "off"])
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=".panels-", suffix=".png", dir=output.parent)
    os.close(fd)
    Path(temporary_name).unlink(missing_ok=True)
    try:
        subprocess.run([*command, temporary_name], check=True, capture_output=True, text=True, timeout=60)
        os.replace(temporary_name, output)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        output.unlink(missing_ok=True)
        print((getattr(exc, "stderr", "") or str(exc)).strip(), file=sys.stderr)
        return 2
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
