"""Validate generated report outputs against schema_registry report contracts.

This is the strongest standardization check: it runs report classes, inspects
the returned DataFrames, and compares sheet keys/columns to the expanded schema
contracts declared in config/schema_registry.yaml.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path[:0] = [str(BACKEND), str(ROOT)]


DYNAMIC_REPORTS = {"custom"}
MESSAGE_COLUMNS = {"Message", "Error"}
REGISTRY_PATH = BACKEND / "config" / "schema_registry.yaml"


def _load_registry() -> Dict[str, Any]:
    return yaml.safe_load(REGISTRY_PATH.read_text()) or {}


def _get_definitions() -> Dict[str, Any]:
    return _load_registry().get("report_definitions") or {}


def _expand_columns(sheet_def: Dict[str, Any], groups: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    columns: List[Dict[str, Any]] = []
    for group_id in sheet_def.get("column_groups") or []:
        columns.extend(dict(col) for col in groups.get(str(group_id), []))
    for col in sheet_def.get("columns") or []:
        group_id = col.get("group") if isinstance(col, dict) else None
        if group_id:
            columns.extend(dict(group_col) for group_col in groups.get(str(group_id), []))
        else:
            columns.append(dict(col))
    return columns


def _build_engine(database: str):
    from config.database_config import DatabaseConfigManager
    from config.report_registry import register_configured_reports
    from config.system_loader import load_config
    from core.database_manager import DatabaseManager
    from core.report_engine import ReportEngine

    db_config_manager = DatabaseConfigManager()
    if database not in db_config_manager.list_databases():
        raise ValueError(f"Unknown database: {database}")

    db_manager = DatabaseManager(db_config_manager)
    db_manager.current_db = database
    engine = ReportEngine(db_manager, load_config())
    register_configured_reports(engine)
    return engine


def _default_database_for_report(report_id: str, definitions: Dict[str, Any]) -> str | None:
    sources = definitions.get(report_id, {}).get("sources") or {}
    primary = sources.get("primary")
    if not primary:
        category = definitions.get(report_id, {}).get("category")
        primary = {"AG": "AG", "LMS": "LMS", "Telios": "Telios", "Language": "Telios"}.get(category)
    if primary == "AG":
        return "AG"
    if primary == "LMS":
        return "LMS"
    if primary == "Telios":
        return "Telios"
    return None


def _expected_sheets(report_id: str, definitions: Dict[str, Any]) -> Dict[str, Any]:
    definition = definitions.get(report_id) or {}
    return ((definition.get("output") or {}).get("sheets") or {})


def _expected_labels(sheet_def: Dict[str, Any]) -> List[str]:
    groups = _load_registry().get("report_column_groups") or {}
    return [
        str(col.get("label"))
        for col in _expand_columns(sheet_def, groups)
        if col.get("label")
    ]


def _is_message_sheet(actual_columns: Iterable[Any]) -> bool:
    return bool(MESSAGE_COLUMNS.intersection({str(col) for col in actual_columns}))


def validate_report_output(
    report_id: str,
    database: str,
    *,
    fail_on_extra: bool,
    allow_message_sheets: bool,
) -> Tuple[List[str], List[str]]:
    """Return (issues, warnings) for one report/database pair."""
    issues: List[str] = []
    warnings: List[str] = []
    definitions = _get_definitions()
    sheet_defs = _expected_sheets(report_id, definitions)

    engine = _build_engine(database)
    report = engine.get_report(report_id, db_name=database, report_id=report_id)
    data = report.generate()

    actual_sheet_keys = set(data.keys())
    expected_sheet_keys = set(sheet_defs.keys())
    missing_sheets = sorted(expected_sheet_keys - actual_sheet_keys)
    extra_sheets = sorted(actual_sheet_keys - expected_sheet_keys)

    if missing_sheets:
        issues.append(f"missing sheets: {missing_sheets}")
    if extra_sheets:
        issues.append(f"extra sheets: {extra_sheets}")

    for sheet_key in sorted(expected_sheet_keys & actual_sheet_keys):
        sheet_def = sheet_defs[sheet_key]
        df = data[sheet_key]
        actual = [str(col) for col in df.columns]

        if allow_message_sheets and _is_message_sheet(actual):
            warnings.append(f"{sheet_key}: message/error fallback columns {actual}")
            continue

        if sheet_def.get("dynamic_columns"):
            expected = _expected_labels(sheet_def)
            missing = [label for label in expected if label not in actual]
            if missing:
                issues.append(f"{sheet_key}: missing stable dynamic columns {missing}")
            continue

        expected = _expected_labels(sheet_def)
        if not expected:
            issues.append(f"{sheet_key}: no expected columns after schema expansion")
            continue

        missing = [label for label in expected if label not in actual]
        extra = [label for label in actual if label not in expected]
        if missing:
            issues.append(f"{sheet_key}: missing columns {missing}")
        if extra:
            message = f"{sheet_key}: extra columns {extra}"
            if fail_on_extra:
                issues.append(message)
            else:
                warnings.append(message)

    return issues, warnings


def iter_report_targets(
    reports: List[str] | None,
    database_override: str | None,
    *,
    include_dynamic: bool,
) -> Iterable[Tuple[str, str]]:
    definitions = _get_definitions()
    report_ids = reports or list(definitions.keys())

    for report_id in report_ids:
        if report_id not in definitions:
            yield report_id, ""
            continue
        if report_id in DYNAMIC_REPORTS and not include_dynamic:
            continue

        database = database_override or _default_database_for_report(report_id, definitions)
        if database:
            yield report_id, database


def validate_static_contracts() -> Tuple[List[str], Dict[str, int]]:
    registry = _load_registry()
    definitions = registry.get("report_definitions") or {}
    systems = registry.get("systems") or {}
    groups = registry.get("report_column_groups") or {}
    issues: List[str] = []
    stats = {
        "reports": len(definitions),
        "sheets": 0,
        "column_sheets": 0,
        "dynamic_sheets": 0,
        "effective_columns": 0,
        "group_uses": 0,
    }

    def table_exists(system: str, table: str) -> bool:
        return table in ((systems.get(system) or {}).get("tables") or {})

    def col_exists(system: str, table: str, column: str) -> bool:
        table_info = ((systems.get(system) or {}).get("tables") or {}).get(table) or {}
        columns = {str(name).lower() for name in table_info.get("columns") or []}
        return str(column).lower() in columns

    for report_id, definition in definitions.items():
        primary = (definition.get("sources") or {}).get("primary")
        for table in (definition.get("sources") or {}).get("tables") or []:
            if primary and not table_exists(primary, table):
                issues.append(f"{report_id}: missing source table {primary}.{table}")

        sheets = ((definition.get("output") or {}).get("sheets") or {})
        stats["sheets"] += len(sheets)
        for sheet_key, sheet_def in sheets.items():
            for group_id in sheet_def.get("column_groups") or []:
                stats["group_uses"] += 1
                if str(group_id) not in groups:
                    issues.append(f"{report_id}.{sheet_key}: unknown column group {group_id}")
            for col in sheet_def.get("columns") or []:
                group_id = col.get("group") if isinstance(col, dict) else None
                if group_id:
                    stats["group_uses"] += 1
                    if str(group_id) not in groups:
                        issues.append(f"{report_id}.{sheet_key}: unknown inline column group {group_id}")

            columns = _expand_columns(sheet_def, groups)
            if columns:
                stats["column_sheets"] += 1
                stats["effective_columns"] += len(columns)
            elif sheet_def.get("dynamic_columns"):
                stats["dynamic_sheets"] += 1
            else:
                issues.append(f"{report_id}.{sheet_key}: no columns or dynamic_columns contract")

            for col in columns:
                ref = col.get("schema_ref") or {}
                system = ref.get("system")
                table = ref.get("table")
                for column in ref.get("columns") or ([] if not ref.get("column") else [ref.get("column")]):
                    if system and table and not col_exists(system, table, column):
                        issues.append(f"{report_id}.{sheet_key}.{col.get('label')}: missing schema ref {system}.{table}.{column}")
                for fallback in col.get("fallbacks") or []:
                    fb_system = fallback.get("system")
                    fb_table = fallback.get("table")
                    fb_column = fallback.get("column")
                    if fb_system and fb_table and fb_column and not col_exists(fb_system, fb_table, fb_column):
                        issues.append(f"{report_id}.{sheet_key}.{col.get('label')}: missing fallback {fb_system}.{fb_table}.{fb_column}")

    return issues, stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate reports and validate returned sheet/column contracts."
    )
    parser.add_argument("--report", action="append", help="Report id to validate. Repeatable.")
    parser.add_argument("--database", help="Override database name for all selected reports.")
    parser.add_argument("--static", action="store_true", help="Validate schema contracts without generating reports.")
    parser.add_argument("--include-dynamic", action="store_true", help="Include custom/dynamic reports.")
    parser.add_argument(
        "--allow-extra",
        action="store_true",
        help="Warn instead of failing when generated sheets include columns outside the schema contract.",
    )
    parser.add_argument(
        "--strict-messages",
        action="store_true",
        help="Fail message/error fallback sheets instead of treating them as warnings.",
    )
    args = parser.parse_args()

    if args.static:
        issues, stats = validate_static_contracts()
        print("Static contract validation")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        if issues:
            print("\nFAIL")
            for issue in issues:
                print(f"  - {issue}")
            return 1
        print("\nOK")
        return 0

    failures = 0
    validated = 0

    for report_id, database in iter_report_targets(
        args.report,
        args.database,
        include_dynamic=args.include_dynamic,
    ):
        if not database:
            print(f"FAIL {report_id}: unknown report id or no database binding")
            failures += 1
            continue

        try:
            issues, warnings = validate_report_output(
                report_id,
                database,
                fail_on_extra=not args.allow_extra,
                allow_message_sheets=not args.strict_messages,
            )
        except Exception as exc:
            print(f"FAIL {report_id} [{database}]: generation error: {exc}")
            failures += 1
            continue

        validated += 1
        for warning in warnings:
            print(f"WARN {report_id} [{database}]: {warning}")

        if issues:
            failures += 1
            print(f"FAIL {report_id} [{database}]")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"OK   {report_id} [{database}]")

    print(f"\nValidated {validated} report(s), failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
