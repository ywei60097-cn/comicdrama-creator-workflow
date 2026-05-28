from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List

from .models import (
    Character,
    DetailLevel,
    NovelAnalysis,
    SceneElement,
    ScriptBlock,
    ScriptFormat,
    StoryBeat,
    StoryboardShot,
    TextDocument,
    WorkflowConfig,
    WorkflowResult,
)
from .text import clean_text, compact_join, split_paragraphs, split_sentences


LOCATION_HINTS = ("地下室", "旧城南街", "钟楼", "巷口", "书房", "老宅", "城", "村", "山", "谷", "宫", "殿", "楼", "街", "巷", "海", "岛", "星", "站", "屋", "房", "宅", "室")
PROP_HINTS = ("放映机", "钥匙", "卷轴", "玉佩", "芯片", "剑", "刀", "枪", "信", "戒", "令", "药")


class ComicDramaProcessor:
    """Rule-based MVP processor with clean extension points for LLM providers."""

    def run(self, document: TextDocument, config: WorkflowConfig) -> WorkflowResult:
        if not config.copyright_confirmation:
            raise ValueError("copyright_confirmation must be true before processing source text.")

        cleaned = clean_text(document.text)
        analysis = self.analyze(TextDocument(title=document.title, source_format=document.source_format, text=cleaned))
        simplified = self.simplify(cleaned, config)
        script = self.convert_to_script(simplified, analysis, config)
        storyboard = self.generate_storyboard(script, analysis, config)
        notices = [
            "MVP uses deterministic extraction. Connect an LLM provider for production-grade adaptation quality.",
            "Generated scripts still require human editorial review before commercial production.",
        ]
        return WorkflowResult(
            config=config,
            analysis=analysis,
            simplified_novel=simplified,
            script=script,
            storyboard=storyboard,
            notices=notices,
        )

    def analyze(self, document: TextDocument) -> NovelAnalysis:
        paragraphs = [paragraph for paragraph in split_paragraphs(document.text) if not paragraph.lstrip().startswith("#")]
        sentences = split_sentences(document.text)
        beats = [
            StoryBeat(index=index + 1, summary=_summarize_paragraph(paragraph), source_excerpt=paragraph[:180])
            for index, paragraph in enumerate(paragraphs[:12])
        ]
        characters = _extract_characters(document.text)
        elements = _extract_elements(document.text)
        synopsis = compact_join((beat.summary for beat in beats), limit=900) or "No synopsis generated."
        if not beats and sentences:
            beats = [StoryBeat(index=1, summary=sentences[0][:120], source_excerpt=sentences[0][:180])]
        return NovelAnalysis(
            title=document.title,
            synopsis=synopsis,
            story_beats=beats,
            characters=characters,
            elements=elements,
        )

    def simplify(self, text: str, config: WorkflowConfig) -> str:
        paragraphs = split_paragraphs(text)
        if not paragraphs:
            return ""
        keep_count = max(1, min(len(paragraphs), int(len(paragraphs) * 0.45) or 1))
        selected = paragraphs[:keep_count]
        dialogue = [p for p in paragraphs if _is_dialogue_heavy(p)]
        dialogue_keep = int(len(dialogue) * config.dialogue_retention_ratio)
        selected.extend(dialogue[:dialogue_keep])
        unique = list(dict.fromkeys(selected))
        return "\n\n".join(_summarize_paragraph(paragraph, limit=220) for paragraph in unique)

    def convert_to_script(
        self,
        simplified: str,
        analysis: NovelAnalysis,
        config: WorkflowConfig,
    ) -> List[ScriptBlock]:
        paragraphs = split_paragraphs(simplified)
        blocks: List[ScriptBlock] = []
        if config.target_format == ScriptFormat.hollywood:
            for index, paragraph in enumerate(paragraphs, start=1):
                scene_name = _pick_scene_name(analysis.elements, index)
                blocks.append(ScriptBlock(block_type="scene_heading", content=f"INT./EXT. {scene_name} - DAY"))
                blocks.extend(_paragraph_to_hollywood_blocks(paragraph))
            return blocks

        pov_prefix = "我看见" if config.narration_pov.value == "first_person" else "画面中"
        for index, paragraph in enumerate(paragraphs, start=1):
            blocks.append(ScriptBlock(block_type="panel", content=f"分镜 {index}"))
            dialogue_blocks = _extract_dialogue_blocks(paragraph)
            narration = _strip_dialogue(paragraph)
            if narration:
                blocks.append(ScriptBlock(block_type="narration", content=f"{pov_prefix}，{narration}"))
            blocks.extend(dialogue_blocks)
        return blocks

    def generate_storyboard(
        self,
        script: Iterable[ScriptBlock],
        analysis: NovelAnalysis,
        config: WorkflowConfig,
    ) -> List[StoryboardShot]:
        detail = {
            DetailLevel.low: "medium shot",
            DetailLevel.medium: "cinematic medium shot with character blocking",
            DetailLevel.high: "cinematic shot, clear foreground/background layers, emotion-focused composition",
        }[config.storyboard_detail]
        shots: List[StoryboardShot] = []
        current_scene = analysis.elements[0].name if analysis.elements else "主场景"
        for index, block in enumerate(script, start=1):
            if block.block_type in {"scene_heading", "panel"}:
                current_scene = block.content
                continue
            if block.block_type not in {"narration", "action", "dialogue"}:
                continue
            prompt = f"{config.style.value} comic drama, {detail}, scene: {current_scene}, content: {block.content[:120]}"
            shots.append(
                StoryboardShot(
                    shot_id=f"S{len(shots) + 1:03d}",
                    scene=current_scene,
                    camera=detail,
                    action=block.content if block.block_type != "dialogue" else "",
                    narration=block.content if block.block_type == "narration" else "",
                    dialogue=block.content if block.block_type == "dialogue" else "",
                    visual_prompt=prompt,
                )
            )
        return shots


