"""Pre-flight checks before running the application."""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path[:0] = [str(BACKEND), str(ROOT)]

errors: list[str] = []


def check(name: str, fn) -> None:
    try:
        fn()
        print(f"OK  {name}")
    except Exception as exc:
        errors.append(f"{name}: {exc}")
        print(f"FAIL {name}: {exc}")


def test_imports() -> None:
    for module in (
        "app.main",
        "app.services",
        "core.schema_guard",
        "config.report_schema",
        "config.report_schema",
        "utils.report_excel_writer",
        "core.report_engine",
        "reports.bt_academy_student_report",
        "reports.language_survey_report",
        "reports.lms_comprehensive_report",
        "reports.batch_detail_report",
        "reports.batch_detailed_report",
        "reports.telios_geojson_report",
        "reports.custom_report",
    ):
        __import__(module)


def test_schema_cte_filter() -> None:
    from core.schema_guard import SchemaGuard

    class FakeDB:
        def execute_query(self, *args, **kwargs):
            import pandas as pd

            return pd.DataFrame()

        def table_exists(self, *args, **kwargs):
            return True

    guard = SchemaGuard(FakeDB(), "LMS", "lms-batch")
    query = "WITH stats AS (SELECT 1 FROM batch b JOIN enrollment e ON b.id = e.batch) SELECT * FROM stats"
    tables = guard.extract_schema_tables(query)
    assert "batch" in tables and "enrollment" in tables, tables
    assert "stats" not in tables, tables


def test_autographa_validation() -> None:
    from reports.bt_academy_student_report import BTAcademyStudentReport as R

    assert R._format_autographa_id("QC in Krobu Language") == "Not specified"
    assert R._format_autographa_id("123456") == "AG-123456"
    assert R._format_autographa_id("AG-123456") == "AG-123456"
    assert R._format_autographa_id("12345") == "Not specified"
    assert R._format_autographa_id("AG-12345") == "Not specified"
    assert R._format_autographa_id("1234567") == "Not specified"
    assert not R._is_valid_ag_id_candidate("MTT in Some Language")
    _, issue = R._evaluate_autographa_candidate("12345")
    assert issue and "incomplete" in issue.lower()


def test_bt_academy_status_fields() -> None:
    from reports.bt_academy_student_report import BTAcademyStudentReport as R

    report = R(db_manager=None)
    assert R._format_validation_status("VALIDATED") == "Validated"
    assert R._format_validation_status("REJECTED") == "Rejected"
    assert R._format_validation_status("") == "Not specified"
    assert report._derive_current_status("Inactive", "VALIDATED", None, None) == "Inactive"
    assert report._derive_current_status("Active", "VALIDATED", None, None) == "Active"
    assert report._derive_current_status("Student", "REJECTED", None, None) == "Inactive"
    assert report._derive_current_status("", "PENDING", None, None) == "Pending"
    assert report._derive_current_status("", "VALIDATED", None, None) == "Active"


def test_report_bindings() -> None:
    from config.schema_registry import get_report_project_binding

    expected = {
        "bt-academy-students": "LMS",
        "language-survey": "Telios",
        "lms-comprehensive": "LMS",
        "telios-geojson": "Telios",
        "user": "AG",
    }
    for report_id, system in expected.items():
        assert get_report_project_binding(report_id) == system, report_id


def test_fastapi_app() -> None:
    from app.main import app

    assert app.title == "RX_PM Reporting API"
    routes = {route.path for route in app.routes}
    for path in ("/api/reports", "/api/reports/preview", "/api/reports/generate"):
        assert path in routes, f"missing route {path}"


