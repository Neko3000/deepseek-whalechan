# Provider routing

Use providers in this order: Codex ImageGen, OpenAI Images API, Nano Banana, Seedream. Never move backward.

Move forward only after the current provider has produced a failed candidate, cannot perform the required reference/edit operation, or has a recorded availability, authentication, quota, rate-limit, timeout, or service error. Never use fallback to bypass a safety rejection.

## Codex ImageGen

Codex comes first whenever it is installed and logged in, whichever agent runs the Skill. Both paths record provider `codex`:

- **Inside Codex:** call the built-in `image_gen` tool, one call per provider-produced image. Load local references when required. Never shell out to `codex exec` from inside Codex.
- **In any other agent:** use `scripts/generate-codex.py` (below). Codex only renders the image; the calling agent keeps prompting, QA, recording, retries and delivery.

Codex ImageGen exposes no pixel-size parameter, so use it for automatic output and validate the returned native dimensions against the frozen ratio. A square result such as `1254x1254` is valid even though `1024x1024` is recommended. For explicit resolution, record `capability` and continue to OpenAI rather than pretending the prompt can guarantee pixels. Copy every returned project-bound image into the run before QA and recording.

### Codex CLI adapter

```bash
python3 scripts/generate-codex.py --check
python3 scripts/generate-codex.py --request request.json --output candidate.png [--dry-run]
```

- `--check` confirms `codex` is on `PATH` and `codex login status` reports a login. On failure, record its category (`unavailable` or `authentication`) as a `codex` provider error, then move to OpenAI.
- The request uses the external adapter contract below; generate it with `build-prompt.py --write-request` (add `--from-prompt` for retries, `--edit-target` for edits). The adapter runs `codex exec --json -s read-only` in a temporary directory, attaches the references in order with `-i`, and asks Codex to call ImageGen once with the prompt verbatim. Each reference's roles and instruction are listed by image number, so write instructions that make each role clear.
- It reads the Codex session record (`$CODEX_HOME/sessions/.../rollout-*-<thread>.jsonl`) to find the saved image, compare the prompt ImageGen actually received with the requested prompt, and count the references the tool used. It copies the image to `--output` without overwriting, and leaves the original under `$CODEX_HOME/generated_images/`.
- It writes `<output>.codex.json` (thread id, Codex version, `prompt_verbatim`, reference counts, output hash, `usable`). Pass it to `record-candidate --transport cli --provider-audit`. `usable: false` means the prompt was rewritten or references were dropped: the image still consumes a slot and cannot pass. `usable: null` means the session record could not verify either; the candidate may pass, but the record marks it unverified and `finalize` lists it under `unverified_provider_audits`.
- Edits, such as filling an empty-text layout, are ordinary requests: `build-prompt.py --from-prompt <prompt> --edit-target <layout.png>` puts the edit target first ("edit target; keep everything except the lettering unchanged"), then the typography reference. Observed edits re-render the whole canvas while preserving its structure, so review the full image again.
- Categories: missing CLI → `unavailable`; no login → `authentication`; timeout → `timeout`; usage or rate limits → `quota` / `rate_limit`; an ImageGen safety failure → `safety_rejection`; no image → `service`.
- Each call also spends roughly 40k tokens of Codex context from the user's ChatGPT plan, and typically takes 1–3 minutes; the first call in a session is slower. The session-record format is not a public Codex contract; if it is missing, the adapter falls back to the thread's image directory and reports `prompt_verbatim: null`.

## External adapter contract

Each adapter accepts `--request <json> --output <png>` and supports `--dry-run`:

```json
{
  "prompt": "complete effective prompt",
  "references": [
    {
      "id": "canonical-identity",
      "path": "path/to/reference.png",
      "roles": ["identity"],
      "instruction": "inherit identity only",
      "sha256": "64 lowercase hexadecimal characters"
    }
  ],
  "output": {
    "format": "png",
    "aspect_ratio": "1:1",
    "resolution": {"mode": "auto", "recommended": "1024x1024"}
  },
  "quality": "medium"
}
```

`build-prompt.py --write-request` writes this request from the frozen assignment; prefer it over hand-written JSON. `quality` is optional and only affects OpenAI; the other adapters accept and ignore it, so one request works across the whole fallback chain. The nested `output` object is required and must specify format, aspect ratio and resolution. Use 1–5 bundled or frozen user references. Resolve relative paths from the request JSON. Adapters preserve the requested output, reference roles, and hashes in audit output while reporting the effective provider size or tier. Never silently approximate an explicit resolution or drop a required role because of a provider limit; report `capability` and route forward. A live adapter writes one PNG and never overwrites an existing path.

### OpenAI

`python3 scripts/generate-openai.py --request request.json --output candidate.png [--dry-run]`

- credential: `OPENAI_API_KEY`
- model override: `OPENAI_IMAGE_MODEL`; default `gpt-image-2`
- base override: `OPENAI_BASE_URL`
- automatic mode chooses a ratio-appropriate size with a nominal 1024-pixel short edge; an explicit size must satisfy `gpt-image-2` constraints: both edges multiples of 16, maximum edge 3840, ratio at most 3:1, and total pixels from 655,360 through 8,294,400

