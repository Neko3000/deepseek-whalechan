# Form profiles

Choose one recommended preset or a confirmed custom head ratio greater than `1.0` for each comic task. Proportions change body geometry only, never age or permanent identity. `asset-catalog.json` is the authority for preset references, targets, and intervals; custom ratios use the frozen numeric target instead.

| Form | Mean target | Acceptance | Visual definition |
| --- | ---: | ---: | --- |
| `standard` | 4.0 heads | 3.846–4.146 | Most extended project form; defined torso and the longest natural limbs of the five forms |
| `compact` | 3.3 heads | 3.105–3.405 | Compact normal-character form with a defined torso and moderately shortened limbs |
| `semi-chibi` | 2.8 heads | 2.689–2.989 | Default; balanced large head, compact torso, and moderately short rounded limbs |
| `chibi` | 2.5 heads | 2.372–2.672 | Oversized head, very short torso, short thick rounded limbs and small extremities |
| `super-deformed` | 2.1 heads | 1.931–2.231 | Most compressed SD form; huge head, minimal torso, tiny rounded limbs and extremities |

Treat these as project definitions, not universal industry boundaries. Judge the pose-neutralized skeleton while ignoring ahoge, headwear, hair, skirt, tail, props, furniture, and panel crop.

## Custom ratios

- Accept any finite measurable target greater than `1.0`.
- If the user gives only a target, use `target ± 0.15`, with the lower bound kept above `1.0`, and freeze the interval.
- Set `mode: custom`, `preset: null`, and `proportion_reference: null`.
- Keep the nearest bundled form only as an identity anchor. It must not receive the `proportion` reference role.
- Lack of a bundled proportion reference is not a rejection reason. Measure the actual candidate with `scripts/measure-form.py` and validate it against the frozen interval.
- Explain that extreme ratios may require retries, but do not replace them with the nearest preset.

## Pose and panel adaptation

- Standing or performing: keep a stable stance and natural reach for the selected skeleton. Shrink props before extending limbs.
- Seated or working: lower and shrink furniture to meet the body. Do not hide elongated anatomy behind furniture or panel edges.
- Walking or running: use a bent-knee stride appropriate to the form.
- Reclining or airborne: follow the anatomical centerline and bend, overlap, or tuck legs without lengthening the skeleton.
- Retarget every reference action onto the frozen preset or custom skeleton. Never import geometry from a reference without the `proportion` role.
- Preserve the same frozen ratio across every panel. Close-ups may crop intentionally, but visible proportions, head construction, limb thickness, and torso length must remain consistent.
- When a panel is crowded, reduce background detail, prop count, or text before compressing, stretching, hiding, or cropping Whale-chan.

## Measurement applicability

Freeze `proportion_check` with the composition: `measured` for assessable full-body landmarks, or `visible-only` for intentional close-ups/partial-body framing. Do not add a full-body view solely to obtain a number. For measured shots, inspect actual landmarks and the overlay; never choose coordinates merely yielding the target ratio. For visible-only shots, record visible proportions and the crop limitation with `H1: NA`; this does not assert a verified whole-body ratio. An accidental crop or an unassessable promised full-body shot fails rather than changing the frozen check mode.

## Mapping

- Missing form → `semi-chibi`.
- “standard”, “标准”, “常规版”, or “4头身” → `standard`.
- “compact”, “紧凑版”, or “3.3头身” → `compact`.
- “semi-chibi”, “半Q版”, or “轻Q版” → `semi-chibi`.
- “chibi” or “Q版” → `chibi`.
- “super-deformed”, “SD”, or “超Q版” → `super-deformed`.
- Never map “幼年化”, “儿童”, or “young” to a proportion form. Form changes proportions, not apparent age.
