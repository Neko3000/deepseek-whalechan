# Final plan and one user confirmation

Complete creative planning before the single generation gate: freeze 2N concise candidates, have another real sub-agent priority-rank all 2N, select the first N, then return to the original author for detailed visual plans. The table reports the result; the user confirms or revises the whole plan.

## Display the complete plan

Show one eight-column base Markdown table per source, with N rows (the following is an N=5 example). Render headers, distribution and confirmation with the saved communication-language `plan` locale. Write the cells in the communication language and keep the exact visible text unchanged:

| 序号 | 创意 | 方向 | 格数 | 档位 | 场景／分镜 | 关键台词 | 入选理由 |
|---|---|---|---|---|---|---|---|
| 1 | 具体创意 | 方向及笑点如何落地 | 1 | A-日漫冲击 | 画面事件、镜头、互动 | 准备上图的关键文字 | 排序中体现的具体优势 |
| 2 | … | … | 2 | C-克制冷幽默 | … | … | … |
| 3 | … | … | 4 | B-漫画爆发 | … | … | … |
| 4 | … | … | 2 | A-日漫冲击（脸→C） | … | … | … |
| 5 | … | … | 1 | A-日漫冲击 | … | … | … |

> 格数分布：1 格 ×2 · 2 格 ×2 · 4 格 ×1 ✓ ｜ 档位分布：A-日漫冲击 ×3 · B-漫画爆发 ×1 · C-克制冷幽默 ×1 ✓

> 档位目标 A:B:C＝3:1:1（60% / 20% / 20%）；实际占比 60% / 20% / 20%；偏差 0 / 0 / 0 个百分点。五张配比已满足。

> 本次目标头身比：2.8 头身（半 Q 版，semi-chibi），适用于全部 5 张。

Numbers identify rows, not mechanisms, layouts or tiers. Name the actual comedy direction; optionally mark a native-direction idea with “（原）” and explain the marker. Use localized equivalents of the descriptive labels `A-日漫冲击`, `B-漫画爆发`, `C-克制冷幽默` in both the tier column and distribution line (`A-Manga impact`, `B-Comic outburst`, `C-Restrained deadpan` in English). Write a declared contrast after the descriptive label, such as “A-日漫冲击（脸→C）”. The helper computes the distribution line and marks each coverage policy as satisfied or user-overridden. Do not impose native/character quotas. Keep cells concise, escape pipes and use `<br>` for line breaks.

Show the target head-to-body ratio immediately below the distribution line and before image totals, never as another table column. Record `proportion` in every new `proposal.options` entry before rendering, including the default `{"mode": "preset", "preset": "semi-chibi"}`. Resolve targets from the preset catalog or the explicit custom ratio. When all N match, show one shared target; otherwise group table row numbers by target, for example “第 1、3、5 张为 2.8 头身（半 Q 版，semi-chibi）；第 2、4 张为 2.5 头身（Q 版，chibi）”. Custom ratios read “3.0 头身（自定义）”. These are planned targets, not measurements of generated images.

Below the table, show:

- N ideas, one image each, N total images per source (default N=5); for multiple sources include each source's count and the grand total.
- Independent role caps (planning 5, selection 2, generation 5 / Codex 3, collection 2, delivery 1), actual observed runtime slots, shared batch limit, dynamic assignment and main-agent orchestration-only duties. Independent selection requires another real agent; report unavailable delegation instead of silently self-reviewing.
- A maximum of three image-producing calls per image, 3N per source, and the provider route.
- Any explicit user overrides, including a nondefault panel-count or exaggeration policy.

Then ask once:

> **确认按以上创意、张数和 sub-agent 分配开始生成吗？** 每个创意生成一张；确认后执行生成、验收和交付。

Wait for an actual affirmative reply to this plan. Silence, a recommendation, an automatically selected UI answer or a planning-only request is not permission to generate. Honor authorization already given for this exact displayed scope; do not invent an additional gate.

Before displaying the plan, inspect runtime capacity and use plan-roles from agent-orchestration.md. Save one shared batch execution policy and dynamic worker_plan. Planning workers author the content; main displays their rendered plan plus current capacity. Role caps are not guaranteed available slots.

