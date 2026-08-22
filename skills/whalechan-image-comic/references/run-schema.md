# Run schema v6

Schema v6 is the only accepted assignment format. It restores required exact visible text and one bundled text-style template per image while retaining the v5 output sub-contract, configurable visual fields, and typed references. Schema v5 is rejected rather than migrated.

## Root contract

```json
{
  "schema_version": 6,
  "run_name": "refrigerator-permission-loophole",
  "input": {
    "type": "text",
    "content": "You may eat the things in my refrigerator.",
    "language": "zh-CN",
    "fact_anchor": "The user permits Whale-chan to eat the refrigerator's contents"
  },
  "creative_pool": [],
  "duels": [],
  "ranked_ideas": ["idea_01", "idea_03", "idea_06"],
  "images": [],
  "execution": {
    "mode": "sequential",
    "requested_parallelism": 1,
    "max_parallelism": 5,
    "commit_strategy": "coordinator-serial"
  },
  "budget": {"per_image_candidates": 3}
}
```

The creative pool contains exactly eight records, duels record winner/loser/reason, the ranking contains three passing ideas, and the five images use rank distribution `3/1/1`, rank-1 executions `1/2/3`, intensity mix `3 C + 2 B`, and at least two panel counts.

## Configurable image fragment

```json
{
  "name": "refrigerator_permission",
  "source_rank": 1,
  "execution": 1,
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
    {"panel": 1, "action": "pushes the entire refrigerator away on a cart"}
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
    }
  ],
  "supporting_character": {"present": false, "interaction": null}
}
```

Missing optional v6 render fields normalize to the defaults shown above. `core_text`, `text_style`, `action_plan`, and `expression_plan` are required; both plans contain exactly one consecutive entry per panel.

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
  "text_style": "03_blue-banner"
}
```

Follow the input's main language and prefer Simplified Chinese for Chinese or mixed Chinese input. Content, punctuation, whitespace, order, and language are frozen. `text_style` is one id from `text-style-routing.md`; its `reference.webp` must be the image's sole `typography` reference.

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
