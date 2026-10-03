---
name: whalechan-image-comic
description: Propose five DeepSeek Whale-chan comic concepts from text, screenshots, images, chat logs, or reasoning traces, then generate verified comics after the user selects concepts and separately confirms image quantities. Use for funny 1/2/4-panel Whale-chan adaptations with exact dialogue, consistent identity, configurable visuals, provider fallbacks and QA. Default to five images per selected concept.
---

# Whale-chan Image Comic

Turn one recognizable fact into five concrete proposals, then generate the user's confirmed selection. Preserve the source's actual comic target, tone and native comedy direction. Jokes come in five directions — reversal, exposure, escalation, recognition and character — each carried by its own fields; do not force every source into an expectation-and-reversal shape. Choice letters and image numbers are identifiers, never creative instructions.

Workflow: analyze → explore and review five proposals → **Gate 1: user selects** → **Gate 2: user confirms proposal/image totals** → expand, validate and freeze → generate, review and deliver. Stop and wait at both gates; selection alone never authorizes generation.

## Load the guidance

Read these before every run:

- `references/proposal-selection.md` for the mandatory seven-column table, both user gates, reply handling and records.
- `references/comedy-engine.md` for source analysis, the five comedy directions, native-direction rules, the optional rhythm layer, selection, and B/C intensity.
- `references/character-personality.md` for Whale-chan, form, outfit, and abstract-supporting-character locks.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/text-style-routing.md` to select one primary text treatment per image and review variety across the set.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/qa-rubric.md` before reviewing any candidate.

## Apply defaults and user overrides

- Offer exactly five proposals A–E. Default to five final PNGs per selected proposal; honor explicit per-proposal quantities, including one each. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Explore distinct premises before allocating images. Keep only actual evaluations and comparisons, not a fixed eight-entry pool or prewritten winners.
- Make the five proposals materially different. Within each selected proposal, develop distinct executions without replacing its core scene, comic turn or user-locked wording. There is no rank allocation or B/C intensity quota.
- Choose 1, 2, or 4 panels by narrative need, not image index or a diversity quota.
- Select typography, framing, cast staging and text placement independently for each joke. Repetition is allowed when justified by the source; random rotation is not creative diversity. A consistent character identity does not require consistent layouts.
- For dialogue-driven material, default to bodily present abstract indigo partners. Record a narrative reason for an offscreen, avatar-only, or omitted role; preserve who speaks and who reacts.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and a pure white `#FFFFFF` background.
- Follow the input's main language; prefer Simplified Chinese for Chinese or mixed Chinese input.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Default to sequential execution. Accept requested parallelism from 1 through 5 and record the lower effective runtime capacity when necessary.
- Start planning immediately, then always wait at Gate 1 and Gate 2. Never infer approval from silence, recommendations or a preselected answer. A planning-only request never authorizes image calls.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Prepare proposals and obtain both user decisions

1. Record `input.source_analysis`: the source event, comic target, tone, meaningful language differences, user corrections, and the source's `native_direction` with its reason (`null` when the source is not funny on its own). Distinguish observed facts from your interpretation; preserve uncertainty instead of inventing a hidden meaning. Extract the fact anchor and source participants with evidence. Use `input.participants: []` only for genuinely solo material. Images supply semantics unless the user requests their visuals; preserve speaker roles without copying real faces or avatars. For image or screenshot sources, keep the source file path in `input.content` and the transcription in `source_event`.
2. Explore premises from this analysis before deciding layouts. Record each premise's direction and carrier fields, mechanism, personality, scene and actual gate reason. Keep at least one proposal in the native direction when one exists. Preserve a reaction or language joke when that is the source's engine; do not automatically replace it with food, laziness, machinery or self-serving wordplay. At most one proposal may be a pure character gag.
3. Reject flat retellings, generic reactions without a source-specific reveal, random metaphors, unclear anchors, decorative scenes and jokes that need explanation. A specific, timed reaction can itself reveal the contradiction.
4. Prepare five passing proposals with concrete scenes, turns, staging and key lines; review them against the source before showing them. Record actual comparisons only. Do not prefill PASS, rank by candidate number, or backfill a candidate pool from finished image plans.
5. Follow `proposal-selection.md`: render the seven-column Markdown table, ask for selection below it and explain the generation strategy. **Stop for Gate 1.** Record the user's chosen proposals, quantities and changes.
6. Show every selected proposal's title and image count, plus proposal and image totals. Include explicit changes. Ask whether to begin and **stop for Gate 2**. A changed selection or quantity requires an updated summary and fresh confirmation. If proposals are redesigned, return to Gate 1.

