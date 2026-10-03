# Final plan and one user confirmation

Complete creative planning before the single generation gate: freeze ten candidates, compare every pair, select five, then plan one image per selected idea. The table reports the result; it is not a selection menu. Do not ask for letters, ratings or acceptance of a recommended combination.

## Display the complete plan

Show one seven-column Markdown table per source, with five rows:

| 序号 | 创意描述 | 核心场景 | 方向｜笑点 | 格数／分镜 | 关键台词 | 入选理由 |
|---|---|---|---|---|---|---|
| 1 | 具体创意 | 画面中的事件 | 方向及笑点如何落地 | 格数、镜头、互动 | 准备上图的关键文字 | 对决中体现的具体优势 |
| 2 | … | … | … | … | … | … |
| 3 | … | … | … | … | … | … |
| 4 | … | … | … | … | … | … |
| 5 | … | … | … | … | … | … |

Numbers identify rows, not mechanisms or layouts. Name the actual comedy direction; optionally mark a native-direction idea with “（原）” and explain the marker. Do not assign stars or impose native/character quotas. Keep cells concise, escape pipes and use `<br>` for line breaks.

Below the table, show:

- Five ideas, one image each, five total images per source; for multiple sources include each source's count and the grand total.
- Worker-to-image assignments, concrete sub-agent count, requested and effective concurrency, and the coordinator's planning, QA, recording and delivery duties. With zero sub-agents, state that the main agent executes all five images serially and explain the limiting reason; a one-sub-agent plan also runs sequentially.
- A maximum of three image-producing calls per image, fifteen per source, and the provider route.
- Any explicit user overrides, including a nondefault panel-count policy.

Then ask once:

> **确认按以上创意、张数和分工开始生成吗？** 每个创意生成一张；确认后执行生成、验收和交付。

Wait for an actual affirmative reply to this plan. Silence, a recommendation, an automatically selected UI answer or a planning-only request is not permission to generate. Honor authorization already given for this exact displayed scope; do not invent an additional gate.

Before displaying the plan, inspect runtime/provider capacity and use `plan-execution` from `provider-routing.md`. Default to automatic sub-agents; cap one five-image run at five workers and the shared batch pool at ten. Respect explicit serial requests. Save the concrete `execution` and matching `worker_plan` in the draft. Display actual observed capacity rather than promising the ceiling; workers reuse the queue without increasing image counts or candidate budgets.

## Record the decision

Use schema v13 and the helper commands in `run-schema.md`. Save drafts under `artifacts/whalechan-image-comic/<run-name>-planning/` unless the user specifies another location. Preserve revisions as separate files. Complete image plans and the worker allocation before rendering the plan; drafts do not require visual QA.

Render the plan with either read-only helper:

```bash
python3 scripts/manage-run.py render-proposal --draft <draft.json>
python3 scripts/manage-run.py summarize-selection --draft <draft.json>
```

Both v13 helpers return the complete table, counts, budget, worker allocation, question and `summary_sha256`; they do not create two gates. Display the Markdown directly, not inside a code block. After the real reply, save `confirmation` with `status: confirmed`, the actual `user_reply` and the returned `summary_sha256`, binding the count, worker allocation and normalized execution settings. Use `worker_plan` and `panel_policy` as specified in `run-schema.md`; full `images` records may be completed after confirmation while preserving the displayed scenes, key lines and panel counts. Hashes are audit metadata, not user-facing text. Helpers render and validate records; they cannot approve on the user's behalf.

Changes to the creative content, quantity or planned allocation require an updated displayed plan and confirmation of that version; the disclosed runtime capacity reductions below do not revise the approved plan. Apply the user's corrections without silently replacing other ideas. A revised core idea changes the frozen candidate pool: preserve the prior version and redo the affected comparisons once for that explicit revision, rather than automatically generating another pool. For multiple sources show one combined execution summary and bind the same reply to each current source plan. Qualify each worker assignment by source and idea. Share one global worker capacity across the batch; do not multiply concurrency by the number of sources. Per-source worker plans describe which workers participate, while the coordinator schedules their jobs within the displayed global limit. Never reuse an old reply for an altered scope.

After confirmation, validate and freeze the assignment, then execute without another routine approval. If runtime capacity falls, disclose the reduction and any necessary queue reassignment; record the lower actual count without editing the frozen plan or its hash. Actual workers must not exceed the confirmed count. Increasing approved capacity requires a revised plan and confirmation. Create and dispatch workers using the runtime's delegation tools; unavailable delegation falls back to serial main-agent execution. Workers write to unique staging paths; only the coordinator records and promotes candidates. Keep retries serial within each image's independent budget.

Historical v10/v11 and both v12 frozen-run formats retain their original contracts and recovery paths; see `run-schema.md`. Do not rewrite their decisions or fabricate a v13 confirmation. Create new runs with v13.
