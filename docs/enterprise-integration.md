# Enterprise Integration

Recommended embedding modes:

- CLI inside an existing pipeline.
- REST API behind an internal gateway.
- Python package imported into an orchestration service.

Integration principles:

- Store prompts and style presets outside application code.
- Keep source text in the enterprise content system; pass only job-scoped payloads to the workflow service.
- Persist generated JSON responses for audit and regeneration.
- Add review states before commercial use.
- Treat copyright confirmation as a required upstream gate.

Example CLI job:

```bash
comicdrama run manuscript.md \
  --config config.json \
  --confirm-rights \
  --format json \
  --output build/workflow-result.json
```

Example API task:

```http
POST /api/v1/workflows/comicdrama
Content-Type: application/json
```

