# Provider routing and execution contract

Dispatch only after Gate 1 selection, Gate 2 confirmation of the current scope and budget, and successful schema v6 validation/initialization. Read-only proposal/summary commands do not authorize provider calls. Scope changes require renewed confirmation; ordinary bounded retries, ordered fallback and lower effective parallelism do not introduce a third approval. Read the frozen assignment through `manage-run.py status` before dispatch so approval, scope and reference integrity are rechecked.

Use providers only in this order:

1. Codex ImageGen / GPT Image 2 (built-in tool inside Codex, `generate-codex.py` elsewhere)
2. OpenAI Images API
3. Nano Banana API
4. Seedream API

Retry a visually correctable defect on the current provider before moving forward. Stop after the first complete PASS. Never use a fallback to bypass a safety rejection.

## Capability check

Before dispatch, compare the frozen assignment with the provider's current capabilities:

- Number and formats of image references.
- Whether references preserve their declared roles closely enough for the task.
- Requested output aspect ratio and resolution mode.
- Meaningful transparent PNG output when `output.alpha` is true.
- Language, text rendering, and other model limitations relevant to the assignment.
- Provider concurrency and account quota.

Return a `capability` error when a required feature is unsupported. Do not silently flatten transparency, drop references, substitute text, or change a confirmed field. Route forward in provider order or obtain renewed confirmation.

## Codex ImageGen

Codex comes first whenever it is installed and logged in, whichever agent runs the Skill. Both paths record provider `codex`.

- **Inside Codex:** use the built-in `image_gen` tool with one candidate per call. Load local reference images when the tool requires them to be visible in context and provide their role limits in the prompt. Never shell out to `codex exec` from inside Codex.
- **In any other agent** (Claude Code, Antigravity, etc.): use `scripts/generate-codex.py`, described below. Codex only renders the image; the calling agent keeps prompting, QA, recording, retries and delivery.

Codex ImageGen does not expose an exact size argument. For `provider-native`, describe the frozen aspect ratio and composition in the prompt, then accept any decoded size whose ratio passes automatic QA. For `exact`, record a `capability` error before generation and route forward. Transparent output through Codex is not verified, so `output.alpha: true` also routes forward with `capability`. Treat references as guidance, not edit targets, unless the confirmed task is explicitly an edit. Copy the project-bound result into the run's candidate or worker staging directory before validation.

### Codex CLI adapter

```bash
python3 scripts/generate-codex.py --check
python3 scripts/generate-codex.py --request request.json --output candidate.png [--dry-run]
```

- `--check` confirms `codex` is on `PATH` and `codex login status` reports a login. On failure, record its category (`unavailable` or `authentication`) as a `codex` provider error, then move to OpenAI.
- The request uses the external adapter request below; generate it with `manage-run.py build-request --run-dir <run> --image <id> --prompt-file <prompt.txt>`. The adapter runs `codex exec --json -s read-only` in a temporary directory, attaches the references in order with `-i`, and asks Codex to call ImageGen once with the prompt verbatim. Each reference's roles and instruction are listed by image number.
- It reads the Codex session record (`$CODEX_HOME/sessions/.../rollout-*-<thread>.jsonl`) to locate the saved image, compare the prompt ImageGen actually received with the requested prompt, and count the references the tool used. It copies the image to `--output` without overwriting and leaves the original under `$CODEX_HOME/generated_images/`.
- It writes `<output>.codex.json` (thread id, Codex version, `prompt_verbatim`, reference counts, output hash, `usable`). Pass it to `record-candidate --transport cli --provider-audit`; omit `--provider-size`. Built-in Codex calls use `--transport builtin` with no audit; other providers omit `--transport`. `usable: false` means the prompt was rewritten or references were dropped: the image still consumes a candidate and cannot pass. `usable: null` means the session record could not verify either; the candidate may pass, but the record marks it unverified and `finalize` lists it under `unverified_provider_audits`.
- Categories: missing CLI → `unavailable`; no login → `authentication`; timeout → `timeout`; usage or rate limits → `quota` / `rate_limit`; an ImageGen safety failure → `safety_rejection`; no image → `service`.
- Each call also spends roughly 40k tokens of Codex context from the user's ChatGPT plan and typically takes 40–60 seconds. The session-record format is not a public Codex contract; if it is missing, the adapter falls back to the thread's image directory and reports `prompt_verbatim: null`.

