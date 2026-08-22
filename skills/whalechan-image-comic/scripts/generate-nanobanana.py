#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the Gemini Nano Banana API."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
import os
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
    unsupported = set(value) - {"prompt", "references", "reference_paths", "output"}
    if unsupported:
        raise AdapterError("request contains unsupported fields", "capability")
    value["reference_paths"] = resolved
    value["references"] = audited
    return value


def mime(path: Path) -> str:
    return mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def classify_http(status: int, detail: str) -> str:
    lowered = detail.lower()
    if status in {401, 403}:
        return "authentication"
    if status == 429:
        return "quota" if "quota" in lowered or "billing" in lowered else "rate_limit"
    if "safety" in lowered or "blocked" in lowered:
        return "safety_rejection"
    if status >= 500:
        return "service"
    return "capability"


def call_api(url: str, api_key: str, body: dict[str, Any], timeout: int) -> dict[str, Any]:
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
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


def extract_image(response: dict[str, Any]) -> bytes:
    if isinstance(response.get("error"), dict):
        error = response["error"]
        raise AdapterError(str(error.get("message") or error.get("status") or "provider error"))
    for candidate in response.get("candidates", []):
        finish_reason = str(candidate.get("finishReason", ""))
        if finish_reason in {"SAFETY", "PROHIBITED_CONTENT"}:
            raise AdapterError(f"Generation blocked: {finish_reason}", "safety_rejection")
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                return base64.b64decode(inline["data"], validate=True)
    raise AdapterError("Nano Banana response contained no image", "service")


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


def provider_settings(output: dict[str, Any]) -> tuple[str, str]:
    if output["aspect_ratio"] not in {"1:1", "9:16"}:
        raise AdapterError(
            "Nano Banana adapter supports only 1:1 and 9:16",
            "capability",
        )
    resolution = output["resolution"]
    if resolution["mode"] != "auto":
        raise AdapterError(
            "Nano Banana cannot guarantee an explicit pixel resolution",
            "capability",
        )
    recommended = resolution["recommended"]
    if recommended is None:
        image_size = "1K"
    else:
        longest_edge = max(dimensions(recommended))
        if longest_edge <= 512:
            image_size = "512"
        elif longest_edge <= 1024:
            image_size = "1K"
        elif longest_edge <= 2048:
            image_size = "2K"
        else:
            image_size = "4K"
    return output["aspect_ratio"], image_size


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
        aspect_ratio, image_size = provider_settings(spec["output"])
        model = args.model or os.environ.get("NANO_BANANA_IMAGE_MODEL", "gemini-3.1-flash-image")
        model = model.removeprefix("models/")
        base_url = os.environ.get(
            "GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1"
        ).rstrip("/")
        output = Path(args.output).resolve()
        endpoint = f"{base_url}/models/{model}:generateContent"
        summary = {
            "provider": "nano-banana",
            "model": model,
            "endpoint": endpoint,
            "reference_paths": [str(path) for path in spec["reference_paths"]],
            "references": spec["references"],
            "prompt_sha256": hashlib.sha256(spec["prompt"].encode("utf-8")).hexdigest(),
            "requested_output": spec["output"],
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "output": str(output),
            "dry_run": args.dry_run,
        }
        if args.dry_run:
            print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
            return 0
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise AdapterError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured", "authentication")
        parts: list[dict[str, Any]] = [{"text": spec["prompt"]}]
        for ref in spec["reference_paths"]:
            parts.append(
                {
                    "inlineData": {
                        "mimeType": mime(ref),
                        "data": base64.b64encode(ref.read_bytes()).decode("ascii"),
                    }
                }
            )
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": image_size,
                },
            },
        }
        response = call_api(endpoint, api_key, body, args.timeout)
        image = extract_image(response)
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
