# Panel grammar

## Shared rules

Render one comic using the frozen output contract. The default is an automatic provider-native square with `1024×1024` recommended but not required; explicit user ratios and dimensions take precedence. Make reading order obvious. Keep the fact anchor visible in text or action. Reserve enough negative space for exact text. Do not use experimental panel overlaps.

Make the drawing supply a second hit rather than illustrate the caption. Show the decisive action, prop, status change, or hidden motive that proves Whale-chan has acted on her stolen reading. Do not add empty text containers, decorative UI, or objects without a narrative job.

Freeze one preset or custom head ratio for the task and preserve it in every panel. State each panel's shot and free-text action. A crop is valid only when that shot requires it and the cut does not pass through a face, hand, joint, fin ear, or tail in a confusing way. If the layout is crowded, remove scene detail or shorten text before shrinking, stretching, hiding, or clipping the character.

Across five tasks, use at least two panel counts.

## One panel

Use for a single theft of meaning, blunt declaration, identity claim, selective denial, or machine-sincere compliment whose situation is already understood. The drawing and one punchline must carry the whole joke. A generic reaction pose is insufficient.

## Two panels

Use top/bottom for normal reading → stolen reading or permission → self-serving consequence. Use left/right for direct comparison, mutual roasting, outer performance → inner truth, or simultaneous status reversal. Panel 2 must change the meaning of panel 1; continuation, repetition, or a new pose alone is a failure.

If the whole-canvas candidate fails cross-panel coherence and exactly two provider slots remain, generate the two panels separately and compose locally. Record both components. Do not use this rescue after a second provider image has already consumed a slot.

## Four panels

Use a `2×2` grid:

1. establish task or expectation;
2. reveal the semantic hinge or Whale-chan's private motive;
3. make the normal resolution appear possible;
4. prove the self-serving alternate reading and land the real punchline.

Do not turn four panels into four paragraphs or four status snapshots. Keep each beat visually distinct. If any panel has no unique narrative function, use fewer panels.

Because every task has only three image-producing calls, never rescue a failed four-panel image by generating four new panels. Retry the complete canvas. Local four-panel composition is permitted only from already-existing inputs that consume no new provider calls.

## Prompt panel blocks

Describe each panel with: shot and intentional crop, the frozen free-text action, visible fact anchor, exact text, transition purpose, and new information. State the reading direction and final visual proof. For whole-canvas generation, preserve permanent identity, frozen style, outfit, palette, proportion, torso length, and limb thickness across panels, with no accidental crop.

## Local composition

Use `scripts/compose-panels.py` only for existing panel images. Pass the frozen `--resolution-mode`, `--aspect-ratio`, and explicit `--width`/`--height` when applicable. In automatic mode it derives the canvas width from the first existing panel and computes the frozen ratio. It normalizes each panel with cover cropping, places white gutters, and outputs an exact canvas without stretching the completed montage. It does not add text.
