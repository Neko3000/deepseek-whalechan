# Assignment-aware QA rubric

Reject a candidate when any applicable gate fails. Compare against the frozen normalized assignment, not against defaults that the user replaced. Automatic checks cannot replace original-resolution visual review.

## Automatic gates

| Gate | PASS |
| --- | --- |
| T1 file | Decodable PNG with positive dimensions at the frozen aspect ratio; exact mode additionally requires the frozen width and height |
| T2 alpha | `output.alpha: false` produces RGB/sRGB with no alpha; `output.alpha: true` produces RGBA/sRGB with meaningful transparent pixels |
| M1 record | Assignment hash, provider/model, prompt, typed references and hashes, candidate path/hash, automatic result, visual result, and error category are recorded |
| N1 naming | Run/image names match the frozen assignment and no existing path was overwritten |

Run deterministic checks with the assignment's alpha policy. For the default provider-native mode:

```bash
python3 scripts/validate-image.py <candidate.png> --aspect-ratio <WIDTH:HEIGHT> \
  --resolution-mode provider-native \
  --alpha <forbidden|required> --write-json <automatic.json>
```

For an exact-resolution assignment:

```bash
python3 scripts/validate-image.py <candidate.png> --aspect-ratio <WIDTH:HEIGHT> \
  --resolution-mode exact --width <width> --height <height> \
  --alpha <forbidden|required> --write-json <automatic.json>
```

Do not resize, crop, pad, or otherwise normalize a candidate before either check. A provider-native candidate may differ from the 1024-pixel recommendation; it passes T1 when its decoded dimensions are positive and match the frozen aspect ratio. Meaningful transparency is an output-format invariant and is checked automatically: alpha must reach 5% opacity or lower on at least 1% of pixels. Do not use pixel-color checks to decide whether an opaque background is the requested color or scene. `record-candidate` re-inspects the candidate and rejects automatic JSON whose hash, gates, or metrics differ from fresh inspection.

Each candidate record preserves three distinct facts: the assignment's `requested_output`, the adapter or tool's `provider_output_request`, and the decoded candidate's `actual_output`. Promotion copies the actual output geometry into `final_output`; it never rewrites the requested intent.

## Visual gates

Inspect the original-resolution image, including all edges, text, and small props.

| Gate | PASS |
| --- | --- |
| V1 style | Matches the frozen canonical or custom style description and only the references carrying `style`; intentional custom rendering is not rejected for differing from canonical art |
| I1 identity | Whale-chan's recognizable face, hair mass, fin ears, ahoge, coherent tail, and humanoid identity survive the selected style and proportion |
| I2 costume | Matches the frozen canonical or custom costume; no missing required item or unconfirmed garment imported from a reference |
| F1a head ratio | Candidate-bound landmark calculation falls inside the frozen acceptance range, whether catalog preset or confirmed custom |
| F1b torso | Torso length and shoulder-to-hip span are coherent with the frozen ratio |
| F1c limbs | Arm/leg length and thickness fit the frozen ratio without stretched reach, stride, or hidden incompatible skeleton |
| F1d extremities | Hands and feet are coherent with the target skeleton and action |
| F1e pose retargeting | Confirmed action and contacts are rebuilt on the target skeleton; a pose reference does not override ratio or cause age/body-species transformation |
| P1 theme | Clearly depicts the frozen subject and moment without importing unauthorized source content |
| A1 anatomy | Face, hands, feet, limbs, tail, and visible connections are natural, complete, and not duplicated or fused |
| O1 objects | Prop count, shape, perspective, scale, grip/contact, and liquid/food behavior are coherent |
| C1 composition/background | Expression, action, camera, crop, subject count, composition, and solid/custom/transparent background match the assignment |
| X1 text | Null text produces no visible text/pseudo-text; enabled text exactly matches content, languages, spelling, punctuation, line breaks, direction, placement, and style, with no additional text |
| S1 cleanup | No extra character, unconfirmed mark, malformed edge, unintended border/seam, watermark, signature, username, QR code, or brand mark |

For transparent output, C1 and S1 additionally require a genuinely transparent backdrop, intact character/prop interiors, and clean hair, fin-ear, ahoge, costume, and tail edges without opaque matte, white/beige fringe, or obvious extraction halo.

## Proportion evidence

