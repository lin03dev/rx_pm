"""FastAPI backend for RX_PM reporting."""

from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.schemas import GenerateReportRequest, GenerateReportResponse
from backend.app.services import generate_report, list_databases, list_reports


app = FastAPI(title="RX_PM Reporting API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/reports")
def reports():
    return {"reports": list_reports()}


@app.get("/api/databases")
def databases():
    return {"databases": list_databases()}


@app.post("/api/reports/generate", response_model=GenerateReportResponse)
def generate(request: GenerateReportRequest):
    try:
        output_file = generate_report(
            report_id=request.report_id,
            database=request.database,
            output_format=request.output_format,
            filters=request.filters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateReportResponse(
        report_id=request.report_id,
        database=request.database,
        output_format=request.output_format,
        output_file=output_file,
    )


@app.get("/api/files")
def download_file(path: str):
    file_path = Path(path).resolve()
    output_root = (ROOT_DIR / "output").resolve()

    if output_root not in file_path.parents and file_path != output_root:
        raise HTTPException(status_code=403, detail="File is outside the output directory")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=file_path.name)
