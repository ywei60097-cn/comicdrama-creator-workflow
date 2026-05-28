# Contributing

Thanks for helping improve ComicDrama Creator Workflow.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Guidelines

- Keep prompts editable in `prompts/`; avoid hard-coding production prompts into Python code.
- Keep enterprise-facing payloads validated by Pydantic models and JSON schemas.
- Do not commit copyrighted novels, scripts, or production assets unless you have permission and include a clear license.
- Add tests for workflow behavior that affects API or CLI outputs.

