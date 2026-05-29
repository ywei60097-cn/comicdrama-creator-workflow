from comicdrama.core.models import TextDocument, WorkflowConfig
from comicdrama.core.processor import ComicDramaProcessor


def test_workflow_requires_rights_confirmation():
    processor = ComicDramaProcessor()
    document = TextDocument(title="Demo", text="林舟说：“你好。”")
    config = WorkflowConfig(copyright_confirmation=False)

    try:
        processor.run(document, config)
    except ValueError as exc:
        assert "copyright_confirmation" in str(exc)
    else:
        raise AssertionError("workflow should require copyright confirmation")


def test_workflow_generates_script_and_storyboard():
    processor = ComicDramaProcessor()
    document = TextDocument(
        title="Demo",
        text="林舟在旧城南街等雨停。\n\n苏晴说：“我们还有六个小时。”",
    )
    config = WorkflowConfig(copyright_confirmation=True)

    result = processor.run(document, config)

    assert result.analysis.title == "Demo"
    assert result.simplified_novel
    assert result.script
    assert result.storyboard
    assert result.batch_operations
    assert result.adaptation_suggestions


def test_workflow_respects_selected_features():
    processor = ComicDramaProcessor()
    document = TextDocument(title="Demo", text="林舟在旧城南街等雨停。\n\n苏晴说：“我们还有六个小时。”")
    config = WorkflowConfig(copyright_confirmation=True, enabled_features=["simplify", "assist_adaptation"])

    result = processor.run(document, config)

    assert result.simplified_novel
    assert not result.script
    assert not result.storyboard
    assert not result.batch_operations
    assert result.adaptation_suggestions


def test_workflow_uses_character_reference_for_assistance():
    processor = ComicDramaProcessor()
    document = TextDocument(title="Demo", text="林舟在旧城南街等雨停。\n\n苏晴说：“我们还有六个小时。”")
    config = WorkflowConfig(
        copyright_confirmation=True,
        enabled_features=["assist_adaptation"],
        character_reference="林舟：冷静的男主角。苏晴：行动力强。",
    )

    result = processor.run(document, config)

    assert any("人物设定参考" in item.suggestion for item in result.adaptation_suggestions)


def test_workflow_uses_llm_for_structured_analysis_and_storyboard():
    processor = ComicDramaProcessor(llm_client=FakeLLMClient())
    document = TextDocument(
        title="Demo",
        text="林舟在旧城南街等雨停。\n\n苏晴说：“我们还有六个小时。”",
    )
    config = WorkflowConfig(copyright_confirmation=True)

    result = processor.run(document, config)

    assert result.analysis.characters[0].name == "林舟"
    assert result.analysis.characters[0].confidence == 0.92
    assert result.storyboard[0].shot_purpose == "建立危机"
    assert any("LLM provider enabled" in notice for notice in result.notices)


class FakeLLMClient:
    def structured_json(self, *, system_prompt, user_prompt, schema_name, schema):
        if schema_name == "comicdrama_analysis":
            return {
                "synopsis": "林舟与苏晴在雨夜发现危机线索。",
                "characters": [
                    {
                        "name": "林舟",
                        "role": "主角",
                        "first_seen": "林舟在旧城南街等雨停。",
                        "traits": ["谨慎"],
                        "visual_notes": ["雨夜中的青年"],
                        "relationship_notes": "与苏晴同行",
                        "evidence": "林舟在旧城南街等雨停。",
                        "confidence": 0.92,
                        "needs_review": False,
                    }
                ],
                "elements": [
                    {
                        "name": "旧城南街",
                        "kind": "location",
                        "description": "雨夜会面地点",
                        "evidence": "林舟在旧城南街等雨停。",
                        "confidence": 0.9,
                        "needs_review": False,
                    }
                ],
                "story_beats": [
                    {
                        "index": 1,
                        "summary": "林舟等待时遇到苏晴。",
                        "source_excerpt": "林舟在旧城南街等雨停。",
                        "conflict": "时间紧迫",
                        "emotional_value": "悬疑",
                    }
                ],
            }
        if schema_name == "comicdrama_storyboard":
            return {
                "storyboard": [
                    {
                        "shot_id": "S001",
                        "scene": "旧城南街",
                        "camera": "远景，雨夜街道",
                        "action": "林舟站在街边等待。",
                        "narration": "雨越来越急。",
                        "dialogue": "",
                        "visual_prompt": "中式漫剧，雨夜旧城南街，青年独自等待",
                        "shot_purpose": "建立危机",
                        "emotion": "紧张",
                    }
                ]
            }
        raise AssertionError(schema_name)
