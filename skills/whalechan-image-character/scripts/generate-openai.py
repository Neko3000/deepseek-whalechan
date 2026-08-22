#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the OpenAI Images API."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import os
import re
import secrets
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


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


class AdapterError(RuntimeError):
    def __init__(self, message: str, category: str = "service") -> None:
        super().__init__(message)
        self.category = category


def resolve_size(
    resolution: Any,
    ratio_width: int,
    ratio_height: int,
) -> tuple[dict[str, Any], str]:
    if not isinstance(resolution, dict) or set(resolution) != {"mode", "width", "height"}:
        raise AdapterError(
            "request.resolution must contain exactly mode, width, and height",
            "capability",
        )
    mode = resolution.get("mode")
    width = resolution.get("width")
    height = resolution.get("height")
    if mode == "provider-native":
        if width is not None or height is not None:
            raise AdapterError(
                "provider-native resolution requires null width and height",
                "capability",
            )
        ratio = ratio_width / ratio_height
        if ratio >= 1:
            height = 1024
            width = round((height * ratio) / 16) * 16
        else:
            width = 1024
            height = round((width / ratio) / 16) * 16
    elif mode == "exact":
        if (
            isinstance(width, bool)
            or not isinstance(width, int)
            or width < 1
            or isinstance(height, bool)
            or not isinstance(height, int)
            or height < 1
        ):
            raise AdapterError(
                "exact resolution requires positive width and height",
                "capability",
            )
    else:
        raise AdapterError(
            "request.resolution.mode must be provider-native or exact",
            "capability",
        )
    if not math.isclose(
        width / height,
        ratio_width / ratio_height,
        rel_tol=0.02,
    ):
        raise AdapterError("request.resolution does not match request.aspect_ratio", "capability")
    if (
        width % 16 != 0
        or height % 16 != 0
        or max(width, height) > 3840
        or max(width, height) / min(width, height) > 3
        or not 655_360 <= width * height <= 8_294_400
    ):
        raise AdapterError("request resolution violates gpt-image-2 size constraints", "capability")
    return {"mode": mode, "width": resolution.get("width"), "height": resolution.get("height")}, f"{width}x{height}"


def load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Cannot read request JSON: {exc}", "capability") from exc
    allowed_fields = {"prompt", "references", "aspect_ratio", "resolution", "output", "quality"}
    if isinstance(value, dict) and value.keys() - allowed_fields:
        raise AdapterError("request contains unsupported fields", "capability")
    if not isinstance(value, dict) or not isinstance(value.get("prompt"), str) or not value["prompt"].strip():
        raise AdapterError("request.prompt must be a non-empty string", "capability")
    refs = value.get("references")
    if not isinstance(refs, list) or not refs:
        raise AdapterError("request.references must contain at least 1 reference", "capability")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(refs):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"].strip():
            raise AdapterError(f"request.references[{index}].path must be a non-empty string", "capability")
        raw_roles = item.get("roles")
        if not isinstance(raw_roles, list) or not raw_roles or any(
            not isinstance(role, str) or not role.strip() for role in raw_roles
        ):
            raise AdapterError(f"request.references[{index}].roles must be a non-empty list of strings", "capability")
        instruction = item.get("instruction")
        if instruction is not None and not isinstance(instruction, str):
            raise AdapterError(f"request.references[{index}].instruction must be a string", "capability")
        raw_path = item["path"]
        roles = [role.strip() for role in raw_roles]
        if len(set(roles)) != len(roles) or not set(roles) <= REFERENCE_ROLES:
            raise AdapterError(
                f"request.references[{index}].roles contains an invalid or duplicate role",
                "capability",
            )
        ref = Path(raw_path)
        if not ref.is_absolute():
            ref = (path.parent / ref).resolve()
        if not ref.is_file():
            raise AdapterError(f"Reference image does not exist: {ref}", "capability")
        normalized_ref: dict[str, Any] = {"path": ref, "roles": roles}
        for field in ("id", "sha256"):
            if field in item:
                if not isinstance(item[field], str) or not item[field].strip():
                    raise AdapterError(
                        f"request.references[{index}].{field} must be a non-empty string",
                        "capability",
                    )
                normalized_ref[field] = item[field].strip()
        expected_sha256 = normalized_ref.get("sha256")
        if expected_sha256 is not None:
            actual_sha256 = hashlib.sha256(ref.read_bytes()).hexdigest()
            if expected_sha256.lower() != actual_sha256:
                raise AdapterError(
                    f"request.references[{index}].sha256 does not match the reference image",
                    "capability",
                )
        if instruction is not None:
            normalized_ref["instruction"] = instruction
        normalized.append(normalized_ref)
    output = value.get("output")
    if not isinstance(output, dict) or set(output) != {"format", "alpha"}:
        raise AdapterError("request.output must contain exactly format and alpha", "capability")
    if output.get("format") != "png":
        raise AdapterError("request.output.format must be png", "capability")
    alpha = output.get("alpha")
    if not isinstance(alpha, bool):
        raise AdapterError("request.output.alpha must be a boolean", "capability")
    aspect_ratio = value.get("aspect_ratio")
    ratio_match = (
        re.fullmatch(r"([1-9]\d*):([1-9]\d*)", aspect_ratio)
        if isinstance(aspect_ratio, str)
        else None
    )
    if ratio_match is None:
        raise AdapterError("request.aspect_ratio must be a positive WIDTH:HEIGHT ratio", "capability")
    ratio_width, ratio_height = (int(item) for item in ratio_match.groups())
    resolution, size = resolve_size(value.get("resolution"), ratio_width, ratio_height)
    value["size"] = size
    value["resolution"] = resolution
    value["references"] = normalized
    value["reference_paths"] = [item["path"] for item in normalized]
    value["output"] = {**output, "alpha": alpha}
    return value


