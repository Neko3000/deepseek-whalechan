---
name: whalechan-image-comic
description: Create five DeepSeek Whale-chan comics from text, screenshots, images, chat logs, or reasoning traces. Compare ten ideas in 45 pairwise duels, select five, then obtain one confirmation of the plan, total and worker allocation. Use for funny 1/2/4-panel Whale-chan adaptations with exact dialogue, consistent identity, configurable visuals, provider fallbacks and QA. Generate one image per selected idea, covering 1/2/4-panel layouts across the set.
---

# Whale-chan Image Comic

Turn one recognizable fact into ten candidates, select five by complete pairwise comparison, and generate one comic per selected idea after confirmation. Preserve the source's actual comic target and tone, considering its native comedy direction during comparison. Jokes come in five directions — reversal, exposure, escalation, recognition and character — each carried by its own fields; do not force every source into an expectation-and-reversal shape. Candidate ids and image numbers are identifiers, never creative instructions.

Workflow: analyze → freeze ten ideas → 45 pairwise duels → select five → plan five images and worker allocation → **one user confirmation of table, totals and allocation** → validate and freeze → generate, review and deliver. Complete planning before this gate; planning alone never authorizes image calls.

## Load the guidance

Read these before every run:

- `references/proposal-selection.md` for the information-only seven-column table, the single user confirmation and its record.
- `references/comedy-engine.md` for source analysis, the five comedy directions, native-direction preferences, the optional rhythm layer, selection, and B/C intensity.
- `references/character-personality.md` for Whale-chan, form, outfit, and abstract-supporting-character locks.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/text-style-routing.md` to select one primary text treatment per image and review variety across the set.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/qa-rubric.md` before reviewing any candidate.
- `references/gallery.md` before exporting the completed task's preview gallery.

## Apply defaults and user overrides

- Generate exactly ten candidates and select five by all 45 pairwise duels. Produce one final PNG per selected idea, five total per source. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Freeze the ten-candidate pool before comparisons. Record actual judgments and all results; do not apply creative admission thresholds, prewrite winners, append candidates or repeatedly generate pools.
- Make candidate scenes, actions and payoffs distinct. Preserve each selected core idea and user-locked wording in its one image. Shared source lines do not justify identical final replies or consequences. There is no B/C intensity quota.
- Cover 1, 2 and 4 panels across the five images, allocating them by narrative need rather than index. Record an explicit user override; never add empty panels to meet the default.
- Select typography, framing, cast staging and text placement independently for each joke. Repetition is allowed when justified by the source; random rotation is not creative diversity. A consistent character identity does not require consistent layouts.
- For dialogue-driven material, default to bodily present abstract indigo partners. Record a narrative reason for an offscreen, avatar-only, or omitted role; preserve who speaks and who reacts.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and a pure white `#FFFFFF` background.
- Follow the input's main language; prefer Simplified Chinese for Chinese or mixed Chinese input.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Default to available sub-agents within the five-worker limit and actual runtime capacity. Show the chosen allocation for confirmation. Honor explicit parallelism from 1 through 5 and record any lower effective capacity; sequential execution uses one worker with the coordinator handling records.
- Start planning immediately. Show the final five-row table, image total, worker allocation and budget together, then obtain one real confirmation. Never infer approval from silence or a preselected answer. A planning-only request never authorizes image calls.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Understand the source and select five ideas

1. Record `input.source_analysis`: source event, comic target, tone, language differences, user corrections and native direction with evidence (`null` when the source has no joke). Separate observed facts from interpretation. Extract the fact anchor and participants; use `input.participants: []` only for solo material. Preserve speaker roles without copying real faces. For screenshot/image sources, retain the file path in `input.content` and the transcription in `source_event`.
2. Author exactly ten distinct candidates, each with direction/carrier fields, scene, key dialogue, visual payoff, mechanism and personality. Native direction and source-grounded character gags are comparative preferences, not quotas. Freeze the pool; do not use creative PASS/FAIL gates or generate more candidates because the pool feels weak.
3. Compare all 45 unique pairs using `comedy-engine.md`. Record winner or draw and a concrete reason. Award 2/1/0 points for win/draw/loss; break ties by head-to-head points, then authored reasons and distinctness. Select the top five and preserve the full record. Ids and order never decide winners.
4. Plan exactly one image per selected idea. Check that the answers, final beats and visual consequences differ; merely changing nouns, fonts or poses does not establish five ideas.

## Complete the plan, confirm once, then freeze

Prepare these decisions before the user confirmation:

