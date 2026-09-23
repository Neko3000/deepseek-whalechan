# Text-style routing

Choose exactly one primary template **per image**, after deciding that image's semantic hinge and emotional turn. Read that template's bundled `template.md`, declare its `reference.webp` as the sole `typography` reference, and send it to the image provider. Copy treatment only; never copy words or the sample joke. One primary template per image does not imply one template for the whole run or batch.

| Template | Use for |
| --- | --- |
| `01_shy-blue-sticker` | bashful refusal, flustered denial, cute protest |
| `02_keyword-bubble` | excuses, spin, false reassurance, keyword reversal |
| `03_blue-banner` | confident improvisation, shameless conclusion |
| `04_burst-command` | command, exposure, anger, accusation |
| `05_outline-poster` | identity claim, boast, slogan, one-line punch |
| `06_top-bottom-punchline` | setup above, action center, large payoff below |
| `07_casual-dialogue` | food, affection, gentle teasing, relaxed laziness |
| `08_confrontation-dialogue` | loud accusation versus small timid reply |
| `09_vertical-panic` | escalating panic, urgent failure, helpless state |
| `10_manga-impact` | extreme disaster, black comedy, abstract breakdown |

Record `text_style_reason` with the specific setup, reversal, or emotional contrast that the lettering should emphasize. "Consistent series", "English text", "cute", or a repeated generic sentence does not explain a choice. English uses the same routing table; adapt lettering language rather than routing every English comic to `07_casual-dialogue`.

The default `semantic` policy has no template-count quota. Select for semantic fit, then review repetitive executions; do not randomly rotate IDs. For example, an accusation can use `04_burst-command`, a shameless claim `03_blue-banner`, and a sincere returning-user moment `07_casual-dialogue`. These are examples, not a slot schedule. A repeated template needs a source-grounded reason for each execution, not a fabricated user override.

If the user explicitly requests one lettering treatment throughout, set `text_style_policy.mode` to `uniform`, name the `template`, and quote the actual `user_instruction`. Do not invent an override from a request for consistent identity, costume, or art style. The default `semantic` mode requires no extra approval.

Adapt a template's composition to `dialogue_plan`: keep different speakers in distinct attributed containers, use thought connectors for thoughts, and leave captions without speech tails. Preserve the primary template's lettering, emphasis, colors and frame character without collapsing all speakers into its sample balloon.

The template's composition notes are suggestions, not shot or panel mandates. `composition` and `action_plan` determine framing and placement; a `typography` reference controls letterforms and treatment only. Do not inherit a top-headline/character-below layout just because it appears in a lettering example. Do not map image number to a template.

Follow the input's main language. Prefer Simplified Chinese for Chinese or mixed Chinese input. Preserve useful model names, error tokens, and technical terms in their original language when that is funnier. Do not mix languages without a reason.

Quote every required semantic string verbatim in the prompt. Separate semantic `core_text` from nonverbal `flavor_text`. Do not use local fonts or programmatic typesetting.

For a text-only failure, spend the second slot on a text-free but composition-matched base with empty bubbles/headline areas. Spend the third slot editing that base with exact core text and the same template reference. Recheck every character; plausible pseudo-text is a failure.
