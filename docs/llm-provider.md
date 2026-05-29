# LLM Provider Configuration

ComicDrama Creator Workflow can run in two modes:

- Rule mode: no model configuration, useful for local UI and contract testing.
- LLM mode: OpenAI-compatible chat completions endpoint for structured analysis and storyboard generation.

## Environment Variables

Configure the provider on the server side. Do not put API keys in the browser.

```bash
export LLM_API_BASE_URL="https://api.example.com/v1"
export LLM_API_KEY="your-api-key"
export LLM_MODEL="your-model-name"
export LLM_TEMPERATURE="0.2"
export LLM_TIMEOUT_SECONDS="90"
export LLM_MAX_OUTPUT_TOKENS="4096"
```

Then start the API:

```bash
set -a
source .env
set +a
PYTHONPATH=src python3 -m uvicorn comicdrama.api.app:app --host 127.0.0.1 --port 8000
```

The browser workbench shows `模型已启用` when the provider is configured.

## API Shape

The client calls:

```text
POST {LLM_API_BASE_URL}/chat/completions
Authorization: Bearer {LLM_API_KEY}
```

It sends `response_format.type=json_schema` to request structured JSON. If your provider does not support JSON schema mode, use an OpenAI-compatible gateway that does, or adapt `src/comicdrama/core/llm.py`.

## Current LLM Tasks

- `prompts/extract-elements.md`: extracts synopsis, characters, locations, props, and story beats with evidence, confidence, and review flags.
- `prompts/storyboard.md`: generates storyboard rows with scene continuity, camera logic, shot purpose, emotion, and visual prompts.

If the provider fails or returns invalid JSON, the workflow falls back to deterministic local logic and records a notice in the result.
