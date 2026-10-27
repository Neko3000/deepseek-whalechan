# Review workflow — QA11

Contents: [Ownership](#ownership) · [Criteria](#criteria) · [Candidate](#candidate) · [Collection](#collection) · [Failure](#failure) · [Timing](#timing)

## Ownership

For v20 use image-task start/ingest/review-start/submit and collection-task prepare/submit from batch-commands.md. Keep all fourteen actual checks and required form evidence. Scripts fill mechanical metadata only; never default checked declarations or PASS. Service errors pause the locked tool; visual failures alone allow same-tool retries.

Review each returned candidate once, at its original resolution, by one designated reviewer. The coordinator checks files and records through scripts, not by opening the picture again. Keep manifest mutations serial: designated collection/delivery-worker-owned. Only the two visual decisions below authorize image-producing retries.

1. Single-image QA: inspect all fourteen categories in one pass and report all observed core defects.
2. Collection QA: inspect one contact sheet per source's N tasks. If it fails, allow one repair round and one focused collection recheck. Do not add another final visual sweep, cross-source image review, or delivery-time visual review.

Local edits produce new candidates and consume slots. Inspect their whole canvas once. Never infer unchanged pixels from the edit instruction. Generation and repairs use complete canvases.

## Criteria

For v20, inspect against the authored panel actions, `visual_description`, exact dialogue and explicit user locks. Preset names and unused effect menus are planning aids, not additional pixel requirements. Nonessential details left open during planning remain open during QA.

Keep J1 joke, K1 source anchor, I1 identity, C1 cast/performance, P1 panels, T1 lettering/ownership, A1 anatomy, V1 visual/expression, S1 style, O1 costume, B1 background, X1 action, E1 tier and H1 proportion. `checked` explicitly attests that the reviewer inspected each category; scripts cannot inspect pixels or prove this assertion.

Treat unreadable or wrong text, missing identity, incorrect speakers, broken narrative order, missing key actions, changed emotion/joke, gross anatomy or material cropping as core defects. Explicit user-locked requirements remain hard requirements.

Accept small mouth/brow variations preserving the intended emotion, unobtrusive sweat/tear/line count differences, and minor edge proximity preserving identity and readability. Record these as `minor_issues`; they do not trigger regeneration. For E1 judge the overall performance, planned contrast and narrative impact. The quantitative manpu palettes and exact face cues in the bundled JSON are creative guidance for QA 11, not automatic rejection thresholds. Preserve exact semantic text, including labels and sound effects.

For measured compositions retain candidate-bound H1 landmark measurement and overlay inspection within the same review. Visible-only shots record a reason and visible cues, never an invented numeric ratio.

## Candidate

the generation worker uses image-task start, ingest, review-start and submit from [batch-commands.md](batch-commands.md#image). Ingest preserves and counts the returned bytes and performs automatic checks. Record review-start when opening the archived candidate, then fill the returned compact report:

```json
{
  "review_status": "reviewed",
  "reviewer": "actual-reviewer-id",
  "method": "direct-image-inspection",
  "checked": ["J1", "K1", "I1", "C1", "P1", "T1", "A1", "V1", "S1", "O1", "B1", "X1", "E1", "H1"],
  "panels": [{"panel": 1, "observed_scene": "Actual visible scene, not copied from the plan"}],
  "text_transcription": ["Actual visible text"],
  "verdict": "PASS",
  "core_defects": [],
  "minor_issues": [{"check": "V1", "detail": "Slight mouth curvature; the intended calm emotion is intact"}],
  "targeted_retry": null,
  "form_evidence": {"mode": "visible-only", "reason": "Planned torso close-up", "observed_cues": ["Large head and short torso"]}
}
```

This example shows structure, not default acceptance. Use one ordered observation per actual panel. A core defect is `{check, detail}`; FAIL requires at least one and a specific `targeted_retry`. A PASS requires exact transcription and no core defects. Measured PASS uses the measurement evidence below. Candidate SHA-256 may be omitted; the manager supplies it, or verifies it when provided.

Submit the compact report with image-task submit from [batch-commands.md](batch-commands.md#image). Its receipt records the verdict and eligible same-tool retry or collection transition. The original three-call budget applies.

## Collection

Use collection-task prepare/submit from [batch-commands.md](batch-commands.md#collection), which merges journals and creates/reuses the sheet. Its local sheet builder is:

```bash
python3 scripts/build-review-sheet.py --run-dir <run>
```

For v20 the script uses ceil(sqrt(N)) columns and ceil(N/columns) rows, preserving all N numbered slots and multi-digit labels. N=5 remains 3×2. Complete images fit without cropping; missing tasks remain gray at their original positions. If a large sheet cannot be meaningfully reviewed at the tool's pixel limit, report that technical limit; do not silently reduce N or add review rounds. `index.json` maps positions to image IDs, premises, exact lines, attempt IDs and hashes. The original candidates remain unchanged. Sheet creation is local and consumes no image budget. If no candidates remain, the script records a skipped collection and no visual call is needed.

Send the sheet and index together for one set review. Inspect only distinctness of ideas/payoffs, identity/style consistency and overall readability/tone. Do not recheck tiny mouths, sweat counts, exact glyphs or other already reviewed single-image details. Small-scale uncertainty is not a core failure.

```json
{
  "review_status": "reviewed",
  "reviewer": "actual-set-reviewer-id",
  "sheet_sha256": "hash from index.json",
  "checked": ["distinctness", "consistency", "overall"],
  "observation": "What the actual sheet shows as a set",
  "verdict": "FAIL",
  "core_defects": [{"check": "distinctness", "images": ["02_image_id"], "detail": "Name the duplicated payoff and comparison image", "targeted_retry": "Correct the execution within its frozen idea"}],
  "minor_issues": []
}
```

`images` names only tasks to repair, not every image mentioned for comparison. For v20 record through collection-task submit.

On first collection failure, only named images with unused slots reopen. Repair them within their frozen plans; each new candidate gets one single-image review. Single-image failures can use the remaining shared budget inside this one repair round. Then build the updated N-slot sheet and submit one focused collection recheck. Keep unchanged candidates as visual context. A recheck cannot name new repair targets or start another collection round. Failed targets become `collection_failed`; exhausted or technically blocked tasks remain missing. If no repair is possible, close the collection without another visual call.

For v20 the delivery worker runs batch-deliver from [batch-commands.md](batch-commands.md#delivery). Its promotion stage runs `promote` for each `collection_accepted` task. The manager revalidates data and hashes without another LLM image inspection. Then `finalize`, using `--allow-partial` for terminal shortfalls, and export the gallery. Do not fill gaps with rejected pictures or restore an earlier set-rejected candidate as a final.

## Failure

- Only a recorded single-image or collection core defect authorizes image-producing retries.
- All returned images count, including invalid PNGs and provider audit failures. At most three calls per image; no transfer or reset on collection repair.
- Automatic metadata, file/hash, schema, audit, promotion, finalization and gallery failures never trigger regeneration. Report or mechanically repair the existing files/records without a new visual judgment.
- Do not bypass a provider safety rejection. Stop dispatch; preserve returned images and mark affected tasks blocked.
- If the premise itself must change, stop the affected task and report the plan conflict. Do not hide a new creative pool or renewed budget in a collection repair.

## Timing

`manifest.events` records generation/review starts, receipt saving, automatic-check completion, single-review recording, sheet creation, collection-review recording, promotion and finalization. The receipt timestamp is when `image-task ingest` receives the saved output, not backend GPU completion time. Pair it with provider/session timestamps when separating transport delay. Record review starts through image-task review-start; never backfill invented timestamps. Scripts enforce stored decisions, not the truthfulness or real-world count of LLM image inspections.

## Proportion evidence — H1

Use within the assigned candidate review. The frozen proportion_check determines measured versus visible-only evidence. Measurement remains part of that review.

### Measured

Run scripts/measure-form.py on the original candidate using its frozen target and acceptance range. Mark skull top excluding hair/headwear, chin, pelvis, knee and sole along the anatomical centerline. Inspect the overlay and correct misplaced landmarks. Report the actual calculated ratio and candidate/target/overlay hashes.

This example illustrates the measured object; coordinates, hashes and ratios come from the actual candidate:

```json
{
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
}
```

Store this object at form_evidence, including candidate_sha256. QA11 fills an omitted top-level report candidate_sha256; its nested measured evidence still requires the actual candidate hash. The target hash binds the frozen proportion. The overlay path and hash identify the inspected measurement artifact.

### Visible-only

For a planned close-up or partial-body view, provide form_evidence with mode: visible-only, a specific reason and nonempty observed_cues. QA11 lists H1 in checked and binds the candidate through the top-level report hash; its compact format has no per-gate verdict map. Describe the visible proportions and report the measurement limitation at delivery. A shot planned as measurable requires measured evidence.

## Model identity observations in the same candidate review

For each registered model in the frozen cast, add one `cast_observations` entry in cast order. Bind `participant`, `character_id`, `representation`, `panels`, `form` and `target_head_ratio` to the plan, and write nonempty `observed_cues` from the actual candidate. Describe its hair/species features, outfit, performance, dialogue ownership and visible proportions; for omitted roles record the observed absence. Do not copy the plan as visual evidence or claim measurements of hidden anatomy.

These observations belong to the existing single candidate inspection, not a second review pass. Mixed identities, missing required actors, costume transfer or changed dialogue ownership are core defects under the existing checks. Minor issues retain the current tolerance policy. Ordinary abstract-only QA records need no additional field. Candidate hashes, the shared three-call budget and the one collection repair round remain unchanged.
