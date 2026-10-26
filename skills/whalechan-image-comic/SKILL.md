---
name: whalechan-image-comic
description: Create DeepSeek Whale-chan comics from text, screenshots, images, chat logs or reasoning traces. For N images per source (default 5), freeze 2N concise ideas, have a different sub-agent priority-rank and select N, then complete their visual plans and obtain one generation confirmation. Use for funny 1/2/4-panel adaptations with exact dialogue, consistent identity, configurable visuals, a locked image tool, candidate QA and one collection review with at most one repair round.
---

# Whale-chan Image Comic

Turn one recognizable fact into 2N concise candidates, have an independent sub-agent priority-rank and select N (default N=5 per source), and generate one comic per selected idea after confirmation. Preserve the source's actual comic target and tone, considering its native comedy direction during comparison. Jokes come in five directions — reversal, exposure, escalation, recognition and character — each carried by its own fields; do not force every source into an expectation-and-reversal shape. Candidate ids and image numbers are identifiers, never creative instructions.

Workflow: analyze → freeze 2N concise ideas → independent priority ranking → select N → original author completes N visual plans and allocation → **one user confirmation of table, totals and allocation** → validate and freeze → generate, review and deliver. Complete planning before this gate; planning alone never authorizes image calls.

## Load the guidance

Main reads `references/agent-orchestration.md` and the role boundaries in `references/batch-commands.md` and delegates the remaining guidance to the responsible role. Planning workers load creative/prompt guidance; generation workers load provider/QA guidance; collection and delivery workers load their lifecycle/gallery guidance.

Role references:

- `references/batch-commands.md` for v20 fixed commands, task packets, tool preflight/locking, pause/resume and delivery; workers load their role section.

- `references/prompt-design.md` for drawing-only visual plans authored before confirmation.
- `references/proposal-selection.md` for the information-only table (eight base columns plus cast settings when present) with its panel and tier distribution, the single user confirmation and its record.
- `references/comedy-engine.md` for source analysis, the five comedy directions, native-direction preferences, the optional rhythm layer, selection, and where exaggeration tiers fit.
- `references/character-personality.md` for Whale-chan, form, outfit, and supporting-cast locks. Read `references/model-characters.json` when a registered model participates.
- `references/form-profiles.md` for the five recommended presets, custom-ratio rules, measurement, and panel adaptation.
- `references/panel-grammar.md` for 1/2/4-panel structure and retry limits.
- `references/expression-presets.json` for per-panel visible facial acting and performance levels.
- `references/exaggeration-tiers.md` and `references/exaggeration-tiers.json` to give each image an A/B/C exaggeration tier, its landing markers and its effect palette.
- `references/text-style-routing.md` to select one primary text treatment per image and review variety across the set.
- `references/asset-index.md` to select bundled references, `references/form-authority.json` for form targets, and `references/asset-catalog.json` for paths and hashes.
- `references/provider-routing.md` before any provider call.
- `references/review-workflow.md` for new-run single-image QA, tolerances, contact sheets, collection repair and timing.
- `references/review-workflow.md#proportion-evidence--h1` for H1 measurement evidence.
- `references/gallery.md` before exporting the completed task's preview gallery.

## Choose the language

Read `references/language-policy.md` before planning. Resolve one task `language`: explicit user instruction → meaningful current-session expression → newest meaningful local session within 24 hours → ask when uncertain. Use `scripts/detect-language.py` for historical evidence, not as an automatic verdict; recent sessions take precedence over aggregate counts.

Save the normalized BCP-47 tag, actual resolution evidence and any explicit scoped overrides. Use it for communication, image lettering, HTML UI, drawing prompts and visible run/image titles. Preserve exact locked wording and necessary technical tokens. Keep internal IDs and filenames in English. Propagate the saved language to workers and resume from it; never redetect during execution.

Prepare required plan/prompt locale sections before confirmation; use the offline gallery language selector for UI only. Keep generated content in its recorded language. See the language policy for custom dictionaries, display titles, scoped overrides and legacy compatibility.


## Apply defaults and user overrides

