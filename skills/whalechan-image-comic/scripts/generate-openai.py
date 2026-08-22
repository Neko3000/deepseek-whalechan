#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the OpenAI Images API."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import mimetypes
import os
import secrets
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from output_contract import dimensions, parse_output


class AdapterError(RuntimeError):
    def __init__(self, message: str, category: str = "service") -> None:
        super().__init__(message)
        self.category = category


def load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Cannot read request JSON: {exc}", "capability") from exc
    if not isinstance(value, dict) or not isinstance(value.get("prompt"), str) or not value["prompt"].strip():
        raise AdapterError("request.prompt must be a non-empty string", "capability")
    refs = value.get("references")
    if not isinstance(refs, list) or not 1 <= len(refs) <= 5:
        raise AdapterError("request references must contain 1 to 5 images", "capability")
    resolved: list[Path] = []
    audited: list[dict[str, Any]] = []
    for index, item in enumerate(refs):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise AdapterError("references require path objects", "capability")
        roles = item.get("roles")
        if not isinstance(roles, list) or not roles or any(not isinstance(role, str) for role in roles):
            raise AdapterError("references require roles", "capability")
        ref_value = item["path"]
        ref = Path(ref_value)
        if not ref.is_absolute():
            ref = (path.parent / ref).resolve()
        if not ref.is_file():
            raise AdapterError(f"Reference image does not exist: {ref}", "capability")
        if item.get("sha256") is not None:
            actual = hashlib.sha256(ref.read_bytes()).hexdigest()
            if item["sha256"] != actual:
                raise AdapterError(f"Reference SHA-256 mismatch: {ref}", "capability")
        resolved.append(ref)
        audited.append({
            "id": item.get("id", f"reference-{index + 1}"),
            "path": str(ref),
            "roles": roles,
            "instruction": item.get("instruction"),
            "sha256": item.get("sha256"),
        })
    value["output"] = parse_output(
        value, lambda message: AdapterError(message, "capability")
    )
    unsupported = set(value) - {
        "prompt", "references", "reference_paths", "output", "quality"
    }
    if unsupported:
        raise AdapterError("request contains unsupported fields", "capability")
    value["reference_paths"] = resolved
    value["references"] = audited
    return value


def size_is_supported(width: int, height: int) -> bool:
    return (
        width % 16 == 0
        and height % 16 == 0
        and max(width, height) <= 3840
        and max(width, height) / min(width, height) <= 3
        and 655_360 <= width * height <= 8_294_400
    )


def effective_size(output: dict[str, Any]) -> str:
    ratio_width, ratio_height = (
        int(item) for item in output["aspect_ratio"].split(":")
    )
    resolution = output["resolution"]
    if resolution["mode"] == "explicit":
        width, height = resolution["width"], resolution["height"]
    else:
        recommended = resolution["recommended"]
        if recommended is not None:
            width, height = dimensions(recommended)
        else:
            ratio = ratio_width / ratio_height
            if ratio >= 1:
                height = 1024
                width = round((height * ratio) / 16) * 16
            else:
                width = 1024
                height = round((width / ratio) / 16) * 16
    if not math.isclose(width / height, ratio_width / ratio_height, rel_tol=0.02):
        raise AdapterError("request.output resolution does not match aspect_ratio", "capability")
    if not size_is_supported(width, height):
        raise AdapterError("request output violates gpt-image-2 size constraints", "capability")
    return f"{width}x{height}"


def mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


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
        size = effective_size(spec["output"])
        model = args.model or os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        output = Path(args.output).resolve()
        summary = {
            "provider": "openai",
            "model": model,
            "endpoint": f"{base_url}/images/edits",
            "reference_paths": [str(path) for path in spec["reference_paths"]],
            "references": spec["references"],
            "prompt_sha256": hashlib.sha256(spec["prompt"].encode("utf-8")).hexdigest(),
            "requested_output": spec["output"],
            "size": size,
            "quality": spec.get("quality", "medium"),
            "output": str(output),
            "dry_run": args.dry_run,
        }
        if args.dry_run:
            print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
            return 0
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise AdapterError("OPENAI_API_KEY is not configured", "authentication")
        payload, content_type = multipart(
            [
                ("model", model),
                ("prompt", spec["prompt"]),
                ("size", size),
                ("quality", spec.get("quality", "medium")),
                ("output_format", "png"),
            ],
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
