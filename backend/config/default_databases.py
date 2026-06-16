"""Load default database definitions from config/default_databases.yaml."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qs, urlparse

import yaml

CONFIG_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASES_FILE = CONFIG_DIR / "default_databases.yaml"


def parse_connection_string(connection_string: str) -> Dict[str, Any]:
    parsed = urlparse(connection_string)
    query = parse_qs(parsed.query)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "database": (parsed.path or "/").lstrip("/") or parsed.hostname,
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "ssl_mode": (query.get("sslmode") or [None])[0],
    }


def load_default_database_definitions(config_file: str | Path = DEFAULT_DATABASES_FILE) -> List[Dict[str, Any]]:
    config_path = Path(config_file)
    if not config_path.exists():
        return []

    with config_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}

    definitions = payload.get("databases", [])
    resolved: List[Dict[str, Any]] = []

    for item in definitions:
        if not isinstance(item, dict) or not item.get("enabled", True):
            continue

        source_config = item.get("source_config") or {}
        connection_string = source_config.get("connection_string")
        env_key = source_config.get("connection_string_env")
        if env_key:
            connection_string = os.getenv(env_key, connection_string)

        if not connection_string:
            continue

        parsed = parse_connection_string(connection_string)
        name = item["name"]
        project = item.get("project") or name
        category = item.get("category") or project

        resolved.append({
            "name": name,
            "host": parsed["host"],
            "port": parsed["port"],
            "database": parsed["database"],
            "user": parsed["user"],
            "password": parsed["password"],
            "ssl_mode": parsed.get("ssl_mode") or "require",
            "description": item.get("description") or f"{name} production database",
            "environment": item.get("environment", "production"),
            "project": project,
            "category": category,
            "target_db": item.get("target_db"),
            "source_dump": item.get("source_dump"),
            "pg_dump_path": source_config.get("pg_dump_path"),
        })

    return resolved