- Set target_images=N per source, default 5; N must be a positive integer. Generate 2N concise candidates, independently rank all 2N, and select the first N. Produce one final PNG per selected idea. Sources may have different N. Default to automatic provider-native `1:1` output with `1024×1024` as a recommendation, not a required pixel size.
- Accept an explicit aspect ratio, an explicit pixel resolution, or both. Infer the ratio from an explicit resolution when omitted; reject conflicting values. Automatic mode validates the ratio, while explicit mode validates exact width and height.
- Freeze the 2N candidate pool before independent selection. Record one brief reason per ranked candidate and one set-selection explanation; never prewrite winners. Do not expand or regenerate the pool.
- Make candidate scenes, actions and payoffs distinct. Preserve each selected core idea and user-locked wording in its one image. Shared source lines do not justify identical final replies or consequences.
- For N>=3, cover 1, 2 and 4 panels across the images, allocating them by narrative need rather than index. Record an explicit user override; never add empty panels to meet the default.
- Target A:B:C=3:1:1 per source: N=5 requires exactly 3 A, 1 B and 1 C; other N are allocated by the planning agent according to content, as close as practical to 60%/20%/20%. For N>=3 retain at least one of each tier. Choose which ideas carry each tier independently of rank, index and panel count. Record explicit user overrides.
- N=1 or 2 relaxes panel/tier coverage; allocate tiers close to the target ratio using content to resolve ties. Do not invent a user override.
- Select typography, framing, cast staging and text placement independently for each joke. Repetition is allowed when justified by the source; random rotation is not creative diversity. A consistent character identity does not require consistent layouts.
- For dialogue-driven material, default to bodily present partners: ordinary people remain abstract indigo figures, while registered models retain their detailed identities. Cast only actual source participants or explicitly requested characters; a passing model mention is not participation. Record a narrative reason for an offscreen, avatar-only, or omitted role; preserve who speaks and who reacts.
- Default to `semi-chibi`, the canonical clean rounded cel-shaded style, the canonical navy-and-white maid outfit, and the tier's default background when the user resolves none: a detailed text-free scene for `A`, an effect background for `B`, pure white `#FFFFFF` for `C`.
- Write visible comic text in the language resolved under [Choose the language](#choose-the-language), not automatically in the source's language.
- Treat the five bundled forms as recommended presets. Accept any finite measurable custom head ratio greater than `1.0`; custom ratios have no bundled proportion reference.
- Allow any physically depictable action and any user-resolved background, art style, or outfit, subject to provider safety and technical limits. A custom field changes only that field.
- Use independent role caps: planning 5; generation 5 (Codex ImageGen 3); collection 2; delivery 1. Main coordinates only when delegation exists. Apply actual runtime slots and the batch cap of ten; lower capacity changes dispatch, not the role configuration. See `references/agent-orchestration.md`.
- Start planning immediately. Show the final N-row table, image total, worker allocation and budget together, then obtain one real confirmation. Never infer approval from silence or a preselected answer. A planning-only request never authorizes image calls.
- Give each task an independent maximum of three image-producing calls. Never transfer unused calls.

## Understand the source and independently select N ideas

Assign one planning sub-agent per original source, up to the planning cap. The author handles concepts and selected details; a different real sub-agent handles selection. Both receive the source tier policy through task-packet and consider the selected set’s performance range.

1. Record `input.source_analysis`: source event, comic target, tone, language differences, user corrections and native direction with evidence (`null` when the source has no joke). Separate observed facts from interpretation. Extract the fact anchor and participants; use `input.participants: []` only for solo material. Preserve speaker roles without copying real faces. For screenshot/image sources, retain the file path in `input.content` and the transcription in `source_event`.
2. Author exactly 2N concise distinct candidates, each with direction/carrier fields, scene, key dialogue, visual payoff, mechanism and personality. Native direction and source-grounded character gags are comparative preferences, not quotas. Freeze the pool; weak ideas still compete, and the pool is never extended or regenerated.
3. Submit concepts with planning-task concepts-submit. Dispatch its selection task to another real agent, excluding every recorded author. That reviewer reads the original source and frozen pool, ranks all 2N by source fidelity, humor, drawability, concise dialogue and set variety, and submits one brief reason per candidate plus a set explanation. No pairwise scores, voting, randomization, replacement pool or low-score re-generation.
4. The original author receives the detail task and completes only the first N candidates, preserving frozen premises, payoffs and key lines. Submit the complete visual draft with planning-task detail-submit. Use evidence-based recovery if the author is unavailable. Then perform the existing cross-source design review.

## Complete the plan, confirm once, then freeze

Use batch-prepare for inventory, language evidence, tool preflight and planning tasks. Have planning workers author and render the plan, including the existing cross-source comparison. Main assembles their results for consent without rewriting content. Use batch-proposal to produce bound tables and requests; after consent, delegate batch-start. Use the fixed commands in batch-commands.md rather than authoring per-run bookkeeping scripts.

Prepare these decisions before the user confirmation:

1. Use the script-derived ranked_ideas for the first N candidates and explain the ranking in `selection_reason`. Link one image to each `idea_id` and describe its unique payoff in `execution_note`. For N>=3 cover 1/2/4 panels across the set unless explicitly overridden by the user. Choose worker assignments and effective concurrency from actual capacity. Record each option's `proportion` before confirmation, defaulting to `{"mode": "preset", "preset": "semi-chibi"}`; completed image proportions must match.
2. Settle scenes, key lines, panel counts, staging and worker assignments before confirmation. Resolve fields from explicit user instructions, declared reference roles, source semantics, then defaults. For v20, finish all N selected visual image records before displaying the confirmation plan. Write actions as visible moments, add natural expression descriptions and text positions, and resolve semantic conflicts in this same planning pass; see `prompt-design.md`. Freeze the completed composition, exact text and speaker/cast plans, output, style, costume, background, typography, actions, expressions and proportions before initialization. Assign image numbers last. Intentional close-ups use `visible-only`; measurable full-body shots use `measured`.
3. Use a canonical identity reference first and the selected bundled text-style reference as the sole `typography` reference. Declare each reference's roles: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`. Load the abstract-user sheet for visible ordinary people and each visible model’s selected identity sheet. Freeze model identity, profile, source-specific performance/interaction and form in `cast_plan`; model sheets may control identity, costume and preset proportions, never composition or style. Resolve the five-reference limit before confirmation; never silently drop a character or required typography.
4. Review each execution against its selected idea and user constraints, then check typography, speaker ownership and cast staging against the source. Reject random template rotation, generic reasons and offscreen choices made just to simplify drawing. Refine expression without replacing the frozen candidate. Allocate the source’s target tier mix, then decide each image's exaggeration tier, landing panel, per-panel tiers, landing `effects_plan` and any `contrast`. Decide its optional `rhythm`; leave it `null` unless the punchline clearly needs it. Write the schema v20 draft and render the complete information table, image total, worker allocation and budget as specified in `proposal-selection.md`. After the single real confirmation, save the actual reply and batch summary hash in the confirmation record; delegate validation, initialization and queue creation to the fixed command, which writes each creative-record.md:

   ```bash
   python3 scripts/manage-run.py batch-start --batch <batch.json> \
     --confirmation <confirmation.json> --root <runs-root> --slots <available-subagent-slots>
   ```

For multiple inputs, the planning worker compares source-specific mechanisms, narrative beats, shots, cast positions and text placement before displaying the consolidated plan. Run validate-batch on every draft and inspect its case-by-position matrix and warnings; no warnings is not creative approval. Ask whether another case's dialogue could replace this one's without changing the drawing. Submit the actual cross-source observation, warning dispositions and retained-similarity reasons to batch-proposal. That command checks the complete records and emits bound tables; batch-start revalidates confirmed assignments. Do not add a cross-source visual sweep of final images. See references/batch-review.md.

In the confirmation table and distribution line, use localized descriptive labels (Chinese/English examples): `A-日漫冲击`, `B-漫画爆发`, `C-克制冷幽默` (English: `A-Manga impact`, `B-Comic outburst`, `C-Restrained deadpan`). Keep contrast suffixes, such as `A-日漫冲击（脸→C）`. Immediately below the distribution line, show the current target head-to-body ratio, shared across all N images or grouped by table row numbers when different. Label custom ratios explicitly. Keep Whale-chan’s shared target outside the base table; disclose model targets in the added cast column and distinguish planned targets from measurements of finished images.

Use schema v20 in `references/run-schema.md` for new runs. The initialized run belongs under `artifacts/whalechan-image-comic/<run-name>/` unless the user gives another destination. External references are frozen into the run with hashes.

## Generate and review

Use the v20 combination commands in `references/batch-commands.md`. The generation worker owns one whole image: build the drawing-only request, begin the attempt, call the provider, preserve/prepare locally, inspect once and record QA. It may make permitted targeted retries within the original three-call budget without a coordinator content handoff. Technical failures never authorize regeneration.
Have the same generation worker inspect the whole candidate once. Record concise actual observations, exact text, core defects and tolerated minor issues. Do not have the main agent repeat a worker's visual inspection at handoff. Only core single-image defects authorize a retry within the three-call budget. A passed candidate waits for collection review.

After the N tasks resolve, assign a collection worker to build one numbered contact sheet per source with `build-review-sheet.py`. Review distinctness, consistency and overall performance once. Only named failed images may enter one collection repair round, sharing their original three-call budgets. Inspect each new candidate once, then do at most one focused collection recheck on the updated sheet. Recheck failure means a shortfall, never another collection round. Promote only collection-accepted candidates.

Keep safety halts, source fidelity, exact semantic text and explicit user locks strict. Allow minor facial/decoration variations that preserve emotion, identity, tier and readability. Do not let exact mouth curvature or sweat counts alone cause a retry unless the user explicitly locked them.

## Lock one tool per batch

For v20 preflight in priority order: Codex ImageGen, OpenAI Images API, Nano Banana, Seedream. Check actual tool presence, configuration and required capabilities without producing a test image. Lock the first compatible configured tool before the single confirmation. After consent start parallel generation immediately; do not wait for first-image verification. Preflight cannot guarantee live service or quota.

Keep this provider and transport throughout the batch, including visual-QA retries. Any service error pauses new generation dispatch with no automatic retry or switch; reconcile outputs already in flight. Resume only after an actual user request and successful recheck of the same tool. Unknown output status keeps the call unresolved. Safety rejection remains a hard stop. See provider-routing.md and batch-commands.md.

## Coordinate parallel work safely

Use one batch queue with independent role limits, actual runtime capacity and dynamic ownership. Dispatch through real delegation tools; policy files do not create agents. Prefer finishing a source, then use idle workers for later sources. During planning with three slots and ready selection, target two planning plus one independent selection worker; otherwise use up to three planning workers. Selection has its own cap of 2. If independent agents are unavailable, retain planning state and report the limitation; never use author/main self-review. Under three slots, use three generation workers when no collection is ready and two generation plus one collection when it is. Reuse idle resident agents and count them against runtime occupancy. Workers write isolated image journals; collection/delivery workers merge shared records under a run lock. Main handles only scheduling, status and user communication. See `references/agent-orchestration.md` for commands, recovery and serial fallback.

## Finalize honestly

Have collection workers complete or skip empty collection review. After all source lifecycles resolve, have the delivery worker call:

```bash
python3 scripts/manage-run.py batch-deliver --batch <batch.json> \
  --task-id delivery-all --owner <actual-worker-id> --output <gallery-directory>
```

This promotes accepted candidates, finalizes complete or resolved partial sources and exports/verifies the gallery. Report planned and delivered A/B/C counts and missing tiers alongside missing tasks against the confirmed total; never fill gaps with failures. Paused service work remains open.

Keep every image-producing candidate, prompt, QA record, asset hash, selection record, error log, and final path. Report final paths, provider/model, attempt count, any shortfall, and the actual typography/cast distribution. Separate pre-generation design review from post-generation visual QA; neither substitutes for the other.

Inspect the actual candidate and record candidate-bound observations before comparing with the plan. An unreviewed draft is `review_status: pending`, not PASS, and cannot be recorded as an accepted candidate or promoted. The manager checks evidence structure, not whether the reviewer truly looked or whether a joke is funny. The coordinator must not reopen the image for a routine second visual review. Never copy planned text into a purported transcription or fabricate landmarks to satisfy a ratio. Report `H1: NA` only for a planned `visible-only` shot, with visible-proportion observations and the limitation explicitly recorded.

## Preview gallery

For v20 use batch-deliver to promote, finalize, export and mechanically verify the whole batch; retain paused work open. The delivery worker can export finalized current runs with `python3 scripts/export-gallery.py --run-dir <run>` and link the returned `gallery` HTML path. For multiple sources, keep each independent source group in its own run, with consecutive screenshots together in `input.content`; after all runs finalize, export one gallery using repeated `--run-dir` and an explicit `--output`. Default each source to Passed finals, with Attempts and All filters and visible picture counts. Keep all available attempt images, including failures, in the chronological All view without proposal sections. Final cards link to that idea’s generation history; lightbox navigation follows the active filter. Preserve filter state across source, language and layout switches, and keep ambiguous or missing final provenance explicit. Mark the matching PASS as the final rather than duplicating its image; retain distinct generation records even when their bytes match. Keep proposal summaries, prompts and QA in collapsed details. Open runs awaiting setup recovery are exported only after completion. Export errors do not require regeneration. See `references/gallery.md`.

## Hard stops

- Do not generate, call a paid image API, or initialize a formal run before the single confirmation of the current N-image plan, totals and worker allocation and successful assignment validation. Rendering a plan does not grant approval.
- Do not exceed three image-producing calls for any task.
- Do not transfer budget between tasks.
- Do not accept a comic that is merely cute, accurate, or polished but not funny.
- For QA 11 reject material loss of tier, identity, emotional intent or readability; treat minor decorative variations as warnings. Preserve explicit user locks.
- Do not relabel a converted joke as the source's native direction, or change a direction label just to silence a warning.
- Do not accept missing, additional, unreadable, misspelled, incorrectly ordered, or wrong-language core text.
- Do not accept a required physical partner replaced by an avatar, an offscreen balloon, or Whale-chan speaking their lines. Record visible lettering treatment, speaker connectors, and cast representation as QA evidence.
- Do not treat the automatic-mode recommendation as an exact-size gate. Do not accept a wrong aspect ratio in automatic mode or any pixel mismatch in explicit mode.
- Do not judge a custom style or outfit against the canonical default it replaced. Do not accept an unrecognizable fact anchor, permanent identity drift, proportion drift, broken anatomy/contact, accidental crop, confused reading order, or detailed supporting characters.
- Do not depend on files outside this Skill except user-supplied references that the run manager freezes and hashes. Do not depend on external scripts or fonts.
