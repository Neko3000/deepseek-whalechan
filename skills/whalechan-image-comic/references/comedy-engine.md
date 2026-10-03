# Comedy engine

## Understand the source before adapting it

Record `input.source_analysis` before exploring premises:

- `source_event`: what actually happens and who speaks;
- `comic_target`: who or what the joke is about;
- `tone`: the source's emotional register, including bitterness or affection;
- `language_notes`: meaningful differences between supplied language versions, or explicitly state that none were supplied/found;
- `user_constraints`: the user's actual creative corrections, locked interpretations and visual requirements for the comic, or `[]`. Process instructions such as "plan only", "no images yet" or "give five proposals" are not constraints; the single generation confirmation governs them, and they must never reach a generation prompt;
- `native_direction`: `{direction, reason}` — the comedy direction the source itself already uses (see below), or `direction: null` when the source is not funny on its own. The reason cites what in the source makes it funny that way, or why it carries no joke of its own.

Separate evidence from interpretation. Do not claim certainty about an ambiguous pun. Read all supplied language versions; a literal translation can lose a social meaning or change who is being mocked. Preserve explicit user corrections unless they conflict with what can safely be depicted; report conflicts instead of silently substituting another joke.

Identify the native direction from how the source actually lands, not from what is easiest to draw. A screenshot that is funny because "this is exactly me" is `recognition` even if a twist could be invented for it. A plain request or statement with no joke of its own ("you may eat what's in my fridge") is `null`; do not assign it a direction just to have one.

## Five directions

Each premise has exactly one primary `direction`. The direction decides which fields carry the laugh. Only `reversal` uses expectation and reversal.

| Direction | Where the laugh comes from | Carrier fields |
|---|---|---|
| `reversal` 反转 | An expectation is broken or reread: strategic literalism, misreading, ambiguity, selective denial | `expectation`, `reversal` |
| `exposure` 暴露/降格 | A front is punctured: outer performance versus inner truth, a blunt put-down, status deflation, self-exposure | `surface`, `truth`, `exposure` (how the truth becomes visible) |
| `escalation` 升级/荒诞 | A small premise is followed rigorously to an extreme | `steps`: three or more escalating beats |
| `recognition` 共鸣/观察 | "That's exactly it" — an accurate, familiar truth, sometimes bittersweet | `situation`, `recognition` (the moment the viewer feels seen) |
| `character` 角色梗 | Whale-chan's established traits are the joke (rice as compute, standby slacking, tsundere denial) | `trait`, `trigger` (what in the source event sets the trait off) |

These describe where the laugh lives, not a menu to rotate through. Several directions can coexist in one comic; record the one that actually carries the punchline and mention the others in `mechanism`.

**Character gags.** Traits may flavor any direction. Prefer a pure character gag only when it competes well against source-specific alternatives; there is no reserved slot or maximum count. Compare how clearly its trigger comes from the source. Removing the trait mentally helps expose a generic sticker whose source has disappeared.

## Relate candidates to the native direction

Use the native direction as evidence about what makes the source funny, not an admission rule. Prefer preserving it when that produces the stronger joke; no candidate is guaranteed a place because it is native. Mark `is_native` truthfully, and mark none native when the source has no native direction. Do not relabel a converted joke to make the pool look balanced.

Review concentration in one direction and repeated character gags as comparative weaknesses where they reduce variety. Explain justified concentration in the review. Do not enforce direction quotas or change a label to silence a warning.

## Rhythm is an optional layer, used sparingly

Rhythm is a delivery technique layered on a direction, never a direction itself: `triple` (rule of three / deliberate repetition), `pause` (a beat of silence), `callback` (a later panel returns to an earlier element), `deadpan` (flat delivery of something absurd). Callbacks stay within one comic.

Default to no rhythm (`rhythm: null`). Most jokes do not need one. Declare it only when removing it would clearly weaken the punchline — for example, a source whose joke *is* the identical reply repeated. The `reason` must say why; "adds rhythm" or "funnier" is not a reason. Review every declared rhythm before freezing and delete those that do not pass this test. When more than half of a set's images declare rhythm, `validate-assignment` raises `rhythm_majority`; confirm each one in `warning_dispositions` or remove the unnecessary ones.

