from __future__ import annotations

import json
from typing import Iterable

from pydantic import BaseModel

from .models import ScriptBlock, StoryboardShot, WorkflowResult


def to_json(model: BaseModel) -> str:
    return model.model_dump_json(indent=2, ensure_ascii=False)


def result_to_markdown(result: WorkflowResult) -> str:
    lines = [
        f"# {result.analysis.title}",
        "",
        "## Synopsis",
        result.analysis.synopsis,
        "",
        "## Simplified Novel",
        result.simplified_novel,
        "",
        "## Characters",
    ]
    for character in result.analysis.characters:
        traits = ", ".join(character.traits) if character.traits else "TBD"
        lines.append(f"- **{character.name}**: {character.role}; traits: {traits}")
    lines.extend(["", "## Elements"])
    for element in result.analysis.elements:
        lines.append(f"- **{element.name}** ({element.kind}): {element.description}")
    lines.extend(["", "## Script"])
    lines.extend(_script_to_markdown(result.script))
    lines.extend(["", "## Storyboard"])
    lines.extend(_storyboard_to_markdown(result.storyboard))
    lines.extend(["", "## Notices"])
    lines.extend(f"- {notice}" for notice in result.notices)
    return "\n".join(lines).strip() + "\n"


def _script_to_markdown(blocks: Iterable[ScriptBlock]) -> list[str]:
    lines = []
    for block in blocks:
        if block.block_type in {"scene_heading", "panel"}:
            lines.append(f"\n### {block.content}")
        elif block.block_type == "dialogue":
            speaker = f"**{block.speaker}**: " if block.speaker else "**Dialogue**: "
            lines.append(f"{speaker}{block.content}")
        else:
            lines.append(f"**{block.block_type.title()}**: {block.content}")
    return lines


def _storyboard_to_markdown(shots: Iterable[StoryboardShot]) -> list[str]:
    lines = ["| Shot | Scene | Camera | Action | Dialogue |", "| --- | --- | --- | --- | --- |"]
    for shot in shots:
        lines.append(
            "| {shot_id} | {scene} | {camera} | {action} | {dialogue} |".format(
                shot_id=_cell(shot.shot_id),
                scene=_cell(shot.scene),
                camera=_cell(shot.camera),
                action=_cell(shot.action or shot.narration),
                dialogue=_cell(shot.dialogue),
            )
        )
    return lines


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def save_json(path: str, model: BaseModel) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(model.model_dump(mode="json"), file, indent=2, ensure_ascii=False)

