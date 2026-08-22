---
name: whalechan-image-character
description: Generate and verify consistent DeepSeek Whale-chan character illustrations from text, screenshots, chat logs, dialogue, or user reference images. Use when Whale-chan identity must stay recognizable while text, language, background, transparency, style, action, outfit, proportions, or generation parallelism may use defaults or explicit user choices.
---

# Whale-chan Image Character

Create verified Whale-chan PNGs. Preserve Whale-chan's permanent identity while resolving every visual dimension independently from the user's request, typed reference images, and canonical defaults. A custom value changes only its own field.

## Load guidance as needed

- Read `references/assignment-schema.md` whenever normalizing, confirming, or freezing a request.
- Read `references/character-spec.md` before building prompts or deciding whether a requested customization preserves Whale-chan identity.
- Read `references/form-profiles.md` when resolving or measuring proportions. The five bundled forms are recommended presets, not the only allowed ratios.
- Read `references/reference-index.md` when selecting bundled or user-supplied references.
- Read `references/provider-routing.md` before any provider call or parallel run.
- Read `references/qa-rubric.md` before reviewing or promoting a candidate.
- Treat `references/reference-catalog.json` as the machine-readable authority for bundled paths, hashes, preset ratios, and preset acceptance ranges.

## Resolve the request

Normalize the request into schema v4 before presenting a plan. Use the user's explicit instructions first, then references only for their declared roles, then canonical defaults for unresolved fields. Do not let a reference silently control unrelated dimensions.

Defaults remain:

- 3 images; `semi-chibi`; canonical style; canonical maid outfit.
- Warm ivory-beige solid background `#F5EADD`; transparency off.
- No visible text. When text is requested without a language, use `zh-Hans`; do not translate or invent wording without confirmation.
- Full-body centered composition, `1:1`, PNG, provider-native resolution, sequential execution with parallelism 1. Prefer 1024×1024 when the selected provider exposes a compatible size control, but do not treat 1024×1024 as a default acceptance requirement.

The user may explicitly request any style, action, outfit, solid/custom/transparent background, exact multilingual text, measurable head ratio greater than 1.0, positive-integer aspect ratio, or exact positive pixel resolution. If the user gives only width and height, derive the aspect ratio; if both are given, require them to agree. Keep extreme but measurable ratios possible; disclose that ratios outside the five presets have no bundled proportion reference and may be harder to satisfy. Provider safety and technical limits still apply.

Input screenshots, chat logs, and dialogue supply subject matter only. They do not authorize copying UI, visible source text, avatars, brands, or visual style unless the user explicitly assigns those roles.

Give the run a kebab-case English name and every image a unique snake_case English name. When one request contains several images, freeze a complete image-level configuration for each one rather than asking workers to inherit unstated choices.

## Confirm before spending

Before any image-generation or paid API call, show a compact plan containing:

```text
输入类型与重点：<type>；<focus>
提取主题：<theme>
运行名称与输出位置：<run-name>；artifacts/whalechan-image-character/<run-name>/
图片清单：<name — subject, expression, action, composition>
逐图配置：<proportion; style; costume; background/alpha; exact text/languages or no text>
输出规格：<format; aspect ratio; provider-native with 1024×1024 recommendation, or exact WIDTH×HEIGHT>
参考图权限：<path/id — declared roles and instruction>
模型顺序：Codex → OpenAI → Nano Banana → Seedream
执行方式：<sequential/parallel; requested and currently effective parallelism>
数量与最大候选：<image count> × 8 = <maximum; confirmed run budget>
```

Stop for explicit confirmation. Confirmation freezes image names/order, subjects, actions, composition, all resolved visual fields, typed references and hashes, output intent, execution request, and candidate budget. Provider-native resolution freezes the aspect ratio and provider-selection policy, not an exact pixel size; record the requested, provider-resolved, and actual output geometry for every candidate. Exact resolution freezes width and height. If requested parallelism cannot be known until execution, state that effective parallelism will be capped by 5, ready tasks, runtime worker slots, and provider limits.

More than 3 images normally exceeds the 24-candidate run budget. Show the raised estimate and require explicit approval. Any later material change requires a revised plan and renewed confirmation.

## Execute the confirmed assignment

1. Write the frozen schema v4 assignment described in `references/assignment-schema.md`, then validate and initialize it:

   ```bash
   python3 scripts/manage-run.py validate-assignment --assignment <assignment.json>
   python3 scripts/manage-run.py init --assignment <assignment.json> \
     --effective-parallelism <current-capacity>
   ```

   For the sequential default, omit the flag or use 1. For a parallel run, calculate current capacity from ready images, runtime worker slots, and provider limits before initialization; the recorded effective value may be lower than the confirmed request.

2. Build each prompt from the normalized assignment in this order: permanent identity → theme → proportion target → resolved style → expression/action/composition → resolved outfit → props/objects → resolved background and alpha → exact text directive → typed-reference role limits → anatomy/contact constraints → output format, aspect ratio, and resolution intent. Include canonical locks only for fields whose mode is `canonical`.
3. Route providers and references according to `provider-routing.md`. Use one provider call per candidate and stop after the first complete PASS.
4. Run deterministic image validation against the frozen resolution mode, inspect the original resolution, measure the frozen proportion, and complete the assignment-aware visual QA in `qa-rubric.md`. Never resize or crop a candidate to make it pass. Promote only when automatic and visual verdicts both pass.
5. Retry with one targeted correction at a time. Use at most 2 candidates per provider by default and 8 candidates per image total.
6. Finalize through `manage-run.py finalize`. Preserve failed numbering gaps and report final paths, provider/model, effective prompt, references, and QA result.

For parallel execution, the main agent is the sole coordinator and manifest writer. Workers may generate and review different ready images in isolated staging directories, but must not mutate the manifest or promote finals. The coordinator serially records and promotes returned results. Never generate two candidates for the same image simultaneously. Request at most 5-way parallelism and downgrade safely when runtime capacity, dependencies, provider capability, or ready-image count is lower.

## Hard stops

- Do not generate before explicit confirmation or exceed the confirmed budget.
- Do not weaken permanent Whale-chan identity, anatomy/contact checks, or assignment-specific QA merely because another field is custom.
- Do not accept missing, misspelled, illegible, additional, or wrong-language text. Source UI, signatures, watermarks, usernames, QR codes, and unconfirmed brand marks always fail.
- Do not silently drop a reference, role, alpha requirement, or other confirmed field because a provider lacks the capability; route forward or seek renewed confirmation.
- Do not silently resize, crop, or convert a provider-native result, and do not send an exact-resolution assignment to a provider that cannot guarantee its width and height.
- Do not route around a safety rejection. Record it as a run-level halt, stop new dispatch, and quarantine uncommitted in-flight results.
- Do not promote from automatic checks alone.
- Do not overwrite bundled references, prior runs, attempts, staging results, or final files.