## Expand and freeze the confirmed assignment

After Gate 2, continue through internal preparation and generation without a third approval:

1. Expand exactly the confirmed quantities. Set `ranked_ideas` to the selected idea ids and explain the selection in `selection_reason`. Link each image by `idea_id` and describe its distinct payoff in `execution_note`. Pose, font and background swaps alone are insufficient.
2. Resolve each field from explicit user instructions, declared reference roles, source semantics, then defaults. Freeze `composition`, `proportion_check`, `output`, `style`, `costume`, `background`, exact `core_text`, `text_style` and reason, `dialogue_plan`, `cast_plan`, `proportion`, `action_plan` and expressions. Assign image numbers last. Intentional close-ups use `visible-only`; measurable full-body shots use `measured`.
3. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Declare each reference's roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. Load the abstract-user pose sheet only when a supporting character appears. Use at most five effective references; never silently drop required typography.
4. Review each execution against its approved proposal and changes, then check typography, speaker ownership and cast staging against the source. Reject random template rotation, generic reasons and offscreen choices made just to simplify drawing. Fix internal execution details without changing the approved core. Decide each image's optional `rhythm`; leave it `null` unless the punchline clearly needs it. Write schema v11 `assignment.json` including the proposal and both user decisions, then validate and initialize; initialization writes `creative-record.md`:

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
python3 scripts/build-prompt.py --run-dir <run> --image <01_name> --write-request
```

Read the returned `prompt_file` and pass every returned reference path in order to the provider. `--write-request` also writes `request_file` (`<prompt>.request.json`), the adapter request for every external provider, built from the frozen references, hashes and output; pass it to `generate-codex.py` or a later fallback adapter instead of assembling JSON by hand. For a saved retry or repair prompt, run `build-prompt.py --run-dir <run> --image <01_name> --from-prompt <prompt.txt> --write-request`. The builder preserves source interpretation, framing, exact wording, speaker ownership and physical/avatar/offscreen staging. It requires the current contract and never overwrites a prompt. For a targeted retry or component rescue, save a separate prompt derived from this one; preserve the frozen typography and cast decisions unless the plan itself is explicitly revised in a new run. Include canonical style, outfit, or proportion locks only when that field remains canonical or preset.

Use bundled and frozen user images as role-scoped references, not edit targets unless the user explicitly requests an edit. Never copy bundled wording, jokes, or exact compositions.

Start with Codex ImageGen whenever Codex is available, regardless of which agent runs this Skill:

- **Running inside Codex** (the built-in `image_gen` tool is available): call it directly.
- **Running in another agent** (Claude Code, Antigravity, etc.): run `python3 scripts/generate-codex.py --check`. If it succeeds, generate each candidate with `generate-codex.py --request <json> --output <png>`; Codex only renders the image, and this agent keeps every other step (prompting, QA, recording, retries, delivery). If the check fails, record its category (`unavailable` or `authentication`) as a `codex` provider error and continue in provider order. Never nest `codex exec` inside Codex.

Codex ImageGen has no explicit pixel-size control: in automatic mode accept any valid native output with the frozen ratio, including square `1254×1254`; do not route away merely because it differs from the `1024×1024` recommendation. If the assignment requires an explicit resolution, record a `capability` error and continue in provider order. For each image-producing call, save the returned image into the workspace, run automatic validation with the frozen output flags, perform original-resolution visual QA, and record it. A returned image consumes one of that task's three slots whether it passes or fails. When `generate-codex.py` reports `usable: false` (prompt rewritten or references dropped), record the image as a failed candidate and retry.

```bash
python3 scripts/validate-image.py <candidate.png> \
  --resolution-mode <auto|explicit> --aspect-ratio <W:H> \
  [--recommended <WIDTHxHEIGHT>|--no-recommendation] \
  [--width <pixels> --height <pixels>] \
  --write-json <automatic.json>
