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

Supported source imports:

- TXT and Markdown
- Selectable-text PDF
- DOCX
- HTML / HTM
- CSV
- JSON
- RTF
- XLSX when the optional spreadsheet dependency is installed

Scanned image PDFs need OCR before they can be processed. Legacy `.doc` and Apple Pages files should be exported to `.docx` or PDF before import.

See `source-imports.md` for the complete import design and extension plan.
