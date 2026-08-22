# Proportion profiles

Proportion changes body geometry only, never age or identity. Use one recommended preset or a confirmed custom head ratio greater than 1.0. Measure the pose-neutralized skeleton while ignoring ahoge, headwear, hair, skirt, tail, props, and furniture.

## Recommended presets

Read exact targets and ranges from `reference-catalog.json`. Display catalog means rounded to one decimal place but validate against the unrounded ranges.

| Preset | Mean target | Acceptance | Visual definition |
| --- | ---: | ---: | --- |
| `standard` | 4.0 heads | 3.846–4.146 | Most extended bundled form; defined torso and longest natural limbs among the presets |
| `compact` | 3.3 heads | 3.105–3.405 | Compact normal-character form with defined torso and moderately shortened limbs |
| `semi-chibi` | 2.8 heads | 2.689–2.989 | Default; balanced large head, compact torso, and moderately short rounded limbs |
| `chibi` | 2.5 heads | 2.372–2.672 | Oversized head, very short torso, short thick rounded limbs, and small extremities |
| `super-deformed` | 2.1 heads | 1.931–2.231 | Most compressed bundled form; huge head, minimal torso, tiny rounded limbs and extremities |

These are project presets, not universal boundaries. Prefer a preset when the user names it or requests its catalog target. Missing proportion resolves to `semi-chibi`.

Aliases:

- `standard`, `标准`, `常规版`, `4头身` → `standard`
- `compact`, `紧凑版`, `3.3头身` → `compact`
- `semi-chibi`, `半Q版`, `轻Q版` → `semi-chibi`
- `chibi`, `Q版` → `chibi`
- `super-deformed`, `SD`, `超Q版` → `super-deformed`

Never map `幼年化`, `儿童`, or `young` to a proportion preset.

## Custom ratio

Any finite measurable target greater than 1.0 is allowed. If the user supplies only a target, propose an acceptance interval of `target ± 0.15`, clipped above 1.0, and freeze it during confirmation. If a requested value falls in or clearly names a preset, recommend that preset and its catalog evidence; honor an explicit request for custom measurement after confirmation.

For a custom target:

- Set `proportion.mode` to `custom` and record the exact target and confirmed interval. Measurement evidence uses `target_source: custom`; preset evidence uses `target_source: preset`.
- Do not assign a bundled image the `proportion` role unless the user explicitly chose one for that purpose.
- A bundled primary may still anchor `identity`; its body geometry is not authority for the custom ratio.
- Explain before confirmation when no bundled proportion reference exists or when an extreme ratio is likely to require retries. Lack of a reference is not a rejection reason.
- Validate the candidate against the frozen numeric interval and assignment hash, not against the nearest preset's appearance.

## Pose adaptation

- Standing or performing: use a stable stance and reach scaled to the confirmed skeleton. Shrink or reposition props before extending limbs.
- Seated or working: scale furniture to the skeleton. Do not hide elongated or compressed anatomy behind furniture.
- Walking or running: use a stride and knee bend consistent with the target ratio.
- Reclining or airborne: follow the anatomical centerline and bend, overlap, or tuck limbs without changing the frozen ratio.
- Retarget every pose reference onto the confirmed skeleton; never trace body geometry from a reference lacking the `proportion` role.

## Paired proportions

When two images depict the same action at different ratios, link them mutually and generate the higher target ratio first. Preset pairs use the catalog's `pairwise_minimum_head_ratio_gap`. Custom or mixed pairs use an explicitly frozen comparison requirement. QA compares actual candidate measurements, must keep apparent age unchanged, and determines pairing from the frozen target ratios rather than preset names.
