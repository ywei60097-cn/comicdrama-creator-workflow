from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ComicStyle(str, Enum):
    chinese = "chinese"
    japanese = "japanese"
    western = "western"
    custom = "custom"


class NarrationPOV(str, Enum):
    first_person = "first_person"
    third_person = "third_person"


class ScriptFormat(str, Enum):
    comic_narration = "comic_narration"
    hollywood = "hollywood"


class DetailLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


DEFAULT_ENABLED_FEATURES = [
    "simplify",
    "extract_elements",
    "convert_script",
    "batch_process",
    "assist_adaptation",
]


class WorkflowConfig(BaseModel):
    style: ComicStyle = ComicStyle.chinese
    target_format: ScriptFormat = ScriptFormat.comic_narration
    dialogue_retention_ratio: float = Field(default=0.8, ge=0.0, le=1.0)
    narration_pov: NarrationPOV = NarrationPOV.third_person
    storyboard_detail: DetailLevel = DetailLevel.medium
    episode_length: str = "short"
    copyright_confirmation: bool = False
    enabled_features: List[str] = Field(default_factory=lambda: list(DEFAULT_ENABLED_FEATURES))
    genre: Optional[str] = None
    tone: Optional[str] = None


class TextDocument(BaseModel):
    title: str = "Untitled Novel"
    source_format: str = "txt"
    text: str


class Character(BaseModel):
    name: str
    role: str = "unknown"
    first_seen: Optional[str] = None
    traits: List[str] = Field(default_factory=list)
    visual_notes: List[str] = Field(default_factory=list)


class SceneElement(BaseModel):
    name: str
    kind: str
    description: str = ""


class StoryBeat(BaseModel):
    index: int
    summary: str
    source_excerpt: str = ""


class ScriptBlock(BaseModel):
    block_type: str
    content: str
    speaker: Optional[str] = None


class StoryboardShot(BaseModel):
    shot_id: str
    scene: str
    camera: str
    action: str
    narration: str = ""
    dialogue: str = ""
    visual_prompt: str = ""


class BatchOperation(BaseModel):
    action: str
    status: str
    detail: str


class AdaptationSuggestion(BaseModel):
    category: str
    priority: str
    suggestion: str


class NovelAnalysis(BaseModel):
    title: str
    synopsis: str
    story_beats: List[StoryBeat]
    characters: List[Character]
    elements: List[SceneElement]


class WorkflowResult(BaseModel):
    config: WorkflowConfig
    analysis: NovelAnalysis
    simplified_novel: str
    script: List[ScriptBlock]
    storyboard: List[StoryboardShot]
    batch_operations: List[BatchOperation] = Field(default_factory=list)
    adaptation_suggestions: List[AdaptationSuggestion] = Field(default_factory=list)
    notices: List[str] = Field(default_factory=list)
