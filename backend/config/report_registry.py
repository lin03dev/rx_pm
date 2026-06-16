"""
Report registry — loads catalogue exclusively from schema_registry.yaml via report_schema.
"""

from importlib import import_module
from typing import Any, Dict, List, Tuple

from config.report_schema import (
    grouped_configured_reports as _grouped_configured_reports,
    list_configured_reports as _list_configured_reports,
    load_report_catalog as _load_report_catalog,
    template_exists,
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


def load_report_catalog() -> Dict[str, Dict[str, Any]]:
    """Return configured reports keyed by report id."""
    return _load_report_catalog()


def import_report_class(report_id: str, report_info: Dict[str, Any]):
    """Import a configured report class."""
    module_path = report_info.get("module")
    class_name = report_info.get("class")
    if not module_path or not class_name:
        raise ValueError(f"Report '{report_id}' is missing module/class config")

    module = import_module(module_path)
    return getattr(module, class_name)


def register_configured_reports(report_engine) -> List[str]:
    """Register all importable reports from the schema catalogue."""
    registered = []
    for report_id, report_info in load_report_catalog().items():
        try:
            report_class = import_report_class(report_id, report_info)
            if report_class is not None:
                report_engine.register_report(report_id, report_class)
                registered.append(report_id)
        except (ImportError, AttributeError, ValueError) as exc:
            logger.warning("Skipping report '%s': %s", report_id, exc)
            continue
    return registered


def list_configured_reports() -> List[Dict[str, Any]]:
    """Return report metadata in display order."""
    return _list_configured_reports()


def grouped_configured_reports() -> List[Tuple[str, Dict[str, Any], List[Dict[str, Any]]]]:
    """Return reports grouped by configured category order."""
    return _grouped_configured_reports()
