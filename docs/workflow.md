# Workflow Guide

The MVP workflow has six stages.

1. Import TXT or Markdown text.
2. Clean paragraphs, whitespace, and line endings.
3. Analyze story beats, characters, locations, and props.
4. Simplify the novel into an adaptation-friendly draft.
5. Convert the draft into comic narration or Hollywood-style script blocks.
6. Generate storyboard rows and export JSON or Markdown.

The browser workbench exposes five selectable features:

- Novel simplification.
- Character, scene, and prop extraction.
- Script format conversion.
- Batch content processing previews.
- Novel adaptation assistance.

For production use, connect an LLM provider at the processor boundary. The deterministic MVP is intentionally conservative and exists to prove the integration contract.

Task behavior should be implemented through task-level system prompts. See `prompt-design.md`.
