"""Database connection management for the API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import psycopg2

from config.connections_store import (
    delete_user_connection,
    is_user_connection,
    load_active_database_names,
    load_primary_database,
    load_selected_by_project,
    prune_selected_by_project,
    save_active_database_names,
    save_primary_database,
    save_project_database_selection,
    upsert_user_connection,
)
from config.database_config import DatabaseConfig, DatabaseConfigManager, DatabaseType
from config.output_config import get_output_config
from config.schema_registry import get_report_project_binding


def _connection_payload(config: DatabaseConfig, active_names: List[str]) -> Dict[str, Any]:
    output_config = get_output_config()
    category = output_config.get_database_category(config.name) or config.project
    return {
        "name": config.name,
        "project": config.project,
        "environment": config.environment,
        "host": config.host,
        "port": config.port,
        "database": config.database,
        "user": config.user,
        "category": category,
        "output_path": output_config.get_output_path(config.name),
        "description": config.description,
        "ssl_mode": config.ssl_mode,
        "active": config.name in active_names,
        "is_custom": is_user_connection(config.name),
        "is_builtin": not is_user_connection(config.name),
    }


def list_database_connections() -> Dict[str, Any]:
    manager = DatabaseConfigManager()
    all_names = manager.list_databases()
    active_names = load_active_database_names(all_names)
    if not active_names:
        active_names = all_names
        save_active_database_names(active_names)

    primary = load_primary_database(active_names[0] if active_names else None)
    selected_by_project = prune_selected_by_project(active_names)
    databases = [_connection_payload(manager.get_config(name), active_names) for name in all_names if manager.get_config(name)]

    return {
        "databases": databases,
        "active": active_names,
        "primary": primary,
        "selected_by_project": selected_by_project,
    }


def set_active_databases(active: List[str], primary: Optional[str] = None) -> Dict[str, Any]:
    manager = DatabaseConfigManager()
    known = set(manager.list_databases())
    cleaned = [name for name in active if name in known]
    if not cleaned:
        raise ValueError("At least one valid database must remain active")

    saved_active = save_active_database_names(cleaned)
    saved_primary = primary if primary in saved_active else saved_active[0]
    save_primary_database(saved_primary)
    selected_by_project = prune_selected_by_project(saved_active)
    return {"active": saved_active, "primary": saved_primary, "selected_by_project": selected_by_project}


def set_project_database_selection(project: str, database: str) -> Dict[str, Any]:
    manager = DatabaseConfigManager()
    known = set(manager.list_databases())
    if database not in known:
        raise ValueError(f"Unknown database: {database}")

    active_names = [name for name in load_active_database_names(manager.list_databases()) if name in known]
    if database not in active_names:
        raise ValueError(f"Database '{database}' is not active")

    output_config = get_output_config()
    category = output_config.get_database_category(database) or manager.get_config(database).project
    if category != project:
        raise ValueError(f"Database '{database}' does not belong to project '{project}'")

    selected_by_project = save_project_database_selection(project, database)
    return {
        "project": project,
        "database": database,
        "selected_by_project": selected_by_project,
    }


def test_database_connection(payload: Dict[str, Any]) -> Dict[str, Any]:
    config = DatabaseConfig(
        name=payload.get("name") or "test",
        db_type=DatabaseType.POSTGRESQL,
        host=str(payload["host"]),
        port=int(payload.get("port", 5432)),
        database=str(payload["database"]),
        user=str(payload["user"]),
        password=str(payload.get("password", "")),
        ssl_mode=payload.get("ssl_mode"),
    )
    connect_kwargs = config.get_connection_params()
    conn = psycopg2.connect(**connect_kwargs)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.fetchone()
    cursor.close()
    conn.close()
    return {"status": "ok", "message": "Connection successful"}


def create_database_connection(payload: Dict[str, Any]) -> Dict[str, Any]:
    name = payload["name"].strip()
    if not name:
        raise ValueError("Connection name is required")

    manager = DatabaseConfigManager()
    if name in manager.list_databases() and not is_user_connection(name):
        raise ValueError(f"Built-in connection '{name}' already exists")

    test_database_connection(payload)
    upsert_user_connection(name, _persistable_payload(payload))
    manager.reload()

    active_names = load_active_database_names(manager.list_databases())
    if payload.get("active", True) and name not in active_names:
        active_names.append(name)
        save_active_database_names(active_names)

    return _connection_payload(manager.get_config(name), active_names)


def update_database_connection(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    manager = DatabaseConfigManager()
    existing = manager.get_config(name)
    if not existing:
        raise ValueError(f"Unknown database: {name}")
    if not is_user_connection(name):
        raise ValueError(f"Built-in connection '{name}' cannot be edited")

    merged = {
        "name": name,
        "host": payload.get("host", existing.host),
        "port": payload.get("port", existing.port),
        "database": payload.get("database", existing.database),
        "user": payload.get("user", existing.user),
        "password": payload.get("password") or existing.password,
        "ssl_mode": payload.get("ssl_mode", existing.ssl_mode),
        "description": payload.get("description", existing.description),
        "environment": payload.get("environment", existing.environment),
        "project": payload.get("project", existing.project),
        "category": payload.get("category", payload.get("project", existing.project)),
    }
    test_database_connection(merged)
    upsert_user_connection(name, _persistable_payload(merged))
    manager.reload()
    active_names = load_active_database_names(manager.list_databases())
    return _connection_payload(manager.get_config(name), active_names)


def delete_database_connection(name: str) -> Dict[str, Any]:
    if not is_user_connection(name):
        raise ValueError(f"Built-in connection '{name}' cannot be deleted")

    if not delete_user_connection(name):
        raise ValueError(f"Unknown custom connection: {name}")

    DatabaseConfigManager().reload()
    active_names = load_active_database_names(DatabaseConfigManager().list_databases())
    active_names = [item for item in active_names if item != name]
    if not active_names:
        active_names = DatabaseConfigManager().list_databases()[:1]
    save_active_database_names(active_names)
    primary = load_primary_database(active_names[0] if active_names else None)
    if primary == name:
        save_primary_database(active_names[0] if active_names else None)
    return {"deleted": name, "active": active_names}


def resolve_databases_for_request(
    database: Optional[str],
    databases: Optional[List[str]],
    report_category: Optional[str] = None,
    report_id: Optional[str] = None,
) -> List[str]:
    manager = DatabaseConfigManager()
    known = set(manager.list_databases())
    active_names = [name for name in load_active_database_names(manager.list_databases()) if name in known]
    if not active_names:
        active_names = manager.list_databases()

    if databases:
        selected = [name for name in databases if name in known]
        if not selected:
            raise ValueError("No valid databases were provided")
        return selected

    if database:
        if database not in known:
            raise ValueError(f"Unknown database: {database}")
        return [database]

    if report_id:
        bound_project = get_report_project_binding(report_id)
        if bound_project:
            scoped = [
                name for name in active_names
                if manager.get_config(name) and manager.get_config(name).project == bound_project
            ]
            if scoped:
                return scoped

    if report_category:
        output_config = get_output_config()
        scoped = [
            name for name in active_names
            if output_config.get_database_category(name) == report_category or manager.get_config(name).project == report_category
        ]
        if scoped:
            return scoped

    return active_names[:1]


def _persistable_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "host": str(payload["host"]),
        "port": int(payload.get("port", 5432)),
        "database": str(payload["database"]),
        "user": str(payload["user"]),
        "password": str(payload.get("password", "")),
        "ssl_mode": payload.get("ssl_mode"),
        "description": payload.get("description"),
        "environment": payload.get("environment", "production"),
        "project": payload.get("project") or payload.get("category"),
        "category": payload.get("category") or payload.get("project"),
    }
