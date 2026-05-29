from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from comicdrama.core.importers import extract_source_text
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
    sheets: Optional[int] = None
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


@app.get("/api/v1/llm/status")
def llm_status() -> dict[str, object]:
    if not processor.llm_client:
        return {"enabled": False, "model": None, "api_base_url": None}
    settings = processor.llm_client.settings
    return {"enabled": True, "model": settings.model, "api_base_url": settings.api_base_url}


@app.post("/api/v1/files/extract-text", response_model=FileExtractResponse)
def extract_text(request: FileExtractRequest) -> FileExtractResponse:
    try:
        raw = base64.b64decode(request.content_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 file payload.") from exc

    try:
        extracted = extract_source_text(request.filename, raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not extract text from file: {exc}") from exc

    return FileExtractResponse(**extracted.__dict__)


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