def _summarize_paragraph(paragraph: str, limit: int = 180) -> str:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    if len(paragraph) <= limit:
        return paragraph
    sentence = split_sentences(paragraph)[0] if split_sentences(paragraph) else paragraph
    return sentence[:limit].rstrip("，,。") + "..."


def _extract_characters(text: str) -> List[Character]:
    patterns = [
        r"([\u4e00-\u9fa5]{2,3})(?:低声|喘着气)?说",
        r"(?:^|[。！？\n])([\u4e00-\u9fa5]{2,3})(?=在)",
        r"([\u4e00-\u9fa5]{2,3})(?=想起)",
        r"([\u4e00-\u9fa5]{2,3})从",
        r"([\u4e00-\u9fa5]{2,3})的出现",
    ]
    candidates: List[str] = []
    for pattern in patterns:
        candidates.extend(re.findall(pattern, text))
    stopwords = {
        "一个",
        "他们",
        "我们",
        "自己",
        "时候",
        "这里",
        "那里",
        "小说",
        "故事",
        "世界",
        "声音",
        "眼前",
        "我在你",
        "如果这",
        "可现",
    }
    normalized = []
    for name in candidates:
        name = name.strip("的和在从了")
        if name not in stopwords and 2 <= len(name) <= 3:
            normalized.append(name)
    counted = Counter(normalized)
    characters = []
    for name, _ in counted.most_common(10):
        if any(hint in name for hint in LOCATION_HINTS + PROP_HINTS):
            continue
        first_seen = _first_sentence_containing(text, name)
        characters.append(Character(name=name, first_seen=first_seen, traits=_infer_traits(first_seen or "")))
    return characters[:8]


def _extract_elements(text: str) -> List[SceneElement]:
    words = Counter(_extract_named_elements(text))
    elements: List[SceneElement] = []
    for word, _ in words.most_common(80):
        if any(hint in word for hint in LOCATION_HINTS):
            elements.append(SceneElement(name=word, kind="location", description=_first_sentence_containing(text, word) or ""))
        elif any(hint in word for hint in PROP_HINTS):
            elements.append(SceneElement(name=word, kind="prop", description=_first_sentence_containing(text, word) or ""))
        if len(elements) >= 12:
            break
    return elements


