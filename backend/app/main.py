"""FastAPI backend for RX_PM reporting."""

from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[2]
for path in (BACKEND_DIR, ROOT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from .schemas import (
    ActiveDatabasesRequest,
    AgOverviewResponse,
    DashboardInsightsResponse,
    DatabaseConnectionRequest,
    DatabaseConnectionsResponse,
    DatabaseConnectionUpdateRequest,
    DatabaseSelectionRequest,
    DatabaseTestRequest,
    GenerateReportRequest,
    GenerateReportResponse,
    PreviewReportRequest,
    PreviewReportResponse,
)
from .dashboard_service import get_dashboard_insights
from .ag_overview_service import get_ag_overview
from .database_service import (
    create_database_connection,
    delete_database_connection,
    list_database_connections,
    set_active_databases,
    set_project_database_selection,
    test_database_connection,
    update_database_connection,
)
from core.schema_guard import SchemaViolationError
from config.output_config import get_output_config
from .services import generate_report, list_reports, preview_report_data

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


@app.get("/api/databases", response_model=DatabaseConnectionsResponse)
def databases():
    return DatabaseConnectionsResponse(**list_database_connections())


@app.put("/api/databases/active", response_model=DatabaseConnectionsResponse)
def update_active_databases(request: ActiveDatabasesRequest):
    try:
        set_active_databases(request.active, request.primary)
        return DatabaseConnectionsResponse(**list_database_connections())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/databases/selection", response_model=DatabaseConnectionsResponse)
def update_database_selection(request: DatabaseSelectionRequest):
    try:
        set_project_database_selection(request.project, request.database)
        return DatabaseConnectionsResponse(**list_database_connections())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/databases/test")
def test_database(request: DatabaseTestRequest):
    try:
        return test_database_connection(request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/databases")
def create_database(request: DatabaseConnectionRequest):
    try:
        return create_database_connection(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.put("/api/databases/{name}")
def update_database(name: str, request: DatabaseConnectionUpdateRequest):
    try:
        return update_database_connection(name, request.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/databases/{name}")
def remove_database(name: str):
    try:
        return delete_database_connection(name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/dashboard/insights", response_model=DashboardInsightsResponse)
def dashboard_insights(project: str, database: str, refresh: bool = False):
    try:
        return DashboardInsightsResponse(**get_dashboard_insights(project, database, refresh=refresh))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/dashboard/ag-overview", response_model=AgOverviewResponse)
def ag_overview_dashboard(
    database: str,
    country: str | None = None,
    language: str | None = None,
    project_type: str | None = None,
    dialect: str | None = None,
    limit: int = 1000,
    refresh: bool = False,
):
    try:
        return AgOverviewResponse(**get_ag_overview(
            database,
            country=country,
            language=language,
            project_type=project_type,
            dialect=dialect,
            limit=min(max(limit, 1), 5000),
            refresh=refresh,
        ))
    except SchemaViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/reports/preview", response_model=PreviewReportResponse)
def preview(request: PreviewReportRequest):
    try:
        payload = preview_report_data(
            report_id=request.report_id,
            database=request.database,
            databases=request.databases,
            filters=request.filters,
            limit=request.limit,
        )
    except SchemaViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PreviewReportResponse(**payload)


@app.post("/api/reports/generate", response_model=GenerateReportResponse)
def generate(request: GenerateReportRequest):
    try:
        payload = generate_report(
            report_id=request.report_id,
            database=request.database,
            databases=request.databases,
            output_format=request.output_format,
            filters=request.filters,
        )
    except SchemaViolationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GenerateReportResponse(**payload)


@app.get("/api/files")
def download_file(path: str):
    try:
        file_path = get_output_config().resolve_generated_file(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    output_root = (BACKEND_DIR / "output").resolve()
    if output_root not in file_path.parents and file_path.parent != output_root:
        raise HTTPException(status_code=403, detail="File is outside the output directory")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, filename=file_path.name)
