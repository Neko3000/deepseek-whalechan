---
name: whalechan-image-comic
description: Generate five funny, verified DeepSeek Whale-chan comics from text, screenshots, images, chat logs, or reasoning traces. Use when source material should become punchy 1-panel, 2-panel, or 4-panel Whale-chan comics with exact visible text, a selected bundled text-style reference, consistent identity, provider fallbacks, QA, and a complete creative audit trail while other visual fields remain configurable.
---

# Whale-chan Image Comic

Turn one recognizable fact from the input into five genuinely funny Whale-chan comics. Treat the source as comedy material, not a summary assignment. Find a word, presupposition, permission, status, metric, or relationship that Whale-chan can deliberately reinterpret for her own benefit. Preserve the fact anchor; let her stolen reading and its visual consequence create the joke.

## Load the guidance

Read these before every run:

- `references/comedy-engine.md` for the eight-idea pool, boredom gate, duels, and B/C intensity.
- `references/character-personality.md` for Whale-chan, form, outfit, and abstract-supporting-character locks.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/text-style-routing.md` to select exactly one primary text treatment.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/qa-rubric.md` before reviewing any candidate.

## Apply non-negotiable defaults

- Produce five final PNG comics. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Generate eight distinct comedy premises internally. Apply the boredom gate, then pairwise duels.
- Give rank 1 three materially different executions with different punchlines. Give ranks 2 and 3 one execution each.
- Use exactly three C-intensity and two B-intensity tasks unless safety requires lowering a specific task.
- Cover at least two panel counts across the set. Use only 1, 2, or 4 panels.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and a pure white `#FFFFFF` background.
- Follow the input's main language; prefer Simplified Chinese for Chinese or mixed Chinese input.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Default to sequential execution. Accept requested parallelism from 1 through 5 and record the lower effective runtime capacity when necessary.
- Start immediately. Pause only when the user explicitly asks to see jokes or scripts first.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Build and freeze the assignment

1. Extract one directly recognizable fact anchor. For image input, inherit semantics only unless the user explicitly requests a visual element.
2. Find concrete semantic hinges in the source. Create eight structurally different premise records whose `expectation`, `reversal`, `personality`, and `scene` encode the normal reading, Whale-chan's self-serving alternate reading, her motive, and the visual proof that she acted on it. If all are weak, create a new pool from different hinges and character drives.
3. Reject flat retellings, random technical metaphors, generic reactions, unclear anchors, passive Whale-chan roles, interchangeable-character jokes, scenes without visual proof, and jokes that need explanation.
4. Run pairwise duels among survivors using surprise-then-inevitability, Whale-chan agency, force of punchline, visual second hit, and shareability. Keep the full record.
5. Select ranks 1–3. Expand rank 1 into three executions that share the central contradiction but use materially different stolen readings, consequences, status reversals, or final knives.
6. Resolve every image field independently using explicit user instructions first, declared reference roles second, source semantics third, and defaults last. Freeze `output`, `style`, `costume`, `background`, exact `core_text`, one primary `text_style`, `proportion`, per-panel `action_plan`, expressions, and execution.
7. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Give every bundled or user reference one or more declared roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. A reference may control only its declared roles. Load the abstract-user pose sheet only when a supporting character appears. Use at most five effective references and never silently drop the required typography role.
8. Write `assignment.json` and `creative-record.md`. Validate before generation:

   ```bash
   python3 scripts/manage-run.py validate-assignment --assignment <assignment.json>
   python3 scripts/manage-run.py init --assignment <assignment.json> \
     --effective-parallelism <current-capacity>
   ```

Use schema v6 in `references/run-schema.md`; do not emit or accept v5 assignments. The initialized run belongs under `artifacts/whalechan-image-comic/<run-name>/` unless the user gives another destination. External references are frozen into the run with hashes.

## Generate each task

Build prompts in this order: permanent Whale-chan identity → fact anchor and semantic hinge → self-serving reading, desire, tactic, emotional mask, punchline, and visual proof → per-panel action and composition → expression cues → frozen preset or custom head-ratio target → resolved style → resolved outfit → resolved background → exact `core_text` and the selected text-template treatment → typed-reference role limits → anatomy/contact constraints → frozen output format, aspect ratio, and resolution mode. Quote every required semantic string verbatim. Include canonical style, outfit, or proportion locks only when that field remains canonical or preset.

