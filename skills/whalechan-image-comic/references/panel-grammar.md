# Panel grammar

## Shared rules

Render one comic using the frozen output contract. The default is an automatic provider-native square with `1024×1024` recommended but not required; explicit user ratios and dimensions take precedence. Make reading order obvious. Keep the fact anchor visible in text or action. Reserve enough negative space for exact text. Do not use experimental panel overlaps.

Make the drawing contribute to the joke rather than merely decorate a caption. An action, prop, status change, expression, silence or juxtaposition may supply the reveal. Do not add empty text containers, decorative UI, or objects without a narrative job.

Freeze one preset or custom head ratio for the task and preserve it in every panel. State each panel's shot and free-text action. A crop is valid only when that shot requires it and the cut does not pass through a face, hand, joint, fin ear, or tail in a confusing way. If the layout is crowded, remove scene detail or shorten text before shrinking, stretching, hiding, or clipping the character.

Repeated panels with no new information fail. The exception is a declared rhythm layer (`triple` or `callback`): deliberate repetition is allowed when the repeated beats are visibly parallel and the final beat deviates. Without a declared rhythm, repetition is still a failure.

Plan one image for each of the five selected ideas. The five-image set must use at least three distinct panel counts: with the supported counts, this means covering 1, 2 and 4 panels. Record any explicit user override to this default policy and show it before confirmation. Choose which idea uses which count from narrative needs, never rank or image index; typography does not determine the count. Rework the distribution if an idea needs fewer panels, so the set still satisfies the policy without empty beats. Different panel counts alone do not prove different jokes.

## Speakers and interaction

Assign every `core_text` entry to a zero-based `text_index`, a panel, a speaker and a `speech`, `thought`, `caption` or `label` delivery. Speaker identity must survive the adaptation. For bodily present partners, the balloon tail points to that figure; thoughts use connectors to their thinker. Narrator captions have no speech tail. A `label` is drawn on its named prop with no bubble. Device playback belongs to the depicted device. Do not attribute all lines to Whale-chan just to simplify framing.

Use `cast_plan` to place each source participant or explain their absence. Record the panels in which the figure or offscreen voice participates. A talking participant cannot be declared absent or omitted from their dialogue's panel. Stage meaningful spatial relationships: left/right, facing, relative scale, pose, contact and reaction. When a partner's reaction is the second joke, show that reaction in the same or following panel rather than substituting a floating question balloon. Match template treatment to this dialogue structure without combining distinct speakers into one container.

## One panel

Use for a single theft of meaning, blunt declaration, identity claim, selective denial, or machine-sincere compliment whose situation is already understood. The drawing and one punchline must carry the whole joke. A generic reaction pose is insufficient.

## Two panels

Use top/bottom for normal reading → stolen reading or permission → self-serving consequence. Use left/right for direct comparison, mutual roasting, outer performance → inner truth, or simultaneous status reversal. Left/right also suits front → truth exposure and situation → recognition. Panel 2 must change, sharpen or escalate the meaning of panel 1; continuation, undeclared repetition, or a new pose alone is a failure.

If the whole-canvas candidate fails cross-panel coherence and exactly two provider slots remain, generate the two panels separately and compose locally. Record both components. Do not use this rescue after a second provider image has already consumed a slot.

## Four panels

Use a `2×2` grid only when four distinct beats are needed. Shape the beats from the proposal's direction. These are examples, not templates:

- **reversal:** establish the expectation → reveal the hinge or private motive → make the normal resolution look possible → land the contradiction.
- **exposure:** the polished front → a crack → the front strains to hold → the truth in full view.
- **escalation:** small → larger → absurd → out of control, with the final step the biggest.
- **recognition:** the situation → a familiar detail → a second detail → the moment the viewer feels seen.
- **character:** the source event → the trait is triggered → the trait takes over → the consequence for the source event.
- **with a `triple` rhythm:** the same beat three times, then a fourth that deviates.

Do not turn four panels into four paragraphs or four status snapshots. Keep each beat visually distinct. If any panel has no unique narrative function, use fewer panels.

Because every task has only three image-producing calls, never rescue a failed four-panel image by generating four new panels. Retry the complete canvas. Local four-panel composition is permitted only from already-existing inputs that consume no new provider calls.

## Prompt panel blocks

Describe each panel with: shot and intentional crop, the frozen free-text action, visible fact anchor, exact text, transition purpose, and new information. State the reading direction and final visual proof. For whole-canvas generation, preserve permanent identity, frozen style, outfit, palette, proportion, torso length, and limb thickness across panels, with no accidental crop.

## Local composition

Use `scripts/compose-panels.py` only for existing panel images. Pass the frozen `--resolution-mode`, `--aspect-ratio`, and explicit `--width`/`--height` when applicable. In automatic mode it derives the canvas width from the first existing panel and computes the frozen ratio. It normalizes each panel with cover cropping, places white gutters, and outputs an exact canvas without stretching the completed montage. It does not add text.
