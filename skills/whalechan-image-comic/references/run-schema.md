# Run schema v9

This contract applies to assignment creation, frozen runs, prompt construction and QA. Source analysis, explicit idea links, independent composition decisions and observed QA are required. Unsupported versions and incomplete required fields are rejected.

## Root contract

```json
{
  "schema_version": 9,
  "run_name": "refrigerator-permission-loophole",
  "input": {
    "type": "text",
    "content": "You may eat the things in my refrigerator.",
    "language": "zh-CN",
    "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents",
    "source_analysis": {
      "source_event": "The user permits Whale-chan to eat things inside a refrigerator.",
      "expectation": "She will take some food, leaving the appliance in place.",
      "actual_turn": "She stretches permission into taking the refrigerator too.",
      "comic_target": "Whale-chan's opportunistic interpretation of permission",
      "tone": "playfully shameless",
      "language_notes": "Only the English source was supplied; Chinese wording is an adaptation.",
      "user_constraints": []
    },
    "participants": [
      {"id": "user", "role": "user", "source_evidence": "The user grants permission in the quoted request."}
    ]
  },
  "creative_pool": [],
  "duels": [],
  "ranked_ideas": ["idea_01", "idea_03", "idea_06"],
  "selection_reason": "These ideas expose distinct permission boundaries through ownership, access and serving size.",
  "images": [],
  "text_style_policy": {"mode": "semantic"},
  "execution": {
    "mode": "sequential",
    "requested_parallelism": 1,
    "max_parallelism": 5,
    "commit_strategy": "coordinator-serial"
  },
  "budget": {"per_image_candidates": 3}
}
```

The nonempty creative pool has no fixed size. Each record has a unique `idea_NN` id, `premise`, `expectation`, `reversal`, `punchline`, `fact_anchor`, `scene`, two personality traits, `mechanism`, `gate` (PASS/FAIL), and a concrete `gate_reason`; FAIL also requires `rejection_reason`. `ranked_ideas` contains one to five unique passing ids. `selection_reason` explains the actual selection. `duels` may be empty; if used, record real winner/loser/reason comparisons. Never synthesize these judgments from ordinals or finished image plans.

The five images link directly to their selected `idea_id` and retain that idea's central `premise` verbatim; execution-specific action, punchline and `execution_note` carry the variation. `source_rank` is derived from the link; a conflicting supplied value is rejected. `execution` is positive and unique within its idea, and execution notes cannot be identical within that idea. No fixed rank distribution, intensity mix, panel-count variety or typography-count quota applies. Five distinct payoffs still require creative review; structural validation cannot prove that they are distinct.

## Configurable image fragment

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
  "premise": "Whale-chan expands permission into ownership",
  "punchline": "She wheels away the whole refrigerator",
  "why_funny": "The user expects food to be taken, but she steals the permission's scope and takes the refrigerator",
  "personality": ["hungry", "smug"],
  "panel_count": 1,
  "layout": "single",
  "intensity": "C",
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
    "acceptance_range": [2.689, 2.989],
    "proportion_reference": "assets/character-references/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp"
  },
  "references": [
    {
      "id": "canonical-identity",
      "path": "assets/character-references/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp",
      "roles": ["identity", "style", "costume", "proportion"],
      "instruction": "Preserve only the declared canonical Whale-chan roles"
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

Missing optional render fields normalize to the defaults shown above. `idea_id`, `execution_note`, `composition`, `proportion_check`, `core_text`, `text_style`, `text_style_reason`, `dialogue_plan`, `cast_plan`, `action_plan` and `expression_plan` are required. All four composition fields are nonempty strings. `proportion_check` is `measured` or `visible-only`, chosen from the planned shot. Action and expression plans contain exactly one consecutive entry per panel. Speaker and cast decisions are never inferred from missing fields. Normalized images carry `qa_contract_version: 9`. Every QA record is checked against the complete frozen image specification.

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

All five images then use that exact template. Quote a real user instruction; do not fabricate one or infer it from a request for consistent character art. Under `semantic`, legitimate repeated lettering does not need a user override. A non-empty reason or varied count does not establish semantic quality: review choices against the source and routing guidance before initialization.

## Participant and dialogue contract

`input.participants` lists supporting interlocutors as `{id, role, source_evidence}`. IDs are unique lowercase identifiers starting with a letter; `whalechan`, `narrator`, and `device` are reserved. A genuinely solo source explicitly uses `[]`. Preserve meaningful source roles instead of removing them to fit a solo layout.

Each image's `cast_plan` contains exactly one entry for every input participant, including deliberately omitted roles:

- `participant`: an input participant ID.
- `representation`: `physical`, `avatar`, `offscreen`, or `absent`.
- `panels`: distinct one-based panel numbers where the figure or voice participates; `absent` requires `[]` and all other modes require at least one panel.
- `reason`: a concrete narrative reason for the chosen representation. All modes require it; offscreen/absent choices receive particular semantic scrutiny.
- `staging`: pose, placement, scale, facing and interaction for `physical` or `avatar`; `null` for nonvisual modes.

Physical and avatar roles require the bundled abstract-user pose sheet. Offscreen/absent-only plans must not load it. A card avatar is counted separately and cannot satisfy a physical-character plan. `cast_plan` is the sole source of participant representation and staging.

Each `dialogue_plan` entry contains `{text_index, panel, speaker, delivery}`. It covers each `core_text` item exactly once, ordered from zero, with nondecreasing panel numbers. `speaker` is `whalechan`, an input participant, `narrator`, or the in-scene `device`; `delivery` is `speech`, `thought`, or `caption`. Narrators use captions. A supporting speaker must be physical, avatar or offscreen in the assigned panel, never absent. These checks establish consistency; source fidelity and the reason for an omission remain design-review responsibilities.

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

`requested_parallelism` is an integer from 1 through 5. It is 1 in sequential mode and greater than 1 in parallel mode. `commit_strategy` is always `coordinator-serial`. Runtime initialization records a possibly lower `effective_parallelism`; this changes scheduling only. Workers use isolated staging directories and never mutate the manifest.
