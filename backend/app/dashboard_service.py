"""Dashboard insight resolution service."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from config.dashboard_insights import (
    CACHE_TTL_SECONDS,
    _insights_cache,
    get_project_insights,
    invalidate_insights_cache,
)
from .services import preview_report_data


def _format_insight_value(value: Any, fmt: str) -> str:
    if value is None:
        return "—"

    text = str(value).strip()
    if not text:
        return "—"

    if fmt == "number":
        normalized = text.replace(",", "").replace("%", "")
        try:
            number = float(normalized)
            if number.is_integer():
                return f"{int(number):,}"
            return f"{number:,.1f}"
        except ValueError:
            return text

    return text


def _sheet_lookup(sheets: Dict[str, Any], sheet_name: str) -> Optional[Dict[str, Any]]:
    if sheet_name in sheets:
        return sheets[sheet_name]

    normalized = sheet_name.strip().lower()
    for name, payload in sheets.items():
        if name.strip().lower() == normalized:
            return payload
    return None


def _resolve_source(source: Dict[str, Any], sheets: Dict[str, Any]) -> Any:
    sheet = _sheet_lookup(sheets, source["sheet"])
    if not sheet:
        raise ValueError(f"Sheet not found: {source['sheet']}")

    source_type = source.get("type", "report_metric")

    if source_type == "report_row_count":
        return sheet.get("total_rows", len(sheet.get("rows", [])))

    metric_column = source.get("metric_column", "Metric")
    value_column = source.get("value_column", "Value")
    target_metric = source.get("metric")

    for row in sheet.get("rows", []):
        if str(row.get(metric_column, "")).strip() == target_metric:
            return row.get(value_column)

    raise ValueError(f"Metric not found: {target_metric}")


def get_dashboard_insights(project: str, database: str, refresh: bool = False) -> Dict[str, Any]:
    """Resolve configured dashboard insights for a project/database pair."""
    cache_key = (project, database)
    now = time.time()

    if refresh:
        invalidate_insights_cache(project, database)

    cached = _insights_cache.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL_SECONDS:
        return cached[1]

    definitions = get_project_insights(project)
    report_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    metrics: List[Dict[str, Any]] = []

    for definition in definitions:
        source = definition.get("source", {})
        report_id = source.get("report_id")
        filters = source.get("filters") or {}
        filters_key = json.dumps(filters, sort_keys=True)
        report_key = (report_id, filters_key)

        metric_payload = {
            "id": definition.get("id") or f"{project}-metric-{len(metrics)}",
            "label": definition.get("label"),
            "description": definition.get("description", ""),
            "format": definition.get("format", "text"),
            "navigate": definition.get("navigate", {}),
            "source_report_id": report_id,
            "status": "ok",
            "value": None,
            "display_value": "—",
            "error": None,
        }

        if not report_id:
            metric_payload["status"] = "error"
            metric_payload["error"] = "Insight is missing report_id"
            metrics.append(metric_payload)
            continue

        try:
            if report_key not in report_cache:
                preview = preview_report_data(
                    report_id=report_id,
                    database=database,
                    filters=filters,
                    limit=500,
                )
                report_cache[report_key] = preview.get("sheets", {})

            raw_value = _resolve_source(source, report_cache[report_key])
            metric_payload["value"] = raw_value
            metric_payload["display_value"] = _format_insight_value(raw_value, metric_payload["format"])
        except Exception as exc:
            metric_payload["status"] = "error"
            metric_payload["error"] = str(exc)

        metrics.append(metric_payload)

    payload = {
        "project": project,
        "database": database,
        "metrics": metrics,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cached": False,
    }

    _insights_cache[cache_key] = (now, payload)
    return payload
