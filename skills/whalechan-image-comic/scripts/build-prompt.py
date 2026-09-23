#!/usr/bin/env python3
"""Build a generation prompt and ordered references from a frozen assignment."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("comic_manage_run", Path(__file__).with_name("manage-run.py"))
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot load run manager")
manage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manage)


def build_prompt(assignment: dict, image: dict) -> str:
    if assignment.get("schema_version") != manage.ASSIGNMENT_SCHEMA_VERSION:
        raise manage.RunError(f"Prompt construction requires schema_version {manage.ASSIGNMENT_SCHEMA_VERSION}")
    if image.get("qa_contract_version") != manage.QA_CONTRACT_VERSION:
        raise manage.RunError(f"Image qa_contract_version must be {manage.QA_CONTRACT_VERSION}")
    if image.get("proportion_check") not in {"measured", "visible-only"}:
        raise manage.RunError("Image proportion_check must be measured or visible-only")
    template_path = manage.SKILL_ROOT / "assets/text-style-templates" / image["text_style"] / "template.md"
    template = template_path.read_text(encoding="utf-8").split("Prompt fragment:")[-1].strip()
    presets, _levels = manage.expression_presets()
    sections = [
        "Create one finished Whale-chan comic. Use references only for their declared roles, never their sample words, joke, pose or composition.",
        "IDENTITY: recognizable humanoid DeepSeek Whale-chan, broad round face, blue-gradient eyes, deep-blue hair with cyan curled ends, paired whale-fin ears, forward ahoge and one coherent whale tail. Preserve the source-specific comic turn through her assigned action, language or reaction; do not invent a different motive.",
        f"FACT ANCHOR: {image['fact_anchor']}\nPREMISE: {image['premise']}\nPUNCHLINE: {image['punchline']}\nVISUAL SECOND HIT: {image['why_funny']}",
        f"PANELS: {image['panel_count']}, {image['layout']}. Read left to right then top to bottom, with clear gutters and intentional crops.",
    ]
    sections.append("SOURCE INTERPRETATION: " + json.dumps(assignment["input"]["source_analysis"], ensure_ascii=False))
    sections.append("COMPOSITION: " + json.dumps(image["composition"], ensure_ascii=False)
                    + "\nEXECUTION: " + image["execution_note"]
                    + "\nThis framing and placement override sample layouts in typography references.")
    for action, expression in zip(image["action_plan"], image["expression_plan"], strict=True):
        preset = presets[expression["preset"]]
        sections.append(
            f"PANEL {action['panel']}: {action['action']}\nEXPRESSION: {expression['preset']}, {expression['performance']}. "
            f"Visible cues: {', '.join(preset['face_cues'])}. Forbidden cues: {', '.join(preset['forbidden_cues'])}."
        )
    sections.append(
        "PROPORTION: " + json.dumps(image["proportion"], ensure_ascii=False)
        + "\nPreserve this skeleton across panels; exclude hair/headwear from head height. Fit props to her reach rather than elongating limbs. "
        + ("Keep assessable full-body landmarks in the planned shot."
           if image["proportion_check"] == "measured"
           else "Keep the planned intentional close-up or partial-body framing; do not add a full-body inset for measurement. Maintain visible proportions.")
    )
    for field in ("style", "costume", "background"):
        sections.append(f"{field.upper()}: {json.dumps(image[field], ensure_ascii=False)}. Only references with this role may control this field.")
    sections.append(
        f"TEXT TEMPLATE: {image['text_style']}\nSELECTION REASON: {image['text_style_reason']}\n{template}\n"
        f"LANGUAGE: {assignment['input']['language']}. Apply the visual lettering treatment in this language even if the reference or template mentions another language. "
        "Use one primary treatment, adapted to the assigned speech/thought/caption ownership. Typography controls lettering, not camera, panel count, cast placement or text placement. Do not merge different speakers into one balloon or replace the selected treatment with another template."
    )
    sections.append("EXACT VISIBLE TEXT, including punctuation, in reading order:\n" + json.dumps(image["core_text"], ensure_ascii=False, indent=2))
    for line in image["dialogue_plan"]:
        sections.append(
            f"TEXT {line['text_index']} in panel {line['panel']}: speaker={line['speaker']}; delivery={line['delivery']}; "
            f"wording={json.dumps(image['core_text'][line['text_index']], ensure_ascii=False)}. "
            "Point speech tails and thought connectors to this speaker; captions have no speaker tail. The reserved device speaker is the in-scene device, not Whale-chan."
        )
    sections.append("CAST: Whale-chan is the protagonist. Only supporting roles explicitly declared below may appear. Keep them subordinate in visual detail, but let their assigned speech, reaction and actions remain legible.")
    for member in image["cast_plan"]:
        representation = member["representation"]
        directions = {
            "physical": "Draw a bodily present, low-detail, desaturated indigo figure with a blank round head, no hair or clothing design. Its speech belongs to this figure, never an off-panel substitute.",
            "avatar": "Draw only the assigned flat avatar on its carrier. This is not an in-scene bodily participant.",
            "offscreen": "This role is deliberately outside the frame. Route only its assigned speech/thought offscreen; do not transfer it to Whale-chan.",
            "absent": "This role is deliberately omitted from this adaptation and has no dialogue or visual appearance.",
        }
        sections.append(
            f"ROLE {member['participant']}: {representation}, panels={member['panels']}. {directions[representation]}\n"
            f"STAGING: {member['staging']}\nNARRATIVE REASON: {member['reason']}"
        )
    sections.append("REFERENCE ROLES:\n" + "\n".join(
        f"Reference {index}: {', '.join(reference['roles'])}. {reference['instruction']}"
        for index, reference in enumerate(image["references"], 1)
    ))
    sections += [
        "FINISH: coherent anatomy, hands, feet, tail and contact. No accidental crops, watermark, copied sample text, unassigned dialogue, pseudo-writing or decorative empty bubbles. Props have no lettering unless specified in exact visible text. Use clear nonverbal symbols only when they serve the joke.",
        "OUTPUT: opaque RGB PNG. " + json.dumps(image["output"], ensure_ascii=False) + ". Recommended resolution is not an exact-size requirement; explicit dimensions are.",
    ]
    return "\n\n".join(sections) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", help="Defaults to the image's staging/prompt-01.txt; never overwritten")
    args = parser.parse_args()
    try:
        run, assignment, _manifest = manage.load_run(args.run_dir)
        image = next((item for item in assignment["images"] if item["id"] == args.image), None)
        if image is None:
            raise manage.RunError(f"Unknown image id: {args.image}")
        prompt = build_prompt(assignment, image)
        destination = Path(args.output).resolve() if args.output else run / "staging" / args.image / "prompt-01.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(prompt)
        print(json.dumps({"prompt_file": str(destination), "references": [item["path"] for item in image["references"]]}, ensure_ascii=False, indent=2))
    except (manage.RunError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
