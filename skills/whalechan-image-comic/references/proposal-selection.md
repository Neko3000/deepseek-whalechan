# Proposal selection and quantity confirmation

Use two distinct user turns before generation. First obtain proposal choices; then show their quantities and obtain permission to begin. The agent must quote actual replies, not manufacture approval records. A recommendation, silence, a preselected UI answer or a Gate 1 choice is not Gate 2 confirmation.

## Gate 1: compare five proposals

Prepare exactly five reviewed, materially different proposals. Use this exact seven-column Markdown layout, one row per choice; replace every placeholder with concrete content. Letters identify choices, not rank, layout or humor mechanism.

| 选择 | 方案 | 核心场景 | 笑点与反转 | 分镜／构图 | 关键台词 | 推荐程度与理由 |
|---|---|---|---|---|---|---|
| A | 具体标题 | 画面中的事件 | 预期与反转 | 格数、镜头、互动 | 准备上图的关键文字 | 星级＋推荐结论＋具体理由 |
| B | … | … | … | … | … | … |
| C | … | … | … | … | … | … |
| D | … | … | … | … | … | … |
| E | … | … | … | … | … | … |

Use ★★★ 首推, ★★☆ 推荐 or ★☆☆ 可选 with a source-specific reason. Do not force a rating distribution or fill slots with rejected ideas. Keep cells concise; escape pipes and use `<br>` for line breaks. Key lines describe the selected joke; render only each execution's frozen `core_text`, retaining any user-locked wording.

Below the table, ask:

> **你想生成哪些方案？** 可选一个或多个。推荐〈编号〉，因为〈具体理由〉。
>
> **生成策略：**每个入选方案默认生成 **5 张**，围绕该创意展开不同演绎。选一个共 5 张，选两个共 10 张，全选共 25 张；也可以指定“五种方案各一张”，共 5 张。选择后，我会汇总方案和张数，请你确认后再开始生成。

Stop and wait. Do not create a full image assignment or spend image calls just to fill unselected alternatives.

## Gate 2: summarize, then wait again

Resolve replies using the displayed choices and recommendations. A choice without a quantity means five images. Explicit positive integer quantities override that default; never confuse five proposals with five total images.

| Gate 1 reply | Gate 2 summary |
|---|---|
| A | 1 proposal, 5 images |
| A＋C | 2 proposals, 5 each, 10 total |
| 全部默认 | 5 proposals, 5 each, 25 total |
| 五种各一张 | 5 proposals, 1 each, 5 total |
| A 两张，C 一张 | 2 proposals, 3 total |
| 按推荐来 | The explicitly displayed recommended combination, five each unless another quantity was specified |

For A＋C, say:

> 已选择 **2 个方案，共 10 张图片**：
>
> - **A｜完美启动率**：5 张
> - **C｜马上正在路上**：5 张
>
> 每个方案围绕已选创意展开不同演绎，生成后进行质量验证。
>
> **确认按以上方案和数量开始生成吗？** 回复“确认”即可开始，也可以调整方案或数量。

Include explicit user changes in the summary. For a small wording or staging correction, preserve the displayed proposal and record the override in `selection.adjustments`; it takes precedence during execution. If the core joke is replaced, issue a revised proposal (increment revision) and repeat Gate 1. Preserve earlier draft files rather than editing frozen history.

Stop and wait even if Gate 1 said “A, start now”: show the actual total first. At Gate 2, an affirmative reply to the current summary authorizes execution. A changed choice, quantity or content override requires a new summary and a new reply; “change A to two and go” still changes the scope being confirmed. Do not reuse an earlier confirmation. Clarify ambiguous replies. Planning-only instructions remain in effect until the user explicitly authorizes generation.

For multiple sources, present one labeled table per source, collect choices, then give one consolidated Gate 2 summary with per-source/per-proposal counts and a grand total. Bind that reply separately to each source's current summary. If any part changes, refresh the combined summary before generating the batch.

After Gate 2, expand only the selected proposals into the confirmed quantities, validate/freeze internally, and generate without a third routine approval. Do not silently increase counts or replace the selected joke. Keep retries within each image's three-call budget; proposal count does not change concurrency limits.

## Save and check the two decisions

Use the proposal, selection and confirmation structures in `run-schema.md`. Before Gate 1, keep a draft under `artifacts/whalechan-image-comic/<run-name>-planning/` (or the user's destination). Name revisions separately, for example `draft-01.json`, `draft-02.json`. A draft needs no `images` or visual QA.

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json>
```

Display the returned `markdown` directly as a table, not inside a code block. Save its `proposal_sha256` in the selection only after the actual Gate 1 reply. Record the reply, resolved choices and explicit changes, then run:

```bash
python3 scripts/manage-run.py summarize-selection --draft <draft.json>
```

Display its `markdown` and wait for Gate 2. Only after that reply, save `confirmation.status: confirmed`, the actual reply and the returned `summary_sha256`. Copy the current proposal and both decision records into the assignment. Both helpers are read-only; neither approves nor initializes a run. Their output hashes are audit metadata, not UI text.

`validate-assignment`, `init`, frozen-run loading and prompt construction require matching approval records and image counts. Hashes detect changed records; they do not prove that a human spoke, that the reply was affirmative, or that the shown table matched the saved proposal. The agent must verify those facts from the conversation and must not bypass the gates by calling a provider directly. Do not fabricate confirmation for an older schema; historical runs stay unchanged.
