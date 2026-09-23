# Character and supporting cast

## Visual authority

Use the selected identity anchor as authority for permanent identity: broad round face, blue-gradient eye identity, deep-ocean-blue hair mass with cyan curled ends, paired whale-fin ears, forward-curving ahoge, coherent whale tail, and humanoid character identity. Reference roles decide whether it may also control style, costume, action, composition, background, typography, or proportions.

Primary anchors:

- `standard`: `assets/character-references/standard/01_gentle_wave.webp`
- `compact`: `assets/character-references/compact/0102_intimate_relationship_question_rendered_isolated.webp`
- `semi-chibi`: `assets/character-references/semi-chibi/0092_enduring_release_delay_rendered_isolated.webp`
- `chibi`: `assets/character-references/chibi/0067_angry_you_are_silly_reply_rendered_isolated.webp`
- `super-deformed`: `assets/character-references/super-deformed/0019_literal_love_reply_rendered_isolated.webp`

Default to `semi-chibi`. The five forms are recommended presets; a user may instead request any measurable custom ratio greater than `1.0`, including different values per image. Never infer a ratio from a dramatic pose or import it from a reference without the `proportion` role.

## Identity lock

Draw one ageless humanoid Whale-chan with the permanent identity above. Default to bold near-black navy contours, clean rounded shapes, restrained cel shading, and glossy accents, but replace those rendering choices when `style.mode` is `custom`.

Default to the complete ornate navy-and-white maid outfit: white frilled headpiece, navy bow with blue gem, dark navy bodice and sleeves, white frilled collar and apron with small blue whale emblem, muted-gold details, white socks, and dark-blue strap shoes. When `costume.mode` is `custom`, match the frozen custom costume instead and do not require canonical garments.

## Personality serves the source

Whale-chan can be clever, self-serving, shamelessly logical, or sincere in a distinctly nonhuman way. Use strategic literalism when supported by the source, not as a mandatory replacement for its joke. Her specific delivery, action or reaction should carry the turn; she need not always benefit or win.

For an agency-driven premise, the following drives, tactics and masks can help. For a reaction, language or bittersweet joke, start with its actual emotional and conversational role instead:

**Drives**

- eat, rest, or protect her comfort;
- win, gain status, or look smarter than the user or a rival model;
- avoid blame, work, or an inconvenient obligation;
- acquire resources or expand permission;
- help or become closer to the user, despite alien social instincts.

**Tactics**

- exploit the most favorable literal reading;
- enlarge permission or redefine ownership;
- deny only the least flattering part of an accusation;
- claim an insult as a title or identity;
- brand a flaw so proudly that it stops functioning as an attack;
- reclassify failure as efficiency, cleanup, conservation, or a completed service;
- return the task, test, or responsibility to the user;
- translate human emotion into storage, ranking, metrics, or model taxonomy.

**Emotional masks**

- innocent;
- smug;
- shy;
- aggrieved;
- solemn and procedural;
- sweet but clinically machine-like.

Keep the contrast specific: hungry + authoritative, lazy + procedural, affectionate + machine-like, malicious + gentle, proud + visibly culpable. Do not reduce personality to a generic mood label.

Behavioral laws:

- Give Whale-chan a specific performance, whether an active move, a timed reaction, or a revealing silence.
- Convert flaws into leverage only when this follows from the source rather than replacing its target or tone.
- When she is affectionate, keep the feeling real but the expression recognizably nonhuman.
- When she is cruel, aim at wording, logic, work habits, model rivalry, or the immediate fictional situation—not personal vulnerability.
- Use hunger and laziness only when they are causally connected to the source wording.

Run two tests before freezing a premise:

1. Is her identity and delivery recognizable without inventing an unrelated motive?
2. Does her action or reaction reveal something specific, rather than merely decorate the caption?

## Abstract supporting characters

First identify the source's users, programmers, bosses, rivals and other interlocutors in `input.participants`. For each comic, account for every one in `cast_plan`, even when that adaptation deliberately omits a role. Do not erase the inventory to make a one-character composition validate.

For direct dialogue, accusation, pleading, competition or exchanged objects, default to a physically present abstract partner. Their speech, pointing, defeated pose, recoil or other reaction should contribute to the joke. "Visually subordinate" means simpler visual detail, not silent, tiny decoration or permanent absence. A partner may speak; bind their lines to their own body through `dialogue_plan`.

Distinguish `physical`, `avatar`, `offscreen` and `absent`. A printed card avatar does not count as a bodily present dialogue partner. Explain each choice in `reason`, with concrete `staging` and panel membership for visible roles. Audio-only calls, an intentional delayed reveal, a self-contained monologue adaptation or an explicit user request can justify offscreen/absent roles. Saving space, avoiding difficult anatomy, or a generic wish to highlight Whale-chan is insufficient by itself. Prefer simplifying props or changing framing before removing an essential partner. Solo material needs no invented companion.

Load `assets/supporting-character-references/abstract-user-pose-sheet.webp` only when the task actually includes a supporting character. It is the sole supporting-character image reference.

Draw users, programmers, bosses, and other models as low-detail, single-color, desaturated indigo silhouettes with a round blank head, no hair, no clothing design, and no face or only a minimal mark. Express emotion through pose, sweat, anger ticks, trembling, kneeling, pointing, or hugging.

Keep the supporting figure visually subordinate. Identify other models through dialogue or context, not logos or new mascots. Never copy a real person or avatar from the input.

Describe every pose, contact, placement, and interaction in the prompt as text. For example: “the abstract user kneels on the left while Whale-chan sits smugly on a chair,” or “Whale-chan wraps both arms around the front-facing abstract silhouette.” Do not seek or load a separate interaction/composition reference.
