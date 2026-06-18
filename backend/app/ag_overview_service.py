"""AG project overview dashboard — direct schema-bound queries."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager
from core.schema_guard import SchemaGuard, SchemaViolationError

_OVERVIEW_CACHE: Dict[Tuple[str, str, str, str, str], Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 120

_OVERVIEW_TABLES = (
    "projects",
    "countries",
    "languages",
    "dialects",
    "users",
    "users_to_projects",
)

_PROJECTS_QUERY = """
SELECT
    c.name AS country,
    l.name AS language,
    l."isoCode" AS language_iso_code,
    COALESCE(d.name, '') AS dialect,
    COALESCE(d."rolvCode", '') AS dialect_rolv_code,
    p.id AS project_id,
    p.name AS project_name,
    p."projectType" AS project_type,
    COALESCE(p.stage::text, '') AS project_stage,
    COUNT(DISTINCT utp."userId") AS assigned_users
FROM projects p
LEFT JOIN countries c ON p."countryId" = c.id
LEFT JOIN languages l ON p."languageId" = l.id
LEFT JOIN dialects d ON p."dialectId" = d.id
LEFT JOIN users_to_projects utp ON utp."projectId" = p.id
WHERE {where_clause}
GROUP BY
    c.name, l.name, l."isoCode", d.name, d."rolvCode",
    p.id, p.name, p."projectType", p.stage
ORDER BY c.name NULLS LAST, l.name NULLS LAST, p.name
"""

_ASSIGNMENTS_QUERY = """
SELECT
    c.name AS country,
    l.name AS language,
    l."isoCode" AS language_iso_code,
    COALESCE(d.name, '') AS dialect,
    p.id AS project_id,
    p.name AS project_name,
    p."projectType" AS project_type,
    COALESCE(p.stage::text, '') AS project_stage,
    u.id AS user_id,
    u.username AS autographa_id,
    COALESCE(NULLIF(u.name, ''), u.username) AS user_name,
    utp.role AS assignment_role
FROM users_to_projects utp
JOIN projects p ON utp."projectId" = p.id
LEFT JOIN countries c ON p."countryId" = c.id
LEFT JOIN languages l ON p."languageId" = l.id
LEFT JOIN dialects d ON p."dialectId" = d.id
JOIN users u ON u.id = utp."userId"
WHERE {where_clause}
ORDER BY c.name NULLS LAST, l.name NULLS LAST, p.name, u.username
"""

_DIMENSION_QUERIES = {
    "countries": """
        SELECT DISTINCT c.name AS name
        FROM countries c
        ORDER BY c.name
    """,
    "languages": """
        SELECT DISTINCT l.name AS name, l."isoCode" AS iso_code
        FROM languages l
        ORDER BY l.name
    """,
    "dialects": """
        SELECT DISTINCT d.name AS name, l.name AS language
        FROM dialects d
        LEFT JOIN languages l ON d."languageId" = l.id
        ORDER BY l.name, d.name
    """,
}


def _clean(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def _records(df: pd.DataFrame, limit: int) -> List[Dict[str, Any]]:
    if df.empty:
        return []
    rows = df.head(limit).to_dict(orient="records")
    return [{key: _clean(val) for key, val in row.items()} for row in rows]


def _build_filters(
    country: Optional[str],
    language: Optional[str],
    project_type: Optional[str],
    dialect: Optional[str],
) -> Tuple[str, Dict[str, Any]]:
    clauses = ["1=1"]
    params: Dict[str, Any] = {}

    if country:
        clauses.append("c.name = %(country)s")
        params["country"] = country
    if language:
        clauses.append("l.name = %(language)s")
        params["language"] = language
    if project_type:
        clauses.append('p."projectType" = %(project_type)s')
        params["project_type"] = project_type
    if dialect:
        clauses.append("d.name = %(dialect)s")
        params["dialect"] = dialect

    return " AND ".join(clauses), params


def get_ag_overview(
    database: str,
    *,
    country: Optional[str] = None,
    language: Optional[str] = None,
    project_type: Optional[str] = None,
    dialect: Optional[str] = None,
    limit: int = 1000,
    refresh: bool = False,
) -> Dict[str, Any]:
    """Return AG overview dashboard data for the selected database."""
    manager = DatabaseConfigManager()
    if database not in manager.list_databases():
        raise ValueError(f"Unknown database: {database}")

    system = SchemaGuard(DatabaseManager(manager), database).system
    if system != "AG":
        raise ValueError(f"AG overview requires an AG database connection (got {system or database})")

    cache_key = (database, country or "", language or "", project_type or "", dialect or "")
    now = time.time()
    if not refresh:
        cached = _OVERVIEW_CACHE.get(cache_key)
        if cached and now - cached[0] < CACHE_TTL_SECONDS:
            payload = dict(cached[1])
            payload["cached"] = True
            return payload

    db_manager = DatabaseManager(manager)
    guard = SchemaGuard(db_manager, database, report_id="user-assignments")
    guard.validate_primary_connection()
    guard.require_tables(*_OVERVIEW_TABLES)

    where_clause, params = _build_filters(country, language, project_type, dialect)

    projects_df = guard.query(
        _PROJECTS_QUERY.format(where_clause=where_clause),
        _OVERVIEW_TABLES,
        params=params,
    )
    assignments_df = guard.query(
        _ASSIGNMENTS_QUERY.format(where_clause=where_clause),
        _OVERVIEW_TABLES,
        params=params,
    )

    countries_df = guard.query(_DIMENSION_QUERIES["countries"], ("countries",))
    languages_df = guard.query(_DIMENSION_QUERIES["languages"], ("languages",))
    dialects_df = guard.query(_DIMENSION_QUERIES["dialects"], ("dialects", "languages"))

    summary = {
        "countries": int(countries_df["name"].nunique()) if not countries_df.empty else 0,
        "languages": int(languages_df["name"].nunique()) if not languages_df.empty else 0,
        "dialects": int(dialects_df["name"].nunique()) if not dialects_df.empty else 0,
        "projects": int(len(projects_df)),
        "assignments": int(len(assignments_df)),
        "users_assigned": int(assignments_df["user_id"].nunique()) if not assignments_df.empty else 0,
        "assigned_users_total": int(projects_df["assigned_users"].sum()) if not projects_df.empty else 0,
    }

    filter_options = {
        "countries": countries_df["name"].dropna().tolist() if not countries_df.empty else [],
        "languages": languages_df["name"].dropna().tolist() if not languages_df.empty else [],
        "project_types": sorted(
            projects_df["project_type"].dropna().unique().tolist()
        ) if not projects_df.empty else [],
        "dialects": dialects_df["name"].dropna().tolist() if not dialects_df.empty else [],
    }

    payload = {
        "database": database,
        "summary": summary,
        "projects": _records(projects_df, limit),
        "assignments": _records(assignments_df, limit),
        "filter_options": filter_options,
        "filters_applied": {
            "country": country,
            "language": language,
            "project_type": project_type,
            "dialect": dialect,
        },
        "limits": {
            "projects": min(limit, len(projects_df)),
            "assignments": min(limit, len(assignments_df)),
            "projects_total": len(projects_df),
            "assignments_total": len(assignments_df),
        },
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cached": False,
    }

    _OVERVIEW_CACHE[cache_key] = (now, payload)
    return payload
