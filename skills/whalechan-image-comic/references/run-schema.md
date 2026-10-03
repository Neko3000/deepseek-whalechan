# Run schema v12

Use this contract for new assignments and frozen prompt construction. Visual QA remains version 9. Generate exactly ten ideas, compare all 45 pairs, select five ideas for one image each, then request one execution confirmation covering the final table, count and worker allocation. Candidate quality is judged comparatively; do not add PASS/FAIL gates or replenish the pool automatically.

New assignments must use v12. Already initialized v10 and v11 runs may still build prompts, record candidates, promote and finalize under their historical contracts; new `validate-assignment` and `init` reject those versions. Never rewrite historical assignments or manufacture v12 confirmations. Reject unsupported versions.

Contents: [Root](#root-contract) · [Tournament](#tournament-and-ranking) · [Directions](#comedy-directions) · [Confirmation](#final-plan-and-one-user-gate) · [Images](#image-fragment) · [Output](#output-size-and-aspect-ratio) · [Text](#visible-text) · [Dialogue](#participant-and-dialogue-contract) · [Preflight](#preflight-and-prompt-construction) · [Visual fields](#custom-visual-fields) · [References](#typed-references) · [Execution](#execution)

## Root contract

```json
{
  "schema_version": 12,
  "run_name": "refrigerator-permission-loophole",
  "input": {
    "type": "text",
    "content": "You may eat the things in my refrigerator.",
    "language": "zh-CN",
    "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents",
    "source_analysis": {
      "source_event": "The user permits Whale-chan to eat things inside a refrigerator.",
      "comic_target": "Whale-chan's opportunistic interpretation of permission",
      "tone": "playfully shameless",
      "language_notes": "Only the English source was supplied; Chinese wording is an adaptation.",
      "user_constraints": [],
      "native_direction": {
        "direction": null,
        "reason": "A plain, sincere permission; any joke is Whale-chan's own interpretation."
      }
    },
    "participants": [
      {"id": "user", "role": "user", "source_evidence": "The user grants permission in the quoted request."}
    ]
  },
  "creative_pool": [],
  "duels": [],
  "tie_breaks": [],
  "ranked_ideas": ["idea_01", "idea_03", "idea_06", "idea_08", "idea_10"],
  "selection_reason": "These ideas expose distinct permission boundaries through ownership, access and serving size.",
  "proposal": {},
  "confirmation": {},
  "images": [],
  "panel_policy": {"mode": "narrative"},
  "worker_plan": {
    "coordinator": "main",
    "max_parallelism": 1,
    "workers": [{"id": "worker-1", "idea_ids": ["idea_01", "idea_03", "idea_06", "idea_08", "idea_10"]}]
  },
  "text_style_policy": {"mode": "semantic"},
  "execution": {
    "mode": "sequential",
    "requested_parallelism": 1,
    "max_parallelism": 5,
    "commit_strategy": "coordinator-serial"
  },
  "budget": {"per_image_candidates": 3},
  "warning_dispositions": []
}
```

The example is a root fragment; populate candidates, tournament records, final options, images and the real confirmation before initialization. `creative_pool` contains exactly ten unique `idea_NN` records. Each has `premise`, `punchline`, `fact_anchor`, `scene`, two personality traits, `mechanism`, `key_lines`, `direction` and its carrier fields. `key_lines` is a nonempty list of strings. Do not include `gate`, `gate_reason` or `rejection_reason`.

`ranked_ideas` contains exactly the tournament's top five distinct IDs in final order. `selection_reason` explains the final set. Optional root `warning_dispositions` contains `{code, reason}` entries for structural review warnings such as `rhythm_majority`; a reason never substitutes for semantic review.

Each of five images links to a different selected `idea_id`, retains its `premise` verbatim and uses `execution: 1`. `source_rank` follows the selected order; conflicting values are rejected. Match the displayed option's `panel_count` and exact ordered `key_lines` in `core_text`. Require an individual `execution_note` describing the idea's distinct visible payoff. Shared source wording is allowed; changing lettering, pose or panel count alone does not establish a different joke.

Default `panel_policy` is `{"mode":"narrative"}` and requires all three supported counts, 1, 2 and 4, across the five images. Only a real user instruction permits `{"mode":"user-override","user_instruction":"All five comics must be single-panel closeups."}`. The override relaxes panel variety, not five distinct ideas or five images. Typography and intensity have no quotas.

## Tournament and ranking

Freeze one pool of ten candidates before comparing them. Record exactly 45 unordered pairs, each once; no self-pairs or unknown IDs:

```json
{
  "duels": [
    {"a": "idea_01", "b": "idea_02", "winner": "idea_01", "reason": "The moving refrigerator shows the permission error before any explanation is needed."},
    {"a": "idea_01", "b": "idea_03", "winner": null, "reason": "Both give equally immediate visual consequences, with different emotional payoffs."}
  ],
  "tie_breaks": [
    {"ideas": ["idea_03", "idea_06"], "reason": "With equal total and head-to-head points, the access joke adds a clearer contrast to the already selected ownership joke."}
  ]
}
```

This fragment shows record shapes, not a complete tournament. A winner must be one of the pair or `null` for a draw. Each idea plays nine matches. Award 2 points for a win, 1 to each drawn idea and 0 for a loss. Compare source fidelity, laugh strength, visual contribution, concise dialogue and character specificity; explain actual content rather than assigning unsupported absolute quality scores.

Run `rank-ideas --draft <file>` to compute standings and `ranked_ideas` from `creative_pool`, `duels` and `tie_breaks` before completing the proposal. The script computes `tournament_results`; do not author a second score table. Sort by total points, then points from matches within the entire equal-total group. For every subgroup still tied, supply one `tie_breaks` record with the exact tied IDs in final order and a concrete comparative reason. If no ties remain, use `[]`. Do not use ID or input position to decide the order. `ranked_ideas` must equal the first five of this computed ranking. Keep all ten candidates and all comparisons, including losses; never extend the pool because relative winners seem weak.

## Comedy directions

`input.source_analysis.native_direction` is `{"direction": <direction> | null, "reason": "..."}`. `direction` is one of `reversal`, `exposure`, `escalation`, `recognition`, `character`, or `null` when the source carries no joke of its own. The reason is required either way.

Each pool idea declares one `direction` and its carrier fields; other directions' fields are not required:

```json
[
  {"id": "idea_01", "direction": "reversal", "expectation": "She takes some food.", "reversal": "She takes the refrigerator."},
  {"id": "idea_02", "direction": "exposure", "surface": "A polite, upbeat reply", "truth": "She finds the user tiresome", "exposure": "The open reasoning box shows the complaint"},
  {"id": "idea_03", "direction": "escalation", "steps": ["fixes the typo", "rewrites the sentence", "retitles it", "turns it into a poem"]},
  {"id": "idea_04", "direction": "recognition", "situation": "A 'quick' 580-second nap", "recognition": "Waking five hours later"},
  {"id": "idea_05", "direction": "character", "trait": "rice as compute currency", "trigger": "A takeout coupon pops up mid-reasoning"}
]
```

(Fragments: each idea also needs the common fields above.) `steps` contains at least three strings. A pure character gag uses `direction: character`. Preserving native comedy and avoiding repetitive character gags are comparison preferences, not minimum or maximum direction quotas. No candidate is automatically selected or excluded for its direction. See `comedy-engine.md`.

## Final plan and one user gate

Author the selected five options in ranking order. These are information rows, not alternatives for the user to select. `proposal` contains `revision`, the exact input `fact_anchor`, matching `native_direction`, and exactly five `options`. The option below is a fragment; the other four describe their own winning ideas.

```json
{
  "proposal": {
    "revision": 1,
    "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents",
    "native_direction": {"direction": null, "reason": "A sincere permission without an original joke."},
    "options": [{
      "title": "整台冰箱都是便当盒",
      "idea_id": "idea_01",
      "premise": "She treats the entire refrigerator as her lunch container.",
      "scene": "用户允许取食，鲸鱼娘却把整台冰箱推走。",
      "direction": "reversal",
      "is_native": false,
      "twist": "取出食物变成接管整个容器。",
      "panel_count": 1,
      "staging": "单格全景：用户许可的气泡旁，鲸鱼娘已经推走整台冰箱。",
      "key_lines": ["可以吃冰箱里的东西", "收到，冰箱归我了"],
      "selection_reason": "实物移动使权限偷换比同池中口头争辩的创意更直观。"
    }]
  }
}
```

Each `premise`, `scene` and `direction` matches its pool idea; `twist` equals that idea's `punchline`, preserving the candidate that won. `is_native` is boolean and equals whether the idea direction matches the non-null source direction. No native or character count is forced. `twist` describes any comic landing, not necessarily a reversal. Remove `choice`, ratings, recommended choices, recommendation reasons and root `selection`. Explicit wording revisions may update final `key_lines` within the same idea; do not disguise a replacement premise as a wording edit.

`render-proposal --draft <file>` and `summarize-selection --draft <file>` are read-only views of this same complete planning record. Both return a seven-column table (序号、创意描述、核心场景、方向｜笑点、格数／分镜、关键台词、入选理由), five images total, worker allocations, one execution-confirmation question and `summary_sha256`. The old summary command name does not create a second gate. Drafts do not need full `images` or a confirmation yet.

Show the table, five images per source, combined batch total, worker allocation and per-image budget before asking whether to execute. Planning-only requests stop here without formal initialization or image calls. The sole confirmation record is:

```json
{
  "confirmation": {
    "status": "confirmed",
    "user_reply": "按表格和分工开始执行",
    "summary_sha256": "hash returned for the exact displayed execution plan"
  }
}
```

Hash canonical JSON using SHA-256 (`ensure_ascii=False`, sorted keys, separators `,` and `:`). The plan hash binds `input`, `proposal`, `creative_pool`, `duels`, `ranked_ideas`, `selection_reason`, `worker_plan`, `tie_breaks`, `panel_policy` and normalized `execution`. An edit to any bound content invalidates the old confirmation. Redisplay the revised plan and obtain a real reply; never refresh a stored confirmation hash yourself. Scripts check consistency, not whether a quoted reply actually happened or meant approval.

Full visual `images` are constructed after confirmation and excluded from that planning hash. Their idea links, premises, panel counts and exact visible text must match the approved plan; internal composition details cannot change its comic turn. Initialization, frozen loading and prompt construction enforce the same contract. Five tasks allow at most 15 image calls, three per task. Delivery groups results and missing tasks by their five ideas. See `proposal-selection.md` for interaction details.

## Image fragment

```json
{
  "name": "refrigerator_permission",
  "idea_id": "idea_01",
  "source_rank": 1,
  "execution": 1,
  "execution_note": "The physical appliance leaves rather than merely granting her another serving.",
  "composition": {
    "shot": "wide full-body action shot",
    "staging": "The user reaches from behind as Whale-chan pushes the refrigerator toward the exit.",
    "text_placement": "Short permission bubble beside the owner; ownership claim beside the moving cart.",
    "reason": "Showing the entire stolen appliance makes the scope expansion visible."
  },
  "proportion_check": "measured",
  "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents",
  "premise": "She treats the entire refrigerator as her lunch container.",
  "punchline": "She wheels away the whole refrigerator",
  "why_funny": "The user expects food to be taken, but she steals the permission's scope and takes the refrigerator",
  "personality": ["hungry", "smug"],
  "panel_count": 1,
  "layout": "single",
  "intensity": "C",
  "rhythm": null,
  "output": {
    "format": "png",
    "aspect_ratio": "1:1",
    "resolution": {
      "mode": "auto",
      "recommended": "1024x1024"
    }
  },
  "expression_plan": [
    {"panel": 1, "preset": "smug", "performance": "punchline_peak"}
  ],
  "action_plan": [
    {"panel": 1, "action": "Whale-chan pushes the entire refrigerator away on a cart while the blank indigo user on the left points in disbelief."}
  ],
  "style": {
    "mode": "canonical",
    "description": "canonical clean rounded cel-shaded Whale-chan style"
  },
  "costume": {
    "mode": "canonical",
    "description": "canonical navy-and-white ornate maid outfit"
  },
  "background": {
    "mode": "solid",
    "description": "pure white #FFFFFF"
  },
  "core_text": ["可以吃冰箱里的东西", "收到，冰箱归我了"],
  "text_style": "03_blue-banner",
  "text_style_reason": "Her oversized confident ownership claim overturns the user's modest permission.",
  "dialogue_plan": [
    {"text_index": 0, "panel": 1, "speaker": "user", "delivery": "speech"},
    {"text_index": 1, "panel": 1, "speaker": "whalechan", "delivery": "speech"}
  ],
  "cast_plan": [
    {
      "participant": "user",
      "representation": "physical",
      "panels": [1],
      "staging": "A subordinate blank indigo user stands on the left, pointing at the departing refrigerator in disbelief.",
      "reason": "The owner's visible reaction exposes how far she stretched the permission."
    }
  ],
  "proportion": {
    "mode": "preset",
    "preset": "semi-chibi",
    "target_head_ratio": 2.8,
    "acceptance_range": [2.695, 2.995],
    "proportion_reference": "assets/character-references/semi-chibi/neutral_standing_front_isolated.webp"
  },
  "references": [
    {
      "id": "canonical-identity",
      "path": "assets/character-references/semi-chibi/neutral_standing_front_isolated.webp",
      "roles": ["identity", "style", "costume", "proportion"],
      "instruction": "Preserve only the declared canonical Whale-chan roles; never copy its facial expression"
    },
    {
      "id": "text-style",
      "path": "assets/text-style-templates/03_blue-banner/reference.webp",
      "roles": ["typography"],
      "instruction": "Apply typography treatment only"
    },
    {
      "id": "abstract-user",
      "path": "assets/supporting-character-references/abstract-user-pose-sheet.webp",
      "roles": ["identity"],
      "instruction": "Only the subordinate blank indigo supporting identity; staging is specified as text."
    }
  ]
}
```

Missing optional render fields normalize to the defaults shown above. `rhythm` defaults to `null`; when declared it is `{"type": "triple" | "pause" | "callback" | "deadpan", "panel": <landing panel>, "reason": "why the punchline needs it"}`. When a set of two or more images has rhythm on more than half of them, `validate-assignment` requires a `{"code": "rhythm_majority", "reason": "..."}` entry in the root `warning_dispositions`. `idea_id`, `execution_note`, `composition`, `proportion_check`, `core_text`, `text_style`, `text_style_reason`, `dialogue_plan`, `cast_plan`, `action_plan` and `expression_plan` are required. All four composition fields are nonempty strings. `proportion_check` is `measured` or `visible-only`, chosen from the planned shot. Action and expression plans contain exactly one consecutive entry per panel. Speaker and cast decisions are never inferred from missing fields. Normalized images carry `qa_contract_version: 9`. Every QA record is checked against the complete frozen image specification.

## Output size and aspect ratio

When `output` is omitted, normalization produces PNG, `1:1`, and automatic resolution with `1024x1024` as a recommendation. A recommendation is not an exact-size gate: a provider-native `1254x1254`, `1536x1536`, or any other valid square output satisfies automatic `1:1`.

An aspect ratio without a resolution remains automatic and lets the target provider choose an appropriate native size:

```json
{
  "output": {
    "format": "png",
    "aspect_ratio": "16:9",
    "resolution": {"mode": "auto"}
  }
}
```

Normalization adds `"recommended": null` for a non-default automatic ratio. An explicit resolution may omit the aspect ratio; normalization infers and reduces it:

```json
{
  "output": {
    "format": "png",
    "resolution": {"mode": "explicit", "width": 1920, "height": 1080}
  }
}
```

The normalized ratio is `16:9`. When both ratio and explicit resolution are supplied, they must agree exactly. Width and height are positive integers. Provider adapters may reject an otherwise valid output contract with `capability` when that provider cannot guarantee the requested ratio or exact pixels; this causes ordered fallback, never silent resizing.

## Visible text

Every image requires a non-empty ordered `core_text` list and exactly one bundled `text_style`:

```json
{
  "core_text": ["收到", "冰箱归我了"],
  "text_style": "03_blue-banner",
  "text_style_reason": "A confident banner magnifies her shameless ownership claim."
}
```

Follow the input's main language and prefer Simplified Chinese for Chinese or mixed Chinese input. Content, punctuation, whitespace, order, and language are frozen. `text_style` is one id from `text-style-routing.md`; its `reference.webp` must be the image's sole `typography` reference.

The default root `text_style_policy` is `{"mode":"semantic"}` with no minimum template count. A user-requested uniform treatment is represented explicitly:

```json
{
  "text_style_policy": {
    "mode": "uniform",
    "template": "07_casual-dialogue",
    "user_instruction": "Use casual-dialogue lettering and bubbles for all five comics."
  }
}
```

All confirmed images then use that exact template. Quote a real user instruction; do not fabricate one or infer it from a request for consistent character art. Under `semantic`, legitimate repeated lettering does not need a user override. A non-empty reason or varied count does not establish semantic quality: review choices against the source and routing guidance before initialization.

## Participant and dialogue contract

For `image` and `screenshot` sources, `input.content` is the source file path or a list of paths (relative to the assignment or absolute); validation requires the files to exist so `init` can freeze them. Put the transcription of what the image shows in `source_analysis.source_event`, never in `content`. Planning drafts follow the same rule.

`input.participants` lists supporting interlocutors as `{id, role, source_evidence}`. IDs are unique lowercase identifiers starting with a letter; `whalechan`, `narrator`, and `device` are reserved. A genuinely solo source explicitly uses `[]`. Preserve meaningful source roles instead of removing them to fit a solo layout.

Each image's `cast_plan` contains exactly one entry for every input participant, including deliberately omitted roles:

- `participant`: an input participant ID.
- `representation`: `physical`, `avatar`, `offscreen`, or `absent`.
- `panels`: distinct one-based panel numbers where the figure or voice participates; `absent` requires `[]` and all other modes require at least one panel.
- `reason`: a concrete narrative reason for the chosen representation. All modes require it; offscreen/absent choices receive particular semantic scrutiny.
- `staging`: pose, placement, scale, facing and interaction for `physical` or `avatar`; `null` for nonvisual modes.

Physical and avatar roles require the bundled abstract-user pose sheet. Offscreen/absent-only plans must not load it. A card avatar is counted separately and cannot satisfy a physical-character plan. `cast_plan` is the sole source of participant representation and staging.

Each `dialogue_plan` entry contains `{text_index, panel, speaker, delivery}`. It covers each `core_text` item exactly once, ordered from zero, with nondecreasing panel numbers. `speaker` is `whalechan`, an input participant, `narrator`, or the in-scene `device`; `delivery` is `speech`, `thought`, `caption`, or `label`. Narrators use captions, or labels for printed writing that belongs to no character. A `label` is writing that belongs to an object — a tag, sign, screen title or a short legible excerpt of a poem scroll — drawn on it without a bubble or tail; it also requires `prop`, naming that object, and `speaker` names who wrote it. A prop needs a `label` only when its readable content is part of the joke (a poem, a sign, a title, a tag the punchline points at); then it carries a legible excerpt and any further writing is drawn as clearly non-letter strokes. Ordinary documents whose words do not matter are drawn with plain gray bars and need no label. A supporting speaker must be physical, avatar or offscreen in the assigned panel, never absent. These checks establish consistency; source fidelity and the reason for an omission remain design-review responsibilities.

## Preflight and prompt construction

`validate-assignment` and `init` enforce this structural contract before generation. For multi-input work, pass every assignment to `validate-batch` with repeated `--assignment` flags. Its design summary includes distributions, a case-by-position matrix and repetition warnings. Warnings require source-grounded review, not arbitrary rotation. A structurally valid batch still requires creative review even when no warnings appear. Save the actual cross-case decisions in `batch-review.md` alongside the assignments before generating; see `batch-review.md` in this reference directory. Categories of cast representation can overlap within an image.

`build-prompt.py --run-dir <run> --image <id>` reads the frozen assignment and verifies its required assignment and reference hashes through the run manager. It writes `staging/<id>/prompt-01.txt` without overwriting and returns the ordered reference paths. Use that prompt and those references for the initial provider call. Retrying changes the saved retry prompt, not the frozen assignment. Review a semantically unsuitable plan before starting a new run rather than rewriting history.

## Custom visual fields

`style.mode` and `costume.mode` are `canonical` or `custom`. Custom mode requires a description and replaces only that field. `background.mode` is `solid` or `custom`; any resolved color, gradient, scene, environment, texture, or graphic field is allowed.

Custom ratio example:

```json
{
  "proportion": {
    "mode": "custom",
    "preset": null,
    "target_head_ratio": 5.0,
    "acceptance_range": [4.85, 5.15],
    "proportion_reference": null
  },
  "identity_anchor_form": "standard"
}
```

Custom targets are finite numbers greater than `1.0`. If only a target is supplied, normalization proposes `target ± 0.15`, keeping the lower bound above `1.0`. The identity anchor remains bundled but loses the `proportion` role.

## Typed references

References may be bundled or user supplied. Allowed roles are `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, and `proportion`. The run manager inspects every image, records metadata and SHA-256, and freezes external files inside the run. Shared roles require instructions that resolve their responsibilities. The effective set contains one through five references, starts with one canonical identity anchor, and contains exactly one bundled text-style `reference.webp` whose variant matches `text_style` and whose sole role is `typography`.

## Execution

`worker_plan.coordinator` is exactly `main`. `workers` contains unique worker `id` values and nonempty `idea_ids` lists. Every selected idea is assigned exactly once across those lists; unknown ideas and duplicate assignments are invalid. `max_parallelism` is 1–5 and equals the number of planned workers, using actual available capacity rather than invented slots.

`execution.requested_parallelism` equals `worker_plan.max_parallelism`; use `sequential` for 1 and `parallel` above 1. `execution.max_parallelism` remains the supported ceiling of 5. `commit_strategy` is always `coordinator-serial`. Runtime initialization records a possibly lower `effective_parallelism`; it only throttles scheduling and does not silently reassign approved ownership. Changing worker assignments requires a revised plan confirmation. Workers use isolated staging directories and never mutate the manifest; the coordinator records results and performs final set review.
