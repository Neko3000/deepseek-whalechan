#!/usr/bin/env python3
"""Export completed runs to an offline gallery; never mutate run records."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

SKILL_ROOT = Path(__file__).resolve().parents[1]
COMIC = SKILL_ROOT.name == "whalechan-image-comic"


class GalleryError(ValueError):
    pass


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def as_text(value):
    if value is None:
        return ""
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


class RunReader:
    def __init__(self, run, assets):
        self.run = run
        self.assets = assets
        self.warnings = []
        self.assignment = read_json(run / "assignment.json")
        self.manifest = read_json(run / "manifest.json")
        if self.assignment.get("schema_version") not in ({10, 11} if COMIC else {5}):
            raise GalleryError(f"Unsupported assignment schema: {run.name}")
        if self.manifest.get("schema_version") != (1 if COMIC else 3):
            raise GalleryError(f"Unsupported manifest schema: {run.name}")
        if self.manifest.get("status") not in {"complete", "partial", "complete_with_failures"}:
            raise GalleryError(f"Finalize the run before exporting: {run.name}")
        if digest(run / "assignment.json") != self.manifest.get("assignment_sha256"):
            raise GalleryError(f"Assignment hash mismatch: {run.name}")
        ids = [item["id"] for item in self.assignment["images"]]
        if len(ids) != len(set(ids)) or set(ids) != set(self.manifest["images"]):
            raise GalleryError(f"Image inventory mismatch: {run.name}")

    def locate(self, value, external=False):
        if not value:
            return None
        path = Path(value)
        old_root = Path(self.assignment.get("run_dir", str(self.run)))
        candidates = []
        if path.is_absolute() and path.is_relative_to(old_root):
            candidates.append(self.run / path.relative_to(old_root))
        if not path.is_absolute():
            candidates.append(self.run / path)
        if external:
            candidates.append(path if path.is_absolute() else SKILL_ROOT / path)
            original = self.assignment.get("source_assignment")
            if original and not path.is_absolute():
                candidates.append(Path(original).parent / path)
        for candidate in candidates:
            resolved = candidate.resolve()
            if (external or resolved.is_relative_to(self.run)) and resolved.is_file():
                return resolved
        return None

    def picture(self, path, label, expected=None):
        if path is None:
            self.warnings.append(f"{label}：图片文件缺失")
            return {"label": label, "src": None}
        sha = digest(path)
        if expected and sha != expected:
            raise GalleryError(f"Image hash mismatch: {label}")
        result = subprocess.run(["magick", "identify", "-ping", "-format", "%m %w %h", f"{path}[0]"],
                                check=True, capture_output=True, text=True, timeout=30)
        format_name, width, height = result.stdout.split()
        extension = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp", "GIF": "gif"}.get(format_name)
        width, height = int(width), int(height)
        if extension is None:
            raise GalleryError(f"Unsupported image format: {label}")
        name = f"{sha}.{extension}"
        target = self.assets / name
        if not target.exists():
            shutil.copyfile(path, target)
        return {"label": label, "src": f"assets/{name}", "width": width, "height": height}

    def sidecar(self, value, label, json_file=False):
        if isinstance(value, dict):
            return value
        path = self.locate(value)
        if path is None:
            self.warnings.append(f"{label}：记录缺失")
            return {} if json_file else ""
        return read_json(path) if json_file else path.read_text(encoding="utf-8")

    def attempt(self, record):
        key = record.get("attempt_id") or record.get("derived_id") or str(record.get("candidate_attempt", ""))
        role = record.get("role", "candidate")
        qa = self.sidecar(record.get("visual_qa"), f"{key} 验收", True)
        auto = self.sidecar(record.get("automatic_qa"), f"{key} 自动验收", True)
        prompt = "" if role == "composite" else (
            self.sidecar(record.get("prompt"), f"{key} 提示词") if COMIC else record.get("prompt", ""))
        picture = self.picture(self.locate(record.get("candidate", record.get("candidate_path"))),
                               f"{key} 候选", record.get("candidate_sha256"))
        return {"id": key, "role": role, "picture": picture,
                "sha256": record.get("candidate_sha256"), "prompt": prompt,
                "provider": record.get("provider"), "model": record.get("model"),
                "verdict": record.get("verdict"), "created_at": record.get("created_at"),
                "defects": qa.get("defects"), "targeted_retry": qa.get("targeted_retry"),
                "automatic": auto.get("overall"), "visual": qa.get("verdict"),
                "sources": record.get("source_attempts", [])}

    def image(self, spec):
        state = self.manifest["images"][spec["id"]]
        records = state.get("attempts", []) + state.get("derived", [])
        attempts = [self.attempt(record) for record in records]
        final = None
        if state.get("status") == "passed":
            final = self.picture(self.locate(state.get("final_path")), spec["id"], state.get("final_sha256"))
        matches = [item for item in attempts if item["sha256"] and item["sha256"] == state.get("final_sha256")
                   and item["role"] != "component" and item["verdict"] == "PASS"]
        origin = matches[0] if len(matches) == 1 else None
        if final and not origin:
            reason = "多个候选与成品哈希相同，无法唯一确定提示词；请查看生成过程" if matches else "成品来源记录缺失"
            self.warnings.append(f"{spec['id']}：{reason}")
        return {"id": spec["id"], "name": spec.get("name", spec["id"]),
                "note": spec.get("execution_note", ""), "status": state.get("status"),
                "final": final, "origin": origin, "attempts": attempts,
                "calls": sum(item.get("consumes_candidate_budget", True) is not False
                             for item in state.get("attempts", [])),
                "errors": [{key: error.get(key) for key in ("provider", "model", "category", "details", "created_at")}
                           for error in state.get("provider_errors", [])]}

    def sources(self):
        source = self.assignment.get("input", {})
        content = source.get("content")
        originals = []
        if source.get("type") in {"image", "screenshot"}:
            values = content if isinstance(content, list) else [content]
            for index, value in enumerate(values, 1):
                archived = sorted((self.run / "source").glob(f"original-{index:02d}.*"))
                path = archived[0] if archived else self.locate(value, external=True)
                originals.append(self.picture(path, f"输入原图 {index}"))
            # A source analysis is an interpretation, never the user's original words.
            request = ""
        else:
            request = "\n".join(as_text(item) for item in content) if isinstance(content, list) else as_text(content)
        analysis = source.get("source_analysis", {}).get("source_event", "")
        return request, originals, analysis

    def build(self):
        assignment = self.assignment
        options = assignment.get("proposal", {}).get("options", [])
        counts = {item["choice"]: item["count"] for item in assignment.get("selection", {}).get("choices", [])}
        proposals = []
        assigned = set()
        for option in options:
            specs = [spec for spec in assignment["images"]
                     if (spec.get("idea_id") == option.get("idea_id") if COMIC
                         else spec.get("proposal_choice") == option["choice"])]
            assigned.update(spec["id"] for spec in specs)
            proposals.append({"choice": option["choice"], "title": option["title"],
                              "scene": option.get("scene", ""),
                              "detail": option.get("twist", option.get("action_expression", "")),
                              "selected": option["choice"] in counts,
                              "planned": counts.get(option["choice"], 0),
                              "images": [self.image(spec) for spec in specs]})
        if assigned != set(self.manifest["images"]):
            raise GalleryError(f"Unlinked proposal images: {self.run.name}")
        references = []
        seen = set()
        for spec in assignment["images"]:
            for ref in spec.get("references", []):
                key = (ref.get("sha256") or ref.get("path"), tuple(ref.get("roles", [])))
                if key in seen:
                    continue
                seen.add(key)
                picture = self.picture(self.locate(ref.get("path"), external=True),
                                       ref.get("id", "参考图"), ref.get("sha256"))
                references.append({**picture, "roles": ref.get("roles", [])})
        request, originals, analysis = self.sources()
        images = [image for proposal in proposals for image in proposal["images"]]
        return {"title": assignment["run_name"], "status": self.manifest["status"],
                "date": self.manifest.get("finalized_at", self.manifest.get("completed_at")),
                "request": request, "originals": originals, "analysis": analysis,
                "references": references, "proposals": proposals,
                "planned": len(images), "passed": sum(item["status"] == "passed" for item in images),
                "calls": sum(item["calls"] for item in images),
                "errors": sum(len(item["errors"]) for item in images),
                "warnings": list(dict.fromkeys(self.warnings))}


def export_gallery(run_dirs, output=None):
    runs = [Path(path).resolve() for path in run_dirs]
    if not runs or len(set(runs)) != len(runs):
        raise GalleryError("Supply distinct run directories")
    if len(runs) > 1 and output is None:
        raise GalleryError("Batch export requires --output")
    destination = Path(output).resolve() if output else runs[0] / "gallery"
    base = destination
    number = 2
    while destination.exists():
        destination = base.with_name(f"{base.name}-{number:02d}")
        number += 1
    destination.mkdir(parents=True)
    try:
        assets = destination / "assets"
        assets.mkdir()
        groups = [RunReader(run, assets).build() for run in runs]
        data = {"skill": "comic" if COMIC else "character", "groups": groups,
                "exported_at": datetime.now(timezone.utc).isoformat()}
        template_root = SKILL_ROOT / "assets" / "gallery"
        template = (template_root / "index.html").read_text(encoding="utf-8")
        payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace(
            "\u2028", "\\u2028").replace("\u2029", "\\u2029")
        # Insert data last: user text is never interpreted as HTML or a template token.
        html = template.replace("/* GALLERY_CSS */", (template_root / "gallery.css").read_text(encoding="utf-8"))
        html = html.replace("/* GALLERY_JS */", (template_root / "gallery.js").read_text(encoding="utf-8"))
        html = html.replace("GALLERY_DATA", payload)
        (destination / "index.html").write_text(html, encoding="utf-8")
    except Exception:
        shutil.rmtree(destination)
        raise
    return {"gallery": str(destination / "index.html"), "groups": len(groups),
            "warnings": {str(index + 1): group["warnings"] for index, group in enumerate(groups) if group["warnings"]}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        print(json.dumps(export_gallery(args.run_dir, args.output), ensure_ascii=False, indent=2))
    except (GalleryError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
