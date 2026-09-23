# QA rubric

Reject when any applicable gate fails. Inspect the original-resolution candidate, including small text and panel edges.

## Design review before generation

Before freezing the assignment, compare the source analysis with the original material and user corrections, then compare each execution, composition and `text_style_reason` with that interpretation. English does not imply casual-dialogue typography. Select lettering for the execution's meaning. Honor a quoted uniformity instruction without mistaking template rotation for creative variety.

Compare `input.participants`, `core_text`, `dialogue_plan`, `cast_plan` and `action_plan` with the source. A direct interlocutor normally appears as an indigo physical partner. Offscreen, avatar and absent choices need a specific narrative purpose; saving space, reducing rendering difficulty, or emphasizing Whale-chan alone is insufficient. Check the whole set for repeated removal of the same partner. A generic reason copied five times is not design evidence. Revise the plan before generating when it fails these checks.

The validator enforces fields, counts, panel membership and reference consistency. It cannot judge truthfulness of a quoted instruction, semantic suitability or the pixels of an image. The agent must actually perform those reviews; do not manufacture PASS records from the assignment alone.

For batches, compare cases both at the same ordinal position and across positions using `batch-review.md`. Inspect mechanism, setup/reveal timing, shots, cast staging and text placement. Same-index patterns are warnings to investigate, not instructions to randomize. Record why a shared structure is justified or what changed; repeat the comparison on the final images.

## Automatic gates

- `F1`: decodable PNG; automatic mode matches the frozen aspect ratio at any provider-native resolution, while explicit mode matches the frozen width and height exactly. Non-square automatic ratios allow small provider rounding; automatic `1:1` still requires equal edges.
- `F2`: RGB/sRGB image without alpha.
- `R1`: prompt, provider, model, reference hashes, candidate hash, and QA records exist.
- `N1`: frozen name is preserved and no path is overwritten.

Run `scripts/validate-image.py` with the assignment's `resolution.mode`, `aspect_ratio`, and explicit dimensions when applicable. Automatic QA schema v2 records the full expected output contract and actual metadata; the run manager rejects QA made against a different contract and enforces R1/N1.

## Visual gates

- `J1 joke`: the source-specific expectation and turn are legible through action, language, reaction or timing. The target and tone survive adaptation; it is neither a flat retelling nor a random metaphor. A self-serving alternate reading is not required.
- `K1 anchor`: viewer can identify the source event from the comic.
- `I1 identity`: permanent face, eye identity, hair mass, fin ears, ahoge, coherent tail, and humanoid identity remain recognizable. Custom style, costume, or proportion is judged against the frozen assignment rather than canonical defaults.
- `C1 character`: Whale-chan's delivery, action or reaction is specific and recognizable rather than a generic decorative pose. Do not require her to win or benefit when that changes the source. Abstract cast stays subordinate but performs its assigned speech, action or reaction. A required physical partner is not replaced by a card avatar or disembodied voice.
- `P1 panels`: count, layout, order, continuity, and timing match the assignment. Every panel has a distinct narrative job; each later beat changes or sharpens the earlier meaning instead of merely repeating it.
- `T1 text`: exact language and wording are complete, readable, correctly ordered, and visually match the selected template's lettering, emphasis and frame treatment. Speech tails, thought connectors and captions preserve every line's assigned speaker and delivery.
- `A1 anatomy`: hands, feet, limbs, tail, props, contacts, and character count are coherent. Furniture and props fit the selected skeleton; anatomy is not stretched or hidden to force the layout.
- `V1 visual`: action, expression, timing or juxtaposition contributes to the joke beyond decorating text. Every crop is intentional. Each panel matches its expression preset and performance level. No watermark, copied sample joke, empty bubble or caption bar, decorative or stray UI, pseudo-text, unexplained symbol, meaningless object, accidental crop, or malformed edge.
- `S1 style`: matches the frozen canonical or custom art style and only references carrying `style`.
- `O1 costume`: matches the frozen canonical or custom outfit; custom clothing is not rejected for omitting maid garments.
- `B1 background`: matches the frozen solid or custom background and only references carrying `background`.
- `X1 action`: every panel performs its frozen free-text action with coherent pose, contact, direction, and prop interaction.
- `H1 proportion`: for `measured`, candidate-bound landmarks fall inside the frozen interval and proportions remain consistent across panels. For a planned `visible-only` shot, use `NA` with visible-proportion evidence and the limitation; do not assert an unmeasured whole-body ratio. Missing landmarks in a promised measurable shot fail instead of becoming NA.

## Visual QA JSON

Start with `review_status: pending`, not an all-PASS template. A pending draft is not accepted by `record-candidate`/`record-component`/`record-composite` and cannot be promoted. Automatic image checks may already have passed, but they say nothing about visual acceptance. Preserve the returned image immediately and review it before spending another image call; unrecorded output still consumes budget.

