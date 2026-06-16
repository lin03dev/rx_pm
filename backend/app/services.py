"""Application services that wrap the existing reporting engine."""

import json
from pathlib import Path
import sys
from typing import Any, Dict, List

import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config.database_config import DatabaseConfigManager
from config.output_config import get_output_config
from config.report_registry import list_configured_reports, load_report_catalog, register_configured_reports
from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from config.system_loader import load_config

from core.schema_guard import SchemaViolationError
from .database_service import list_database_connections, resolve_databases_for_request


def list_reports() -> List[Dict]:
    """Return configured report metadata."""
    return list_configured_reports()


def list_databases() -> List[Dict]:
    """Return configured database metadata plus active flags."""
    return list_database_connections()["databases"]


def get_report_category(report_id: str) -> str:
    report_info = load_report_catalog().get(report_id, {})
    return report_info.get("category", "Utility")


def generate_report(
    report_id: str,
    output_format: str,
    filters: Dict[str, str] | None = None,
    database: str | None = None,
    databases: List[str] | None = None,
) -> Dict[str, Any]:
    """Generate a configured report for one or more databases."""
    target_databases = resolve_databases_for_request(
        database, databases, get_report_category(report_id), report_id=report_id
    )
    outputs = []

    for db_name in target_databases:
        engine = _build_report_engine(db_name)
        output_file = engine.generate_report(
            report_name=report_id,
            output_format=output_format,
            filters=filters or {},
            db_name=db_name,
        )
        resolved_output = get_output_config().resolve_generated_file(output_file)
        outputs.append({
            "report_id": report_id,
            "database": db_name,
            "output_format": output_format,
            "output_file": str(resolved_output),
        })

    first = outputs[0]
    return {
        "report_id": report_id,
        "output_format": output_format,
        "outputs": outputs,
        "database": first["database"] if len(outputs) == 1 else None,
        "output_file": first["output_file"] if len(outputs) == 1 else None,
    }


def _build_report_engine(database: str) -> ReportEngine:
    db_config_manager = DatabaseConfigManager()
    if database not in db_config_manager.list_databases():
        raise ValueError(f"Unknown database: {database}")

    db_manager = DatabaseManager(db_config_manager)
    db_manager.current_db = database
    engine = ReportEngine(db_manager, load_config())
    register_configured_reports(engine)
    return engine


def _sheet_payload(df: pd.DataFrame, limit: int) -> Dict[str, Any]:
    if df.empty:
        return {
            "columns": list(df.columns) if len(df.columns) else ["Message"],
            "rows": [{"Message": "No data available for this report"}] if not len(df.columns) else [],
            "total_rows": 0,
            "truncated": False,
        }

    total_rows = len(df)
    preview = df.head(limit)
    rows = json.loads(preview.to_json(orient="records", date_format="iso", default_handler=str))
    return {
        "columns": [str(column) for column in preview.columns],
        "rows": rows,
        "total_rows": total_rows,
        "truncated": total_rows > limit,
    }


def preview_report_data(
    report_id: str,
    filters: Dict[str, str] | None = None,
    limit: int = 500,
    database: str | None = None,
    databases: List[str] | None = None,
) -> Dict[str, Any]:
    """Generate report data for dashboard preview without writing a file."""
    target_databases = resolve_databases_for_request(
        database, databases, get_report_category(report_id), report_id=report_id
    )
    results: Dict[str, Dict[str, Any]] = {}
    primary_sheets: Dict[str, Any] = {}

    for db_name in target_databases:
        engine = _build_report_engine(db_name)
        report = engine.get_report(report_id, db_name=db_name, report_id=report_id)

        if filters:
            report.apply_filters(filters)

        data = report.generate()
        sheet_names = report.get_sheet_names()
        sheets: Dict[str, Any] = {}

        for key, df in data.items():
            display_name = sheet_names.get(key, key)
            sheets[display_name] = _sheet_payload(df, limit)

        results[db_name] = sheets
        if not primary_sheets:
            primary_sheets = sheets

    primary_database = target_databases[0]
    return {
        "report_id": report_id,
        "database": primary_database if len(target_databases) == 1 else None,
        "databases": target_databases,
        "sheets": primary_sheets,
        "results": results,
    }