def effective_prompt(spec: dict[str, Any]) -> str:
    prompt = spec["prompt"]
    if spec["output"]["alpha"]:
        return f"{prompt}\n\nOutput requirement: PNG with a genuinely transparent background and clean subject edges."
    return prompt


def reference_summary(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "path": str(item["path"]),
            "roles": item["roles"],
            **({"id": item["id"]} if "id" in item else {}),
            **({"sha256": item["sha256"]} if "sha256" in item else {}),
            **({"instruction": item["instruction"]} if "instruction" in item else {}),
        }
        for item in spec["references"]
    ]


def request_fields(spec: dict[str, Any], model: str) -> list[tuple[str, str]]:
    fields = [
        ("model", model),
        ("prompt", effective_prompt(spec)),
        ("size", spec["size"]),
        ("quality", spec.get("quality", "medium")),
        ("output_format", "png"),
    ]
    if spec["output"]["alpha"]:
        fields.append(("background", "transparent"))
    return fields


def mime(path: Path) -> str:
    prefix = path.read_bytes()[:12]
    if prefix.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if prefix.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if prefix.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if prefix.startswith(b"RIFF") and prefix[8:12] == b"WEBP":
        return "image/webp"
    raise AdapterError(f"Unsupported reference image format: {path}", "capability")


def multipart(fields: list[tuple[str, str]], files: list[Path]) -> tuple[bytes, str]:
    boundary = f"----whalechan-{secrets.token_hex(12)}"
    body: list[bytes] = []
    for name, value in fields:
        body.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for path in files:
        body.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="image[]"; filename="{path.name}"\r\n'
                ).encode(),
                f"Content-Type: {mime(path)}\r\n\r\n".encode(),
                path.read_bytes(),
                b"\r\n",
            ]
        )
    body.append(f"--{boundary}--\r\n".encode())
    return b"".join(body), f"multipart/form-data; boundary={boundary}"


def classify_http(status: int, detail: str) -> str:
    lowered = detail.lower()
    if status in {401, 403}:
        return "authentication"
    if status == 429:
        return "quota" if "quota" in lowered or "billing" in lowered else "rate_limit"
    if "moderation_blocked" in lowered or "safety" in lowered:
        return "safety_rejection"
    if status >= 500:
        return "service"
    return "capability"


def post(url: str, headers: dict[str, str], payload: bytes, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:4000]
        raise AdapterError(f"HTTP {exc.code}: {detail}", classify_http(exc.code, detail)) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AdapterError(f"Network request failed: {exc}", "timeout") from exc
    except json.JSONDecodeError as exc:
        raise AdapterError("Provider returned invalid JSON", "service") from exc


def extract_image(response: dict[str, Any], timeout: int) -> bytes:
    error = response.get("error")
    if isinstance(error, dict):
        message = str(error.get("message") or error.get("code") or "provider error")
        category = "safety_rejection" if error.get("code") == "moderation_blocked" else "service"
        raise AdapterError(message, category)
    for item in response.get("data", []):
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"], validate=True)
        if item.get("url"):
            try:
                with urllib.request.urlopen(item["url"], timeout=timeout) as result:
                    return result.read()
            except (urllib.error.URLError, TimeoutError) as exc:
                raise AdapterError(f"Could not download output: {exc}", "service") from exc
    raise AdapterError("OpenAI response contained no image", "service")


def write_once(path: Path, data: bytes) -> None:
    if path.exists():
        raise AdapterError(f"Output already exists: {path}", "capability")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        request_path = Path(args.request).resolve()
        spec = load_request(request_path)
        model = args.model or os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        output = Path(args.output).resolve()
        prompt = effective_prompt(spec)
        references = reference_summary(spec)
        summary = {
            "provider": "openai",
            "model": model,
            "endpoint": f"{base_url}/images/edits",
            "reference_paths": [str(path) for path in spec["reference_paths"]],
            "references": references,
            "reference_count": len(references),
            "reference_roles": [item["roles"] for item in references],
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "size": spec["size"],
            "resolution_mode": spec["resolution"]["mode"],
            "quality": spec.get("quality", "medium"),
            "output": str(output),
            "output_alpha": spec["output"]["alpha"],
            "transparency_handling": "native" if spec["output"]["alpha"] else "opaque-default",
            "dry_run": args.dry_run,
        }
        if args.dry_run:
            print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
            return 0
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AdapterError("OPENAI_API_KEY is not configured", "authentication")
        payload, content_type = multipart(
            request_fields(spec, model),
            spec["reference_paths"],
        )
        response = post(
            summary["endpoint"],
            {"Authorization": f"Bearer {api_key}", "Content-Type": content_type},
            payload,
            args.timeout,
        )
        image = extract_image(response, args.timeout)
        write_once(output, image)
        print(
            json.dumps(
                {"ok": True, **summary, "dry_run": False, "output_sha256": hashlib.sha256(image).hexdigest()},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except (AdapterError, ValueError, base64.binascii.Error) as exc:
        category = exc.category if isinstance(exc, AdapterError) else "service"
        print(json.dumps({"ok": False, "category": category, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
