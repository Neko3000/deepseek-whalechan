# Cross-case creative review

Run this before the first image call in a multi-source batch and again on the selected final images. Keep the review beside the batch assignments; do not rewrite frozen history.

## Compare sources, not slots

Start with each source's actual turn, comic target, tone, language differences and user corrections. Compare the five selected ideas within each source and across sources in a case-by-position matrix. Each source contributes five images, one per idea; check both the unique creative payoff and the 1/2/4-panel coverage (or the recorded user override). Inspect mechanism, setup/reveal timing, panel count/layout, shot, character staging, text placement and lettering. Also compare across positions: shuffling images can disguise the same recipe.

`validate-batch` provides structural signals, not semantic verdicts. Same-position layouts/templates, identical panel sequences and repeated staging deserve inspection. A repeated visual identity is expected. Neither repeated structure nor every image passing structural checks is automatically wrong; the question is whether each decision follows its source. Different template counts are not proof of different jokes.

Inspect repeated key lines, complete dialogue sequences and final punchlines as well as layout warnings. Cite the affected images. Shared source wording can be necessary, but identical replies and consequences require a concrete explanation or an in-idea revision. A generic claim that all five share a source is insufficient. Text similarity is a review signal, not an automatic elimination threshold or permission to generate another pool.

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

Perform this agent review before displaying the complete plan for the single user confirmation. Review final images again without another routine approval. After confirmation, changes to the core idea or execution allocation require an updated displayed plan and confirmation of that revision. Do not satisfy a warning by random font rotation, forced camera variety, or merely reordering images. If repetition is legitimate, retain it and record why.

## Honest limits

Scripts cannot establish humor or independent visual inspection from prose fields. Record what was actually inspected and leave pending work pending. Compare final images with their sources as well as with each other; a perfectly rendered wrong interpretation still fails.
