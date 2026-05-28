from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from comicdrama.core.models import NovelAnalysis, TextDocument, WorkflowConfig, WorkflowResult
from comicdrama.core.processor import ComicDramaProcessor


class WorkflowRequest(BaseModel):
    document: TextDocument
    config: WorkflowConfig


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