### Nano Banana

`python3 scripts/generate-nanobanana.py --request request.json --output candidate.png [--dry-run]`

- credential: `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- model override: `NANO_BANANA_IMAGE_MODEL`
- base override: `GEMINI_BASE_URL`
- supports automatic `1:1` and `9:16` output using the provider's `512`/`1K`/`2K`/`4K` tiers; rejects explicit pixel resolution because the API does not guarantee exact dimensions

### Seedream

`python3 scripts/generate-seedream.py --request request.json --output candidate.png [--dry-run]`

- credential: `ARK_API_KEY`
- model override: `SEEDREAM_IMAGE_MODEL`
- base override: `SEEDREAM_BASE_URL`
- the verified adapter supports automatic `1:1` and `9:16`; it uses `1024x1024` and `1024x1792` respectively, and accepts explicit output only when it equals a verified native size

Record credentials neither in stdout nor in the run. Provider errors without images consume no candidate slot; any viewable returned image consumes one.

## Sub-agent coordinator

Default to automatic sub-agent execution; the shared batch ceiling is 10, and a five-image run uses at most five. Before the single plan confirmation, inspect available delegation tools, free worker slots (exclude the main agent and occupied slots), initially ready images, provider concurrency and explicit user limits. Do not launch workers to probe capacity. If provider concurrency is unknown, use 1 conservatively and disclose the uncertainty. If delegation is unavailable, use 0 worker slots. Explicit serial execution uses the main agent.

Resolve the concrete plan with the read-only helper, using observed values rather than these illustrative numbers:

```bash
python3 scripts/manage-run.py plan-execution \
  --ready-images 5 --worker-slots 3 --provider-limit 3
# Add --user-limit <limit> or --serial when requested.
```

Copy the returned `execution` into the draft and create a matching `worker_plan`; for one run pass its five ready images, keeping `subagent_count` at most five. The helper resolves the minimum of ready images, available worker slots, provider limit, user limit and 10; it returns 0 for explicit serial execution or unavailable capacity. `requested_parallelism` and `worker_plan.max_parallelism` equal `max(1, subagent_count)`. Use one worker entry per sub-agent; with zero, use `workers: []` and main-agent ownership of all five images. Show the exact count and limiting reasons alongside image totals; the allowed ceiling is not observed capacity. Workers reuse the queue without increasing image counts or budgets. A changed plan requires a refreshed summary; an increase after confirmation requires renewed consent.

After the single confirmation, finish expansion, validation, freezing and any required batch review. Recheck capacity, tell the user if it fell, then initialize with `--effective-parallelism` and `--effective-subagents`. Actual workers may be fewer than confirmed, including 0 with parallelism 1 for main-agent fallback. Disclose necessary queue reassignment when workers are lost; this is a runtime reduction, not a rewrite of frozen ownership or the approval hash. Existing frozen runs retain their original authorization; do not turn an old main-agent serial run into a sub-agent run.


### Dispatch and collect

1. Use the runtime's sub-agent creation tool (for example `spawn_agent`) to create up to the confirmed, currently available worker count. No delegation support means the main agent executes serially; never substitute a nested agent CLI to evade that limit. Reuse workers through the runtime's follow-up mechanism rather than creating one per image.
2. Give each worker one ready image/candidate, the Skill path, read-only frozen assignment, exact image id, authorized provider and remaining budget, reference paths/roles, and a unique `staging/<image-id>/<attempt-id>/` directory. Restrict its task to that candidate. Workers must not spawn more agents, change the approved plan or write the manifest.
3. The worker builds the prompt, calls one provider once, preserves any returned image immediately, validates/measures and performs actual visual QA. It returns prompt/request/candidate/QA/audit paths, hashes, provider/model, transport and errors. A failure or timeout after an image was produced still consumes a slot; inspect staging before any retry. Workers must not call `record-*`, `promote`, `finalize`, or independently retry/fall back.
4. The main agent collects completed results, verifies hashes and evidence, then serially records errors/candidates and promotes only PASS results. It assigns the next ready image or a permitted retry to an available worker. Never dispatch two candidates for the same image. Retries and provider fallback wait until the preceding result is recorded; reduce active dispatch if the next provider has lower capacity.
5. On a safety rejection, stop new dispatch, interrupt outstanding work where supported and quarantine uncommitted results. Preserve returned candidates and account for consumed attempts. When work is resolved, release workers if supported and finalize through the manager.

For multiple source assignments under one confirmation, show both per-run worker allocations and the aggregate concurrent worker count. Share one pool across the batch: do not multiply the runtime/provider limit or the ceiling of 10 by the number of sources. Each five-image run uses at most five workers; reuse workers across runs and qualify jobs by source and idea. Freeze each run's allocation; increasing it requires confirmation. Serial manifest writes remain the coordinator's responsibility across the whole batch.
