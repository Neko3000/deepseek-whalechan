#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the Volcengine Ark Seedream API."""

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

from output_contract import parse_output


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


def effective_size(output: dict[str, Any]) -> str:
    native_sizes = {"1:1": (1024, 1024), "9:16": (1024, 1792)}
    ratio = output["aspect_ratio"]
    if ratio not in native_sizes:
        raise AdapterError(
            "Seedream adapter supports only 1:1 and 9:16",
            "capability",
        )
    native = native_sizes[ratio]
    resolution = output["resolution"]
    if resolution["mode"] == "explicit":
        requested = (resolution["width"], resolution["height"])
        if requested != native:
            raise AdapterError(
                "Seedream explicit resolution must match its verified native size",
                "capability",
            )
    return f"{native[0]}x{native[1]}"


def mime(path: Path) -> str:
    return (mimetypes.guess_type(path.name)[0] or "image/png").lower()


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
        size = effective_size(spec["output"])
        model = args.model or os.environ.get(
            "SEEDREAM_IMAGE_MODEL", "doubao-seedream-5-0-lite-260128"
        )
        base_url = os.environ.get(
            "SEEDREAM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
        ).rstrip("/")
        endpoint = f"{base_url}/images/generations"
        output = Path(args.output).resolve()
        summary = {
            "provider": "seedream",
            "model": model,
            "endpoint": endpoint,
            "reference_paths": [str(path) for path in spec["reference_paths"]],
            "references": spec["references"],
            "prompt_sha256": hashlib.sha256(spec["prompt"].encode("utf-8")).hexdigest(),
            "requested_output": spec["output"],
            "size": size,
            "output": str(output),
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
            "prompt": spec["prompt"],
            "image": references if len(references) > 1 else references[0],
            "size": size,
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
