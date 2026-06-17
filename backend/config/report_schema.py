"""
Schema-based report catalogue — single source of truth from schema_registry.yaml.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config.schema_registry import load_schema_registry

OUTPUT_DEFAULTS: Dict[str, Any] = {
    "header": {"fill": "1B4F72", "font_color": "FFFFFF", "bold": True},
    "body": {"wrap_text": True},
    "freeze_header": True,
    "auto_width": True,
    "max_column_width": 50,
}

DEFAULT_REPORT_CATEGORIES: Dict[str, Dict[str, str]] = {
    "AG": {"display_name": "AG Reports"},
    "LMS": {"display_name": "LMS Reports"},
    "Telios": {"display_name": "Telios Reports"},
    "Language": {"display_name": "Language Survey Reports"},
    "Utility": {"display_name": "Utility Reports"},
}

CATEGORY_DB_BINDING: Dict[str, str] = {
    "AG": "AG",
    "LMS": "LMS",
    "Telios": "Telios",
    "Language": "Telios",
    "Utility": "Utility",
}


def get_report_definitions() -> Dict[str, Any]:
    return load_schema_registry().get("report_definitions") or {}


def get_report_categories() -> Dict[str, Any]:
    registry = load_schema_registry()
    categories = registry.get("report_categories") or {}
    merged = {key: dict(value) for key, value in DEFAULT_REPORT_CATEGORIES.items()}
    merged.update(categories)
    return merged


def get_column_groups() -> Dict[str, List[Dict[str, Any]]]:
    groups = load_schema_registry().get("report_column_groups") or {}
    return {
        str(group_id): list(columns or [])
        for group_id, columns in groups.items()
    }


def get_report_definition(report_id: str) -> Optional[Dict[str, Any]]:
    definition = get_report_definitions().get(report_id)
    if not definition:
        return None
    return {"id": report_id, **definition}


def load_report_catalog() -> Dict[str, Dict[str, Any]]:
    """Build API/CLI catalogue from schema report_definitions."""
    catalog: Dict[str, Dict[str, Any]] = {}
    for report_id, definition in get_report_definitions().items():
        module_path = definition.get("module")
        class_name = definition.get("class")
        if not module_path or not class_name:
            continue

        sheets = (definition.get("output") or {}).get("sheets") or {}
        sheet_display_names = [
            str(sheet.get("display_name") or key.replace("_", " ").title())
            for key, sheet in sheets.items()
        ]
        catalog[report_id] = {
            "display_name": definition.get("display_name", report_id),
            "description": definition.get("description", ""),
            "category": definition.get("category", "Utility"),
            "standard": bool(definition.get("standard", False)),
            "template_id": definition.get("template_id", report_id),
            "module": module_path,
            "class": class_name,
            "available_filters": list(definition.get("filters") or []),
            "sheets": sheet_display_names,
        }
    return catalog


def get_report_db_binding(report_id: str) -> Optional[str]:
    definition = get_report_definition(report_id)
    if not definition:
        return None
    category = definition.get("category")
    if category:
        return CATEGORY_DB_BINDING.get(category)
    sources = definition.get("sources") or {}
    return sources.get("primary")


def get_available_filters(report_id: str) -> List[str]:
    definition = get_report_definition(report_id)
    if not definition:
        return []
    return list(definition.get("filters") or [])


def get_sheet_names(report_id: str) -> Dict[str, str]:
    definition = get_report_definition(report_id)
    if not definition:
        return {}
    sheets = (definition.get("output") or {}).get("sheets") or {}
    return {
        key: str(sheet.get("display_name") or key.replace("_", " ").title())
        for key, sheet in sheets.items()
    }


def list_report_definitions() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for report_id, info in get_report_definitions().items():
        sheets = (info.get("output") or {}).get("sheets") or {}
        items.append({
            "id": report_id,
            "version": info.get("version", "1.0"),
            "category": info.get("category", ""),
            "description": info.get("description", ""),
            "sheet_count": len(sheets),
            "sheet_keys": list(sheets.keys()),
            "filters": info.get("filters") or [],
        })
    return sorted(items, key=lambda item: (item["category"], item["id"]))


def definition_exists(report_id: str) -> bool:
    return report_id in get_report_definitions()


def resolve_template_id(report_id: str) -> str:
    definition = get_report_definition(report_id)
    if definition and definition.get("template_id"):
        return str(definition["template_id"])
    return report_id


def get_report_template(report_id: str) -> Optional[Dict[str, Any]]:
    return build_output_template(resolve_template_id(report_id))


def get_sheet_template(report_id: str, sheet_key: str) -> Optional[Dict[str, Any]]:
    template_id = resolve_template_id(report_id)
    sheet = get_sheet_definition(template_id, sheet_key)
    if not sheet:
        return None
    built = build_output_template(template_id)
    if not built:
        return None
    return (built.get("sheets") or {}).get(sheet_key)


def list_report_templates() -> List[Dict[str, Any]]:
    return list_report_definitions()


def template_exists(report_id: str) -> bool:
    return definition_exists(resolve_template_id(report_id))


def get_sheet_definition(report_id: str, sheet_key: str) -> Optional[Dict[str, Any]]:
    definition = get_report_definition(report_id)
    if not definition:
        return None
    return ((definition.get("output") or {}).get("sheets") or {}).get(sheet_key)


def resolve_sheet_columns(sheet: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expand shared column groups plus local columns into one ordered list."""
    groups = get_column_groups()
    columns: List[Dict[str, Any]] = []

    for group_id in sheet.get("column_groups") or []:
        for col in groups.get(str(group_id), []):
            columns.append(dict(col))

    for col in sheet.get("columns") or []:
        group_id = col.get("group") if isinstance(col, dict) else None
        if group_id:
            columns.extend(dict(group_col) for group_col in groups.get(str(group_id), []))
            continue
        columns.append(dict(col))
    return columns


