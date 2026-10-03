# Assignment schema v5

Schema v5 stores the complete confirmed result of field-by-field resolution. `mode` records whether a value came from the canonical default or a custom request; consumers must not re-merge defaults or reinterpret references. Historical schemas, including v4, are rejected without migration or fabricated approval records.

## Root object

```json
{
  "schema_version": 5,
  "proposal": {},
  "selection": {},
  "scope": {"configurations": []},
  "confirmation": {
    "status": "confirmed",
    "user_reply": "确认",
    "summary_sha256": "hash returned for the displayed scope",
    "confirmed_at": "ISO-8601 timestamp"
  },
  "input": {
    "type": "text",
    "content": "original input",
    "focus": null
  },
  "run_name": "semantic-kebab-name",
  "image_count": 1,
  "images": [],
  "execution": {
    "mode": "sequential",
    "requested_parallelism": 1,
    "max_parallelism": 5,
    "commit_strategy": "coordinator-serial"
  },
  "budget": {
    "per_image_candidates": 8,
    "per_provider_candidates": 2,
    "run_candidates": 8,
    "confirmed_over_24": false
  }
}
```

Required invariants:

- Both real user decisions and their matching hashes are required before initialization. The root example is a fragment: fill proposal, selection, scope and images before validation.
- `image_count` equals `images.length`; names are unique snake_case strings.
- `run_name` is kebab-case and the image order is frozen.
- Candidate limits are positive, `per_image_candidates <= 8`, and `run_candidates` covers the confirmed maximum. A value over 24 requires `confirmed_over_24: true`.
- `requested_parallelism` is an integer from 1 through 5. `mode` is `sequential` when it is 1 and `parallel` otherwise. Effective parallelism is runtime evidence, not a frozen promise.
- `commit_strategy` is always `coordinator-serial`.

Screenshot `input.content` must contain an existing file path or an ordered list of paths, resolved relative to the assignment JSON when not absolute. Initialization archives these inputs under `source/original-01.*`, etc., for offline gallery export. This does not change reference roles or approval records.

## Proposal and Gate 1

A planning draft needs only `proposal`. For `explore`, author five distinct options A–E. For `direct`, provide the user's specified scenes without adding alternatives; `request` preserves the user instruction supporting that mode. Options require unique uppercase-letter choices, ratings 1–3 and nonempty descriptive fields. Recommendations must name displayed choices.

```json
{
  "proposal": {
    "revision": 1,
    "mode": "direct",
    "request": "画一张全身鲸鱼娘挥手图，不要文字",
    "options": [{
      "choice": "A",
      "title": "轻轻招手",
      "scene": "鲸鱼娘站立问候",
      "action_expression": "右手挥手，温柔微笑",
      "composition": "全身居中，正面",
      "visual_text": "标准女仆装、semi-chibi、米白背景、无文字",
      "rating": 3,
      "recommendation_reason": "完整呈现用户指定的问候动作"
    }],
    "recommended_choices": ["A"]
  },
  "selection": {
    "proposal_sha256": "hash returned by render-proposal",
    "user_reply": "选 A，一张",
    "choices": [{"choice": "A", "count": 1}],
    "adjustments": []
  }
}
```

Omitted selection counts mean **1**, not 3 or 5; explicit counts must be positive integers. Preserve exact real replies and record only explicit user changes. A changed proposal requires a new Gate 1 record.

## Scope and Gate 2

Before Gate 2, add `run_name`, `execution`, `budget` and `scope.configurations`. Each configuration has:

| Field | Contract |
| --- | --- |
| `id` | Unique snake_case name, such as `wave` |
| `choice` | Selected proposal letter |
| `count` | Positive image count for this configuration |
| `variation` | Explicit permitted execution variation, or a statement that the scene is fixed |
| `requirements` | Resolved locked fields using the image-field structures below |