def _extract_named_elements(text: str) -> List[str]:
    results: List[str] = []
    location_terms = "|".join(sorted(LOCATION_HINTS, key=len, reverse=True))
    prop_terms = "|".join(sorted([hint for hint in PROP_HINTS if hint != "信"], key=len, reverse=True))
    for match in re.findall(rf"[\u4e00-\u9fa5]{{1,8}}(?:{location_terms})", text):
        results.append(_trim_element(match, LOCATION_HINTS))
    for match in re.findall(rf"[\u4e00-\u9fa5]{{0,6}}(?:{prop_terms})", text):
        results.append(_trim_element(match, PROP_HINTS))
    for match in re.findall(r"(?:署名的信|一封信|书信|来信|信纸)", text):
        results.append(match)
    return [item for item in results if len(item) >= 2]


def _trim_element(value: str, hints: tuple[str, ...]) -> str:
    value = value.strip("，。！？：“”\"、 \n")
    prefixes = ("在", "从", "到", "进", "的", "一封没有署名的", "一枚裂开的", "旧式")
    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix) :]
    for delimiter in ("从", "在", "回", "进", "到", "向", "的"):
        if delimiter in value:
            value = value.rsplit(delimiter, 1)[-1]
    for hint in sorted(hints, key=len, reverse=True):
        if len(hint) > 1 and hint in value:
            index = value.find(hint)
            return value[max(0, index - 4) : index + len(hint)]
    for hint in hints:
        index = value.find(hint)
        if index >= 0:
            return value[max(0, index - 3) : index + len(hint)]
    return value[-6:]


def _first_sentence_containing(text: str, term: str) -> str:
    for sentence in split_sentences(text):
        if term in sentence:
            return sentence[:160]
    return ""


def _infer_traits(sentence: str) -> List[str]:
    traits = []
    mapping = {
        "冷": "冷静",
        "笑": "外向",
        "怒": "强冲突",
        "哭": "情绪脆弱",
        "剑": "战斗相关",
        "王": "权力关系",
    }
    for marker, trait in mapping.items():
        if marker in sentence:
            traits.append(trait)
    return traits[:3]


def _is_dialogue_heavy(paragraph: str) -> bool:
    return any(mark in paragraph for mark in ("“", "”", "\"", "：", ":"))


def _extract_dialogue_blocks(paragraph: str) -> List[ScriptBlock]:
    quoted = re.findall(r"[“\"]([^”\"]+)[”\"]", paragraph)
    blocks = [ScriptBlock(block_type="dialogue", content=item.strip()) for item in quoted if item.strip()]
    if not blocks and ("：" in paragraph or ":" in paragraph):
        for line in paragraph.splitlines():
            if "：" in line:
                speaker, content = line.split("：", 1)
                blocks.append(ScriptBlock(block_type="dialogue", speaker=speaker.strip(), content=content.strip()))
            elif ":" in line:
                speaker, content = line.split(":", 1)
                blocks.append(ScriptBlock(block_type="dialogue", speaker=speaker.strip(), content=content.strip()))
    return blocks


def _strip_dialogue(paragraph: str) -> str:
    return re.sub(r"[“\"].+?[”\"]", "", paragraph).strip()


def _pick_scene_name(elements: List[SceneElement], index: int) -> str:
    locations = [element.name for element in elements if element.kind == "location"]
    if not locations:
        return f"SCENE {index}"
    return locations[(index - 1) % len(locations)]


def _paragraph_to_hollywood_blocks(paragraph: str) -> List[ScriptBlock]:
    blocks = []
    action = _strip_dialogue(paragraph)
    if action:
        blocks.append(ScriptBlock(block_type="action", content=action))
    blocks.extend(_extract_dialogue_blocks(paragraph))
    return blocks
