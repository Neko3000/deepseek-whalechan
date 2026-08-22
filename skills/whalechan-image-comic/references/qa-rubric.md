# QA rubric

Reject when any applicable gate fails. Inspect the original-resolution candidate, including small text and panel edges.

## Automatic gates

- `F1`: decodable PNG; automatic mode matches the frozen aspect ratio at any provider-native resolution, while explicit mode matches the frozen width and height exactly. Non-square automatic ratios allow small provider rounding; automatic `1:1` still requires equal edges.
- `F2`: RGB/sRGB image without alpha.
- `R1`: prompt, provider, model, reference hashes, candidate hash, and QA records exist.
- `N1`: frozen name is preserved and no path is overwritten.

Run `scripts/validate-image.py` with the assignment's `resolution.mode`, `aspect_ratio`, and explicit dimensions when applicable. Automatic QA schema v2 records the full expected output contract and actual metadata; the run manager rejects QA made against a different contract and enforces R1/N1.

## Visual gates

- `J1 joke`: the normal reading, specific semantic hinge, Whale-chan's self-serving alternate reading, and final knife are immediately legible. The turn is surprising before it lands and traceable after it lands; it is neither a flat retelling nor a random metaphor.
- `K1 anchor`: viewer can identify the source event from the comic.
- `I1 identity`: permanent face, eye identity, hair mass, fin ears, ahoge, coherent tail, and humanoid identity remain recognizable. Custom style, costume, or proportion is judged against the frozen assignment rather than canonical defaults.
- `C1 character`: Whale-chan's concrete desire and tactic cause her to make an active choice that changes the outcome; replacing her with a generic cute maid would materially weaken the joke. Abstract cast stays subordinate.
- `P1 panels`: count, layout, order, continuity, and timing match the assignment. Every panel has a distinct narrative job; each later beat changes or sharpens the earlier meaning instead of merely repeating it.
- `T1 text`: exact language and wording are complete, readable, correctly ordered, and visually match the selected template.
- `A1 anatomy`: hands, feet, limbs, tail, props, contacts, and character count are coherent. Furniture and props fit the selected skeleton; anatomy is not stretched or hidden to force the layout.
- `V1 visual`: one decisive action or prop proves the stolen reading and adds a second hit beyond the text. Every crop is intentional. Each panel matches its expression preset and performance level. No watermark, copied sample joke, empty bubble or caption bar, decorative or stray UI, pseudo-text, unexplained symbol, meaningless object, accidental crop, or malformed edge.
- `S1 style`: matches the frozen canonical or custom art style and only references carrying `style`.
- `O1 costume`: matches the frozen canonical or custom outfit; custom clothing is not rejected for omitting maid garments.
- `B1 background`: matches the frozen solid or custom background and only references carrying `background`.
- `X1 action`: every panel performs its frozen free-text action with coherent pose, contact, direction, and prop interaction.
- `H1 proportion`: candidate-bound landmark measurement falls inside the frozen preset or custom acceptance interval and remains consistent across panels.

## Visual QA JSON

```json
{
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

A PASS requires all configurable gates PASS, matching hashes, concrete comedy evidence, exact `core_text` transcription, selected-template agreement, resolved style/costume/background/action evidence, candidate-bound form measurement, intentional crops, one ordered expression entry per panel, no defects, and `targeted_retry: null`. Run `scripts/measure-form.py` on the unmodified candidate. Mark skull top excluding hair/headwear, chin, pelvis, knee, and sole along the anatomical centerline; inspect its overlay and rerun when landmarks are misplaced. The calculated ratio must fall inside the frozen preset or custom interval.

A FAIL requires at least one failed gate, specific observable defects, and one primary targeted correction. Do not write “improve it.”