Requirements must include `subject`, `action`, `composition`, `style`, `costume`, `background`, `text`, `proportion`, `references` and `output`. Also include `expression`, `props`, `objects`, `counterpart` and `pairwise_minimum_head_ratio_gap` when user-locked or relevant to a paired assignment. Omitted optional fields may be authored within the approved variation; include them to lock exact values. Use separate configuration groups for different approved ratios, actions, wording or output settings. Counts per proposal must equal Gate 1 selections.

Run `summarize-selection` and show its Markdown. Preserve the returned normalized configurations and reference hashes. After the actual affirmative reply, write the confirmation shown in the root fragment with its `summary_sha256` and ISO timestamp. For an approved ceiling above 24, set `confirmed_over_24: true`; the raised budget is approved at Gate 2, not a third gate.

The summary hash covers the complete proposal and selection, run name, requested execution, candidate limits, configuration counts/variation and normalized requirements. Typed reference hashes, IDs, roles and instructions are included; storage paths and derived image metadata are excluded. Setting `confirmed_over_24` after consent and adding derived `estimated_maximum` do not alter that hash. The numeric budget itself does.

Hashes use SHA-256 of canonical JSON (`ensure_ascii=False`, sorted keys, compact separators). Changed requirements or reference bytes invalidate confirmation. Changed image expansion is rejected against confirmed requirements, even if the summary is unchanged. Hashes cannot prove actual human consent or semantic fidelity.

After Gate 2, expand exactly each configuration's count. Every image requires `proposal_choice`, `configuration_id` and `execution_note`. Copy locked fields from its requirements unchanged; assign names/order and author permitted details internally. Validate and initialize without another routine approval. `validate-assignment`, `init` and frozen-run loading check the same approval contract. Initialization freezes external references from both scope and images into run inputs; their new paths do not invalidate consent. Old runs remain untouched.

## Image object

```json
{
  "name": "gentle_wave",
  "proposal_choice": "A",
  "configuration_id": "wave",
  "execution_note": "Execute the selected greeting scene with the approved gentle expression",
  "subject": "one Whale-chan",
  "expression": "gentle smile",
  "action": "waves with her right hand",
  "composition": "full body, centered, front view",
  "props": [],
  "objects": [],
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
    "description": "warm ivory-beige #F5EADD"
  },
  "text": null,
  "proportion": {
    "mode": "preset",
    "preset": "semi-chibi",
    "target_head_ratio": 2.8,
    "acceptance_range": [2.689, 2.989],
    "proportion_reference": "assets/reference-images/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp"
  },
  "references": [
    {
      "id": "canonical-identity",
      "path": "/absolute/path/to/assets/reference-images/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp",
      "roles": ["identity", "style", "costume", "proportion"],
      "instruction": "Canonical Whale-chan identity anchor"
    }
  ],
  "output": {
    "format": "png",
    "aspect_ratio": "1:1",
    "alpha": false,
    "resolution": {
      "mode": "provider-native",
      "width": null,
      "height": null
    }
  },
  "counterpart": null
}
```

Schema v5 input is strict: all fields shown above are explicit, including nullable `text` and `counterpart`, empty `props`/`objects`, complete modes, the canonical identity reference, output intent, execution, and budget. Unknown fields are rejected.

`style.mode` and `costume.mode` are `canonical` or `custom`. Their descriptions are always the resolved requirements. A custom style may replace canonical linework, rendering, and palette; a custom costume may replace every canonical garment and ornament. Neither changes permanent identity unless the user revises the assignment.

`action` is always a confirmed free-text requirement, not an override flag. Any physically depictable action is allowed, subject to anatomy and contact QA.

## Background and output alpha

`background.mode` is:

- `solid`: one resolved color or simple solid/gradient field. Default is warm ivory-beige `#F5EADD`.
- `custom`: a resolved environment, landscape, texture, border, graphic field, or other non-solid background.
- `transparent`: no rendered background; the PNG must contain meaningful transparency.

`background.description` is required. `transparent` requires `output.format: "png"` and `output.alpha: true`. `solid` and `custom` require `output.alpha: false` unless the schema is revised and reconfirmed. Transparency is never inferred from PNG format or a reference image.

