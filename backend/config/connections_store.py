"""
Persistent storage for user-defined database connections and active selection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
USER_CONNECTIONS_FILE = CONFIG_DIR / "user_connections.yaml"
ACTIVE_DATABASES_FILE = CONFIG_DIR / "active_databases.yaml"


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _write_yaml(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, default_flow_style=False, sort_keys=False)


def load_user_connections() -> Dict[str, Dict[str, Any]]:
    data = _read_yaml(USER_CONNECTIONS_FILE)
    connections = data.get("connections", {})
    return {name: info for name, info in connections.items() if isinstance(info, dict)}


def save_user_connections(connections: Dict[str, Dict[str, Any]]) -> None:
    _write_yaml(USER_CONNECTIONS_FILE, {"connections": connections})


def upsert_user_connection(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    connections = load_user_connections()
    connections[name] = payload
    save_user_connections(connections)
    return payload


def delete_user_connection(name: str) -> bool:
    connections = load_user_connections()
    if name not in connections:
        return False
    del connections[name]
    save_user_connections(connections)
    return True


def is_user_connection(name: str) -> bool:
    return name in load_user_connections()


def load_active_database_names(default_names: Optional[List[str]] = None) -> List[str]:
    data = _read_yaml(ACTIVE_DATABASES_FILE)
    active = data.get("active")
    if isinstance(active, list) and active:
        return [str(item) for item in active]

    default_list = list(default_names or [])
    preferred = ["LMS", "AG", "Telios"]
    preferred_active = [name for name in preferred if name in default_list]
    if preferred_active:
        return preferred_active

    return default_list


def save_active_database_names(active: List[str]) -> List[str]:
    cleaned = []
    seen = set()
    for name in active:
        if name and name not in seen:
            cleaned.append(name)
            seen.add(name)
    _write_yaml(ACTIVE_DATABASES_FILE, {"active": cleaned})
    return cleaned


def load_primary_database(default_name: Optional[str] = None) -> Optional[str]:
    data = _read_yaml(ACTIVE_DATABASES_FILE)
    primary = data.get("primary")
    return str(primary) if primary else default_name


def load_selected_by_project() -> Dict[str, str]:
    data = _read_yaml(ACTIVE_DATABASES_FILE)
    raw = data.get("selected_by_project") or {}
    if not isinstance(raw, dict):
        return {}
    return {str(project): str(database) for project, database in raw.items() if project and database}


def save_selected_by_project(selected: Dict[str, str]) -> Dict[str, str]:
    data = _read_yaml(ACTIVE_DATABASES_FILE)
    cleaned: Dict[str, str] = {}
    for project, database in selected.items():
        if project and database:
            cleaned[str(project)] = str(database)
    data["selected_by_project"] = cleaned
    _write_yaml(ACTIVE_DATABASES_FILE, data)
    return cleaned


def save_project_database_selection(project: str, database: str) -> Dict[str, str]:
    selected = load_selected_by_project()
    selected[str(project)] = str(database)
    return save_selected_by_project(selected)


def prune_selected_by_project(active_names: List[str]) -> Dict[str, str]:
    active_set = set(active_names)
    selected = {project: db for project, db in load_selected_by_project().items() if db in active_set}
    return save_selected_by_project(selected)


def save_primary_database(name: Optional[str]) -> None:
    data = _read_yaml(ACTIVE_DATABASES_FILE)
    if name:
        data["primary"] = name
    elif "primary" in data:
        del data["primary"]
    _write_yaml(ACTIVE_DATABASES_FILE, data)
