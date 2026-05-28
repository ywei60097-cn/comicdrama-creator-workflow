# API Guide

Start the API:

```bash
uvicorn comicdrama.api.app:app --reload
```

Endpoints:

- `GET /health`
- `POST /api/v1/novel/analyze`
- `POST /api/v1/novel/simplify`
- `POST /api/v1/script/convert`
- `POST /api/v1/workflows/comicdrama`

All endpoints accept a `WorkflowRequest` object:

```json
{
  "document": {
    "title": "Demo",
    "source_format": "md",
    "text": "..."
  },
  "config": {
    "copyright_confirmation": true
  }
}
```

Use `schemas/workflow-result.schema.json` as the stable response contract for enterprise adapters.

