# Asset selection index

Use schema v4 `asset-catalog.json` as path and SHA-256 authority. Use this file for semantic routing and `model-characters.json` for registered model identities, aliases, personality and reference selection.

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
| semi-chibi | `neutral_standing_front_isolated.webp` | **primary**; standing, calm neutral expression, front view |
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

- `abstract-user-pose-sheet.webp`: the shared identity sheet for ordinary users, programmers and other abstract indigo people; accusation, kneeling defeat, open-arm contact and neutral sweat.
- `models/<id>/<form>.webp`: 40 original detailed model-character sheets, one for each of eight registered models and five forms. Each sheet shows three views of one actor. Do not use the discarded simplified variants or interpret the views as multiple actors.

| Model id | Identity registry entry |
| --- | --- |
| `claude` | Claude |
| `gpt` | GPT |
| `gemini` | Gemini |
| `grok` | Grok |
| `qwen` | Qwen |
| `kimi` | Kimi |
| `glm` | GLM |
| `doubao` | Doubao / Seed |

Paths start at `assets/supporting-character-references/`. Forms are `standard` about 4.0 heads, `compact` 3.3, `semi-chibi` 2.8 (default), `chibi` 2.5 and `super-deformed` 2.1. For custom ratios, choose the frozen `identity_form` sheet for identity and any explicitly declared costume role, not proportions; never let its depicted body ratio replace the requested target. The existing 15 Whale-chan references and `form-authority.json` remain unchanged; these model sheets retain their accepted natural variation rather than acquiring a new strict admission test.

Load supporting images only for declared `physical` or `avatar` roles. Offscreen/absent records still freeze identity/personality/form but have null image references. Source participation or an explicit user casting request must justify each role; aliases do not turn a passing mention into a cast member.

Every model reference requires `identity`; optional roles are `costume` and preset `proportion` only. Custom model ratios forbid `proportion`. Describe every interaction, pointing, kneeling, hugging, facing, scale and placement in text instead of using a model sheet as a pose/composition reference. Bind instructions to the named actor to prevent identity mixing.

Keep the effective set at five or fewer: canonical Whale-chan and typography leave three slots. The abstract sheet counts as one even when shared by multiple ordinary people; each distinct model/form sheet also counts. Account for any additional custom references. Raise an overflow during planning and resolve it openly; do not silently omit actors or required identity images.