Inspect the unmodified candidate and mark:

- `head-top`: top of skull, excluding ahoge, hair volume, and headwear.
- `chin`: bottom of chin on the skull axis.
- `pelvis`: center of pelvis under the costume.
- `knee`: center of one representative knee.
- `sole`: bottom of the same foot.

For bent, seated, walking, reclining, or airborne poses, follow the anatomical centerline instead of the canvas bounding box. Run `measure-form.py` with the frozen preset or custom target as supported by the assignment. Review the overlay, correct misplaced landmarks, and rerun when needed. Evidence must bind the candidate hash and frozen proportion target hash; never copy ratios or PASS objects between candidates.

For a preset, pass the identity-anchor form normally. For a custom target, also pass the frozen target and range:

```bash
python3 scripts/measure-form.py <candidate.png> --form <identity-anchor-form> \
  --confirmed-mean-head-ratio <target> --confirmed-acceptance-range <min> <max> \
  --head-top X Y --chin X Y --pelvis X Y --knee X Y --sole X Y \
  --write-overlay <measurement.png> --write-json <measurement.json>
```

The form selects catalog and identity context only in a custom run; it does not become proportion authority.

Use this semantic structure:

```json
{
  "verdict": "PASS",
  "candidate_sha256": "64 lowercase hexadecimal characters",
  "gates": {
    "V1": "PASS",
    "I1": "PASS",
    "I2": "PASS",
    "F1a": "PASS",
    "F1b": "PASS",
    "F1c": "PASS",
    "F1d": "PASS",
    "F1e": "PASS",
    "P1": "PASS",
    "A1": "PASS",
    "O1": "PASS",
    "C1": "PASS",
    "X1": "PASS",
    "S1": "PASS"
  },
  "form_evidence": {
    "measurement_method": "pose-neutralized-skeleton",
    "target_source": "custom",
    "target_sha256": "64 lowercase hexadecimal characters",
    "mean_head_ratio": 5.0,
    "acceptance_range": [4.85, 5.15],
    "head_axis": {"top": [500, 100], "chin": [500, 260]},
    "body_segments": [
      {"name": "chin_to_pelvis", "start": [500, 260], "end": [500, 500]},
      {"name": "pelvis_to_knee", "start": [500, 500], "end": [500, 690]},
      {"name": "knee_to_sole", "start": [500, 690], "end": [500, 900]}
    ],
    "calculated_head_ratio": 5.0,
    "measurement_overlay": "/absolute/path/to/measurement.png",
    "measurement_overlay_sha256": "64 lowercase hexadecimal characters",
    "catalog_sha256": "64 lowercase hexadecimal characters",
    "torso": "observable target-relative assessment",
    "arms": "observable target-relative assessment",
    "legs": "observable target-relative assessment",
    "hands_feet": "observable target-relative assessment",
    "pose_retargeted": true
  },
  "defects": [],
  "targeted_retry": null
}
```

For a preset target, `target_source` is `preset`; for a custom target it is `custom`. `catalog_sha256` and `target_sha256` are required in both modes. `mean_head_ratio` and `acceptance_range` must match the frozen assignment exactly; preset values must also match the catalog.

## Pairwise evidence

When a lower-ratio image links a higher-ratio `counterpart`, inspect both actual outputs together and include:

```json
{
  "pairwise_evidence": {
    "counterpart": "higher_ratio_image_name",
    "expanded_form_head_ratio": 4.96,
    "compact_form_head_ratio": 3.28,
    "head_ratio_clearly_different": true,
    "compact_form_torso_visibly_shorter": true,
    "compact_form_limbs_visibly_shorter": true,
    "apparent_age_unchanged": true
  }
}
```

Both images must link mutually. The higher-ratio PASS must be recorded first. The measured gap must satisfy the frozen `pairwise_minimum_head_ratio_gap`: use the catalog minimum for preset pairs and one explicitly confirmed positive requirement for custom/mixed pairs. A failed lower-ratio candidate may be recorded without pairwise evidence.

Use `FAIL` for any failed gate, list specific observable defects, and provide one targeted retry instruction. A PASS requires every applicable gate to pass, measured ratio within range, current hashes, `pose_retargeted: true`, empty defects, and null retry. Promote only when deterministic and validated visual verdicts both pass.
