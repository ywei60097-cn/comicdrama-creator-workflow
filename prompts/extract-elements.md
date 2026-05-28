# Element Extraction Prompt

Extract structured adaptation elements from the source novel.

Return JSON with:

- characters: name, role, traits, relationship notes, visual notes.
- locations: name, description, atmosphere, recurring use.
- props: name, story function, owner, visual notes.
- story_beats: index, summary, conflict, emotional value.

Prefer explicit evidence from the source. Mark uncertain items as `needs_review`.