def test_schema_report_definitions() -> None:
    from config.report_schema import (
        build_output_template,
        get_sheet_column_labels,
        validate_all_report_definitions,
        validate_schema_refs,
    )

    errors = validate_all_report_definitions()
    assert not errors, errors

    bt_errors = validate_schema_refs("bt-academy-students")
    assert not bt_errors, bt_errors

    template = build_output_template("bt-academy-students")
    assert template and "student_roster" in template.get("sheets", {}), template

    labels = get_sheet_column_labels("bt-academy-students", "student_roster")
    assert "Validation Status" in labels
    assert "Current Status" in labels
    assert labels.index("Autographa id") < labels.index("Validation Status")


def test_report_templates() -> None:
    from config.report_schema import get_report_template, list_report_templates, template_exists

    templates = list_report_templates()
    assert templates, "expected at least one report template"
    bt = get_report_template("bt-academy-students")
    assert bt and "student_roster" in bt.get("sheets", {}), bt
    assert template_exists("bt-academy-students")
    roster = bt["sheets"]["student_roster"]
    column_names = [col["name"] for col in roster.get("columns", [])]
    assert "Validation Status" in column_names
    assert "Current Status" in column_names


def test_report_template_writer() -> None:
    import pandas as pd
    from utils.report_excel_writer import ReportExcelWriter

    writer = ReportExcelWriter()
    df = pd.DataFrame([
        {
            "Autographa id": "AG-123456",
            "Name of student": "Test User",
            "Country": "India",
            "Language": "Hindi",
            "Role": "MTT",
            "LMS roles": "Student",
            "Enrollments": 1,
            "Batches": "Batch A",
            "Validation Status": "Validated",
            "Current Status": "Active",
            "Remarks": "",
            "Date of enrolment": "2024-01-01",
        }
    ])
    path = BACKEND / "output" / "reports" / "_preflight_template_test.xlsx"
    path.parent.mkdir(parents=True, exist_ok=True)
    writer.save_report(
        path,
        {"student_roster": df},
        {"student_roster": "BT Academy Students"},
        report_id="bt-academy-students",
    )
    assert path.exists()
    path.unlink(missing_ok=True)


def test_ag_lms_catalog() -> None:
    from config.report_schema import validate_report_catalog, list_report_definitions

    errors = validate_report_catalog()
    assert not errors, errors
    definitions = list_report_definitions()
    ids = {item["id"] for item in definitions}
    for report_id in (
        "bt-academy-students",
        "user-activity",
        "lms-comprehensive",
        "lms",
        "lms-batch",
        "batch-detail",
        "user",
        "worklog",
        "consolidated",
    ):
        assert report_id in ids, f"missing definition for {report_id}"


def test_schema_output_helpers() -> None:
    import pandas as pd
    from config.report_schema import apply_schema_output, resolve_sheet_names

    df = pd.DataFrame({"Metric": ["Total"], "Value": [1]})
    ordered = apply_schema_output("lms", {"summary_stats": df})
    assert "summary_stats" in ordered
    names = resolve_sheet_names("lms", {"summary_stats": "Old Name"})
    assert names["summary_stats"] == "Summary Statistics"


def test_lms_comprehensive_no_recursion() -> None:
    import inspect
    from reports.lms_comprehensive_report import LMSComprehensiveReport

    source = inspect.getsource(LMSComprehensiveReport._get_summary_stats)
    assert "self.generate()" not in source


def main() -> int:
    check("imports", test_imports)
    check("schema CTE filter", test_schema_cte_filter)
    check("autographa validation", test_autographa_validation)
    check("BT Academy status fields", test_bt_academy_status_fields)
    check("report bindings", test_report_bindings)
    check("FastAPI app + routes", test_fastapi_app)
    check("schema report definitions", test_schema_report_definitions)
    check("report templates", test_report_templates)
    check("report template writer", test_report_template_writer)
    check("AG/LMS catalog schema", test_ag_lms_catalog)
    check("schema output helpers", test_schema_output_helpers)
    check("LMS comprehensive stats", test_lms_comprehensive_no_recursion)

    if errors:
        print("\nPREFLIGHT FAILED")
        for item in errors:
            print(f"  - {item}")
        return 1

    print("\nPREFLIGHT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
