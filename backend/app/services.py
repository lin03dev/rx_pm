"""Application services that wrap the existing reporting engine."""

from pathlib import Path
from typing import Dict, List

from config.database_config import DatabaseConfigManager
from config.output_config import get_output_config
from config.report_registry import list_configured_reports, register_configured_reports
from core.database_manager import DatabaseManager
from core.report_engine import ReportEngine
from run import load_config


def list_reports() -> List[Dict]:
    """Return configured report metadata."""
    return list_configured_reports()


def list_databases() -> List[Dict]:
    """Return configured database metadata plus output path mapping."""
    db_config_manager = DatabaseConfigManager()
    output_config = get_output_config()
    databases = []

    for db_name in db_config_manager.list_databases():
        db_config = db_config_manager.get_config(db_name)
        databases.append({
            "name": db_name,
            "project": db_config.project,
            "environment": db_config.environment,
            "host": db_config.host,
            "category": output_config.get_database_category(db_name),
            "output_path": output_config.get_output_path(db_name),
        })

    return databases


def generate_report(report_id: str, database: str, output_format: str, filters: Dict[str, str] | None = None) -> str:
    """Generate a configured report and return its output path."""
    db_config_manager = DatabaseConfigManager()
    if database not in db_config_manager.list_databases():
        raise ValueError(f"Unknown database: {database}")

    db_manager = DatabaseManager(db_config_manager)
    db_manager.current_db = database
    engine = ReportEngine(db_manager, load_config())
    register_configured_reports(engine)

    output_file = engine.generate_report(
        report_name=report_id,
        output_format=output_format,
        filters=filters or {},
        db_name=database,
    )
    return str(Path(output_file))
