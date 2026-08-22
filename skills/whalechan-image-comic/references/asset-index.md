# Asset selection index

Use `asset-catalog.json` as path and SHA-256 authority. Use this file for semantic routing.

## Character references

Always place the selected identity-anchor primary first. Declare its roles explicitly. Add bundled or user references only when they control a needed field, keeping the effective provider set at five or fewer.

| Form | File | Role and tags |
| --- | --- | --- |
| standard | `01_gentle_wave.webp` | **primary**; standing, gentle wave, full-body identity |
| standard | `03_light_turning_step.webp` | turn, step, dynamic skirt |
| standard | `05_side_reclining_pose.webp` | side reclining, full-body bend, floor contact |
| compact | `0102_intimate_relationship_question_rendered_isolated.webp` | **primary**; standing, conversation, composed |
| compact | `0080_lounging_on_chair_rendered_isolated.webp` | chair, seated, relaxed, lazy |
| compact | `04_light_turn.webp` | turn, short step, dynamic skirt |
| semi-chibi | `0092_enduring_release_delay_rendered_isolated.webp` | **primary**; standing, emotional, front view |
| semi-chibi | `0015_data_still_in_brain_rendered_isolated.webp` | gesture, pointing at head, explanation |
| semi-chibi | `0076_sitting_ready_on_chair_rendered_isolated.webp` | chair, seated, attentive |
| chibi | `0067_angry_you_are_silly_reply_rendered_isolated.webp` | **primary**; anger, pointing, wide stance |
| chibi | `0054_rice_identity_comic_rendered_isolated.webp` | rice bowl, food, raised fist |
| chibi | `0057_patting_full_belly_rendered_isolated.webp` | reclining, full belly, food, lazy |
| super-deformed | `0019_literal_love_reply_rendered_isolated.webp` | **primary**; neutral standing, tiny fists |
| super-deformed | `0040_kicked_from_chair_rendered_isolated.webp` | airborne, panic, chair, flailing |
| super-deformed | `0081_stranded_on_floor_rendered_isolated.webp` | prone, exhaustion, floor contact |

All paths begin with `assets/character-references/<form>/`.

## Comic references

| File | Panel/layout | Comedy, emotion, and composition tags |
| --- | --- | --- |
| `0014_shy_refusal_rendered.webp` | 1; text left, character right | shy denial, pleading, blue sticker headline |
| `0015_data_still_in_brain_rendered.webp` | 1; large bubble + full body | excuse, keyword reveal, cheerful spin |
| `0017_refusing_to_think_rendered.webp` | 1; close-up + UI-like card | blunt answer, meta AI, shameless refusal |
| `0018_improvised_user_reply_rendered.webp` | 1; top banner + dual reaction | confident improvisation, ghosted panic self |
| `0019_literal_love_reply_rendered.webp` | 1; dialogue + faded inner self | literal response, carbon-based thinking, two-layer reaction |
| `0021_blunt_reasoning_reply_rendered.webp` | 1; thought bubble + close-up | deadpan insult, reasoning-time contrast |
| `0031_holding_unknown_symbol_rendered.webp` | 1; speech + prop | literal misunderstanding, curiosity, sign prop |
| `0043_holding_rice_bowl_and_chopsticks_rendered.webp` | 1; headline above | food identity, loud boast, dynamic prop |
| `0047_bringing_rice_to_programmer_rendered.webp` | 1; two-character scene | programmer, food, walking, casual dialogue |
| `0049_kneeling_beside_empty_bowl_rendered.webp` | 1; off-panel accusation | confrontation, crying denial, empty bowl |
| `0051_kneeling_proud_beside_bowl_rendered.webp` | 1; off-panel accusation | confrontation, proud comeback, empty bowl |
| `0052_mocking_inferior_model_rendered.webp` | 1; close-up + bottom punch | model rivalry, smug mockery, pointing down |
| `0057_patting_full_belly_rendered.webp` | 1; reclined dialogue | food, belly, affectionate laziness |
| `0058_lounging_on_whale_sofa_rendered.webp` | 1; large top headline | extreme laziness, sofa, checklist, props |
| `0078_saluting_for_deepseek_rendered.webp` | 1; portrait + bottom declaration | serious oath, deadpan loyalty, poster text |

All paths begin with `assets/comic-references/`.

For 2- and 4-panel requests, select the closest single-panel action/style reference and describe the panel layout explicitly. Do not pretend a one-panel reference defines multi-panel order.

## Text-style references

Use the routing table in `text-style-routing.md` for every task. Load exactly one selected `reference.webp` as the sole `typography` reference and read its `template.md` for prompt language.

## User references

User images are allowed. Every reference must declare one or more roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`, plus an instruction when roles overlap. Explicit user instructions outrank references. During initialization, copy external references into the run and bind their paths and SHA-256 hashes. Do not let a reference silently affect undeclared fields.

The canonical identity anchor stays first. When style, costume, or proportion is custom, remove that role from the identity anchor even though the pixels still depict the canonical default. Custom ratios normally have no `proportion` reference.

## Supporting-character references

- `abstract-user-pose-sheet.webp`: the only supporting-character image reference; identity sheet for accusation, kneeling defeat, open-arm contact, and neutral sweat.

Load it only when a supporting character appears. Specify pointing, kneeling, hugging, facing, scale, side, and every other interaction in the prompt as text. Do not load another image for interaction or composition.
