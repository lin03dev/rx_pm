"""
LMS Comprehensive Report - schema-bound to LMS tables only.
Survey data belongs to Telios and is intentionally excluded.
"""

import pandas as pd
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class LMSComprehensiveReport(BaseReportV2):
    """Comprehensive LMS report using only registered LMS schema tables."""

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)

    def generate(self) -> Dict[str, pd.DataFrame]:
        results = {
            'batch_summary': self._get_batch_summary(),
            'enrollment_summary': self._get_enrollment_summary(),
            'participant_details': self._get_participant_details(),
            'module_completion': self._get_module_completion(),
            'assignment_status': self._get_assignment_status(),
            'attendance_summary': self._get_attendance_summary(),
        }
        results['summary_stats'] = self._get_summary_stats(results)
        return results

    def _get_batch_summary(self) -> pd.DataFrame:
        query = """
        SELECT 
            b.id as batch_id,
            b.batch as batch_name,
            b.location,
            TO_CHAR(b.start_date, 'YYYY-MM-DD') as start_date,
            TO_CHAR(b.enddate, 'YYYY-MM-DD') as end_date,
            c.title as course_name,
            cnt.country as country_name,
            b.batch_status_id,
            COUNT(DISTINCT e.id) as total_enrollments,
            COUNT(DISTINCT CASE WHEN e.role = 'MTT' THEN e.id END) as mtt_count,
            COUNT(DISTINCT CASE WHEN e.role = 'trainer' THEN e.id END) as trainer_count,
            COUNT(DISTINCT CASE WHEN e.role = 'admin' THEN e.id END) as admin_count
        FROM batch b
        LEFT JOIN enrollment e ON b.id = e.batch
        LEFT JOIN course c ON b.course_id = c.id
        LEFT JOIN country cnt ON b.country_id = cnt.id
        GROUP BY b.id, b.batch, b.location, b.start_date, b.enddate, c.title, cnt.country, b.batch_status_id
        ORDER BY b.start_date DESC
        """
        return self.schema.query_optional(
            query,
            ["batch", "enrollment", "course", "country"],
            message="LMS batch summary unavailable",
        )

    def _get_enrollment_summary(self) -> pd.DataFrame:
        query = """
        SELECT 
            b.batch as batch_name,
            b.location,
            c.title as course_name,
            e.role,
            COUNT(e.id) as enrollment_count,
            COUNT(DISTINCT p.id) as unique_participants
        FROM batch b
        JOIN enrollment e ON b.id = e.batch
        LEFT JOIN course c ON b.course_id = c.id
        LEFT JOIN person p ON e.student = p.id
        GROUP BY b.batch, b.location, c.title, e.role
        ORDER BY b.batch, e.role
        """
        return self.schema.query_optional(
            query,
            ["batch", "enrollment", "course", "person"],
            message="LMS enrollment summary unavailable",
        )

    def _get_participant_details(self) -> pd.DataFrame:
        query = """
        SELECT 
            p.id as person_id,
            p.firstname,
            p.lastname,
            p.email,
            p.phone,
            p.gender,
            cnt.country as country,
            p.state,
            p.region,
            p.enrollmentdate,
            p.date_of_joining,
            p.date_of_leaving,
            b.batch as batch_name,
            e.role as enrollment_role
        FROM person p
        LEFT JOIN enrollment e ON p.id = e.student
        LEFT JOIN batch b ON e.batch = b.id
        LEFT JOIN country cnt ON p.country_id = cnt.id
        ORDER BY p.id
        LIMIT 5000
        """
        return self.schema.query_optional(
            query,
            ["person", "enrollment", "batch", "country"],
            message="LMS participant details unavailable",
        )

    def _get_module_completion(self) -> pd.DataFrame:
        query = """
        SELECT 
            b.batch as batch_name,
            m.module as module_name,
            m.description as module_description,
            COUNT(DISTINCT e.id) as total_enrolled,
            COUNT(DISTINCT a.id) as attendance_records,
            COUNT(DISTINCT CASE WHEN a.ispresent = true THEN e.id END) as attended_count
        FROM batch b
        JOIN batchmodule bm ON b.id = bm.batchid
        JOIN module m ON bm.moduleid = m.id
        LEFT JOIN enrollment e ON b.id = e.batch
        LEFT JOIN attendance a ON e.id = a.enrollment AND a.module = m.id
        GROUP BY b.batch, m.module, m.description
        ORDER BY b.batch, m.module
        """
        df = self.schema.query_optional(
            query,
            ["batch", "batchmodule", "module", "enrollment", "attendance"],
            message="LMS module completion unavailable",
        )
        if not df.empty and 'total_enrolled' in df.columns:
            df['attendance_rate'] = df.apply(
                lambda row: round((row['attended_count'] / row['total_enrolled'] * 100), 1)
                if row['total_enrolled'] > 0 else 0,
                axis=1,
            )
        return df

    def _get_assignment_status(self) -> pd.DataFrame:
        query = """
        SELECT 
            b.batch as batch_name,
            a.assignment as assignment_name,
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            ss.submissionstatus as status_name,
            asub.comment as feedback,
            asub.file_url
        FROM assignmentsubmission asub
        JOIN enrollment e ON asub.enrollment = e.id
        JOIN batch b ON e.batch = b.id
        JOIN person p ON e.student = p.id
        LEFT JOIN assignment a ON asub.assignment = a.id
        LEFT JOIN submissionstatus ss ON asub.submissionstatus = ss.id
        WHERE asub.id IS NOT NULL
        ORDER BY b.batch, a.assignment
        """
        return self.schema.query_optional(
            query,
            ["assignmentsubmission", "enrollment", "batch", "person", "assignment", "submissionstatus"],
            message="LMS assignment status unavailable",
        )

    def _get_attendance_summary(self) -> pd.DataFrame:
        query = """
        SELECT 
            b.batch as batch_name,
            m.module as module_name,
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            COUNT(a.id) as total_sessions,
            SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) as present_count,
            ROUND(100.0 * SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) as attendance_rate
        FROM attendance a
        JOIN enrollment e ON a.enrollment = e.id
        JOIN batch b ON e.batch = b.id
        JOIN person p ON e.student = p.id
        JOIN module m ON a.module = m.id
        GROUP BY b.batch, m.module, p.firstname, p.lastname
        ORDER BY b.batch, m.module, attendance_rate DESC
        """
        return self.schema.query_optional(
            query,
            ["attendance", "enrollment", "batch", "person", "module"],
            message="LMS attendance summary unavailable",
        )

    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        summary = []

        batch_df = results.get('batch_summary', pd.DataFrame())
        if not batch_df.empty and 'total_enrollments' in batch_df.columns:
            summary.append({'Metric': 'Total Batches', 'Value': len(batch_df)})
            total = batch_df['total_enrollments'].sum()
            summary.append({'Metric': 'Total Enrollments', 'Value': int(total) if not pd.isna(total) else 0})

        participants = results.get('participant_details', pd.DataFrame())
        if not participants.empty and 'person_id' in participants.columns:
            summary.append({'Metric': 'Total Participants', 'Value': len(participants)})

        assignments = results.get('assignment_status', pd.DataFrame())
        if not assignments.empty:
            summary.append({'Metric': 'Total Submissions', 'Value': len(assignments)})

        if not summary:
            summary = [{'Metric': 'Status', 'Value': 'No LMS data available'}]
        return pd.DataFrame(summary)

