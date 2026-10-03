# Comedy engine

## Understand the source before adapting it

Record `input.source_analysis` before exploring premises:

- `source_event`: what actually happens and who speaks;
- `comic_target`: who or what the joke is about;
- `tone`: the source's emotional register, including bitterness or affection;
- `language_notes`: meaningful differences between supplied language versions, or explicitly state that none were supplied/found;
- `user_constraints`: the user's actual creative corrections, locked interpretations and visual requirements for the comic, or `[]`. Process instructions such as "plan only", "no images yet" or "give five proposals" are not constraints; the two user gates govern them, and they must never reach a generation prompt;
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

**Character gags.** A character trait may also flavor any other direction without restriction. A *pure* character-gag proposal (`direction: character`) is optional, never a slot to fill: offer one only when it is stronger than the best remaining alternative, not as a default fifth option. When offered: its `trigger` must come from the source event, the fact anchor must stay recognizable (K1), and at most one of the five proposals may be a pure character gag. Remove the trait mentally: if nothing of the source remains, it is a generic sticker, not an adaptation.

## Relate proposals to the native direction

- When `native_direction` is set, at least one proposal must keep that direction and be marked `is_native: true`. It should preserve the source's own laugh, not just its topic.
- The other proposals may move to a different direction when that reveals something real about the source. Mark them `is_native: false`. Never relabel a converted joke as native.
- When `native_direction` is `null`, choose freely and mark none native.
- Four or more proposals in one direction trigger a `same_direction` warning. It is allowed when the source's native direction is genuinely the strongest, but write a source-grounded reason in `proposal.warning_dispositions`; never change a label just to silence the warning.

## Rhythm is an optional layer, used sparingly

Rhythm is a delivery technique layered on a direction, never a direction itself: `triple` (rule of three / deliberate repetition), `pause` (a beat of silence), `callback` (a later panel returns to an earlier element), `deadpan` (flat delivery of something absurd). Callbacks stay within one comic.

Default to no rhythm (`rhythm: null`). Most jokes do not need one. Declare it only when removing it would clearly weaken the punchline — for example, a source whose joke *is* the identical reply repeated. The `reason` must say why; "adds rhythm" or "funnier" is not a reason. Review every declared rhythm before freezing and delete those that do not pass this test. When more than half of a set's images declare rhythm, `validate-assignment` raises `rhythm_majority`; confirm each one in `warning_dispositions` or remove the unnecessary ones.

## Evaluate actual candidates

Explore enough distinct premises to prepare five worthwhile proposals. Each premise record contains `premise`, `direction` with its carrier fields, `punchline`, `personality`, `fact_anchor`, `scene`, a short `mechanism`, and an actual `gate_reason`. Keep unsuccessful candidates when genuinely considered; the pool has no fixed size or PASS/FAIL distribution.

For each premise ask:

1. Is the recognizable source event preserved, including speaker and target?
2. Does the laugh follow from the source rather than a random association?
3. Is its carrier visible without explanation — the broken expectation, the punctured front, each escalation step, the recognizable moment, or the triggered trait?
4. Does the drawing add information through an action, expression, juxtaposition, reveal or timing?
5. Does Whale-chan's delivery remain recognizable without forcing the same motive every time?
6. Does each major scene element serve this joke?

Reject illustrated summaries, decorative reaction poses, unrelated meme slang, explanations disguised as dialogue, repeated panels with no new information (unless a declared rhythm needs the repetition and its last beat deviates), and jokes present only in the author's rationale. Distinguish a generic shocked face from a precise reaction that changes the meaning of a line.

Do not force a source into `reversal`. A recognition or escalation source rewritten as "expected X, got Y" usually loses what made it funny. Self-serving theft of meaning is one reversal tactic, not a universal requirement; avoid replacing an insult, a clown/self-exposure joke or a sincere return with generic food, laziness or technical spectacle.

If the candidates are weak, revisit the interpretation or explore another direction. Record only actual candidates, comparisons and judgments.

## Select, then stage, then number

Offer five passing ideas through the seven-column table and both user gates in `proposal-selection.md`. Explain relative recommendations using source fidelity, clarity, surprise, visual contribution and timing. Do not pretend taste is a precise numerical measurement. Use optional pairwise duels only for actual comparisons. After both gates, set `ranked_ideas` to exactly the user-selected ideas and explain that selection in `selection_reason`; recommendations do not override it.

Allocate the confirmed image count to each selected proposal, defaulting to five per proposal. Each image links to its `idea_id` and explains its new payoff in `execution_note`. Keep the approved central premise, direction and scene; apply explicit user changes and preserve locked wording. Vary the consequence, timing or reveal within that scope. Font, pose and background swaps alone do not count. Changing the core proposal requires renewed user selection and quantity confirmation.

Choose framing, panel count, cast placement and text placement from the execution. Record `composition` and the reason for it. Choose lettering independently. Assign image numbers only after these decisions. A helper can serialize authored decisions, but must not compute creative fields, winning ideas or semantic approval from image indices. Never derive the candidate pool backward from finished image plans.

## Control intensity without a quota

- `B`: restrained or moderate delivery, including gentle, dry, bittersweet or sharp verbal humor.
- `C`: heightened delivery, stronger status reversal, accusation, absurd consequence or exaggerated reaction.

Choose intensity from the source's tone and the execution. A quiet close-up may be the strongest punchline. Never use vulnerable groups, private information, hate, discrimination, sexual humiliation or actual harm as a shortcut to a joke. Random cruelty is not a punchline.

## Keep text disciplined

Prefer a compact final knife and short bubbles. Put the strongest word near the end when the language permits it. Preserve meaningful pauses and direct insults when they are the source's mechanism rather than euphemizing them into a different joke. Follow applicable safety limits.

The text should perform the joke, not explain it. Put every intended semantic string in `core_text` with speaker/delivery attribution; writing on an object uses `delivery: label` with its `prop`. A plan or carrier that relies on a written prop (a labelled folder, a poem scroll) must give that writing a `label` line, or describe the prop by shape and color instead. Keep analytical explanations in the creative record. Review executions within and across the selected proposals and, for batches, use `batch-review.md` before generation.
