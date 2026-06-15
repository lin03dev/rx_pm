"""
Report registry helpers backed by config/report_config.yaml.
"""

from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


DEFAULT_REPORT_CONFIG = {
    "categories": {
        "AG": {"display_name": "AG Reports"},
        "LMS": {"display_name": "LMS Reports"},
        "Language": {"display_name": "Language Survey Reports"},
        "Utility": {"display_name": "Utility Reports"},
    },
    "reports": {},
}


def load_report_config(config_file: str = "config/report_config.yaml") -> Dict[str, Any]:
    """Load report catalogue configuration."""
    config_path = Path(config_file)
    if not config_path.exists():
        return DEFAULT_REPORT_CONFIG.copy()

    with config_path.open("r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}

    config = DEFAULT_REPORT_CONFIG.copy()
    config.update(loaded)
    config.setdefault("categories", DEFAULT_REPORT_CONFIG["categories"])
    config.setdefault("reports", {})
    return config


def load_report_catalog(config_file: str = "config/report_config.yaml") -> Dict[str, Dict[str, Any]]:
    """Return configured reports keyed by report id."""
    return load_report_config(config_file).get("reports", {})


def import_report_class(report_id: str, report_info: Dict[str, Any]):
    """Import a configured report class."""
    module_path = report_info.get("module")
    class_name = report_info.get("class")
    if not module_path or not class_name:
        raise ValueError(f"Report '{report_id}' is missing module/class config")

    module = import_module(module_path)
    return getattr(module, class_name)


def register_configured_reports(report_engine, config_file: str = "config/report_config.yaml") -> List[str]:
    """Register all importable reports from the report catalogue."""
    registered = []
    for report_id, report_info in load_report_catalog(config_file).items():
        try:
            report_class = import_report_class(report_id, report_info)
            if report_class is not None:
                report_engine.register_report(report_id, report_class)
                registered.append(report_id)
        except (ImportError, AttributeError, ValueError):
            continue
    return registered


def list_configured_reports(config_file: str = "config/report_config.yaml") -> List[Dict[str, Any]]:
    """Return report metadata in display order."""
    reports = []
    for report_id, info in load_report_catalog(config_file).items():
        reports.append({
            "id": report_id,
            "name": info.get("display_name", report_id),
            "description": info.get("description", ""),
            "category": info.get("category", "Utility"),
            "available_filters": info.get("available_filters", []),
            "sheets": info.get("sheets", []),
        })
    return reports


def grouped_configured_reports(config_file: str = "config/report_config.yaml") -> List[Tuple[str, Dict[str, Any], List[Dict[str, Any]]]]:
    """Return reports grouped by configured category order."""
    config = load_report_config(config_file)
    categories = config.get("categories", {})
    reports = list_configured_reports(config_file)
    grouped = []

    for category_id, category_info in categories.items():
        category_reports = [report for report in reports if report["category"] == category_id]
        if category_reports:
            grouped.append((category_id, category_info, category_reports))

    known_categories = set(categories)
    uncategorized = [report for report in reports if report["category"] not in known_categories]
    if uncategorized:
        grouped.append(("Other", {"display_name": "Other Reports"}, uncategorized))

    return grouped
