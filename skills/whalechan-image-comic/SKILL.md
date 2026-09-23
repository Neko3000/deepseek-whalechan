---
name: whalechan-image-comic
description: Generate five funny, verified DeepSeek Whale-chan comics from text, screenshots, images, chat logs, or reasoning traces. Use when source material should become punchy 1-panel, 2-panel, or 4-panel Whale-chan comics with exact speaker-attributed text, per-image typography choices, staged abstract supporting characters, consistent identity, provider fallbacks, QA, and a complete creative audit trail while other visual fields remain configurable.
---

# Whale-chan Image Comic

Turn one recognizable fact from the input into five genuinely funny Whale-chan comics. Preserve the source's actual comic target, turn and tone before adapting it. A strategic reinterpretation is one possible mechanism, not a requirement: language, reaction, timing, status exposure and bittersweet recognition can also carry the joke. The source determines the expression; image numbers only identify files.

## Load the guidance

Read these before every run:

- `references/comedy-engine.md` for source analysis, premise exploration, selection, and B/C intensity.
- `references/character-personality.md` for Whale-chan, form, outfit, and abstract-supporting-character locks.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/text-style-routing.md` to select one primary text treatment per image and review variety across the set.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/qa-rubric.md` before reviewing any candidate.

## Apply defaults and user overrides

- Produce five final PNG comics. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Explore distinct premises before allocating images. Keep only actual evaluations and comparisons, not a fixed eight-entry pool or prewritten winners.
- Select five materially different executions, with explicit idea links. There is no rank allocation or B/C intensity quota.
- Choose 1, 2, or 4 panels by narrative need, not image index or a diversity quota.
- Select typography, framing, cast staging and text placement independently for each joke. Repetition is allowed when justified by the source; random rotation is not creative diversity. A consistent character identity does not require consistent layouts.
- For dialogue-driven material, default to bodily present abstract indigo partners. Record a narrative reason for an offscreen, avatar-only, or omitted role; preserve who speaks and who reacts.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and a pure white `#FFFFFF` background.
- Follow the input's main language; prefer Simplified Chinese for Chinese or mixed Chinese input.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Default to sequential execution. Accept requested parallelism from 1 through 5 and record the lower effective runtime capacity when necessary.
- Start immediately. Pause only when the user explicitly asks to see jokes or scripts first.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Build and freeze the assignment

1. Record `input.source_analysis`: the source event, audience expectation, actual turn, comic target, tone, meaningful language differences and user corrections. Distinguish observed facts from your interpretation; preserve uncertainty instead of inventing a hidden meaning. Extract the fact anchor and source participants with evidence. Use `input.participants: []` only for genuinely solo material. Images supply semantics unless the user requests their visuals; preserve speaker roles without copying real faces or avatars.
2. Explore premises from this analysis before deciding layouts. Record each premise's expectation, reversal, mechanism, personality, scene and actual gate reason. Preserve a reaction or language joke when that is the source's engine; do not automatically replace it with food, laziness, machinery or self-serving wordplay.
3. Reject flat retellings, generic reactions without a source-specific reveal, random metaphors, unclear anchors, decorative scenes and jokes that need explanation. A specific, timed reaction can itself reveal the contradiction.
4. Select passing ideas with a concrete `selection_reason`. Pairwise duels are optional; record only comparisons actually made. Do not prefill PASS, rank by candidate number, or backfill a candidate pool from finished image plans.
5. Allocate five executions to selected ideas without a fixed rank distribution. Link each image by `idea_id`; explain its distinct payoff in `execution_note`. Pose, font and background changes alone do not create another execution.
6. Resolve every image field using explicit user instructions first, declared reference roles second, source semantics third, and defaults last. Freeze `composition` (shot, staging, text placement and narrative reason), `proportion_check`, `output`, `style`, `costume`, `background`, exact `core_text`, `text_style` and its semantic reason, per-line `dialogue_plan`, per-participant `cast_plan`, `proportion`, per-panel `action_plan` and expressions. Assign image numbers last. Helpers may serialize decisions, not derive creative fields from ordinal positions. Intentional close-ups use `visible-only` proportion review; measurable full-body shots use `measured`.
7. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Give every bundled or user reference one or more declared roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. A reference may control only its declared roles. Load the abstract-user pose sheet only when a supporting character appears. Use at most five effective references and never silently drop the required typography role.
8. Review the design before freezing it: compare each typography choice with its joke, each speaker with the source, and each cast decision with the visible interaction the scene needs. Reject random template rotation, generic selection reasons, and offscreen decisions based only on saving space, avoiding drawing difficulty, or keeping Whale-chan prominent. Fix the plan first; a later image matching a weak plan is insufficient. Write `assignment.json`; validation and initialization produce `creative-record.md` with these decisions:

   ```bash
   python3 scripts/manage-run.py validate-assignment --assignment <assignment.json>
   python3 scripts/manage-run.py init --assignment <assignment.json> \
     --effective-parallelism <current-capacity>
   ```

