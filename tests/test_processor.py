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