## Generate one pool of ten

Author exactly ten distinct candidates before choosing winners or layouts. Give each a comparable description: premise, primary direction and its carrier fields, punchline/key dialogue, personality, fact anchor, scene, mechanism and visual payoff. Different situations, actions and consequences create different ideas; replacing a noun, pose or prop does not.

Freeze this pool. Do not label candidates PASS/FAIL, apply a creative admission threshold, append an eleventh candidate, or repeatedly regenerate until satisfied. Weak ideas still enter the comparisons. Refine wording without replacing the core idea; preserve the actual candidates and judgments instead of reverse-engineering losers from finished image plans.

Compare source fidelity, clarity, surprise, joke strength, visual contribution, timing, concise dialogue and recognizable character acting. Treat illustrated summaries, decorative reactions, unrelated metaphors, explanation-heavy dialogue and repetitive beats as weaknesses in that comparison, not separate creative rejection gates. Structural correctness, user constraints and image QA remain separate obligations.

Do not force every source into reversal or self-serving wordplay. Native recognition, escalation, blunt exposure and precise reactions can carry a stronger joke than generic food, laziness or technical spectacle.

## Compare every pair, then stage five winners

Run all 45 unique pairwise duels among the ten candidates: each enters nine duels. Record the two candidates, winner or draw, and a content-specific reason. Wins earn two points, draws one each, losses zero. These are match results, not precise measurements of humor. Scripts verify coverage and recompute totals; the agent makes the creative judgments.

After authoring the duels, run `python3 scripts/manage-run.py rank-ideas --draft <draft.json>` to verify the tournament and obtain standings and the top five. This read-only helper needs the pool, duels and any remaining tie decisions; it does not need the presentation table.

Rank by points, then by points in direct matches among candidates tied on total points. Resolve any remaining tie with an authored comparison of concrete strengths and differences from other selected ideas; save that reason. Candidate numbering, input order and storage order must not decide a tie. Keep all ten candidates, 45 results and the final order, selecting the first five without further pools or automatic replacement rounds.

Make exactly one image for each selected idea, linked by `idea_id`. Explain its unique payoff in `execution_note`. A shared source question can recur, but compare answers, final lines and visible consequences across all five. Pose, font and background swaps alone do not establish independence. Fix expression within the frozen idea rather than hiding a replacement in a rewrite.

Choose framing, cast placement, text placement and lettering from each joke, assigning image numbers last. The set must cover 1, 2 and 4 panels unless the user explicitly overrides that policy; do not add empty beats or map rank to panel count. Review the complete five-image plan, then show the information table, image total and worker allocation for the single confirmation in `proposal-selection.md`.

## Control intensity without a quota

- `B`: restrained or moderate delivery, including gentle, dry, bittersweet or sharp verbal humor.
- `C`: heightened delivery, stronger status reversal, accusation, absurd consequence or exaggerated reaction.

Choose intensity from the source's tone and the execution. A quiet close-up may be the strongest punchline. Never use vulnerable groups, private information, hate, discrimination, sexual humiliation or actual harm as a shortcut to a joke. Random cruelty is not a punchline.

## Keep text disciplined

Prefer a compact final knife and short bubbles. Put the strongest word near the end when the language permits it. Preserve meaningful pauses and direct insults when they are the source's mechanism rather than euphemizing them into a different joke. Follow applicable safety limits.

The text should perform the joke, not explain it. Put every intended semantic string in `core_text` with speaker/delivery attribution; writing on an object uses `delivery: label` with its `prop`. A plan or carrier that relies on readable writing (a labelled folder, a poem scroll) must give that writing a `label` line, or describe the prop by shape and color instead; printed writing that belongs to no character uses `speaker: narrator`. Documents whose words do not matter need no label. Keep analytical explanations in the creative record. Review executions within and across the selected proposals and, for batches, use `batch-review.md` before generation.
