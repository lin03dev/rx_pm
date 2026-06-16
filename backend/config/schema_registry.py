"""Load schema metadata and report-to-database bindings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
REGISTRY_FILE = CONFIG_DIR / "schema_registry.yaml"


@lru_cache(maxsize=1)
def load_schema_registry(config_file: str | Path = REGISTRY_FILE) -> Dict[str, Any]:
    path = Path(config_file)
    if not path.exists():
        return {"systems": {}, "cross_db_reports": {}, "report_definitions": {}}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def get_system_for_connection(connection_name: str) -> Optional[str]:
    registry = load_schema_registry()
    for system, info in registry.get("systems", {}).items():
        names = {name.lower() for name in info.get("connection_names", [])}
        if connection_name.lower() in names:
            return system
    return None


def get_companion_connection(primary_connection: str, target_system: str) -> Optional[str]:
    registry = load_schema_registry()
    system_info = registry.get("systems", {}).get(target_system, {})
    candidates = system_info.get("connection_names", [])
    if not candidates:
        return None

    primary_lower = primary_connection.lower()
    dev_mode = "dev" in primary_lower
    ordered = sorted(
        candidates,
        key=lambda name: (0 if ("dev" in name.lower()) == dev_mode else 1, name.lower()),
    )
    return ordered[0] if ordered else None


def get_cross_db_report_config(report_id: str) -> Dict[str, Any]:
    return load_schema_registry().get("cross_db_reports", {}).get(report_id, {})


def get_report_project_binding(report_id: str) -> Optional[str]:
    from config.report_schema import get_report_db_binding

    return get_report_db_binding(report_id)


def is_cross_db_enrichment_allowed(report_id: str, target_system: str) -> bool:
    cross_db = get_cross_db_report_config(report_id)
    if not cross_db:
        return False
    return any(item.get("system") == target_system for item in cross_db.get("enrichments", []))


def list_system_tables(system: str) -> Dict[str, Any]:
    return load_schema_registry().get("systems", {}).get(system, {}).get("tables", {})


def get_report_definition(report_id: str) -> Optional[Dict[str, Any]]:
    from config.report_schema import get_report_definition as _get_report_definition

    return _get_report_definition(report_id)
