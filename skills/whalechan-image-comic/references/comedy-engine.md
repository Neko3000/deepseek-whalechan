# Comedy engine

## Understand the source before adapting it

Record `input.source_analysis` before exploring premises:

- `source_event`: what actually happens and who speaks;
- `expectation`: what the audience reasonably expects;
- `actual_turn`: what violates or reframes that expectation;
- `comic_target`: who or what the joke is about;
- `tone`: the source's emotional register, including bitterness or affection;
- `language_notes`: meaningful differences between supplied language versions, or explicitly state that none were supplied/found;
- `user_constraints`: the user's actual corrections and locked interpretations, or `[]`.

Separate evidence from interpretation. Do not claim certainty about an ambiguous pun. Read all supplied language versions; a literal translation can lose a social meaning or change who is being mocked. Preserve explicit user corrections unless they conflict with what can safely be depicted; report conflicts instead of silently substituting another joke.

## Explore mechanisms, not a fixed menu

Generate enough genuinely distinct premises to find five worthwhile executions. A premise record contains `expectation`, `reversal`, `premise`, `punchline`, `personality`, `fact_anchor`, `scene`, a short `mechanism`, and an actual `gate_reason`. Keep unsuccessful candidates when they were genuinely considered; neither PASS nor FAIL has a quota.

Possible mechanisms include strategic literalism, selective denial, status exposure, conversational misreading, linguistic ambiguity, direct verbal aggression, reaction-based revelation, outer performance versus inner truth, effort/output anticlimax, and bittersweet recognition. These are examples, not ordered slots. Do not select the same mechanism sequence for every case.

Self-serving theft of meaning works when the source supports it: preserve the normal reading, let Whale-chan exploit another reading, and show the consequence. It is not a universal requirement. A source-specific reaction or silence can deliver the reveal; do not invent a personal advantage just to make it qualify. Avoid replacing an insult, a clown/self-exposure joke or a sincere return with generic food, laziness or technical spectacle.

## Evaluate actual candidates

For each premise ask:

1. Is the recognizable source event preserved, including speaker and target?
2. Does the turn follow from that source rather than a random association?
3. Can the audience understand the expectation and payoff without an explanation?
4. Does the drawing add information through an action, expression, juxtaposition, reveal or timing?
5. Does Whale-chan's delivery remain recognizable without forcing the same motive every time?
6. Does each major scene element serve this joke?

Reject illustrated summaries, decorative reaction poses, unrelated meme slang, explanations disguised as dialogue, repeated panels with no new information, and jokes present only in the author's rationale. Distinguish a generic shocked face from a precise reaction that changes the meaning of a line.

If the candidates are weak, revisit the interpretation or explore another mechanism. Record only actual candidates, comparisons and judgments.

## Select, then stage, then number

Select one to five passing ideas in `ranked_ideas`, explaining the tradeoff in `selection_reason`. Use optional pairwise duels only for comparisons actually made; an empty duel list is more honest than a scripted tournament. Judge source fidelity, clarity, surprise, visual contribution and timing, without pretending subjective taste is a numerical measurement.

Allocate five executions to these ideas. Each image links to its real `idea_id` and explains its new payoff in `execution_note`. Allocate executions by the strength and range of the selected ideas. Reusing a premise is fine when the consequence, reveal, emotional angle or final knife materially changes; font, pose and background swaps alone do not count.

Choose framing, panel count, cast placement and text placement from the execution. Record `composition` and the reason for it. Choose lettering independently. Assign image numbers only after these decisions. A helper can serialize authored decisions, but must not compute creative fields, winning ideas or semantic approval from image indices. Never derive the candidate pool backward from finished image plans.

## Control intensity without a quota

- `B`: restrained or moderate delivery, including gentle, dry, bittersweet or sharp verbal humor.
- `C`: heightened delivery, stronger status reversal, accusation, absurd consequence or exaggerated reaction.

Choose intensity from the source's tone and the execution. A quiet close-up may be the strongest punchline. Never use vulnerable groups, private information, hate, discrimination, sexual humiliation or actual harm as a shortcut to a joke. Random cruelty is not a punchline.

## Keep text disciplined

Prefer a compact final knife and short bubbles. Put the strongest word near the end when the language permits it. Preserve meaningful pauses and direct insults when they are the source's mechanism rather than euphemizing them into a different joke. Follow applicable safety limits.

The text should perform the joke, not explain it. Put every intended semantic string, including prop labels, in `core_text` with speaker/delivery attribution. Keep analytical explanations in the creative record. Review the five executions together and, for batches, use `batch-review.md` before generation.
