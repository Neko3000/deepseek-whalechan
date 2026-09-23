# Cross-case creative review

Run this before the first image call in a multi-source batch and again on the selected final images. Keep the review beside the batch assignments; do not rewrite frozen history.

## Compare sources, not slots

Start with each source's actual turn, comic target, tone, language differences and user corrections. Then compare every case's five executions in a case-by-position matrix. Inspect mechanism, setup/reveal timing, panel count/layout, shot, character staging, text placement and lettering. Also compare across positions: shuffling images can disguise the same recipe.

`validate-batch` provides structural signals, not semantic verdicts. Same-position layouts/templates, identical panel sequences and repeated staging deserve inspection. A repeated visual identity is expected. Neither repeated structure nor all candidates passing is automatically wrong; the question is whether each decision follows its source. Different template counts are not proof of different jokes.

Use two counterfactual checks:

- **Dialogue substitution:** could another case's dialogue replace this one without materially changing the picture? If yes, explain what makes the scene source-specific or redesign it.
- **Ordinal removal:** hide image numbers. Can you still justify each shot, panel count and text treatment from the selected premise? Changing order should only change identifiers, not creative choices.

## Review record

Write `batch-review.md` with:

1. Cases and versions reviewed, with paths to assignments or candidate images.
2. Specific repeated combinations, including those not caught by the script.
3. For each concern, affected cases/images and either a source-grounded reason to retain it or the actual revision made.
4. Any uncertainty requiring source clarification; do not silently assume an ambiguous joke.
5. Conclusion: ready for generation, revise plans, or final images still need review.

This is an agent review, not a mandatory extra user approval. Respect explicit requests to see plans first. Do not satisfy a warning by random font rotation, forced camera variety, or merely reordering images. If repetition is legitimate, retain it and record why.

## Honest limits

Scripts cannot establish humor or independent visual inspection from prose fields. Record what was actually inspected and leave pending work pending. Compare final images with their sources as well as with each other; a perfectly rendered wrong interpretation still fails.
