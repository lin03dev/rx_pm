"""
Dashboard insight configuration and resolution helpers.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_DASHBOARD_CONFIG = CONFIG_DIR / "dashboard_config.yaml"
CACHE_TTL_SECONDS = 300

_insights_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, Any]]] = {}


def load_dashboard_config(config_file: str | Path = DEFAULT_DASHBOARD_CONFIG) -> Dict[str, List[Dict[str, Any]]]:
    config_path = Path(config_file)
    if not config_path.exists():
        return {}

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}

    return {key: value for key, value in loaded.items() if isinstance(value, list)}


def get_project_insights(project: str, config_file: str | Path = DEFAULT_DASHBOARD_CONFIG) -> List[Dict[str, Any]]:
    return load_dashboard_config(config_file).get(project, [])


def list_dashboard_projects(config_file: str | Path = DEFAULT_DASHBOARD_CONFIG) -> List[str]:
    return list(load_dashboard_config(config_file).keys())


def invalidate_insights_cache(project: Optional[str] = None, database: Optional[str] = None) -> None:
    if project is None and database is None:
        _insights_cache.clear()
        return

    keys_to_remove = [
        key
        for key in _insights_cache
        if (project is None or key[0] == project) and (database is None or key[1] == database)
    ]
    for key in keys_to_remove:
        _insights_cache.pop(key, None)