def get_sheet_column_labels(report_id: str, sheet_key: str) -> List[str]:
    sheet = get_sheet_definition(report_id, sheet_key)
    if not sheet:
        return []
    return [
        str(col.get("label"))
        for col in resolve_sheet_columns(sheet)
        if col.get("label")
    ]


def order_dataframe_columns(report_id: str, sheet_key: str, df: pd.DataFrame) -> pd.DataFrame:
    labels = get_sheet_column_labels(report_id, sheet_key)
    if not labels:
        return df
    ordered = [label for label in labels if label in df.columns]
    remaining = [name for name in df.columns if name not in ordered]
    if not ordered:
        return df
    return df[ordered + remaining]


def build_output_template(report_id: str) -> Optional[Dict[str, Any]]:
    """Convert a schema report_definition into excel-writer template format."""
    definition = get_report_definition(report_id)
    if not definition:
        return None

    output = definition.get("output") or {}
    defaults = {**OUTPUT_DEFAULTS, **(output.get("defaults") or {})}
    sheets: Dict[str, Any] = {}

    for sheet_key, sheet_def in (output.get("sheets") or {}).items():
        sheet_template: Dict[str, Any] = {
            key: value
            for key, value in sheet_def.items()
            if key not in {"columns", "column_groups"}
        }
        columns: List[Dict[str, Any]] = []
        for col in resolve_sheet_columns(sheet_def):
            entry = {"name": col.get("label") or col.get("key")}
            if col.get("width") is not None:
                entry["width"] = col["width"]
            if col.get("align"):
                entry["align"] = col["align"]
            columns.append(entry)
        if columns:
            sheet_template["columns"] = columns
        sheets[sheet_key] = sheet_template

    return {
        "id": report_id,
        "defaults": defaults,
        "version": definition.get("version", "1.0"),
        "category": definition.get("category", ""),
        "description": definition.get("description", ""),
        "filename_prefix": definition.get("filename_prefix"),
        "sheets": sheets,
    }


def _schema_has_column(system: str, table: str, column: str) -> bool:
    registry = load_schema_registry()
    tables = registry.get("systems", {}).get(system, {}).get("tables", {})
    table_info = tables.get(table)
    if not table_info:
        return False
    columns = {name.lower() for name in table_info.get("columns", [])}
    return column.lower() in columns


def validate_schema_refs(report_id: str) -> List[str]:
    """Return validation errors for schema_ref entries in a report definition."""
    definition = get_report_definition(report_id)
    if not definition:
        return [f"Report definition not found: {report_id}"]

    errors: List[str] = []
    binding = get_report_db_binding(report_id)
    sources = definition.get("sources") or {}
    primary = sources.get("primary") or binding

    for table_name in sources.get("tables") or []:
        if primary:
            tables = load_schema_registry().get("systems", {}).get(primary, {}).get("tables", {})
            if table_name not in tables:
                errors.append(f"{report_id}: source table '{table_name}' not in {primary} schema")

    output = definition.get("output") or {}
    for sheet_key, sheet_def in (output.get("sheets") or {}).items():
        for group_id in sheet_def.get("column_groups") or []:
            if str(group_id) not in get_column_groups():
                errors.append(f"{report_id}.{sheet_key}: unknown column group '{group_id}'")
        for col in sheet_def.get("columns") or []:
            group_id = col.get("group") if isinstance(col, dict) else None
            if group_id and str(group_id) not in get_column_groups():
                errors.append(f"{report_id}.{sheet_key}: unknown inline column group '{group_id}'")

        for col in resolve_sheet_columns(sheet_def):
            label = col.get("label") or col.get("key") or "?"
            schema_ref = col.get("schema_ref") or {}
            system = schema_ref.get("system")
            table = schema_ref.get("table")
            if not system or not table:
                continue
            if schema_ref.get("columns"):
                for sub_col in schema_ref["columns"]:
                    if not _schema_has_column(system, table, sub_col):
                        errors.append(
                            f"{report_id}.{sheet_key}.{label}: "
                            f"missing {system}.{table}.{sub_col}"
                        )
            elif schema_ref.get("column"):
                if not _schema_has_column(system, table, schema_ref["column"]):
                    errors.append(
                        f"{report_id}.{sheet_key}.{label}: "
                        f"missing {system}.{table}.{schema_ref['column']}"
                    )
            for fallback in col.get("fallbacks") or []:
                fb_system = fallback.get("system")
                fb_table = fallback.get("table")
                fb_column = fallback.get("column")
                if fb_system and fb_table and fb_column and not _schema_has_column(fb_system, fb_table, fb_column):
                    errors.append(
                        f"{report_id}.{sheet_key}.{label} fallback: "
                        f"missing {fb_system}.{fb_table}.{fb_column}"
                    )
    return errors