## External adapter request

The external scripts accept `--request <json> --output <png>` and support `--dry-run`. Resolve relative paths against the request JSON directory.

```json
{
  "prompt": "full effective prompt",
  "references": [
    {
      "id": "canonical-identity",
      "path": "path/to/reference.png",
      "roles": ["identity"],
      "instruction": "inherit identity only",
      "sha256": "64 lowercase hexadecimal characters"
    }
  ],
  "aspect_ratio": "1:1",
  "resolution": {
    "mode": "provider-native",
    "width": null,
    "height": null
  },
  "output": {
    "format": "png",
    "alpha": false
  }
}
```

`manage-run.py build-request` writes this request from the frozen image and a saved prompt; prefer it over hand-written JSON. The adapter extracts paths for the provider request but preserves IDs, roles, instructions, and hashes in dry-run and audit output. A dry-run validates capabilities and prints a credential-free summary; it never makes a network call. A live call writes exactly one candidate PNG. Never log credential values.

When recording a candidate, copy the adapter's resolved size control into `record-candidate --provider-size`: use values such as `1024x1024` when the provider receives exact pixels or `1K` when it receives a native tier. Omit it for a tool such as built-in Codex ImageGen that exposes no size control. This audit value does not change the frozen assignment.

Every reference must declare at least one role. `output.format`, `output.alpha`, `aspect_ratio`, and the complete `resolution` object are required because their defaults were already resolved in the frozen assignment. `aspect_ratio` may be any positive integer `WIDTH:HEIGHT` ratio. `provider-native` requires null width and height; `exact` requires positive width and height consistent with the ratio. Adapters resolve provider-native geometry according to their own verified controls and reject exact requirements they cannot guarantee. Reference MIME types are detected from file bytes, not filename extensions.

Use the smallest confirmed reference set within provider limits. If an adapter has not implemented structured references or alpha output, report `capability`; never discard confirmed reference roles or output semantics.

## External providers

### OpenAI Images API

- Script: `scripts/generate-openai.py`
- Credential: `OPENAI_API_KEY`
- Model override: `OPENAI_IMAGE_MODEL`; default `gpt-image-2`
- Base URL override: `OPENAI_BASE_URL`; default `https://api.openai.com/v1`
- References use multipart `POST /images/edits`; generation without references uses `POST /images/generations`.

### Nano Banana API

- Script: `scripts/generate-nanobanana.py`
- Credential: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- Model override: `NANO_BANANA_IMAGE_MODEL`; default `gemini-3.1-flash-image`
- Base URL override: `GEMINI_BASE_URL`; default `https://generativelanguage.googleapis.com/v1`
- References use Gemini `generateContent` with text plus base64 image parts and image response modality.

### Seedream API

- Script: `scripts/generate-seedream.py`
- Credential: `ARK_API_KEY`
- Model override: `SEEDREAM_IMAGE_MODEL`; default `doubao-seedream-5-0-lite-260128`
- Base URL override: `SEEDREAM_BASE_URL`; default `https://ark.cn-beijing.volces.com/api/v3`
- References use `POST /images/generations` with one data URL or a list of data URLs; request PNG output without provider watermarks.

Model availability and exact transparency/reference limits can vary by account and change over time. Keep model overrides and rely on adapter capability validation rather than assuming support.

Current adapter-specific capability boundaries are explicit:

- OpenAI defaults to `gpt-image-2`, implements native transparent output, and supports both modes. Provider-native uses a 1024-pixel short-edge recommendation snapped to a valid multiple of 16. Exact resolution must satisfy the model constraints: both edges are multiples of 16, neither edge exceeds 3840 pixels, the long-to-short edge ratio is at most 3:1, and the total pixel count is 655,360 through 8,294,400. A model override may have narrower limits.
- Nano Banana accepts only `1:1` and `9:16`; provider-native uses its native `1K` output control. The adapter rejects exact resolution and transparent output until native contracts for those requirements are verified.
- Seedream accepts only `1:1` and `9:16`; provider-native maps them to 1024×1024 and 1024×1792. Exact mode accepts only the corresponding verified native size. The adapter rejects transparent output until a native alpha contract is verified.

