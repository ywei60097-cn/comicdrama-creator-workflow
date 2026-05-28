from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def read_text_file(path: str) -> str:
    file_path = Path(path)
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type: {file_path.suffix}. Use {supported}.")
    return file_path.read_text(encoding="utf-8")


def clean_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_paragraphs(text: str) -> List[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", clean_text(text)) if part.strip()]


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[。！？!?])\s*", clean_text(text))
    return [part.strip() for part in parts if part.strip()]


def compact_join(items: Iterable[str], limit: int = 1200) -> str:
    output: List[str] = []
    total = 0
    for item in items:
        if total + len(item) > limit:
            break
        output.append(item)
        total += len(item)
    return "\n".join(output)

