from __future__ import annotations

import base64
import binascii
from io import BytesIO
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from comicdrama.core.models import NovelAnalysis, TextDocument, WorkflowConfig, WorkflowResult
from comicdrama.core.processor import ComicDramaProcessor


class WorkflowRequest(BaseModel):
    document: TextDocument
    config: WorkflowConfig


class FileExtractRequest(BaseModel):
    filename: str
    content_base64: str


class FileExtractResponse(BaseModel):
    filename: str
    title: str
    source_format: str
    text: str
    pages: Optional[int] = None
    notices: List[str] = Field(default_factory=list)


app = FastAPI(
    title="ComicDrama Creator Workflow API",
    version="0.1.0",
    description="API for simplifying novels, extracting adaptation elements, and generating comic-drama scripts.",
)
processor = ComicDramaProcessor()
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/files/extract-text", response_model=FileExtractResponse)
def extract_text(request: FileExtractRequest) -> FileExtractResponse:
    suffix = Path(request.filename).suffix.lower()
    title = Path(request.filename).stem or "Untitled Novel"
    try:
        raw = base64.b64decode(request.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 file payload.") from exc

    if suffix in {".txt", ".md"}:
        return FileExtractResponse(
            filename=request.filename,
            title=title,
            source_format=suffix.lstrip("."),
            text=_decode_text(raw),
        )
    if suffix == ".pdf":
        text, pages = _extract_pdf_text(raw)
        notices = []
        if not text.strip():
            notices.append("No selectable text was found. Scanned PDFs require OCR before processing.")
        return FileExtractResponse(
            filename=request.filename,
            title=title,
            source_format="pdf",
            text=text,
            pages=pages,
            notices=notices,
        )
    raise HTTPException(status_code=400, detail="Only TXT, MD, and PDF files are supported.")


@app.post("/api/v1/novel/analyze", response_model=NovelAnalysis)
def analyze(request: WorkflowRequest) -> NovelAnalysis:
    return processor.analyze(request.document)


@app.post("/api/v1/workflows/comicdrama", response_model=WorkflowResult)
def run_workflow(request: WorkflowRequest) -> WorkflowResult:
    try:
        return processor.run(request.document, request.config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/v1/novel/simplify")
def simplify(request: WorkflowRequest) -> dict[str, str]:
    try:
        result = processor.run(request.document, request.config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"title": request.document.title, "simplified_novel": result.simplified_novel}


@app.post("/api/v1/script/convert")
def convert_script(request: WorkflowRequest) -> dict[str, object]:
    try:
        result = processor.run(request.document, request.config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"title": request.document.title, "script": result.script}


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Could not decode text file. Use UTF-8 or GB18030.")


def _extract_pdf_text(raw: bytes) -> tuple[str, int]:
    try:
        from PyPDF2 import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PDF support requires PyPDF2. Install project dependencies first.") from exc

    try:
        reader = PdfReader(BytesIO(raw))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append(f"## Page {index}\n\n{page_text.strip()}")
        return "\n\n".join(pages).strip(), len(reader.pages)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not extract text from PDF: {exc}") from exc