For multiple inputs, finish all assignments, then run `python3 scripts/manage-run.py validate-batch --assignment <first.json> --assignment <second.json>` with every assignment before the first generation call. Review its case-by-position matrix and warnings, not just aggregate counts. Compare mechanisms, narrative beats, shots, cast positions and text placement across cases and across positions; changing order must not hide a repeated skeleton. Ask whether another case's dialogue could replace this one's without changing the drawing. Save a `batch-review.md` beside the assignments naming the compared cases, warning dispositions, source-specific reasons for retained similarities, and revisions. Do not generate until this review is actually performed. Structural validity is not creative approval; no warnings is not approval either. Repeat this comparison on final images. See `references/batch-review.md`.

Use the current schema in `references/run-schema.md`. All assignment, generation and QA operations require that contract. The initialized run belongs under `artifacts/whalechan-image-comic/<run-name>/` unless the user gives another destination. External references are frozen into the run with hashes.

## Generate each task

Build the initial prompt from the frozen assignment rather than recreating its defaults:

```bash
python3 scripts/build-prompt.py --run-dir <run> --image <01_name>
```

Read the returned `prompt_file` and pass every returned reference path in order to the provider. The builder preserves source interpretation, framing, exact wording, speaker ownership and physical/avatar/offscreen staging. It requires the current contract and never overwrites a prompt. For a targeted retry or component rescue, save a separate prompt derived from this one; preserve the frozen typography and cast decisions unless the plan itself is explicitly revised in a new run. Include canonical style, outfit, or proportion locks only when that field remains canonical or preset.

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

- **The joke is flat:** diagnose source misreading, illustrated retelling, random metaphor, generic reaction, missing reveal or lost timing. Revisit the source analysis before rewriting text, panels or premise. Do not replace every weak joke with the same self-serving reinterpretation.
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

Keep every image-producing candidate, prompt, QA record, asset hash, duel, error log, and final path. Report final paths, provider/model, attempt count, any shortfall, and the actual typography/cast distribution. Separate pre-generation design review from post-generation visual QA; neither substitutes for the other.

Inspect the actual candidate and record candidate-bound observations before comparing with the plan. An unreviewed draft is `review_status: pending`, not PASS, and cannot be recorded as an accepted candidate or promoted. The manager checks evidence structure, not whether the reviewer truly looked or whether a joke is funny. Never copy planned text into a purported transcription or fabricate landmarks to satisfy a ratio. Report `H1: NA` only for a planned `visible-only` shot, with visible-proportion observations and the limitation explicitly recorded.

## Hard stops

- Do not generate before the assignment validates.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not accept a required physical partner replaced by an avatar, an offscreen balloon, or Whale-chan speaking their lines. Record visible lettering treatment, speaker connectors, and cast representation as QA evidence.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
