# Source Import Design

ComicDrama Creator Workflow uses a single document import contract:

```http
POST /api/v1/files/extract-text
```

The endpoint accepts a filename and base64 payload, then returns normalized text that can be passed into the main comic-drama workflow.

## Supported Formats

| Format | Status | Extraction Strategy | Notes |
| --- | --- | --- | --- |
| TXT | Stable | Decode text | UTF-8, GB18030, and Big5 are attempted. |
| MD / Markdown | Stable | Decode text | Markdown structure is preserved as plain text. |
| PDF | Stable | `PyPDF2` selectable-text extraction | Scanned image PDFs require OCR before import. |
| DOCX | Stable | `python-docx` paragraphs and tables | Recommended Word format. |
| HTML / HTM | Stable | Standard-library HTML parser | Scripts and styles are ignored. |
| CSV | Stable | Standard-library CSV reader | Rows are converted to pipe-delimited text. |
| JSON | Stable | Recursive flattening | Useful for structured story bibles or exports. |
| RTF | Basic | Lightweight control-word stripping | Good enough for simple RTF, not a full fidelity parser. |
| XLSX | Optional | `openpyxl` worksheets | Install `comicdrama-creator-workflow[spreadsheet]`. |
| DOC | Unsupported | N/A | Convert legacy `.doc` to `.docx` or PDF first. |
| Pages | Unsupported | N/A | Export to `.docx` or PDF first. |

## Product Rules

- Importers should return plain text, title, source format, and format-specific metadata.
- Importers should not start the creative workflow automatically.
- OCR is a separate capability and should be added behind the same endpoint later.
- Enterprise connectors should normalize cloud documents into this same endpoint or directly into `TextDocument`.

## Future Extensions

- OCR for scanned PDFs and image manuscripts.
- EPUB chapter extraction.
- Cloud document import from Feishu, Google Docs, Notion, or enterprise CMS.
- Batch upload with per-file status and merged project manifests.
