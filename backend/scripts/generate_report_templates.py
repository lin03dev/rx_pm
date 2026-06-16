#!/usr/bin/env python3
"""Generate blank Excel layout files from schema_registry report_definitions."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

import pandas as pd

from config.report_schema import get_report_template, list_report_templates
from utils.report_excel_writer import get_report_excel_writer


def _display_name(sheet_key: str, sheet_template: dict) -> str:
    return str(sheet_template.get("display_name") or sheet_key.replace("_", " ").title())[:31]


def generate_layout(template_id: str, output_dir: Path) -> Path | None:
    template = get_report_template(template_id)
    if not template:
        return None

    category = template.get("category", "Utility")
    target_dir = output_dir / category
    target_dir.mkdir(parents=True, exist_ok=True)

    prefix = template.get("filename_prefix") or template_id.replace("-", "_")
    output_path = target_dir / f"{prefix}_layout.xlsx"

    sheet_names: dict[str, str] = {}
    report_data: dict[str, pd.DataFrame] = {}

    for sheet_key, sheet_template in (template.get("sheets") or {}).items():
        columns = [col["name"] for col in (sheet_template.get("columns") or []) if col.get("name")]
        if not columns and sheet_template.get("layout") == "key_value":
            columns = [
                sheet_template.get("metric_column", "Metric"),
                sheet_template.get("value_column", "Value"),
            ]
        if not columns:
            continue

        sheet_names[sheet_key] = _display_name(sheet_key, sheet_template)
        report_data[sheet_key] = pd.DataFrame(columns=columns)

    if not report_data:
        return None

    writer = get_report_excel_writer()
    writer.save_report(output_path, report_data, sheet_names, report_id=template_id)
    return output_path


def main() -> int:
    output_root = BACKEND / "output" / "templates"
    generated = []

    print("=" * 60)
    print("REPORT LAYOUT TEMPLATE GENERATOR")
    print("=" * 60)

    for item in list_report_templates():
        path = generate_layout(item["id"], output_root)
        if path:
            generated.append(path)
            print(f"OK  {item['id']} -> {path.relative_to(BACKEND)}")

    print(f"\nGenerated {len(generated)} report layout file(s)")
    print(f"Location: {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