`output.aspect_ratio` accepts any positive integer `WIDTH:HEIGHT` ratio and defaults to `1:1`. If the user gives only exact width and height, derive and freeze the corresponding ratio. If the user gives both, require the dimensions to match the ratio within validator tolerance.

`output.resolution.mode` is:

- `provider-native`: the default. `width` and `height` are null. Ask the selected provider for the frozen aspect ratio and use its suitable native output. Prefer 1024×1024 for the default square request when the provider exposes a compatible size control, but do not reject a different positive square size solely for differing from that recommendation.
- `exact`: `width` and `height` are positive integers and are hard requirements. Skip a provider with a capability error before generation when it cannot guarantee both values.

Do not silently crop, resize, pad, or normalize a candidate in either mode. Automatic QA checks the actual aspect ratio in both modes and checks exact width and height only in `exact` mode. Every attempt records the frozen requested output, provider-resolved request, and actual decoded output geometry.

## Text and language

No text is represented only by `"text": null`. When visible text is confirmed, use:

```json
{
  "text": {
    "content": "你好 / Hello",
    "languages": ["zh-Hans", "en"],
    "direction": "ltr",
    "placement": "above the character",
    "style": "rounded deep-blue lettering"
  }
}
```

- `content` is the exact final string, including punctuation, whitespace, and line breaks.
- `languages` contains one or more BCP-47 tags. When text is non-null and the user did not specify a language, use `["zh-Hans"]`.
- `direction` is `ltr`, `rtl`, or `vertical`.
- Do not translate, paraphrase, or copy source text without explicit instruction and Gate 2 confirmation of the exact wording.
- A typography reference can guide appearance and layout, never replace `content`.

## Proportion

Preset example:

```json
{
  "mode": "preset",
  "preset": "semi-chibi",
  "target_head_ratio": 2.8,
  "acceptance_range": [2.689, 2.989],
  "proportion_reference": "assets/reference-images/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp"
}
```

Custom example:

```json
{
  "mode": "custom",
  "preset": null,
  "target_head_ratio": 5.0,
  "acceptance_range": [4.85, 5.15],
  "proportion_reference": null
}
```

The target and both bounds must be finite numbers greater than 1.0; the range must contain the target. If the user gives only a custom target, propose `target ± 0.15` and freeze it during confirmation. The five presets and their catalog intervals remain preferred when the request falls into an existing form. A custom ratio may have no proportion reference; identity references remain allowed but must not acquire a `proportion` role implicitly.

## Typed references

```json
{
  "id": "user-style-01",
  "source": "external",
  "path": "/absolute/frozen/input/path/reference.png",
  "roles": ["style", "composition"],
  "instruction": "inherit only the watercolor texture and negative-space composition",
  "format": "PNG",
  "width": 1024,
  "height": 1024,
  "colorspace": "sRGB",
  "sha256": "64 lowercase hexadecimal characters"
}
```

Allowed roles are `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, and `proportion`. A reference may affect only its declared roles. Validation derives `source` (`bundled` or `external`), `format`, `width`, `height`, `colorspace`, and `sha256`; supplied hashes must match and cannot bypass inspection. Every supplied reference must be decodable and included in the Gate 2 summary. During `init`, external references are copied into run inputs, their frozen paths/hashes replace the source paths, and the manifest records the complete assignment hash. Every later state mutation rechecks that assignment and all reference hashes. Conflicts between references with the same role must be resolved in `instruction` or by revising the selected references before confirmation.

## Counterparts and dependencies

`counterpart` is either null or the exact name of another mutually linked image depicting the same action at a different target ratio. Generate and pass the higher-ratio image first. Pairwise QA compares the actual frozen targets and measurements. For presets, use the catalog recommended minimum ratio gap; for custom or mixed pairs, freeze one shared positive comparison gap during confirmation rather than inferring it from form names.
