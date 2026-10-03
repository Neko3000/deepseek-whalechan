#!/usr/bin/env python3
"""Generate one Whale-chan candidate through the local Codex CLI's built-in ImageGen."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any



IMAGE_MODEL = "gpt-image"
REASONING_EFFORT = "low"
SAFETY_MARKERS = ("safety", "moderation", "policy", "content_filter", "blocked")
QUOTA_MARKERS = ("usage limit", "quota", "insufficient", "billing")
RATE_MARKERS = ("rate limit", "rate_limit", "too many requests", "429")
# Specific phrases only: a bare "login" also appears in unrelated service errors.
AUTH_MARKERS = ("not logged in", "please log in", "login required", "unauthorized", "401", "authentication failed")


class AdapterError(RuntimeError):
    def __init__(self, message: str, category: str = "service") -> None:
        super().__init__(message)
        self.category = category


REFERENCE_ROLES = {
    "identity", "style", "pose_action", "composition",
    "costume", "background", "typography", "proportion",
}


def load_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"Cannot read request JSON: {exc}", "capability") from exc
    if not isinstance(value, dict) or not isinstance(value.get("prompt"), str) or not value["prompt"].strip():
        raise AdapterError("request.prompt must be a non-empty string", "capability")
    if value.keys() - {"prompt", "references", "aspect_ratio", "resolution", "output", "quality"}:
        raise AdapterError("request contains unsupported fields", "capability")
    refs = value.get("references")
    if not isinstance(refs, list) or not refs:
        raise AdapterError("request.references must contain at least 1 reference", "capability")
    audited: list[dict[str, Any]] = []
    for index, item in enumerate(refs):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"].strip():
            raise AdapterError(f"request.references[{index}].path must be a non-empty string", "capability")
        roles = item.get("roles")
        if (
            not isinstance(roles, list) or not roles
            or any(not isinstance(role, str) for role in roles)
            or len(set(roles)) != len(roles) or not set(roles) <= REFERENCE_ROLES
        ):
            raise AdapterError(f"request.references[{index}].roles contains an invalid or duplicate role", "capability")
        instruction = item.get("instruction")
        if instruction is not None and not isinstance(instruction, str):
            raise AdapterError(f"request.references[{index}].instruction must be a string", "capability")
        ref = Path(item["path"])
        if not ref.is_absolute():
            ref = (path.parent / ref).resolve()
        if not ref.is_file():
            raise AdapterError(f"Reference image does not exist: {ref}", "capability")
        if item.get("sha256") is not None:
            if item["sha256"].lower() != hashlib.sha256(ref.read_bytes()).hexdigest():
                raise AdapterError(f"request.references[{index}].sha256 does not match the reference image", "capability")
        audited.append({
            "id": item.get("id", f"reference-{index + 1}"),
            "path": str(ref),
            "roles": roles,
            "instruction": instruction,
            "sha256": item.get("sha256"),
        })
    output = value.get("output")
    if not isinstance(output, dict) or set(output) != {"format", "alpha"} or output.get("format") != "png":
        raise AdapterError("request.output must contain exactly format png and alpha", "capability")
    if not isinstance(output.get("alpha"), bool):
        raise AdapterError("request.output.alpha must be a boolean", "capability")
    if output["alpha"]:
        raise AdapterError(
            "Codex ImageGen transparent output is not verified; alpha needs the next provider",
            "capability",
        )
    aspect_ratio = value.get("aspect_ratio")
    if not isinstance(aspect_ratio, str) or re.fullmatch(r"[1-9]\d*:[1-9]\d*", aspect_ratio) is None:
        raise AdapterError("request.aspect_ratio must be a positive WIDTH:HEIGHT ratio", "capability")
    resolution = value.get("resolution")
    if not isinstance(resolution, dict) or set(resolution) != {"mode", "width", "height"}:
        raise AdapterError("request.resolution must contain exactly mode, width, and height", "capability")
    if resolution["mode"] == "exact":
        raise AdapterError(
            "Codex ImageGen exposes no pixel-size control; exact resolution needs the next provider",
            "capability",
        )
    if resolution["mode"] != "provider-native" or resolution["width"] is not None or resolution["height"] is not None:
        raise AdapterError("provider-native resolution requires null width and height", "capability")
    value["references"] = audited
    value["requested_output"] = {
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "output": output,
    }
    return value


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def run_quiet(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AdapterError(f"{' '.join(command[:2])} timed out after {timeout}s", "timeout") from exc
    except OSError as exc:
        raise AdapterError(f"Cannot run {command[0]}: {exc}", "unavailable") from exc


def check_codex() -> dict[str, Any]:
    executable = shutil.which("codex")
    if executable is None:
        raise AdapterError("Codex CLI is not installed or not on PATH", "unavailable")
    version = run_quiet([executable, "--version"], 30)
    status = run_quiet([executable, "login", "status"], 30)
    detail = (status.stdout + status.stderr).strip()
    if status.returncode != 0 or "logged in" not in detail.lower() or "not logged in" in detail.lower():
        raise AdapterError(f"Codex CLI is not logged in: {detail[:300]}", "authentication")
    return {
        "executable": executable,
        "version": version.stdout.strip() or version.stderr.strip(),
        "login": detail.splitlines()[0] if detail else "",
    }


def build_instruction(spec: dict[str, Any]) -> str:
    lines = [
        "Call your built-in image generation tool exactly once, passing the text between "
        "<prompt> tags verbatim as the image prompt and including every attached image. "
        "Do not run shell commands, edit files, or rewrite the prompt.",
        "",
        "Attached images, in order:",
    ]
    for index, ref in enumerate(spec["references"], start=1):
        note = ref["instruction"] or "use only for the declared roles"
        lines.append(f"- Image {index} ({', '.join(ref['roles'])}): {note}")
    lines.extend([
        "",
        "After the tool returns, reply with only DONE.",
        "",
        "<prompt>",
        spec["prompt"].strip(),
        "</prompt>",
        "",
    ])
    return "\n".join(lines)


def codex_command(executable: str, workdir: Path, references: list[dict[str, Any]]) -> list[str]:
    command = [
        executable, "exec", "--skip-git-repo-check", "-s", "read-only", "--json",
        "-C", str(workdir), "-c", f'model_reasoning_effort="{REASONING_EFFORT}"',
    ]
    for ref in references:
        command.extend(["-i", ref["path"]])
    # `-i` accepts several values; `--` stops it from swallowing the stdin marker.
    command.extend(["--", "-"])
    return command


def classify_text(text: str, *, image_failure: bool = False) -> str:
    lowered = text.lower()
    # Safety is only inferred from an ImageGen failure, never from general CLI noise.
    if image_failure and any(marker in lowered for marker in SAFETY_MARKERS):
        return "safety_rejection"
    for markers, category in (
        (QUOTA_MARKERS, "quota"),
        (RATE_MARKERS, "rate_limit"),
        (AUTH_MARKERS, "authentication"),
    ):
        if any(marker in lowered for marker in markers):
            return category
    return "service"


def parse_events(stdout: str) -> tuple[str | None, list[str]]:
    thread_id = None
    failures: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "thread.started":
            thread_id = event.get("thread_id")
        elif kind in {"turn.failed", "error"}:
            error = event.get("error") or event
            failures.append(str(error.get("message") or error))
    return thread_id, failures


def find_rollout(home: Path, thread_id: str) -> Path | None:
    for _ in range(10):
        matches = sorted(home.glob(f"sessions/*/*/*/rollout-*{thread_id}.jsonl"))
        if matches:
            return matches[-1]
        time.sleep(0.5)
    return None


def read_rollout(path: Path) -> dict[str, Any]:
    generations: list[dict[str, Any]] = []
    attached = 0
    tool_images: int | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(line).get("payload", {})
        except json.JSONDecodeError:
            continue
        item = payload.get("item") or {}
        if item.get("kind") == "image_gen.generation":
            generations.append(item)
        elif payload.get("type") == "message" and payload.get("role") == "user":
            attached = max(attached, sum(
                1 for part in payload.get("content", []) if part.get("type") == "input_image"
            ))
        elif payload.get("type") == "custom_tool_call" and "image_gen" in str(payload.get("input")):
            # ImageGen receives references either as recent attachments or as explicit paths.
            call = payload["input"]
            recent = re.search(r"num_last_images_to_include\s*:\s*(\d+)", call)
            paths = re.search(r"referenced_image_paths\s*:\s*\[(.*?)\]", call, re.S)
            tool_images = (int(recent.group(1)) if recent else 0) + (
                len(re.findall(r'"(?:[^"\\]|\\.)*"', paths.group(1))) if paths else 0
            )
    return {"generations": generations, "attached_images": attached, "tool_reference_images": tool_images}


def usable_verdict(prompt_verbatim: bool | None, tool_images: int | None, expected: int) -> bool | None:
    """False: prompt rewritten or references dropped. None: the session record could not verify either."""
    if prompt_verbatim is False or tool_images not in (None, expected):
        return False
    if prompt_verbatim is None or tool_images is None:
        return None
    return True


def copy_once(source: Path, destination: Path) -> None:
    if destination.exists():
        raise AdapterError(f"Output already exists: {destination}", "capability")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copyfile(source, temp_name)
        os.replace(temp_name, destination)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def write_json_once(path: Path, value: dict[str, Any]) -> None:
    if path.exists():
        raise AdapterError(f"Audit file already exists: {path}", "capability")
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate(spec: dict[str, Any], codex: dict[str, Any], output: Path, audit_path: Path, timeout: int) -> dict[str, Any]:
    instruction = build_instruction(spec)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="whalechan-codex-") as workdir:
        command = codex_command(codex["executable"], Path(workdir), spec["references"])
        try:
            completed = subprocess.run(
                command, input=instruction, capture_output=True, text=True, timeout=timeout, cwd=workdir
            )
        except subprocess.TimeoutExpired as exc:
            raise AdapterError(f"codex exec timed out after {timeout}s", "timeout") from exc
    thread_id, failures = parse_events(completed.stdout)
    if thread_id is None:
        detail = (completed.stderr or completed.stdout).strip()[-1000:]
        raise AdapterError(f"codex exec did not start a thread: {detail}", classify_text(detail))
    home = codex_home()
    rollout = find_rollout(home, thread_id)
    evidence = read_rollout(rollout) if rollout else {
        "generations": [], "attached_images": None, "tool_reference_images": None,
    }
    generations = evidence["generations"]
    for item in generations:
        if item.get("failure"):
            raise AdapterError(f"Codex ImageGen failed: {item['failure']}", classify_text(str(item["failure"]), image_failure=True))
    saved = [Path(item["savedPath"]) for item in generations if item.get("savedPath")]
    revised = generations[0].get("revisedPrompt") if generations else None
    if not saved:
        # Rollout format is not a public contract; fall back to the thread's image directory.
        saved = sorted((home / "generated_images" / thread_id).glob("*.png"))
    if not saved:
        detail = "; ".join(failures) or (completed.stderr or "").strip()[-1000:] or "no image was produced"
        raise AdapterError(f"Codex returned no image (thread {thread_id}): {detail}", classify_text(detail))
    source = saved[0]
    if not source.is_file():
        raise AdapterError(f"Codex image is missing on disk: {source}", "service")
    copy_once(source, output)
    prompt_verbatim = None if revised is None else revised.strip() == spec["prompt"].strip()
    audit = {
        "provider": "codex",
        "transport": "cli",
        "model": IMAGE_MODEL,
        "codex_version": codex["version"],
        "thread_id": thread_id,
        "rollout_path": str(rollout) if rollout else None,
        "saved_path": str(source),
        "generation_count": len(saved),
        "attached_images": evidence["attached_images"],
        "tool_reference_images": evidence["tool_reference_images"],
        "expected_reference_images": len(spec["references"]),
        "prompt_sha256": hashlib.sha256(spec["prompt"].strip().encode("utf-8")).hexdigest(),
        "prompt_verbatim": prompt_verbatim,
        "revised_prompt": revised,
        "references": spec["references"],
        "requested_output": spec["requested_output"],
        "output": str(output),
        "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "duration_seconds": round(time.time() - started, 1),
    }
    audit["usable"] = usable_verdict(prompt_verbatim, audit["tool_reference_images"], len(spec["references"]))
    write_json_once(audit_path, audit)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only report whether Codex CLI can be used")
    parser.add_argument("--request")
    parser.add_argument("--output")
    parser.add_argument("--audit", help="Audit JSON path; defaults to <output>.codex.json")
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.check:
            print(json.dumps({"ok": True, "provider": "codex", "transport": "cli", **check_codex()}, ensure_ascii=False, indent=2))
            return 0
        if not args.request or not args.output:
            parser.error("--request and --output are required unless --check is used")
        spec = load_request(Path(args.request).resolve())
        output = Path(args.output).resolve()
        audit_path = Path(args.audit).resolve() if args.audit else output.with_name(output.name + ".codex.json")
        if args.dry_run:
            executable = shutil.which("codex") or "codex"
            print(json.dumps({
                "ok": True, "provider": "codex", "transport": "cli", "model": IMAGE_MODEL,
                "command": codex_command(executable, Path("<temporary-directory>"), spec["references"]),
                "instruction": build_instruction(spec),
                "references": spec["references"], "requested_output": spec["requested_output"],
                "output": str(output), "audit": str(audit_path), "dry_run": True,
            }, ensure_ascii=False, indent=2))
            return 0
        for path in (output, audit_path):
            if path.exists():
                raise AdapterError(f"Output already exists: {path}", "capability")
        audit = generate(spec, check_codex(), output, audit_path, args.timeout)
        print(json.dumps({"ok": True, "audit": str(audit_path), **{
            key: audit[key] for key in (
                "provider", "transport", "model", "thread_id", "prompt_verbatim", "usable",
                "tool_reference_images", "expected_reference_images", "output", "output_sha256",
                "duration_seconds",
            )
        }}, ensure_ascii=False, indent=2))
        return 0
    except AdapterError as exc:
        print(json.dumps({"ok": False, "category": exc.category, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
