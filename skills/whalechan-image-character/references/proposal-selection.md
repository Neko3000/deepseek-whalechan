# Proposal selection and execution confirmation

Use two user decisions: choose directions, then confirm the displayed quantities, settings and budget to begin. Quote actual replies. Recommendations, silence, preselected UI options and draft files are not consent. Planning-only requests never authorize generation. Respect explicit authorization already given for the same displayed scope; do not invent additional approvals.

## Gate 1: select directions

For an open theme (`proposal.mode: explore`), review five materially different proposals A–E. For precisely specified scenes (`direct`), present those scenes without forcing five alternatives; `proposal.request` preserves the user instruction supporting this choice. Identity and all explicit user constraints apply to every option. A–E are identifiers, not rankings or instructions to rotate styles.

Display the output of `render-proposal` as a Markdown table, not a code block:

| 选择 | 方案 | 核心场景 | 动作与表情 | 构图 | 视觉配置／文字 | 推荐程度与理由 |
|---|---|---|---|---|---|---|
| A | Concrete title | Visible scene | Action and emotion | Framing and layout | Settings and exact text, or no text | Stars and specific reason |

Use ★★★, ★★☆ or ★☆☆ without a rating quota. Shared settings may be explained above the table, but every option must state its visual/text intent clearly. Do not import comic-only requirements such as punchlines or panel counts.

Below the table, ask which proposals to use and explain the strategy: each selected proposal defaults to **one final image**; explicit positive counts override it. A+C means two images; A two and C one means three; all five means five. “按推荐来” refers only to the displayed recommended combination. Clarify ambiguous quantities; never silently multiply a user-specified total.

Stop and wait. Do not generate or fully expand unselected options.

## Gate 2: confirm the execution scope

Record the Gate 1 reply, choices/counts and explicit changes. Resolve selected configuration groups before asking to begin. Each group has a proposal choice, count, locked requirements and a stated variation scope. Subject, action, composition, style, costume, background/alpha, exact text/languages, proportion, output and typed references are required locks. Also lock expression, props, objects and pairwise requirements whenever the user specified them. Multiple groups may belong to one proposal when variants need different locked settings.

Show each selected title and count, the proposal and image totals, all explicit changes, each configuration and its allowed variation, output location, provider order, execution request and maximum candidates. The default candidate ceiling is total images × 8, not the final-image total. Above 24, explicitly include approval of the raised ceiling in this same Gate 2 question; no extra budget gate.

Ask: **确认按以上方案、数量、配置和候选预算开始生成吗？** Then wait. A Gate 1 reply saying “A，开始吧” still needs the actual scope summary. A changed selection, quantity or locked setting requires the updated summary and a fresh affirmative reply; do not reuse consent to an older summary.

Small wording/staging changes go in `selection.adjustments` and the corresponding requirements. If the core direction is replaced, revise the proposal and repeat Gate 1. Preserve prior draft revisions. Never recompute an approval hash as a substitute for a real user reply.

After Gate 2, expand only the approved configuration counts. Each image links to its proposal and configuration and carries an execution note. Review fidelity internally, validate and freeze; do not add a third routine approval. Unlocked execution details remain bounded by the approved variation and user intent. Reduced effective parallelism, bounded retries and normal provider fallback do not alter the authorization. Permanent identity and existing QA remain mandatory.

## Drafts and audit records

Keep revisioned drafts under `artifacts/whalechan-image-character/<run-name>-planning/`, unless the user specifies a destination. Gate 1 needs only `proposal`:

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json>
```

After the actual selection, save its `proposal_sha256`, the reply and choices. Add `run_name`, `scope`, `execution` and `budget`, then run:

```bash
python3 scripts/manage-run.py summarize-selection --draft <draft.json>
```

Display the returned Markdown. The helper inspects references and returns normalized configurations with content hashes: preserve these in the next draft so changed bytes are detected. Neither helper writes a file, creates consent, initializes a run or calls a provider. A draft needs no `images` or visual QA.

After the actual Gate 2 reply, save `confirmation.status: confirmed`, its reply, timestamp and returned `summary_sha256`. Set `budget.confirmed_over_24: true` only when the user approved the displayed ceiling above 24. Then expand images using those requirements. See `assignment-schema.md` for the contract.

Validation, initialization and frozen-run loading recheck the approval chain, configuration counts and locked fields. Reference identities, bytes and roles are bound, while storage paths may change when copied into the run. These checks establish record consistency, not whether a human actually replied or whether the expansion is creatively faithful. The agent must verify those facts from the conversation and review; direct provider calls must not bypass either gate.
