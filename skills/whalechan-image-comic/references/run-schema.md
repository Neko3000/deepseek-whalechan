# Run schema v20

New assignments use v20, independent role limits and exclusive image-task journals. Retain QA 11 and the drawing-only visual contract. See agent-orchestration.md for task commands and ownership.

Contents: [Root](#root-contract) · [Selection](#independent-priority-selection) · [Directions](#comedy-directions) · [Confirmation](#final-plan-and-one-user-gate) · [Images](#image-fragment) · [Exaggeration](#exaggeration-tiers) · [Output](#output-size-and-aspect-ratio) · [Text](#visible-text) · [Dialogue](#participant-and-dialogue-contract) · [Preflight](#preflight-and-prompt-construction) · [Visual fields](#custom-visual-fields) · [References](#typed-references) · [Execution](#execution)

See `language-policy.md` for required language records, locale packs, display titles and v19 compatibility.

## Root contract

```json
{
  "schema_version": 20,
  "language": "en",
  "language_overrides": {"visible_text": "zh-Hans"},
  "language_resolution": {"source": "explicit", "reason": "Example: English task with explicitly requested Chinese lettering"},
  "run_title": "Whale-chan illustration",
  "source_id": "source-a",
  "target_images": 5,
  "author_agent_ids": ["actual-author-agent-id"],
  "concept_task_id": "concepts-source-a",
  "pool_sha256": "script-derived-hash",
  "selection_review": {},
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
  "ranked_ideas": ["idea_01", "idea_03", "idea_06", "idea_08", "idea_10"],
  "selection_reason": "These ideas expose distinct permission boundaries through ownership, access and serving size.",
  "proposal": {},
  "confirmation": {},
  "images": [],
  "panel_policy": {"mode": "narrative"},
  "exaggeration_policy": {"mode": "target-ratio", "ratio": {"A": 3, "B": 1, "C": 1}},
  "worker_plan": {"coordinator": "main", "allocation": "dynamic"},
  "text_style_policy": {"mode": "semantic"},
  "execution": {
    "batch_id": "example-batch",
    "planning_mode": "independent-priority-ranking",
    "role_limits": {"planning": 5, "selection": 2, "generation": 5, "codex_generation": 3, "collection": 2, "delivery": 1},
    "batch_limit": 10,
    "scheduling": "source-first-generation-priority",
    "commit_strategy": "worker-serial-merge",
    "tool": {"provider": "codex", "transport": "builtin", "model": "unknown", "on_error": "pause"}
  },
  "budget": {"per_image_candidates": 3},
  "warning_dispositions": []
}
```

The example is a root fragment; populate candidates, independent selection records, final options, images and the real confirmation before initialization. `creative_pool` contains exactly 2N unique `idea_NN` records. Each has `premise`, `punchline`, `fact_anchor`, `scene`, two personality traits, `mechanism`, `key_lines`, `direction` and its carrier fields. `key_lines` is a nonempty list of strings.

`ranked_ideas` contains exactly the first N distinct IDs from selection_review.ranking in final order. `selection_reason` explains the final set. Optional root `warning_dispositions` contains `{code, reason}` entries for structural review warnings such as `rhythm_majority`; a reason never substitutes for semantic review.

Each of N images links to a different selected `idea_id`, retains its `premise` verbatim and uses `execution: 1`. `source_rank` follows the selected order; conflicting values are rejected. Match the displayed option's `panel_count` and exact ordered `key_lines` in `core_text`. Require an individual `execution_note` describing the idea's distinct visible payoff. Shared source wording is allowed; changing lettering, pose or panel count alone does not establish a different joke.

Default `panel_policy` is `{"mode":"narrative"}` and requires all three supported counts, 1, 2 and 4, across N images when N>=3. Only a real user instruction permits `{"mode":"user-override","user_instruction":"All five comics must be single-panel closeups."}`. The override relaxes panel variety, not N distinct ideas or N images. New sources use exaggeration_policy={"mode":"target-ratio","ratio":{"A":3,"B":1,"C":1}}: N=5 requires 3:1:1 exactly; other N are allocated by content close to 60%/20%/20%, with all three present when N>=3. A real user instruction permits {"mode":"user-override","user_instruction":"..."}. Assignments explicitly record the source tier policy; batch-prepare resolves its default before planning. The source inventory and detail/proposal must agree on it, and the existing confirmation projection binds it. Typography has no quota.

## Independent priority selection

target_images is a strict positive integer per source, defaulted to 5 by batch-prepare. Reject bool, strings, zero, negatives and fractional values. It is not limited by the batch concurrency cap. Candidate IDs use idea_ plus at least two digits, including idea_100.

concepts-submit accepts input and creative_pool only, with no full image records. It binds source_id, target_images, author_agent_ids and concept_task_id from the real queue. pool_sha256 hashes the canonical projection of source_id, target_images, input, creative_pool, author_agent_ids and concept_task_id. Input includes original source paths/text and constraints; author contributors survive recovery.

selection-submit accepts the semantic fields below; scripts fill identities and bindings:

~~~json
{
  "review_method": "independent-priority-ranking",
  "source_id": "source-a",
  "target_images": 5,
  "pool_sha256": "the frozen pool hash",
  "reviewer_agent_id": "actual-other-agent-id",
  "selection_task_id": "selection-source-a",
  "ranking": [{"idea_id": "idea_01", "reason": "One short actual comparative reason"}],
  "selection_reason": "Why the first N work as a set."
}
~~~

This illustrates shape only. ranking must contain all 2N candidates exactly once, ordered by comprehensive priority, with no extra score fields. Optional attention_points records risks for detail work. The reviewer must be a different real sub-agent from every author, never main. Selection commands bind the real task owner; merely authoring a different string is not proof of delegation.

The script derives ranked_ideas from ranking[:N]. N proposal.options and N images follow that exact order. Pool, ranking, source and candidate key_lines stay frozen while the author expands selected drawings. No extra candidate pool, early elimination to fewer than N, low-score regeneration or default re-ranking. v20 rejects duels, tie_breaks and tournament_results. N=1/2 relaxes coverage while aiming close to the tier target; N>=3 retains independent panel/tier coverage. The new ratio policy additionally fixes 3:1:1 when N=5.

The confirmation projection additionally includes target_images, source_id, author_agent_ids, concept_task_id, pool_sha256 and the complete selection_review instead of duels/tie_breaks. It retains the existing visual_plan, tool, role policy and QA11 bindings. Subsequent generation task owners remain dynamic.

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

Author the selected N options in ranking order. These are information rows, not alternatives for the user to select. `proposal` contains `revision`, the exact input `fact_anchor`, matching `native_direction`, and exactly N options. The option below is a fragment; the other N-1 describe their own selected ideas.

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
      "exaggeration": "A",
      "contrast": null,
      "proportion": {"mode": "preset", "preset": "semi-chibi"},
      "staging": "单格全景：用户许可的气泡旁，鲸鱼娘已经推走整台冰箱。",
      "key_lines": ["可以吃冰箱里的东西", "收到，冰箱归我了", "咚——！"],
      "selection_reason": "实物移动使权限偷换比同池中口头争辩的创意更直观。"
    }]
  }
}
```

Each `premise`, `scene` and `direction` matches its pool idea; `twist` equals that idea's `punchline`, preserving the candidate that won. `is_native` is boolean and equals whether the idea direction matches the non-null source direction. No native or character count is forced. `exaggeration` is `A`, `B` or `C`; `contrast` is `null` or `{axes, lowered_to}` and must match the image's contrast. `twist` describes any comic landing, not necessarily a reversal. For v20 key_lines must exactly preserve the frozen candidate; content changes require an explicit new planning revision.

New plans record `proportion` on every option using the same preset/custom object as an image: `{"mode": "preset", "preset": "semi-chibi"}` by default, or e.g. `{"mode": "custom", "target_head_ratio": 3.0}`. Preset targets and intervals come from the catalog; custom intervals default to target ± 0.15 with the lower bound above 1.0. All N options must record it if any does. The proposal already participates in the confirmation hash, so changing a planned proportion invalidates that confirmation. Completed images must normalize to the same proportion as their corresponding options.

`render-proposal --draft <file>` and `summarize-selection --draft <file>` are read-only views of this same complete planning record and accept current drafts. Both return an eight-column table (序号、创意、方向、格数、档位、场景／分镜、关键台词、入选理由), with fixed descriptive tier labels, followed by the panel and tier distribution line, target head-to-body ratios, N images total, worker allocations, one execution-confirmation question and `summary_sha256`. Ratios appear below the table, shared when identical or grouped by table row number when different. Drafts require all N selected visual `images`, but no confirmation yet; the scene/staging cells are rendered from those same panel records.

Show the table, N images per source, combined batch total, worker allocation and per-image budget before asking whether to execute. Planning-only requests stop here without formal initialization or image calls. The sole confirmation record is:

```json
{
  "confirmation": {
    "status": "confirmed",
    "user_reply": "按表格和分工开始执行",
    "summary_sha256": "hash returned for the exact displayed execution plan"
  }
}
```

Hash canonical JSON using SHA-256 (`ensure_ascii=False`, sorted keys, separators `,` and `:`). For v20 the plan hash additionally binds the fixed review workflow version, one candidate inspection, minor tolerance, one collection repair round and the two allowed regeneration sources. The plan hash binds input, proposal, creative_pool, ranked_ideas, selection_reason, worker_plan, panel_policy, exaggeration_policy, execution and the independent-selection provenance described above. An edit to any bound content invalidates the old confirmation. Redisplay the revised plan and obtain a real reply; never refresh a stored confirmation hash yourself. Scripts check consistency, not whether a quoted reply actually happened or meant approval.

For v20 the same hash also binds `visual_plan`: normalized drawing settings, proportion, ordered reference roles/instructions/content hashes, framing, panel actions, visible expressions, exact text with its speaker/carrier/position, cast and landing effects. Runtime paths, timestamps and generated IDs are excluded. Full images are required before confirmation; normalization and reference copying preserve this projection. Idea links, panel counts, tiers, contrasts, proportions and exact wording must still match the selected options. No old confirmation can authorize changed visual content.

N tasks allow at most 3N image calls, three per task. See `proposal-selection.md` for the single user gate.

## Image fragment

```json
{
  "name": "refrigerator_permission",
  "title": "Refrigerator permission",
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
  "proportion_check": "visible-only",
  "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents",
  "premise": "She treats the entire refrigerator as her lunch container.",
  "punchline": "She wheels away the whole refrigerator",
  "why_funny": "The user expects food to be taken, but she steals the permission's scope and takes the refrigerator",
  "personality": ["hungry", "smug"],
  "panel_count": 1,
  "layout": "single",
  "exaggeration": "A",
  "landing_panel": 1,
  "contrast": null,
  "effects_plan": [
    {"axis": "effect_lines", "effect": "concentration lines converge on the departing refrigerator"},
    {"axis": "world_reaction", "effect": "the user is knocked to their knees by the gust"}
  ],
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
    {"panel": 1, "preset": "smug", "performance": "manga_burst", "tier": "A",
     "visual_description": "Her half-lidded gaze and broad one-sided grin show exaggerated satisfaction."}
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
    "mode": "custom",
    "description": "low-angle kitchen with an open pantry and tiled floor; every label and screen blank",
    "origin": "tier"
  },
  "core_text": ["可以吃冰箱里的东西", "收到，冰箱归我了", "咚——！"],
  "lettering_description": "Bold dark brush lettering with a blue rectangular caption band and white speech balloons.",
  "text_style": "03_blue-banner",
  "text_style_reason": "Her oversized confident ownership claim overturns the user's modest permission.",
  "dialogue_plan": [
    {"text_index": 0, "panel": 1, "speaker": "user", "delivery": "speech", "placement": "upper left, tail to the user"},
    {"text_index": 1, "panel": 1, "speaker": "whalechan", "delivery": "speech", "placement": "upper right, tail to Whale-chan"},
    {"text_index": 2, "panel": 1, "speaker": "narrator", "delivery": "sfx", "placement": "beside the refrigerator wheels"}
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

Missing optional render fields normalize to the defaults shown above. `rhythm` defaults to `null`; when declared it is `{"type": "triple" | "pause" | "callback" | "deadpan", "panel": <landing panel>, "reason": "why the punchline needs it"}`. When a set of two or more images has rhythm on more than half of them, `validate-assignment` requires a `{"code": "rhythm_majority", "reason": "..."}` entry in the root `warning_dispositions`. `idea_id`, `execution_note`, `lettering_description`, `proportion_check`, `core_text`, `text_style`, `text_style_reason`, `dialogue_plan`, `cast_plan`, `action_plan` and `expression_plan` are required. See `review-workflow.md` for the compact QA JSON and collection records. For v20, composition is optional; supplied shot/staging fields describe necessary shared framing. Every expression requires a nonempty `visual_description`, and every dialogue entry requires a nonempty `placement`. `proportion_check` is `measured` or `visible-only`, chosen from the planned shot. Action and expression plans contain exactly one consecutive entry per panel. Speaker and cast decisions are never inferred from missing fields. Normalized images carry `qa_contract_version: 11`. Every QA record is checked against the complete frozen image specification.

## Exaggeration tiers

`references/exaggeration-tiers.json` is the authority for each tier's ten axes, landing markers, allowed performance levels, sound-effect limits and default background; `exaggeration-tiers.md` explains how to choose them.

- `exaggeration`: `A`, `B` or `C`, the tier of the landing panel. It matches the confirmed option.
- `landing_panel`: the panel where the punchline lands; defaults to the last panel.
- `expression_plan[].tier`: each panel's tier. Setup panels never exceed the landing tier, the landing panel equals `exaggeration`, and each `performance` must be allowed by its tier (`C` up to `heightened`, `B` adds `punchline_peak`, `A` adds `manga_burst`).
- `contrast`: `null` or `{panel, axes, lowered_to, reason}` on the landing panel. `axes` names distinct axes from the tiers file; `lowered_to` is below the image tier. Lowered axes use the lower tier's palette, and landing markers whose axes are all lowered are waived.
- `effects_plan`: the landing panel's key effects as `{axis, effect}`; required for `A` and `B`, optional for `C`.
- Drawn sound effects (`delivery: sfx`) per panel stay within that panel's tier limit: `A` two of at most four characters, `B` one, `C` none. Punctuation and dashes do not count as characters.
- A single-panel image whose face reaches `manga_burst` uses `proportion_check: visible-only`; in a multi-panel image, measure a panel without deformation.

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

The normalized ratio is `16:9`. When both ratio and explicit resolution are supplied, they must agree exactly. Width and height are positive integers. Provider adapters may reject an otherwise valid output contract with `capability` when that provider cannot guarantee the requested ratio or exact pixels; v20 checks compatibility before confirmation and pauses on later errors. Exact output dimensions remain binding.

## Visible text

Every image requires a non-empty ordered `core_text` list and exactly one bundled `text_style`:

```json
{
  "core_text": ["收到", "冰箱归我了"],
  "text_style": "03_blue-banner",
  "text_style_reason": "A confident banner magnifies her shameless ownership claim."
}
```

Write every string in `input.language`: the session language, or the language the user specified for visible text, not automatically the source's language. Content, punctuation, whitespace, order, and language are frozen. `text_style` is one id from `text-style-routing.md`; its `reference.webp` must be the image's sole `typography` reference.

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

Each `dialogue_plan` entry contains `{text_index, panel, speaker, delivery, placement}`. It covers each `core_text` item exactly once, ordered from zero, with nondecreasing panel numbers. `speaker` is `whalechan`, an input participant, `narrator`, or the in-scene `device`; `delivery` is `speech`, `thought`, `caption`, `label` or `sfx`. Narrators use captions, labels for printed writing that belongs to no character, or `sfx` for drawn sound effects; `sfx` always belongs to the narrator and is hand-lettered into the scene without a balloon or tail. A `label` is writing that belongs to an object — a tag, sign, screen title or a short legible excerpt of a poem scroll — drawn on it without a bubble or tail; it also requires `prop`, naming that object, and `speaker` names who wrote it. A prop needs a `label` only when its readable content is part of the joke (a poem, a sign, a title, a tag the punchline points at); then it carries a legible excerpt and any further writing is drawn as clearly non-letter strokes. Ordinary documents whose words do not matter are drawn with plain gray bars and need no label. A supporting speaker must be physical, avatar or offscreen in the assigned panel, never absent. These checks establish consistency; source fidelity and the reason for an omission remain design-review responsibilities.

## Preflight and prompt construction

Author the drawing fields and resolve semantic conflicts before `render-proposal`; see `prompt-design.md`. Missing visual records fail before confirmation. Use absolute external-reference paths during planning; bundled references may be skill-relative.

`validate-assignment` and `init` enforce this structural contract before generation. For multi-input work, pass every planning draft to `validate-batch` with repeated `--draft` flags before displaying the plan, and every confirmed assignment with repeated `--assignment` flags before generating; one call takes one kind. The draft summary covers direction, panel count, tier, staging and key lines from the planned options; the assignment summary adds layouts, templates, shots, beats and cast. Both include distributions, a case-by-position matrix and repetition warnings. Warnings require source-grounded review, not arbitrary rotation. A structurally valid batch still requires creative review even when no warnings appear. Save the actual cross-case decisions in `batch-review.md` alongside the assignments before generating; see `batch-review.md` in this reference directory. Categories of cast representation can overlap within an image.

`build-prompt.py --run-dir <run> --image <id>` reads the frozen assignment and verifies its required assignment and reference hashes through the run manager. It writes `staging/<id>/prompt-01.txt` without overwriting and returns the ordered reference paths. Use that prompt and those references for the initial provider call. Retrying changes the saved retry prompt, not the frozen assignment. Review a semantically unsuitable plan before starting a new run rather than rewriting history.

## Custom visual fields

`style.mode` and `costume.mode` are `canonical` or `custom`. Custom mode requires a description and replaces only that field. `background.mode` is `solid` or `custom`; any resolved color, gradient, scene, environment, texture, or graphic field is allowed. `background.origin` is `tier` when the background follows the image's tier default, or `user` when the user resolved it. An omitted background normalizes to the tier default with `origin: tier`; a tier-C default must be the solid `pure white #FFFFFF`.

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

Use the exact dynamic worker_plan and normalized execution shape in the root example. All sources in one batch share the same batch_id, role_limits, batch_limit and strategy. Role limits are independent and do not multiply by the number of sources. v20 defaults are planning 5, selection 2, generation 5 / Codex 3, collection 2 and delivery 1. Limits are positive integers at most 10; batch_limit is at most 10. Runtime constraints can only lower actual dispatch.

The confirmation binds execution policy. Resident IDs, task ownership, queue timestamps and changing available slots belong in the batch queue, outside the frozen hash. Initial effective_parallelism/effective_subagent_count in the manifest record initialization only; consult batch events for current activity, not those initial observations.

Each image journal at tasks/<image>/state.json binds assignment_sha256, image, owner, task_id, revision, in-flight call, attempt state and events. It is authoritative for single-image attempts and remaining budget. The manifest keeps merged task revisions/hashes and collection decisions. Shared operations acquire a run lock and all affected image locks; they validate candidates and QA before idempotent projection. Re-reading an unchanged journal must preserve later collection/promotion decisions.

Claim unique image ownership before beginning a call. Record begin before invoking the provider and prepare immediately after preserving returned bytes. An unresolved flight prevents another call. Only recorded single-image core failures or collection repair targets allow retries. Finish releases ownership only after single-image resolution. Recovery changes owner after factual reconciliation and never clears flight or replenishes budget.

Use agent-orchestration.md for queue/worker receipts, task dependencies, CLI examples and capacity degradation.

For v20 the confirmation binds execution.tool (provider, transport, model, on_error=pause). Preflight evidence/timestamps live in the batch, outside this semantic projection. The manifest batch_file points to the shared queue, whose execution must match. Batch status distinguishes planning, initializing, preflight_required, ready, paused and complete. Paused is not a finalized shortfall. Batch lock precedes run/image locks for claim, begin and error; never acquire a batch lock while holding a run/image lock. Combination commands release local locks before writing queue receipts. See batch-commands.md.

## Registered model cast (additive v20 fields)

`input.participants[].character_id` may explicitly identify `abstract-user`, `claude`, `gpt`, `gemini`, `grok`, `qwen`, `kimi`, `glm` or `doubao`. Otherwise the complete participant role/id is resolved through registered aliases. Participation still needs source evidence or an explicit user request; merely mentioning a model is insufficient.

Each model in `images[].cast_plan` records `character_id`, `performance` and `interaction`, alongside the existing participant, representation, panels, staging and reason. `form` inherits the image preset/custom proportion unless explicitly overridden. Presets resolve their target from the existing form authority; a custom form needs `target_head_ratio` or an inherited custom target, with optional preset `identity_form` for identity only.

Normalization freezes `form`, `target_head_ratio`, `identity_form`, `reference`, `reference_sha256`, `character_profile` and `profile_sha256`. Profiles include visual identity, costume, fictional personality and bundled display translations. Never edit derived metadata to conceal a changed identity. Offscreen/absent models retain their profile but use null reference/hash. Old abstract-only casts without model fields retain their previous visual projection.

List the exact visible cast sheets in `image.references`, with actor-specific instructions and the `identity` role. Models may additionally control `costume` and preset `proportion`; custom ratios forbid the latter. No model sheet may control style, action or composition. Whale-chan and typography still consume two of the five reference slots. Validation occurs during pre-confirmation visual planning and initialization.

The existing single confirmation binds the normalized cast inside `visual_plan`; no selection gate or new proposal format is introduced. Assignment schemas 19/20, QA11, batch locking, role orchestration and gallery delivery remain in place. Asset catalog v4 adds model/form metadata. As with any catalog change, previously frozen runs require their matching Skill/catalog; do not rewrite their hashes to resume them against a different asset bundle.