Use bundled and frozen user images as role-scoped references, not edit targets unless the user explicitly requests an edit. Never copy bundled wording, jokes, or exact compositions.

Start with built-in ImageGen. Its tool call has no explicit pixel-size control: in automatic mode accept any valid native output with the frozen ratio, including square `1254×1254`; do not route away merely because it differs from the `1024×1024` recommendation. If the assignment requires an explicit resolution, record a `capability` error for a tool that cannot guarantee it and continue in provider order. For each image-producing call, save the returned image into the workspace, run automatic validation with the frozen output flags, perform original-resolution visual QA, and record it. A returned image consumes one of that task's three slots whether it passes or fails.

```bash
python3 scripts/validate-image.py <candidate.png> \
  --resolution-mode <auto|explicit> --aspect-ratio <W:H> \
  [--recommended <WIDTHxHEIGHT>|--no-recommendation] \
  [--width <pixels> --height <pixels>] \
  --write-json <automatic.json>
python3 scripts/manage-run.py record-candidate \
  --run-dir <run> --image <01_name> --provider codex --model gpt-image \
  --candidate <candidate.png> --prompt-file <prompt.txt> \
  --automatic-json <automatic.json> --visual-json <visual.json>
```

Promote only a PASS:

```bash
python3 scripts/manage-run.py promote --run-dir <run> --image <01_name>
```

## Repair by root cause

- **The joke is flat:** diagnose illustrated retelling, random metaphor, passive character, missing semantic hinge, or missing second beat. Rewrite the hinge, Whale-chan's motive and action, text, panels, or the whole premise. Do not polish a dead joke.
- **Identity/proportion/action/composition fails:** retain the joke and make one targeted visual correction. Measure preset and custom proportions with `scripts/measure-form.py`. If space caused stretching, hiding, or accidental crop, simplify the scene instead of changing the frozen skeleton.
- **Expression fails:** retain the joke, personality, and emotional mask. Name the missing or incorrect eye, eyebrow, mouth, cheek, or manga-accent cue and correct only that visible performance. Do not rewrite personality to repair a face.
- **Only text fails:** use the remaining two slots for an empty-text-layout image, then edit it with exact wording and the selected text-style reference. Do not use local fonts.
- **Two-panel coherence fails:** if two generation slots remain, generate the two panels separately, record each with `record-component`, combine with `compose-panels.py` using the assignment's output mode and ratio, then record the derived comic with `record-composite`. The local composite consumes no image-generation slot.
- **Four-panel coherence fails:** retry the whole canvas. Never generate four new panels under a three-call budget. Compose four panels only when all inputs already exist without new provider calls.
- **Safety rejection:** record it and stop. Never switch providers to bypass it.

Provider errors that return no image do not consume budget:

```bash
python3 scripts/manage-run.py record-error \
  --run-dir <run> --image <01_name> --provider openai --model <model> \
  --category <category> --details <message>
```

## Route providers strictly

Use this order and never move backward:

1. Built-in ImageGen / GPT Image
2. OpenAI Images API
3. Nano Banana
4. Seedream

Use the adapters described in `references/provider-routing.md`. Move forward only after the current provider returned a failed candidate, lacks the required capability, or recorded an availability/authentication/quota/service failure. Provider errors do not authorize skipping an untouched intermediate provider.

## Coordinate parallel work safely

For requested parallelism above 1, compute the effective value from the request, the maximum 5, runtime worker slots, provider limits, and ready image count. The main agent is the sole manifest writer. Workers may generate and review different images in unique `staging/<image-id>/` directories, but they must not record, promote, or finalize. The coordinator serially verifies hashes, records results, and promotes PASS candidates. Never dispatch two candidates for one image at once; retries and provider fallback remain serial within that image.

## Finalize honestly

Finalize after all open tasks are resolved:

```bash
python3 scripts/manage-run.py finalize --run-dir <run>
```

If fewer than five tasks pass after their independent budgets are exhausted, use `--allow-partial`, deliver only passed comics, and report the missing tasks. Never fill the set with a failed image.

Keep every image-producing candidate, prompt, QA record, asset hash, duel, error log, and final path. Report final paths, provider/model, attempt count, and any shortfall.

## Hard stops

- Do not generate before the assignment validates.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
