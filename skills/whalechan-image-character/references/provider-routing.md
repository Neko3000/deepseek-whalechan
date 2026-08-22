# Provider routing and execution contract

Use providers only in this order:

1. Built-in Codex ImageGen / GPT Image 2
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

## Built-in Codex ImageGen

Use the built-in `image_gen` tool with one candidate per call. Its current Codex tool contract does not expose an exact size argument. For `provider-native`, describe the frozen aspect ratio and composition in the prompt, then accept any decoded size whose ratio passes automatic QA. For `exact`, record a `capability` error before generation and route forward. Load local reference images when the tool requires them to be visible in context and provide their role limits in the prompt. Treat references as guidance, not edit targets, unless the confirmed task is explicitly an edit. Copy the project-bound result into the run's candidate or worker staging directory before validation.

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

The adapter extracts paths for the provider request but preserves IDs, roles, instructions, and hashes in dry-run and audit output. A dry-run validates capabilities and prints a credential-free summary; it never makes a network call. A live call writes exactly one candidate PNG. Never log credential values.

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

## Parallel coordinator

Sequential execution is the default. When `requested_parallelism > 1`, compute:

```text
effective_parallelism = min(
  requested_parallelism,
  5,
  runtime_available_worker_slots,
  provider_concurrency_limit,
  ready_image_count
)
```

Record requested and effective values. At initialization, the effective value must not exceed the number of initially ready images. Downgrading capacity does not change image semantics and does not require renewed confirmation; changing assignment content or budget does.

The main agent is the sole coordinator and manifest writer:

- Dispatch only different ready images; never dispatch two candidates for one image at once.
- Give each worker a unique staging directory and read-only access to the frozen assignment.
- Workers may build prompts, call one provider, validate, measure, and visually review their candidate. They must not call manifest mutation or final promotion commands.
- The coordinator serially records errors/candidates and promotes PASS results after checking hashes and evidence.
- Honor counterpart dependencies: the higher-ratio counterpart must PASS before the lower-ratio task becomes ready.
- On safety rejection, set the whole run to `safety_blocked`, stop new dispatches, and quarantine uncommitted in-flight results pending review.

This single-writer contract is required even when the runtime can support five worker calls.

## Errors and budgets

- Authentication, quota, rate-limit, timeout, service, and capability failures that return no viewable image are provider errors; record them without consuming candidate budget.
- A response containing a viewable image is one candidate whether it passes or fails.
- Record moderation/safety rejection separately and stop automatic routing.
- Limit transient retries; never create an unbounded adapter loop.
- Never exceed 2 candidates per provider by default, 8 per image, or the confirmed run budget.
