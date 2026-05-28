from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from .core.exporters import result_to_markdown, save_json, to_json
from .core.models import ScriptFormat, TextDocument, WorkflowConfig
from .core.processor import ComicDramaProcessor
from .core.text import read_text_file


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        _dispatch(args)
    except Exception as exc:
        raise SystemExit(f"error: {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comicdrama", description="Novel-to-comic-drama workflow toolkit.")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("run", "simplify", "extract", "script"):
        cmd = sub.add_parser(command)
        cmd.add_argument("input", help="Input TXT or MD file.")
        cmd.add_argument("--title", default=None)
        cmd.add_argument("--config", default=None, help="JSON config file.")
        cmd.add_argument("--output", "-o", default=None, help="Output file path.")
        cmd.add_argument("--format", choices=("json", "markdown"), default="json")
        cmd.add_argument("--style", choices=("chinese", "japanese", "western", "custom"), default=None)
        cmd.add_argument("--target-format", choices=("comic_narration", "hollywood"), default=None)
        cmd.add_argument("--dialogue-ratio", type=float, default=None)
        cmd.add_argument("--pov", choices=("first_person", "third_person"), default=None)
        cmd.add_argument("--storyboard-detail", choices=("low", "medium", "high"), default=None)
        cmd.add_argument("--confirm-rights", action="store_true", help="Confirm legal rights to process the source.")
    return parser


def _dispatch(args: argparse.Namespace) -> None:
    config = _load_config(args)
    text = read_text_file(args.input)
    title = args.title or Path(args.input).stem
    document = TextDocument(title=title, source_format=Path(args.input).suffix.lstrip("."), text=text)
    processor = ComicDramaProcessor()

    if args.command == "simplify":
        result = processor.run(document, config)
        payload: Any = {"title": title, "simplified_novel": result.simplified_novel}
        _emit(args, payload, markdown=f"# {title}\n\n{result.simplified_novel}\n")
        return
    if args.command == "extract":
        analysis = processor.analyze(document)
        _emit(args, analysis)
        return
    if args.command == "script":
        result = processor.run(document, config)
        payload = {"title": title, "script": [block.model_dump(mode="json") for block in result.script]}
        _emit(args, payload)
        return

    result = processor.run(document, config)
    if args.output and args.format == "json":
        save_json(args.output, result)
    elif args.output:
        Path(args.output).write_text(result_to_markdown(result), encoding="utf-8")
    else:
        print(result_to_markdown(result) if args.format == "markdown" else to_json(result))


def _load_config(args: argparse.Namespace) -> WorkflowConfig:
    data: Dict[str, Any] = {}
    if args.config:
        data.update(json.loads(Path(args.config).read_text(encoding="utf-8")))
    overrides = {
        "style": args.style,
        "target_format": args.target_format,
        "dialogue_retention_ratio": args.dialogue_ratio,
        "narration_pov": args.pov,
        "storyboard_detail": args.storyboard_detail,
    }
    data.update({key: value for key, value in overrides.items() if value is not None})
    if args.confirm_rights:
        data["copyright_confirmation"] = True
    return WorkflowConfig(**data)


def _emit(args: argparse.Namespace, payload: Any, markdown: str | None = None) -> None:
    if args.format == "markdown":
        text = markdown or f"```json\n{json.dumps(_jsonable(payload), ensure_ascii=False, indent=2)}\n```\n"
    elif hasattr(payload, "model_dump_json"):
        text = payload.model_dump_json(indent=2, ensure_ascii=False)
    else:
        text = json.dumps(_jsonable(payload), ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


def _jsonable(payload: Any) -> Any:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="json")
    return payload


if __name__ == "__main__":
    main()

