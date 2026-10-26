# Character and supporting cast

## Visual authority

Use the selected identity anchor as authority for permanent identity: broad round face, blue-gradient eye identity, deep-ocean-blue hair mass with cyan curled ends, paired whale-fin ears, forward-curving ahoge, coherent whale tail, and humanoid character identity. Reference roles decide whether it may also control style, costume, action, composition, background, typography, or proportions.

Primary anchors:

- `standard`: `assets/character-references/standard/01_gentle_wave.webp`
- `compact`: `assets/character-references/compact/0102_intimate_relationship_question_rendered_isolated.webp`
- `semi-chibi`: `assets/character-references/semi-chibi/neutral_standing_front_isolated.webp`
- `chibi`: `assets/character-references/chibi/0067_angry_you_are_silly_reply_rendered_isolated.webp`
- `super-deformed`: `assets/character-references/super-deformed/0019_literal_love_reply_rendered_isolated.webp`

Default to `semi-chibi`. The five forms are recommended presets; a user may instead request any measurable custom ratio greater than `1.0`, including different values per image. Never infer a ratio from a dramatic pose or import it from a reference without the `proportion` role.

## Identity lock

Draw one ageless humanoid Whale-chan with the permanent identity above. Default to bold near-black navy contours, clean rounded shapes, restrained cel shading, and glossy accents, but replace those rendering choices when `style.mode` is `custom`.

An `A`-tier `manga_burst` panel may deform the face and silhouette freely — blank eyes, giant mouths, chibi shifts, a face-only gekiga rendering. Identity then rests on the anchors rather than the face: keep at least three of hair, fin ears, ahoge, tail and maid outfit clearly visible, and keep any gekiga rendering on the face instead of the whole canvas.

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

## Supporting-cast eligibility and staging

First identify the source's users, programmers, bosses, models and other actual interlocutors in `input.participants`. Include a new character only when the user explicitly requests that casting. Quote the source event or actual user request in `source_evidence`; never invent participation because a model name appears in a comparison, quoted example or passing mention. For every proposal and comic, account for every participant, including deliberate absence. Do not erase the inventory to make a solo composition validate.

For direct dialogue, accusation, pleading, competition or exchanged objects, default to a physically present partner. Their speech, pointing, defeated pose, recoil or other reaction should contribute to the joke. Whale-chan remains the protagonist, but a partner may speak, react or win when the source requires it. Bind each line to its own speaker through `dialogue_plan`.

Distinguish `physical`, `avatar`, `offscreen` and `absent`. A printed card avatar does not count as a bodily present dialogue partner. Explain each choice in `reason`, with concrete `staging` and panel membership for visible roles. Audio-only calls, an intentional delayed reveal, a self-contained monologue adaptation or an explicit user request can justify offscreen/absent roles. Saving space, avoiding difficult anatomy, or a generic wish to highlight Whale-chan is insufficient by itself. Prefer simplifying props or changing framing before removing an essential partner. Solo material needs no invented companion.

## Ordinary people remain abstract

Draw users, programmers, bosses and other ordinary people as low-detail, single-color, desaturated indigo silhouettes with a round blank head, no hair, no clothing design, and no face or only a minimal mark. Use `character_id: abstract-user` and load `assets/supporting-character-references/abstract-user-pose-sheet.webp` for their `physical` or `avatar` representation only. Express emotion through pose, sweat, anger ticks, trembling, kneeling, pointing, or hugging. Keep visual detail subordinate without making them silent, tiny decoration or permanently absent.

Never copy a real person or avatar from the input. Describe pose, contact, placement and interaction as text; do not load an additional image merely to define an interaction pose.

## Registered model characters

Read `model-characters.json` when Claude, GPT, Gemini, Grok, Qwen, Kimi, GLM or Doubao/Seed actually participates. It is the single authority for aliases, original detailed visual identity, default costume, personality and per-form reference paths. An explicit participant `character_id` maps a generic role such as `assistant`; it must not contradict a role that already names a registered model. Otherwise resolve the participant's complete role or id through registered aliases. Do not infer an actor from a substring mention elsewhere in the material.

Use the model's own hair, species features, outfit and ornaments from `assets/supporting-character-references/models/<id>/<form>.webp`. These are the original detailed designs, not the discarded simplified variants. Do not give every model Whale-chan's maid costume, whale features or anonymous indigo appearance. A reference sheet's front, side and back are views of one actor, never permission to add three copies.

Use the registry personality as a baseline, then freeze a source-specific `performance` and narrative `interaction` for each proposal. Claude's baseline is the well-bred young lady from a distinguished family（显赫教养型大小姐）. Personalities guide delivery, reactions and choices; they do not authorize invented rivalry, moral superiority, new motives or a different punchline. Explicit user changes and the source's actual tone take precedence.

Default to the proposal's `semi-chibi` form, about 2.8 heads; display the current form and approximate ratio rather than opening another mandatory question. Presets are `standard` about 4.0, `compact` 3.3, `chibi` 2.5 and `super-deformed` 2.1. Custom ratios use a nearby preset sheet for identity and any declared costume role, never to replace the requested body ratio. Preserve each model's frozen form across panels. The 40 bundled model sheets have accepted natural variation; their inclusion does not create a stricter remeasurement gate or change Whale-chan's existing 15-reference form authority.

Visible models require their selected identity reference. Offscreen/absent models keep their frozen identity, personality and form metadata but have no loaded image reference. With Whale-chan and typography occupying two of five slots, at most three other effective reference images remain; an abstract-person sheet also uses a slot. Raise any shortage during planning and resolve the cast visibly with the user rather than silently removing actors or dropping identity references.