def validate_report_output(report_id: str, report_data: Dict[str, pd.DataFrame]) -> List[str]:
    """Validate generated report DataFrames against schema column definitions."""
    definition = get_report_definition(report_id)
    if not definition:
        return []

    errors: List[str] = []
    sheets = (definition.get("output") or {}).get("sheets") or {}

    for sheet_key, sheet_def in sheets.items():
        if sheet_key not in report_data:
            continue
        df = report_data[sheet_key]
        if df.empty or "Message" in df.columns or "Error" in df.columns:
            continue

        expected = get_sheet_column_labels(report_id, sheet_key)
        if not expected:
            continue

        actual = [str(name) for name in df.columns]
        missing = [label for label in expected if label not in actual]
        if missing:
            errors.append(f"{report_id}.{sheet_key}: missing columns {missing}")

    return errors


def validate_all_report_definitions() -> List[str]:
    errors: List[str] = []
    for report_id in get_report_definitions():
        errors.extend(validate_schema_refs(report_id))
    errors.extend(validate_report_catalog())
    return errors


def validate_report_catalog() -> List[str]:
    """Ensure catalogue reports are fully defined in schema_registry."""
    errors: List[str] = []
    catalog = load_report_catalog()
    ag_lms_categories = {"AG", "LMS"}

    for report_id, info in catalog.items():
        category = info.get("category")
        if category not in ag_lms_categories:
            continue
        if not get_report_db_binding(report_id):
            errors.append(f"{report_id}: missing database binding for category {category}")
        definition = get_report_definitions().get(report_id, {})
        if info.get("standard") and not definition_exists(report_id):
            errors.append(f"{report_id}: standard report missing report_definitions entry")
        if not info_has_template_coverage(report_id, definition):
            errors.append(f"{report_id}: report_definitions missing output.sheets")

    for report_id, definition in get_report_definitions().items():
        category = definition.get("category")
        if category not in ag_lms_categories:
            continue
        if not definition.get("module") or not definition.get("class"):
            errors.append(f"{report_id}: AG/LMS report missing module/class in schema")
        elif report_id not in catalog:
            errors.append(f"{report_id}: AG/LMS report not in catalogue (check module/class)")

    return errors


def info_has_template_coverage(report_id: str, definition: Dict[str, Any]) -> bool:
    sheets = (definition.get("output") or {}).get("sheets") or {}
    return bool(sheets)


def apply_schema_output(report_id: str, report_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    if not definition_exists(report_id):
        return report_data
    return {
        key: order_dataframe_columns(report_id, key, df)
        for key, df in report_data.items()
    }


def resolve_sheet_names(report_id: str, fallback: Dict[str, str]) -> Dict[str, str]:
    schema_names = get_sheet_names(report_id)
    if not schema_names:
        return fallback
    resolved = dict(fallback)
    resolved.update(schema_names)
    return resolved


def grouped_configured_reports() -> List[Tuple[str, Dict[str, Any], List[Dict[str, Any]]]]:
    """Return reports grouped by configured category order."""
    categories = get_report_categories()
    reports = list_configured_reports()
    grouped: List[Tuple[str, Dict[str, Any], List[Dict[str, Any]]]] = []

    for category_id, category_info in categories.items():
        category_reports = [report for report in reports if report["category"] == category_id]
        if category_reports:
            grouped.append((category_id, category_info, category_reports))

    known_categories = set(categories)
    uncategorized = [report for report in reports if report["category"] not in known_categories]
    if uncategorized:
        grouped.append(("Other", {"display_name": "Other Reports"}, uncategorized))

    return grouped


def list_configured_reports() -> List[Dict[str, Any]]:
    """Return report metadata in display order."""
    reports = []
    for report_id, info in load_report_catalog().items():
        reports.append({
            "id": report_id,
            "name": info.get("display_name", report_id),
            "description": info.get("description", ""),
            "category": info.get("category", "Utility"),
            "standard": bool(info.get("standard", False)),
            "template_id": info.get("template_id"),
            "has_template": template_exists(report_id),
            "available_filters": info.get("available_filters", []),
            "sheets": info.get("sheets", []),
        })
    reports.sort(key=lambda item: (not item["standard"], item["name"].lower()))
    return reports