Inspect the actual image first, transcribe what is visibly written, and describe each panel before comparing with the frozen plan. Use a separate reviewer/context when available. Both reviewed PASS and reviewed FAIL need `review_status: reviewed` and an `observation` object: candidate hash, reviewer identity, method `direct-image-inspection`, ordered `panels` entries with `panel` and `observed_scene`, and actual `text_transcription`. Component observations cover the inspected component rather than pretending to inspect the whole comic. Text similarity to the plan is expected for a good render, but copying the plan is not inspection. A hash and a reviewer's assertion do not prove truthfulness; the agent remains responsible for examining pixels.

The following illustrates a completed measured review, not default values to prefill:

```json
{
  "review_status": "reviewed",
  "observation": {
    "candidate_sha256": "64 lowercase hexadecimal characters",
    "reviewer": "identifier of the agent or human who actually inspected this image",
    "method": "direct-image-inspection",
    "panels": [{"panel": 1, "observed_scene": "describe the visible scene and location-specific reveal"}],
    "text_transcription": ["exact visible line"]
  },
  "verdict": "PASS",
  "candidate_sha256": "64 lowercase hexadecimal characters",
  "gates": {
    "J1": "PASS",
    "K1": "PASS",
    "I1": "PASS",
    "C1": "PASS",
    "P1": "PASS",
    "T1": "PASS",
    "A1": "PASS",
    "V1": "PASS",
    "S1": "PASS",
    "O1": "PASS",
    "B1": "PASS",
    "X1": "PASS",
    "H1": "PASS"
  },
  "evidence": {
    "why_funny": "one concrete sentence",
    "fact_anchor_visible_as": "observable text or action",
    "text_transcription": ["exact visible line"],
    "text_style_match": {
      "template": "03_blue-banner",
      "observed_cues": ["blue banner treatment", "oversized outlined claim"]
    },
    "dialogue_match": [
      {
        "text_index": 0,
        "panel": 1,
        "speaker": "whalechan",
        "delivery": "speech",
        "observed_cues": ["the balloon tail points to Whale-chan's mouth"]
      }
    ],
    "cast_match": [],
    "style_match": "observable match to the frozen style",
    "costume_match": "observable match to the frozen costume",
    "background_match": "observable match to the frozen background",
    "action_match": "ordered observable match to every panel action",
    "form_evidence": {
      "candidate_sha256": "64 lowercase hexadecimal characters",
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
      "measurement_overlay": "/absolute/path/measurement.png",
      "measurement_overlay_sha256": "64 lowercase hexadecimal characters"
    },
    "form_consistency": "observable comparison across all panels",
    "crop_status": "which assigned shots crop the body and why each crop is intentional",
    "expression_match": [
      {
        "panel": 1,
        "preset": "smug",
        "performance": "punchline_peak",
        "observed_cues": ["half-lidded eyes", "one raised mouth corner"],
        "forbidden_cues_present": []
      }
    ]
  },
  "defects": [],
  "targeted_retry": null
}
```

A measured PASS requires all gates PASS, matching hashes, concrete comedy evidence, exact `core_text` transcription, selected-template agreement, resolved style/costume/background/action evidence, candidate-bound form measurement, intentional crops, one ordered expression entry per panel, no defects, and `targeted_retry: null`. Run `scripts/measure-form.py` on the unmodified candidate. Mark skull top excluding hair/headwear, chin, pelvis, knee, and sole along the anatomical centerline; inspect its overlay and rerun when landmarks are misplaced. Never pick coordinates to manufacture a passing ratio.

For `proportion_check: visible-only`, a PASS instead requires `H1: NA`, all other gates PASS, and `form_evidence` with `mode: visible-only`, `candidate_sha256`, a specific `reason` why whole-body measurement is inapplicable, and nonempty `observed_cues` describing visible proportions. Do not include an invented `calculated_head_ratio`. Record the limitation in delivery; visible-only review is not numeric ratio verification. Other gates do not accept NA.

For full comics, `text_style_match` names the frozen template and concrete visible cues; `dialogue_match` has one ordered entry per planned line with matching `text_index`, `panel`, `speaker`, `delivery` and non-empty `observed_cues`. `cast_match` has one entry per planned participant with matching `participant`, `representation`, `panels` and concrete `observed_cues` describing the figure, avatar, offscreen attribution or verified absence. It is `[]` only for an empty cast plan. A picture of an avatar cannot be recorded as a physical figure. A correct transcript alone does not prove correct typography or attribution.

A FAIL requires at least one failed gate, specific observable defects, and one primary targeted correction. Do not write “improve it.”
