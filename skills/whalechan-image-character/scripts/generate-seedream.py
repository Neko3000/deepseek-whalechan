#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the Volcengine Ark Seedream API."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
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


def load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Cannot read request JSON: {exc}", "capability") from exc
    allowed_fields = {"prompt", "references", "aspect_ratio", "resolution", "output"}
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
    if alpha:
        raise AdapterError(
            "Seedream adapter has no verified native transparent-output contract",
            "capability",
        )
    aspect_ratio = value.get("aspect_ratio")
    if aspect_ratio not in {"1:1", "9:16"}:
        raise AdapterError("request.aspect_ratio must be 1:1 or 9:16", "capability")
    resolution = value.get("resolution")
    if not isinstance(resolution, dict) or set(resolution) != {"mode", "width", "height"}:
        raise AdapterError(
            "request.resolution must contain exactly mode, width, and height",
            "capability",
        )
    native_sizes = {"1:1": (1024, 1024), "9:16": (1024, 1792)}
    mode = resolution.get("mode")
    width = resolution.get("width")
    height = resolution.get("height")
    if mode == "provider-native":
        if width is not None or height is not None:
            raise AdapterError(
                "provider-native resolution requires null width and height",
                "capability",
            )
        width, height = native_sizes[aspect_ratio]
    elif mode == "exact":
        if (width, height) != native_sizes[aspect_ratio]:
            raise AdapterError(
                "Seedream exact resolution must match its verified native size for the aspect ratio",
                "capability",
            )
    else:
        raise AdapterError(
            "request.resolution.mode must be provider-native or exact",
            "capability",
        )
    size = f"{width}x{height}"
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


def data_url(path: Path) -> str:
    return f"data:{mime(path)};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def classify_http(status: int, detail: str) -> str:
    lowered = detail.lower()
    if status in {401, 403}:
        return "authentication"
    if status == 429:
        return "quota" if "quota" in lowered or "balance" in lowered else "rate_limit"
    if "safety" in lowered or "risk" in lowered or "blocked" in lowered:
        return "safety_rejection"
    if status >= 500:
        return "service"
    return "capability"


def call_api(url: str, api_key: str, body: dict[str, Any], timeout: int) -> dict[str, Any]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
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
    if isinstance(response.get("error"), dict):
        error = response["error"]
        message = str(error.get("message") or error.get("code") or "provider error")
        category = "safety_rejection" if "risk" in message.lower() else "service"
        raise AdapterError(message, category)
    for item in response.get("data", []):
        if isinstance(item.get("error"), dict):
            message = str(item["error"].get("message") or item["error"].get("code"))
            raise AdapterError(message)
        if item.get("b64_json"):
            return base64.b64decode(item["b64_json"], validate=True)
        if item.get("url"):
            try:
                with urllib.request.urlopen(item["url"], timeout=timeout) as result:
                    return result.read()
            except (urllib.error.URLError, TimeoutError) as exc:
                raise AdapterError(f"Could not download output: {exc}", "service") from exc
    raise AdapterError("Seedream response contained no image", "service")


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
        model = args.model or os.environ.get(
            "SEEDREAM_IMAGE_MODEL", "doubao-seedream-5-0-lite-260128"
        )
        base_url = os.environ.get(
            "SEEDREAM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        ).rstrip("/")
        endpoint = f"{base_url}/images/generations"
        output = Path(args.output).resolve()
        prompt = effective_prompt(spec)
        references = reference_summary(spec)
        summary = {
            "provider": "seedream",
            "model": model,
            "endpoint": endpoint,
            "reference_paths": [str(path) for path in spec["reference_paths"]],
            "references": references,
            "reference_count": len(references),
            "reference_roles": [item["roles"] for item in references],
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "size": spec["size"],
            "resolution_mode": spec["resolution"]["mode"],
            "output": str(output),
            "output_alpha": spec["output"]["alpha"],
            "transparency_handling": "prompt-only" if spec["output"]["alpha"] else "opaque-default",
            "dry_run": args.dry_run,
        }
        if args.dry_run:
            print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
            return 0
        api_key = os.environ.get("ARK_API_KEY")
        if not api_key:
            raise AdapterError("ARK_API_KEY is not configured", "authentication")
        references = [data_url(path) for path in spec["reference_paths"]]
        body = {
            "model": model,
            "prompt": prompt,
            "image": references if len(references) > 1 else references[0],
            "size": spec["size"],
            "output_format": "png",
            "response_format": "b64_json",
            "watermark": False,
        }
        response = call_api(endpoint, api_key, body, args.timeout)
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