## Record the decision

Use the current schema and the helper commands in `run-schema.md`. Save drafts under `artifacts/whalechan-image-comic/<run-name>-planning/` unless the user specifies another location. Preserve revisions as separate files. Complete image plans and the worker allocation before rendering the plan; drafts do not require visual QA.

Render the plan with either read-only helper:

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json>
python3 scripts/manage-run.py summarize-selection --draft <draft.json>
```

`summarize-selection` is an alias of `render-proposal`; both return the complete table, counts, budget, worker allocation, question and `summary_sha256`. Display the Markdown directly, not inside a code block. After the real reply, save `confirmation` with `status: confirmed`, the actual `user_reply` and the returned `summary_sha256`, binding the count, worker allocation and normalized execution settings. Use `worker_plan`, `panel_policy` and `exaggeration_policy` as specified in `run-schema.md`; full v20 `images` records must exist before this display. The scene/staging cells come from their panel actions and expression descriptions; the confirmation also binds the visual projection used by the prompt builder. See `prompt-design.md`. Hashes are audit metadata, not user-facing text. Helpers render and validate records; they cannot approve on the user's behalf.

Changes to creative content, quantity or approved role/batch limits require updated consent. Normal role switching and capacity changes within those limits do not. Preserve previous versions for substantive revisions. For multiple sources show one combined execution summary and bind the same actual reply to each current source plan; never multiply quotas by source count. Generation worker assignments remain dynamic; frozen author/reviewer identities and task IDs are part of v20 selection provenance and its confirmation hash.

Disclose the QA 11 policy in the execution summary: one candidate inspection, minor-issue tolerance, one collection contact-sheet review and at most one repair round within the same three-call budget.

After confirmation, assign validation/freezing to a planning worker. Main dispatches actual sub-agents through runtime tools. Generation workers own isolated image journals and permitted retries; collection/delivery workers reconcile and mutate shared manifests serially. Follow agent-orchestration.md for capacity reductions, resident reuse, ownership and recovery.

For v20 use batch-proposal to combine per-source tables, tool/capacity disclosures and budgets. Bind the actual single user reply to its returned batch summary; batch-start derives each source confirmation from the bound summaries without another question. Report structural-warning dispositions in the authored cross-source observation. Tool preflight does not authorize generation; provider selection is locked before this gate. See batch-commands.md.

## Selection handoff

Candidate authors submit only input and creative_pool via concepts-submit. Candidates carry no scores, preselected winners or complete images. The selection worker reads the original source and frozen pool and submits exactly 2N ordered {idea_id, reason} rows and selection_reason, optionally attention_points. The script fills provenance and derives the first N IDs. Use one concise reason per row; no new candidate pool, low-score regeneration or second semantic ranking.

The detail worker preserves the frozen pool, selected order and exact candidate key_lines while completing N proposal.options and images. Copy the source exaggeration_policy from the task packet. New N=5 sets require exactly 3 A, 1 B and 1 C; for other N allocate by content close to 60%/20%/20% and review the displayed percentage deviations. N>=3 retains independent panel/tier coverage; N=1/2 relaxes coverage. Candidate authors and selectors consider this target before the author assigns tiers in detail work. A real content/constraint conflict is reported, not hidden by replacing selected ideas. User-requested changes to N/core content start an explicit new planning revision.

See batch-commands.md for staged submissions and run-schema.md for record shapes.

## Model cast disclosure in the same confirmation

When a visual plan declares character identities, the renderer adds a ninth cast/settings column. Show each role’s representation, model/form and target ratio, reference thumbnail, fictional personality, authored performance and interaction. Read these from the normalized `images[].cast_plan` visual contract, not a separate proposal cast record. The existing single confirmation binds the cast together with all drawing fields; do not restore the older two-gate workflow. A changed identity, performance, form or reference invalidates that confirmation. Ordinary legacy abstract-only plans retain their existing projection.

Use the task communication locale’s `cast` section. Model descriptions are bundled in English and Simplified Chinese. For other languages, author `localizations.<tag>.cast` and `localizations.<tag>.characters.<character_id>` before displaying the plan; keep the same identity, costume and personality meaning.