## Sub-agent coordinator

Default to automatic sub-agent execution; the ceiling is 10. Before Gate 2, inspect available delegation tools, free worker slots (exclude the main agent and occupied slots), initially ready images, provider concurrency and explicit user limits. Do not launch workers to probe capacity. If provider concurrency is unknown, use 1 conservatively and disclose the uncertainty. If delegation is unavailable, use 0 worker slots. Explicit serial execution uses the main agent.

Resolve the concrete plan with the read-only helper, using observed values rather than these illustrative numbers:

```bash
python3 scripts/manage-run.py plan-execution \
  --ready-images 10 --worker-slots 3 --provider-limit 3
# Add --user-limit <limit> or --serial when requested.
```

Copy the returned `execution` into the Gate 2 draft. `subagent_count` is the minimum of ready images, available worker slots, provider limit, user limit and 10; it is 0 for explicit serial execution. `requested_parallelism` is `max(1, subagent_count)`. One image can use one worker but has no multi-image speedup. Show the exact worker count and any limiting reason alongside image totals; do not claim that 10 slots exist just because the Skill allows them. State that workers reuse the queue and do not increase image counts or candidate budgets. A changed plan requires a refreshed Gate 2 summary; an increase after confirmation requires renewed consent.

After Gate 2, finish expansion, validation, freezing and any required batch review. Recheck capacity, tell the user if it fell, then initialize with `--effective-parallelism` and `--effective-subagents`. Actual workers may be fewer than confirmed, including 0 with parallelism 1 for main-agent fallback. Existing frozen runs retain their original authorization; do not turn an old serial run into a sub-agent run.


For proportion counterpart pairs, the higher-ratio image must PASS before the lower-ratio image is ready. Exclude blocked counterparts when estimating Gate 2 capacity.

### Dispatch and collect

1. Use the runtime's sub-agent creation tool (for example `spawn_agent`) to create up to the confirmed, currently available worker count. No delegation support means the main agent executes serially; never substitute a nested agent CLI to evade that limit. Reuse workers through the runtime's follow-up mechanism rather than creating one per image.
2. Give each worker one ready image/candidate, the Skill path, read-only frozen assignment, exact image id, authorized provider and remaining budget, reference paths/roles, and a unique `staging/<image-id>/<attempt-id>/` directory. Restrict its task to that candidate. Workers must not spawn more agents, change the approved plan or write the manifest.
3. The worker builds the prompt, calls one provider once, preserves any returned image immediately, validates/measures and performs actual visual QA. It returns prompt/request/candidate/QA/audit paths, hashes, provider/model, transport and errors. A failure or timeout after an image was produced still consumes a slot; inspect staging before any retry. Workers must not call `record-*`, `promote`, `finalize`, or independently retry/fall back.
4. The main agent collects completed results, verifies hashes and evidence, then serially records errors/candidates and promotes only PASS results. It assigns the next ready image or a permitted retry to an available worker. Never dispatch two candidates for the same image. Retries and provider fallback wait until the preceding result is recorded; reduce active dispatch if the next provider has lower capacity.
5. On a safety rejection, stop new dispatch, interrupt outstanding work where supported and quarantine uncommitted results. Preserve returned candidates and account for consumed attempts. When work is resolved, release workers if supported and finalize through the manager.

For multiple source assignments under one Gate 2 confirmation, show both per-run worker allocations and the aggregate concurrent worker count. Share one pool across the batch: do not multiply the runtime/provider limit or the ceiling of 10 by the number of sources. Freeze each run's allocation; increasing it requires confirmation. Serial manifest writes remain the coordinator's responsibility across the whole batch.

## Errors and budgets

- Authentication, quota, rate-limit, timeout, service, and capability failures that return no viewable image are provider errors; record them without consuming candidate budget.
- A response containing a viewable image is one candidate whether it passes or fails.
- Record moderation/safety rejection separately and stop automatic routing.
- Limit transient retries; never create an unbounded adapter loop.
- Never exceed 2 candidates per provider by default, 8 per image, or the confirmed run budget.
