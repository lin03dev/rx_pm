#!/usr/bin/env python3
"""Diagnose Autographa ID resolution for BT Academy report."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.database_config import DatabaseConfigManager
from core.database_manager import DatabaseManager
from reports.bt_academy_student_report import BTAcademyStudentReport


def main() -> int:
    db_manager = DatabaseManager(DatabaseConfigManager())
    report = BTAcademyStudentReport(db_manager, db_name="LMS_Dev", report_id="bt-academy-students")

    ag_db = report._resolve_ag_database()
    print(f"AG companion DB: {ag_db}")

    profiles = report._fetch_ag_user_profiles()
    print(f"AG indexed emails: {len(profiles['by_email'])}")
    print(f"AG indexed rolls: {len(profiles['by_roll'])}")
    print(f"AG indexed names: {len(profiles['by_name'])}")
    print(f"AG all profiles: {len(profiles.get('all_profiles', []))}")

    if ag_db:
        q = """
        SELECT username, email, name
        FROM users
        WHERE role::text != 'SUPER_ADMIN'
        LIMIT 15
        """
        try:
            df = db_manager.execute_query(q, db_name=ag_db)
            print("\nSample AG users.username / email:")
            for _, row in df.iterrows():
                un = row.get("username")
                canonical, issue = report._evaluate_autographa_candidate(un)
                print(f"  username={un!r} -> {canonical or issue}")
        except Exception as exc:
            print(f"AG sample query failed: {exc}")

    lms_q = """
    SELECT
        p.id,
        TRIM(COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '')) AS name,
        p.email,
        p.rollnumber,
        lu.login
    FROM person p
    JOIN enrollment e ON e.student = p.id
    LEFT JOIN "user" lu ON lu."personId" = p.id
    LIMIT 15
    """
    try:
        lms = db_manager.execute_query(lms_q, db_name="LMS_Dev")
        print("\nSample LMS person rollnumber / user.login:")
        for _, row in lms.iterrows():
            for field in ("rollnumber", "login"):
                val = row.get(field)
                canonical, issue = report._evaluate_autographa_candidate(val)
                print(f"  {row.get('name')[:30]!r} {field}={val!r} -> {canonical or issue or 'empty'}")
    except Exception as exc:
        print(f"LMS sample query failed: {exc}")

    roster, _ = report._get_student_roster()
    if "Autographa id" in roster.columns:
        valid = roster["Autographa id"].str.match(r"^AG-\d{6}$", na=False).sum()
        missing = (roster["Autographa id"] == "Not specified").sum()
        print(f"\nRoster: {len(roster)} students, {valid} valid IDs, {missing} not specified")
        if missing:
            print("Sample missing remarks:")
            miss = roster[roster["Autographa id"] == "Not specified"].head(5)
            for _, row in miss.iterrows():
                print(f"  {row['Name of student']!r}: {row.get('Remarks', '')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
