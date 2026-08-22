# Character specification

Whale-chan identity is permanent. Style, costume, background, text, action, and proportion are independently resolved fields whose canonical values are defaults rather than universal locks.

## Permanent identity

Preserve these traits in every mode:

- One recognizable, ageless humanoid Whale-chan with two arms, two legs, paired side whale-fin ears, one forward-curving ahoge, and one coherent whale tail connected naturally to the body.
- Broad round face, large expressive eyes, tiny nose, small expressive mouth, rosy cheek placement, and the characteristic deep-ocean-blue hair mass fading toward cyan curled ends when the confirmed style supports color.
- Stable face construction, hair silhouette, fin-ear placement, ahoge silhouette, tail construction, and decorative density sufficient to distinguish Whale-chan from a generic blue-haired character.
- The requested proportion changes geometry, never apparent age. Do not silently transform the character into a child, giant whale, whale-bodied creature, mermaid, or half-whale.
- Correct anatomy, tail attachment, object geometry, grip, support, and contact for the confirmed action.

A custom medium may simplify, pixelate, flatten, recolor, or stylize these features, but must preserve their recognizable structure. If a request would remove or replace the permanent identity itself, explain the conflict and seek a revised assignment rather than treating it as a style override.

## Canonical style default

When `style.mode` is `canonical`, use the selected preset's bundled primary as style authority:

- Bold near-black navy outer contours with finer interior lines.
- Clean rounded shapes, restrained soft cel shading, and sparse glossy highlights.
- Cool navy, ocean blue, cyan-blue, clean white, warm pale skin, and restrained muted-gold accents.
- Moderate saturation and contrast; avoid unintended neon, washed-out, gray, muddy, painterly, or harshly contrasted rendering.

When `style.mode` is `custom`, follow the frozen description and references carrying the `style` role. Do not reject an intended watercolor, pixel-art, monochrome, painterly, 3D, print, or other rendering choice merely because it differs from the canonical style. Canonical references may still carry `identity`, but must not control style unless `style` is one of their declared roles.

## Canonical costume default

When `costume.mode` is `canonical`, keep the complete navy-and-white ornate maid outfit: white frilled headpiece, navy neck bow with blue gem, dark-navy sleeves and bodice, white frilled collar and apron with the small blue whale emblem, muted-gold piping/embroidery/bows/buttons, white frilled hem and socks, and dark-blue strap shoes. The whale emblem is a graphic, not text.

When `costume.mode` is `custom`, render the frozen costume description and any `costume` references. Do not require canonical garments, emblem, palette, or ornaments. A costume change never implicitly changes identity, style, action, or proportion.

## Background and text defaults

- Default background: solid warm ivory-beige `#F5EADD`, no alpha. A confirmed custom background may contain a complete environment, landscape, texture, border, gradient, or scene. A confirmed transparent background must produce meaningful alpha and no rendered backdrop.
- Default text: none. When enabled, render only the exact frozen content, languages, direction, line breaks, placement, and style. Never inherit source UI or text without authorization.
- Always reject unconfirmed signatures, watermarks, usernames, QR codes, and brand marks.

## Dynamic prompt blocks

Every provider prompt must contain the permanent identity block and only the defaults still active after normalization.

Permanent identity meaning:

```text
DeepSeek Whale-chan, one consistent ageless humanoid character: broad round face, expressive eyes, characteristic deep-ocean-blue-to-cyan curled hair when color is applicable, paired side whale-fin ears, one forward-curving ahoge, and one coherent naturally attached whale tail; two correct arms and two correct legs. Preserve the recognizable face, hair mass, fin-ear placement, ahoge silhouette, and tail construction. Follow the frozen head ratio without changing apparent age. Correct anatomy, contact, and object geometry.
```

Append the canonical style block only for `style.mode: canonical`; otherwise append the complete custom style description and typed style-reference limits. Do the same independently for costume, background, and proportion. Append a strict no-text directive when `text` is null; otherwise append the exact text contract. Add only defect-specific corrections on retries.
