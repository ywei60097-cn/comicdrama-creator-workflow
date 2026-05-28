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

