# Offline preview gallery

After generation and QA, finalize the run and export its gallery before delivery. This uses Python 3 and the existing ImageMagick `magick` dependency, with no image API calls or frontend build step.

```bash
python3 scripts/export-gallery.py --run-dir <completed-run>
python3 scripts/export-gallery.py --run-dir <source-a-run> --run-dir <source-b-run> \
  --output artifacts/whalechan-image-comic/<batch-name>/gallery
```

A single run defaults to `<run>/gallery/index.html`. A batch requires `--output`. Existing outputs are preserved by selecting `gallery-02`, `gallery-03`, etc. The command prints the actual HTML path and missing-record warnings as JSON. Link that path in the final delivery. Copy or zip the entire gallery directory when sharing; the HTML needs its adjacent `assets/` folder.

## Organization and interaction

One independent source group or creative theme is one run and one tab. Consecutive screenshots share that run's `input.content` list and proposal set. Preserve the user-specified grouping and order; do not split consecutive screenshots into separate runs just for display. For a batch, export all finalized runs in the requested tab order in one call. A single gallery contains only one skill's runs.

Source/theme tabs wrap into three columns on desktop and two columns at widths up to 700px. Labels wrap in full rather than truncating or requiring horizontal scrolling.

Show original requests, source images and separately labelled visual references above one continuous comic-image grid per source. Display all available candidate, failed-attempt, component and composite images directly; do not create proposal headings or separate proposal image grids. Use the same flat sequence in list view. Keep proposal names, scene descriptions, prompts and QA in each image's collapsed details, and retain selected and unselected summaries under one collapsed records section. Include unselected summaries from the frozen `creative_pool` when proposal options contain only the selected five.

Order comic images by their recorded timestamps, normalizing timezones. Preserve original task/attempt order for equal timestamps; put absent or invalid timestamps last in that same stable order. Retain a separate card for each image-bearing record, even when multiple records have identical bytes. Mark the uniquely matched PASS record as the final and avoid a second card for its final-file copy. If multiple records match, label the candidates as matching the final with ambiguous provenance; do not choose a prompt arbitrarily. Show a standalone final only when no available eligible attempt picture matches it, and expose missing provenance explicitly.

Open any comic card in a lightbox with keyboard navigation across the entire source's flat image sequence, including failed versions, native-size viewing, details and focus restoration. Keep original-input and visual-reference navigation in their own collections. The shared character-gallery branch retains proposal grouping; mirror shared exporters/templates while limiting the flat layout to comic exports.

## Evidence and counts

Finals are matched to recorded candidates by hash, never by assuming the last attempt won. Actual prompts are collapsed and copyable; every candidate keeps its own prompt, provider/model, QA results and recorded defects. Browser clipboard restrictions fall back to selected text for manual copying.

A generation count is the number of image-producing attempts, including failed candidates and comic components. Local composition and promotion add no calls. The flat grid can therefore contain more pictures than generation calls when local composites are included. Errors that returned no image remain text records and never create image cards. Composite comics expose their source components and prompts, not an invented single prompt. A partial run shows failed versions directly with failure badges and preserves gaps in its records; failed candidates never acquire final badges.

The exporter reads supported records without modifying or migrating them: character assignment v5–6 / manifest v3, or comic assignment v10–13 / manifest v1 in the comic skill. It checks the assignment hash and available recorded image hashes, but does not perform or replace visual QA. Missing optional historical files appear as missing, never fabricated. Unsupported schemas, changed hashes and open runs fail export. Setup-blocked runs remain open and resumable under the existing workflow; do not finalize them just to obtain a gallery.

Character screenshot inputs must name existing files, absolute or relative to the assignment file. New runs archive them as `source/original-01.*`, etc. Text requests remain text. Historical source files are used only when their recorded paths still resolve. Source interpretations are labelled separately from user wording.

Image files are copied byte for byte and deduplicated by content hash. HTML embeds its script, styles and data; all image paths are relative, and no network access or `fetch()` is needed. Prompt/source text is rendered as text. Gallery folders remain portable after being moved. In-repository gallery templates/exporters are mirrored in both skills so either skill can be installed alone; keep mirrored files identical when editing them.
