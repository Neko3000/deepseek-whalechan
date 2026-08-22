# Provider routing

Use providers in this order: built-in Codex ImageGen, OpenAI Images API, Nano Banana, Seedream. Never move backward.

Move forward only after the current provider has produced a failed candidate, cannot perform the required reference/edit operation, or has a recorded availability, authentication, quota, rate-limit, timeout, or service error. Never use fallback to bypass a safety rejection.

## Built-in ImageGen

Use one call per provider-produced image. Load local references when required. The built-in tool exposes no pixel-size parameter, so use it for automatic output and validate the returned native dimensions against the frozen ratio. A square result such as `1254x1254` is valid even though `1024x1024` is recommended. For explicit resolution, record `capability` and continue to OpenAI rather than pretending the prompt can guarantee pixels. Copy every returned project-bound image into the run before QA and recording. Record provider as `codex`.

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

The v5 nested `output` object is required; legacy top-level `size`, `aspect_ratio`, and `image_size` fields are rejected. Use 1–5 bundled or frozen user references. Resolve relative paths from the request JSON. Adapters preserve the requested output, reference roles, and hashes in audit output while reporting the effective provider size or tier. Never silently approximate an explicit resolution or drop a required role because of a provider limit; report `capability` and route forward. A live adapter writes one PNG and never overwrites an existing path.

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

## Parallel coordinator

Sequential execution is the default. For a parallel request, compute:

```text
effective_parallelism = min(
  requested_parallelism,
  5,
  runtime_available_worker_slots,
  provider_concurrency_limit,
  ready_image_count
)
```

Record requested and effective values. Lower runtime capacity changes only scheduling, not image semantics.

The main agent is the sole manifest writer. Dispatch only different ready images and give each worker a unique `staging/<image-id>/` directory plus read-only access to the frozen assignment. Workers may build one prompt, call one provider, validate, measure, and visually review. They must not call `record-*`, `promote`, or `finalize`. The coordinator verifies returned hashes and evidence, then serially records and promotes. Never generate two candidates for one image simultaneously. A retry or provider fallback may start only after the previous result for that image has been recorded.