python3 scripts/manage-run.py record-candidate \
  --run-dir <run> --image <01_name> --provider codex --model gpt-image \
  --candidate <candidate.png> --prompt-file <prompt.txt> \
  --automatic-json <automatic.json> --visual-json <visual.json> \
  --transport <cli|builtin> [--provider-audit <candidate.png.codex.json>]
```

Codex candidates declare `--transport`: `cli` for `generate-codex.py` output, which must pass `--provider-audit` with the audit file written beside it, or `builtin` for the built-in tool, which has no audit file. Other providers omit `--transport`. The manager binds the audit to the candidate hash, refuses a PASS when `usable` is false, and flags `usable: null` as unverified in the record and the final report.

Promote only a PASS:

```bash
python3 scripts/manage-run.py promote --run-dir <run> --image <01_name>
```

## Repair by root cause

- **The joke is flat:** diagnose source misreading, illustrated retelling, missing reveal or lost timing. Correct the execution within the approved proposal. If the core proposal must change, present revised proposals through both gates in a new run; never silently replace the selected joke.
- **Identity/proportion/action/composition fails:** retain the joke and make one targeted visual correction. Measure preset and custom proportions with `scripts/measure-form.py`. If space caused stretching, hiding, or accidental crop, simplify the scene instead of changing the frozen skeleton.
- **Expression fails:** retain the joke, personality, and emotional mask. Name the missing or incorrect eye, eyebrow, mouth, cheek, or manga-accent cue and correct only that visible performance. Do not rewrite personality to repair a face. When the rest of the candidate passes, prefer an expression-only edit: save a repair prompt naming each face change, then `build-prompt.py --from-prompt <repair prompt> --edit-target <candidate> --edit-instruction "edit target; change only the named facial features, keep everything else unchanged"`. Edit requests carry only the edit target and the typography reference, so an identity reference's own expression cannot leak back in. Review the whole canvas again.
- **Only text fails:** with two slots left, generate an empty-text-layout image, then edit it with exact wording and the selected text-style reference. With one slot left, edit the failed candidate directly (`build-prompt.py --from-prompt <repair prompt> --edit-target <candidate>`), changing only the lettering, and review the whole canvas again. Do not use local fonts. For the edit, save the lettering prompt and run `build-prompt.py ... --from-prompt <prompt.txt> --edit-target <layout.png>`: its request places the layout first as the edit target and the frozen text-style reference second.
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

1. Codex ImageGen / GPT Image (built-in tool inside Codex, `generate-codex.py` elsewhere)
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

Finalize against the confirmed task total. If fewer tasks pass after budgets are exhausted, use `--allow-partial`, deliver only passed comics grouped by proposal, and report the missing tasks per proposal. Never fill the set with a failed image.

If every provider failed only for setup reasons (`unavailable`, `authentication` or `quota`) while tasks still have unused slots, leave the run open instead: a finalized run cannot accept more images. Report what to configure (install and log in to Codex CLI, or set a provider key) so the same run can resume without repeating either gate. Use `--allow-partial` in that case only when the user asks to close the run.

Keep every image-producing candidate, prompt, QA record, asset hash, duel, error log, and final path. Report final paths, provider/model, attempt count, any shortfall, and the actual typography/cast distribution. Separate pre-generation design review from post-generation visual QA; neither substitutes for the other.

Inspect the actual candidate and record candidate-bound observations before comparing with the plan. An unreviewed draft is `review_status: pending`, not PASS, and cannot be recorded as an accepted candidate or promoted. The manager checks evidence structure, not whether the reviewer truly looked or whether a joke is funny. Never copy planned text into a purported transcription or fabricate landmarks to satisfy a ratio. Report `H1: NA` only for a planned `visible-only` shot, with visible-proportion observations and the limitation explicitly recorded.

## Hard stops

- Do not generate, call a paid image API, or initialize a formal run before both user gates are completed for the current proposal and quantity summary and the assignment validates. Draft rendering and selection summaries do not grant approval.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- Do not relabel a converted joke as the source's native direction, or change a direction label just to silence a warning.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not accept a required physical partner replaced by an avatar, an offscreen balloon, or Whale-chan speaking their lines. Record visible lettering treatment, speaker connectors, and cast representation as QA evidence.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
