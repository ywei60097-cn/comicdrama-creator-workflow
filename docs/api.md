# API Guide

Start the API:

```bash
PYTHONPATH=src python3 -m uvicorn comicdrama.api.app:app --reload
```

The browser workbench is available at:

```text
http://127.0.0.1:8000/
```

Endpoints:

- `GET /health`
- `POST /api/v1/files/extract-text`
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

PDF upload support extracts selectable text from PDF files. Scanned image PDFs need OCR before they can be processed.