1. Set `ranked_ideas` to the five winners and explain the ranking in `selection_reason`. Link one image to each `idea_id` and describe its unique payoff in `execution_note`. Cover 1/2/4 panels across the set unless explicitly overridden by the user. Choose worker assignments and effective concurrency from actual capacity.
2. Settle scenes, key lines, panel counts, staging and worker assignments before confirmation. Resolve fields from explicit user instructions, declared reference roles, source semantics, then defaults. Detailed image fields may be completed afterward while preserving the displayed plan and user constraints; omit `images` from an unfinished planning draft. Freeze the completed composition, exact text and speaker/cast plans, output, style, costume, background, typography, actions, expressions and proportions before initialization. Assign image numbers last. Intentional close-ups use `visible-only`; measurable full-body shots use `measured`.
3. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Declare each reference's roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. Load the abstract-user pose sheet only when a supporting character appears. Use at most five effective references; never silently drop required typography.
4. Review each execution against its selected idea and user constraints, then check typography, speaker ownership and cast staging against the source. Reject random template rotation, generic reasons and offscreen choices made just to simplify drawing. Refine expression without replacing the frozen candidate. Decide each image's optional `rhythm`; leave it `null` unless the punchline clearly needs it. Write the schema v12 draft and render the complete information table, image total, worker allocation and budget as specified in `proposal-selection.md`. After the single real confirmation, save its bound record in `assignment.json`, then validate and initialize; initialization writes `creative-record.md`:

   ```bash
   python3 scripts/manage-run.py validate-assignment --assignment <assignment.json>
   python3 scripts/manage-run.py init --assignment <assignment.json> \
     --effective-parallelism <current-capacity>
   ```

For multiple inputs, compare source-specific mechanisms, narrative beats and staging before displaying the consolidated plan. Once assignments are confirmed, run `python3 scripts/manage-run.py validate-batch --assignment <first.json> --assignment <second.json>` with every assignment before the first generation call. Review its case-by-position matrix and warnings, not just aggregate counts. Compare mechanisms, narrative beats, shots, cast positions and text placement across cases and across positions; changing order must not hide a repeated skeleton. Ask whether another case's dialogue could replace this one's without changing the drawing. Save a `batch-review.md` beside the assignments naming the compared cases, warning dispositions, source-specific reasons for retained similarities, and revisions. Do not generate until this review is actually performed. Structural validity is not creative approval; no warnings is not approval either. Repeat this comparison on final images. See `references/batch-review.md`.

Use schema v12 in `references/run-schema.md` for new runs. Preserve v10/v11 frozen runs and their original recovery contract; never rewrite their approval history. The initialized run belongs under `artifacts/whalechan-image-comic/<run-name>/` unless the user gives another destination. External references are frozen into the run with hashes.

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

- **The joke is flat:** diagnose source misreading, illustrated retelling, missing reveal or lost timing. Correct the execution within the approved proposal. If the core idea must change, preserve the old run and present the revised complete plan for one new confirmation; never silently replace it or automatically regenerate the candidate pool.
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

Display worker-to-image assignments before confirmation. For requested parallelism above 1, compute the effective value from the request, the maximum 5, runtime worker slots, provider limits, and ready image count. Across multiple sources, share this worker capacity globally; never launch a separate full worker pool per source. Show source-qualified idea assignments in the consolidated confirmation. The main agent is the sole manifest writer. Workers may generate and review different images in unique `staging/<image-id>/` directories, but they must not record, promote, or finalize. The coordinator serially verifies hashes, records results, and promotes PASS candidates. Never dispatch two candidates for one image at once; retries and provider fallback remain serial within that image.

## Finalize honestly

Finalize after all open tasks are resolved:

```bash
python3 scripts/manage-run.py finalize --run-dir <run>
```

Finalize against the confirmed task total. If fewer tasks pass after budgets are exhausted, use `--allow-partial`, deliver only passed comics grouped by proposal, and report the missing tasks per proposal. Never fill the set with a failed image.

If every provider failed only for setup reasons (`unavailable`, `authentication` or `quota`) while tasks still have unused slots, leave the run open instead: a finalized run cannot accept more images. Report what to configure (install and log in to Codex CLI, or set a provider key) so the same run can resume within its confirmed scope. Use `--allow-partial` in that case only when the user asks to close the run.

Keep every image-producing candidate, prompt, QA record, asset hash, duel, error log, and final path. Report final paths, provider/model, attempt count, any shortfall, and the actual typography/cast distribution. Separate pre-generation design review from post-generation visual QA; neither substitutes for the other.

Inspect the actual candidate and record candidate-bound observations before comparing with the plan. An unreviewed draft is `review_status: pending`, not PASS, and cannot be recorded as an accepted candidate or promoted. The manager checks evidence structure, not whether the reviewer truly looked or whether a joke is funny. Never copy planned text into a purported transcription or fabricate landmarks to satisfy a ratio. Report `H1: NA` only for a planned `visible-only` shot, with visible-proportion observations and the limitation explicitly recorded.

## Preview gallery

Before final delivery, export the finalized run with `python3 scripts/export-gallery.py --run-dir <run>` and link the returned `gallery` HTML path. For multiple sources, keep each independent source group in its own run, with consecutive screenshots together in `input.content`; after all runs finalize, export one gallery using repeated `--run-dir` and an explicit `--output`. Include all proposals, final images and recorded attempts. Local composites show their component prompts and consume no extra generation call. Open runs awaiting setup recovery are exported only after completion. Export errors do not require regeneration. See `references/gallery.md`.

## Hard stops

- Do not generate, call a paid image API, or initialize a formal run before the single confirmation of the current five-image plan, totals and worker allocation and successful assignment validation. Rendering a plan does not grant approval.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- Do not relabel a converted joke as the source's native direction, or change a direction label just to silence a warning.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not accept a required physical partner replaced by an avatar, an offscreen balloon, or Whale-chan speaking their lines. Record visible lettering treatment, speaker connectors, and cast representation as QA evidence.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
