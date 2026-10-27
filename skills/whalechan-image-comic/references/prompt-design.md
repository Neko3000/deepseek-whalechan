# Drawing-only prompts — drawing contract

For v20 a planning sub-agent authors the selected N-image visual plan after independent selection. Generation workers assemble frozen fields; main coordinates only.

Write the visual plan during the existing planning pass, before the single confirmation. The builder assembles these fields directly; do not add another LLM rewrite, review agent or confirmation. Keep analysis, selection reasons, approval and QA records internal. Every sentence sent to the image model should guide a visible result.

Allocate each source's tier mix during detail planning: exactly 3A/1B/1C for new five-image sets; other N approach 60%/20%/20% by content. Translate each image's assigned tier into visible performance. Keep the batch ratio in internal plans and confirmation summaries; the API prompt contains the individual drawing descriptions.

Write drawing prose in the resolved prompt language and visible dialogue in the resolved visible-text language. For differing communication/prompt languages, provide localized proposal `display_staging` during planning. The rendered plan quotes the drawing fields: translate its scene cells faithfully into the communication language when presenting them, preserving all locked details and exact dialogue. This is presentation within planning, not another rewrite of the image prompt.

## Author the drawing

- Shared settings: layout, style, costume, background, proportion and `lettering_description`. Describe the lettering's appearance, not its template ID or selection reason. Keep the existing typography reference and selection policy.
- `action_plan[].action`: describe the panel's setting, participants and visible moment. Make necessary contact, direction and object state concrete. Include the visible evidence carrying the source fact and joke. Do not merely say “show the reversal.”
- `expression_plan[].visual_description`: name the emotion and a few natural facial/postural cues. Keep presets and performance levels for internal planning, but never paste their entire cue/forbidden lists into the drawing description. Preserve explicit user locks; incidental mouth curves or sweat counts are flexible.
- `dialogue_plan[].placement`: give each text item a readable position alongside its existing speaker, panel and delivery. Labels still require `prop`. `core_text` remains the exact wording authority.
- `cast_plan`: keep it as the authority for supporting-role representation and panels. Registered models also freeze their identity, profile, form, source-specific `performance` and `interaction`. Their reference sheets control only declared actor roles; do not replace them with abstract figures or copy Whale-chan’s costume. Avoid repeating staging in every action unless the interaction requires it.
- Optional `composition.shot` and `composition.staging` supply necessary shared framing. Put panel-specific framing in that panel's action. `effects_plan` supplies selected landing effects, not a menu of possibilities.

Resolve defaults into real appearances. A user-defined setting replaces its corresponding default. Leave unspecified, nonessential camera and decorative choices open. Reference materials and selection are unchanged; reference instructions should identify the relevant visual features.

## Resolve conflicts before confirmation

In the same planning pass, compare each action with its expression, cast, words and framing. Sleeping with closed eyes cannot simultaneously require wide panic eyes. A bent prop must visibly touch the part bending it. Choose a drawable moment; use deliberate afterimages only when they help. Check that dialogue leaves the key action visible and that the source's recognizable fact survives the adaptation.

Translate every explicit user requirement into the relevant drawing field. Convert A/B/C, contrast and rhythm into specific visual choices in those fields. Never drop a necessary action or emotion simply to shorten the prompt. Internal explanations do not compensate for missing visible evidence.

The scripts check panel coverage, word ownership, positions, references and confirmation consistency. They cannot prove semantic compatibility or artistic quality. Do not add a boolean “review passed” to substitute for this reasoning. Fix incomplete drafts before the existing user gate; an actual confirmed-plan change uses the existing revision procedure.

## Output and retries

The generated order is IMAGE, CHARACTERS AND REFERENCES, then PANEL 1..N. Each text entry appears in its panel once, together with its carrier and placement. Intentional repetitions across panels remain separate entries. Never paste dialogue again into action, effect or lettering descriptions; refer to its speaker or position instead. Necessary visual restrictions belong next to the affected description.

Keep source analysis, reasons, template/preset labels, QA tolerances, paths and configuration JSON out of visual prose. Format, size and reference metadata use the supported request parameters. Do not promise unsupported pixel dimensions through prompting.

For an authorized retry, save a separate prompt with the same drawing skeleton and the specific visual correction; omit defect-report prose, QA codes and retry budgets. Describe retained and changed visual content for edits. This does not authorize another call: the unchanged single-image/collection policy controls that decision.

No fixed character limit applies. Track length and first-pass performance separately.

For v20 image-task start assembles the already authored frozen request; do not rewrite an initial prompt at dispatch. Supply a targeted drawing-only retry file only after a recorded eligible core defect. Tool state, task IDs, budgets, timestamps and review codes remain outside API drawing text.

Model profiles supply localized appearance, costume and personality summaries; authored performance and interaction stay in the prompt language. For scoped communication/prompt language differences, provide `display_performance` and `display_interaction` in each model cast record for the communication table. These display strings are also bound to confirmation.
