#!/usr/bin/env python3
"""Build the deterministic machine-readable catalog for bundled assets."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FORM_AUTHORITY = ROOT / "references" / "form-authority.json"
OUTPUT = ROOT / "references" / "asset-catalog.json"
ALLOWED = {".png", ".jpg", ".jpeg", ".webp", ".md"}
FORM_ORDER = ("standard", "compact", "semi-chibi", "chibi", "super-deformed")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def classify(relative: Path) -> tuple[str, str | None]:
    parts = relative.parts
    category = parts[0]
    if category == "character-references":
        return "character", parts[1]
    if category == "comic-references":
        return "comic", None
    if category == "text-style-templates":
        return "text-style", parts[1]
    if category == "supporting-character-references":
        return "supporting-character", None
    raise ValueError(f"Unexpected asset category: {relative}")


def load_character_forms() -> dict[str, dict[str, object]]:
    value = json.loads(FORM_AUTHORITY.read_text(encoding="utf-8"))
    forms = value.get("character_forms")
    if set(value) != {"schema_version", "character_forms"}:
        raise ValueError("form-authority.json contains unsupported fields")
    if value.get("schema_version") != 1 or not isinstance(forms, dict):
        raise ValueError("form-authority.json must use schema_version 1")
    if tuple(forms) != FORM_ORDER:
        raise ValueError("form-authority.json must define all five forms in order")

    actual = {
        path.relative_to(ASSETS / "character-references").as_posix()
        for path in (ASSETS / "character-references").glob("*/*.webp")
    }
    if len(actual) != 15 or any(path.split("/", 1)[0] not in FORM_ORDER for path in actual):
        raise ValueError("character references must contain exactly three images for each form")
    normalized = {}
    for form, profile in forms.items():
        if not isinstance(profile, dict):
            raise ValueError(f"character form {form} must be an object")
        primary = profile.get("primary")
        mean = profile.get("mean_head_ratio")
        acceptance = profile.get("acceptance_range")
        if (
            not isinstance(primary, str)
            or not primary.startswith(f"{form}/")
            or primary not in actual
            or isinstance(mean, bool)
            or not isinstance(mean, (int, float))
            or not isinstance(acceptance, list)
            or len(acceptance) != 2
            or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in acceptance)
            or not acceptance[0] <= mean <= acceptance[1]
        ):
            raise ValueError(f"character form {form} has invalid authority metadata")
        form_paths = {path for path in actual if path.startswith(f"{form}/")}
        if len(form_paths) != 3:
            raise ValueError(f"character form {form} must contain exactly three references")
        normalized[form] = {
            "primary": f"assets/character-references/{primary}",
            "mean_head_ratio": mean,
            "acceptance_range": acceptance,
        }
    return normalized


def main() -> int:
    character_forms = load_character_forms()
    entries = []
    for path in sorted(item for item in ASSETS.rglob("*") if item.is_file()):
        if path.suffix.lower() not in ALLOWED:
            continue
        relative = path.relative_to(ASSETS)
        kind, variant = classify(relative)
        entries.append(
            {
                "path": (Path("assets") / relative).as_posix(),
                "kind": kind,
                "variant": variant,
                "sha256": digest(path),
            }
        )
    value = {
        "schema_version": 3,
        "asset_count": len(entries),
        "character_forms": character_forms,
        "assets": entries,
    }
    fd, temporary = tempfile.mkstemp(prefix=".asset-catalog.", dir=OUTPUT.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, OUTPUT)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
    print(json.dumps({"output": str(OUTPUT), "asset_count": len(entries)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
