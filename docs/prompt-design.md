# Prompt Design

ComicDrama Creator Workflow should be driven by task-level system prompts, not by scattered keyword filters.

## Principle

Each product capability needs:

- A clear professional role.
- A precise task boundary.
- Input assumptions.
- Hard constraints.
- Step-by-step workflow.
- Output contract.
- Quality checks.

## Current Task Prompts

- `prompts/simplify.md`: original novel simplification and chapter reconstruction.
- `prompts/character-naming.md`: character naming optimization and kinship consistency.
- `prompts/extract-elements.md`: characters, locations, props, and story beats.
- `prompts/convert-script.md`: comic narration or Hollywood script conversion.
- `prompts/storyboard.md`: storyboard row generation.

## Novel Simplification Requirements

Example task:

> 将原创小说《东海没有海》前 13 章简练为 3 章，每章约 1000 字的短篇小说，最后给 Word 文档。

The simplification prompt must preserve:

- Main plot framework.
- Key characters and relationships.
- Major conflicts and turns.
- Important dialogue.
- Chapter hooks and adaptation value.

Hard checks:

- Chapter endings must be complete sentences.
- It is acceptable to exceed the requested chapter length by 1%-15% to preserve completeness.
- Do not cut mid-sentence to satisfy a word target.
- Do not alter the original main ending unless requested.

## Character Naming Requirements

Example task:

> 优化小说剧本中的男主角姓名，让其符合时代特色，注意亲属关系要保持，不能出现爷孙或者父子不同姓，最后给 Word 文档。

The naming prompt must preserve:

- Kinship consistency.
- Nicknames and rural/family forms of address when appropriate.
- Name-related jokes, narration, and dialogue through semantic rewriting.

