# Reference image index

References are typed evidence, not global visual authority. Each reference may control only the roles declared in the frozen assignment: `identity`, `style`, `pose_action`, `composition`, `costume`, `background`, `typography`, or `proportion`.

Resolve each field independently in this order:

1. Explicit confirmed user requirement.
2. Confirmed references carrying that field's role and instruction.
3. Canonical default for an unresolved field.
4. Minimal provider completion.

Never let a style reference import its character, costume, text, or background; never let a pose reference import its body ratio; never let typography replace the frozen text content.

## Bundled presets

`reference-catalog.json` is the path, hash, ratio, and mean authority. This file supplies semantic roles.

### `standard`

Primary: `standard/01_gentle_wave.webp`

- `01_gentle_wave`: identity, canonical style, canonical costume, preset proportion, front standing, gentle wave.
- `03_light_turning_step`: turning pose, short step, back three-quarter composition.
- `05_side_reclining_pose`: reclining pose, floor-cushion contact, overlapped legs.

### `compact`

Primary: `compact/0102_intimate_relationship_question_rendered_isolated.webp`

- `0102`: identity, canonical style, canonical costume, preset proportion, front standing, conversation.
- `0080`: seated pose, armchair contact, relaxed gesture.
- `04_light_turn`: turning pose, short step, skirt contact.

### `semi-chibi` — default

Primary: `semi-chibi/0092_enduring_release_delay_rendered_isolated.webp`

- `0092`: identity, canonical style, canonical costume, preset proportion, front standing, emotional expression.
- `0015`: dynamic standing pose, hand gesture, short step.
- `0076`: seated pose, chair contact, front composition.

### `chibi`

Primary: `chibi/0067_angry_you_are_silly_reply_rendered_isolated.webp`

- `0067`: identity, canonical style, canonical costume, preset proportion, wide stance, pointing, anger.
- `0054`: carrying a bowl, food contact, raised fist.
- `0057`: reclining pose, belly touch, overlapped legs.

### `super-deformed`

Primary: `super-deformed/0019_literal_love_reply_rendered_isolated.webp`

- `0019`: identity, canonical style, canonical costume, preset proportion, neutral standing, small fist gesture.
- `0040`: airborne pose, flailing, chair interaction, panic.
- `0081`: prone pose, floor contact, exhaustion.

## Assign bundled roles

For a fully canonical preset, use that preset's primary with `identity`, `style`, `costume`, and `proportion`; add only the nearest useful auxiliary with `pose_action` or `composition`. Do not upload all assets.

Remove a role whenever the corresponding field is custom:

- Custom style: remove `style` from bundled references.
- Custom costume: remove `costume`.
- Custom ratio: remove `proportion` unless the user explicitly chose an image as proportion evidence.
- Custom background or typography: bundled character references receive neither role by default.

The primary may remain as an `identity` anchor after other roles are removed. For an uncataloged action, describe it in the prompt; a pose reference is optional. Bundled references must stay within the selected identity-anchor form. A separately supplied user reference may carry `pose_action` regardless of its source proportions only when its geometry is explicitly retargeted to the frozen ratio.

## User references

Validate each supplied file as a decodable image and derive its format, dimensions, colorspace, and SHA-256. Freeze its `id`, path, roles, and a short inheritance instruction during confirmation; during run initialization, copy external files into immutable run inputs and replace their source paths with the frozen copies. List exactly which files will be sent to the provider.

Use the smallest set that communicates the confirmed requirements. If references conflict within one role, resolve priority or combination in their instructions before confirmation. If a provider cannot accept all confirmed references or preserve their roles, do not silently omit them; route to a capable provider or seek a revised confirmation.
