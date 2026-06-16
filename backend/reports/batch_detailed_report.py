"""
Batch Detailed Report - Complete Working Version
"""

import pandas as pd
import re
from datetime import datetime
from typing import Dict, Any, List

from reports.base_report_v2 import BaseReportV2


class BatchDetailedReport(BaseReportV2):
    
    def __init__(self, db_manager, batch_id=None, batch_name=None, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.batch_id = batch_id
        self.batch_name = batch_name
        self.batch_info = None
        
    def _clean_filename(self, text: str) -> str:
        text = text.replace(' ', '_')
        text = re.sub(r'[^\w\-_]', '', text)
        text = re.sub(r'_+', '_', text)
        text = text.strip('_')
        if len(text) > 50:
            text = text[:50]
        return text
    
    def _sanitize_sheet_name(self, name: str) -> str:
        invalid_chars = r'[\[\]\:\*\?/\\]'
        name = re.sub(invalid_chars, '_', name)
        name = name.replace(' ', '_')
        name = re.sub(r'[^\w\-_]', '', name)
        if len(name) > 31:
            name = name[:31]
        return name.strip('_')
    
    def _table_columns(self, table_name: str) -> List[str]:
        return [name.lower() for name in self.schema.table_columns(table_name)]

    def _table_exists(self, table_name: str) -> bool:
        return self.schema.has_table(table_name)

    def _batch_foreign_key(self, column_base: str) -> str:
        columns = self.schema.table_columns("batch")
        if f"{column_base}_id" in columns:
            return f"b.{column_base}_id"
        if column_base in columns:
            return f"b.{column_base}"
        return f"b.{column_base}_id"

    def _get_batch_info(self) -> Dict[str, Any]:
        if self.batch_id:
            filter_clause = f"b.id = {self.batch_id}"
        elif self.batch_name:
            filter_clause = f"b.batch = '{self.batch_name}'"
        else:
            return None
            
        course_fk = self._batch_foreign_key("course")
        country_fk = self._batch_foreign_key("country")

        query = f"""
        SELECT 
            b.id as batch_id,
            b.batch as batch_name,
            b.location,
            b.start_date,
            b.enddate as end_date,
            COALESCE(c.title, 'No Course') as course_name,
            cnt.country as country_name,
            bs.batchstatus as batch_status
        FROM batch b
        LEFT JOIN course c ON {course_fk} = c.id
        LEFT JOIN country cnt ON {country_fk} = cnt.id
        LEFT JOIN batchstatus bs ON b.batch_status_id = bs.id
        WHERE {filter_clause}
        """
        df = self.execute_query(query)
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        self.batch_info = self._get_batch_info()
        if not self.batch_info:
            return {'error': pd.DataFrame({'Error': ['Batch not found']})}
        
        results = {}
        
        results['batch_overview'] = self._get_batch_overview()
        results['participants'] = self._get_participants()
        results['module_schedule'] = self._get_module_schedule()
        results['attendance_matrix'] = self._get_attendance_matrix()
        results['attendance_details'] = self._get_attendance_details()
        results['attendance_summary'] = self._get_attendance_summary()
        results['assignment_submissions'] = self._get_assignment_submissions()
        results['participant_progress'] = self._get_participant_progress()
        results['trainers'] = self._get_trainers()
        results['summary_stats'] = self._get_summary_stats(results)
        
        return results
    
    def _get_batch_overview(self) -> pd.DataFrame:
        start_date = self.batch_info.get('start_date')
        end_date = self.batch_info.get('end_date')
        
        data = [{
            'Batch Name': self.batch_info.get('batch_name'),
            'Course': self.batch_info.get('course_name'),
            'Location': self.batch_info.get('location'),
            'Country': self.batch_info.get('country_name'),
            'Start Date': start_date.strftime('%Y-%m-%d') if pd.notna(start_date) else 'Not set',
            'End Date': end_date.strftime('%Y-%m-%d') if pd.notna(end_date) else 'Not set',
            'Status': self.batch_info.get('batch_status')
        }]
        return pd.DataFrame(data)
    
    def _get_participants(self) -> pd.DataFrame:
        query = f"""
        SELECT 
            p.id as participant_id,
            p.firstname,
            p.lastname,
            p.email,
            p.gender,
            e.role
        FROM enrollment e
        JOIN person p ON e.student = p.id
        WHERE e.batch = {self.batch_info['batch_id']}
        ORDER BY p.lastname
        """
        df = self.execute_query(query)
        if df.empty:
            df = pd.DataFrame({'Message': ['No participants enrolled']})
        else:
            df['full_name'] = df['firstname'] + ' ' + df['lastname'].fillna('')
            df = df[['participant_id', 'full_name', 'email', 'gender', 'role']]
        return df
    
    def _get_module_schedule(self) -> pd.DataFrame:
        try:
            query = f"""
            SELECT 
                s.id as session_id,
                s.name as session_name
            FROM sessions s
            WHERE s.batch = {self.batch_info['batch_id']}
            ORDER BY s.name
            """
            df = self.execute_query(query)
            if df.empty:
                df = pd.DataFrame({'Message': ['No sessions scheduled']})
        except Exception as e:
            df = pd.DataFrame({'Message': [f'Could not retrieve session data']})
        return df
    
    def _get_attendance_matrix(self) -> pd.DataFrame:
        try:
            query = f"""
            SELECT 
                p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
                s.name as session_name,
                CASE WHEN MAX(CASE WHEN sa.attendance = true THEN 1 ELSE 0 END) = 1 THEN '✓' ELSE '✗' END as attendance
            FROM session_attendance sa
            JOIN sessions s ON sa.sessionid = s.id
            JOIN enrollment e ON sa.enrollmentid = e.id
            JOIN person p ON e.student = p.id
            WHERE s.batch = {self.batch_info['batch_id']}
            GROUP BY p.firstname, p.lastname, s.name
            ORDER BY p.lastname, s.name
            """
            attendance_df = self.execute_query(query)
            
            if attendance_df.empty:
                return pd.DataFrame({'Message': ['No attendance records for this batch']})
            
            pivot_df = attendance_df.pivot_table(
                index='participant_name',
                columns='session_name',
                values='attendance',
                aggfunc='first'
            )
            
            pivot_df['Attendance %'] = pivot_df.apply(
                lambda row: (row != '✗').sum() / len(pivot_df.columns) * 100, axis=1
            )
            
            pivot_df = pivot_df.sort_values('Attendance %', ascending=False)
            pivot_df['Attendance %'] = pivot_df['Attendance %'].round(1).astype(str) + '%'
            pivot_df = pivot_df.reset_index()
            
            if len(pivot_df) > 0:
                session_cols = [col for col in pivot_df.columns if col not in ['participant_name', 'Attendance %']]
                summary_row = {'participant_name': '📊 SESSION ATTENDANCE %'}
                for col in session_cols:
                    present_count = sum(1 for _, row in pivot_df.iterrows() if row[col] == '✓')
                    total_participants = len(pivot_df)
                    summary_row[col] = f"{round(present_count / total_participants * 100, 1)}%" if total_participants > 0 else '0%'
                summary_row['Attendance %'] = f"{pivot_df['Attendance %'].str.rstrip('%').astype(float).mean():.1f}%"
                pivot_df = pd.concat([pivot_df, pd.DataFrame([summary_row])], ignore_index=True)
            
            return pivot_df
            
        except Exception as e:
            return pd.DataFrame({'Message': [f'Error: {str(e)}']})
    
    def _get_attendance_details(self) -> pd.DataFrame:
        try:
            query = f"""
            SELECT 
                p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
                s.name as session_name,
                CASE WHEN sa.attendance = true THEN 'Present' ELSE 'Absent' END as status
            FROM session_attendance sa
            JOIN sessions s ON sa.sessionid = s.id
            JOIN enrollment e ON sa.enrollmentid = e.id
            JOIN person p ON e.student = p.id
            WHERE s.batch = {self.batch_info['batch_id']}
            ORDER BY p.lastname, s.name
            """
            df = self.execute_query(query)
            if df.empty:
                df = pd.DataFrame({'Message': ['No attendance records']})
        except Exception as e:
            df = pd.DataFrame({'Message': [f'Error: {str(e)}']})
        return df
    
    def _get_attendance_summary(self) -> pd.DataFrame:
        query = f"""
        SELECT 
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            COUNT(DISTINCT sa.sessionid) as total_sessions,
            SUM(CASE WHEN sa.attendance = true THEN 1 ELSE 0 END) as present_count,
            ROUND(100.0 * SUM(CASE WHEN sa.attendance = true THEN 1 ELSE 0 END) / NULLIF(COUNT(sa.id), 0), 1) as attendance_rate
        FROM session_attendance sa
        JOIN sessions s ON sa.sessionid = s.id
        JOIN enrollment e ON sa.enrollmentid = e.id
        JOIN person p ON e.student = p.id
        WHERE s.batch = {self.batch_info['batch_id']}
        GROUP BY p.firstname, p.lastname
        ORDER BY attendance_rate DESC
        """
        df = self.execute_query(query)
        if df.empty:
            df = pd.DataFrame({'Message': ['No attendance data available']})
        return df
    
    def _get_assignment_submissions(self) -> pd.DataFrame:
        query = f"""
        SELECT 
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            a.assignment as assignment_name,
            CASE 
                WHEN asub.id IS NULL THEN '❌ NOT SUBMITTED'
                WHEN asub.submissionstatus = 3 THEN '✅ APPROVED'
                WHEN asub.submissionstatus = 2 THEN '⚠️ REDO REQUIRED'
                WHEN asub.submissionstatus = 4 THEN '❌ REJECTED'
                WHEN asub.submissionstatus = 1 THEN '📤 SUBMITTED'
                ELSE '⏳ PENDING'
            END as submission_status,
            asub.comment as feedback
        FROM enrollment e
        JOIN person p ON e.student = p.id
        LEFT JOIN assignmentsubmission asub ON asub.enrollment = e.id
        LEFT JOIN assignment a ON asub.assignment = a.id
        WHERE e.batch = {self.batch_info['batch_id']}
        ORDER BY p.lastname, a.assignment
        """
        df = self.execute_query(query)
        if df.empty:
            df = pd.DataFrame({'Message': ['No assignment submissions found']})
        return df
    
    def _get_participant_progress(self) -> pd.DataFrame:
        query = f"""
        SELECT 
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            COUNT(DISTINCT sa.sessionid) as sessions_attended,
            COUNT(DISTINCT asub.id) as assignments_submitted
        FROM enrollment e
        JOIN person p ON e.student = p.id
        LEFT JOIN session_attendance sa ON sa.enrollmentid = e.id
        LEFT JOIN assignmentsubmission asub ON e.id = asub.enrollment
        WHERE e.batch = {self.batch_info['batch_id']}
        GROUP BY p.firstname, p.lastname
        ORDER BY p.lastname
        """
        df = self.execute_query(query)
        if df.empty:
            df = pd.DataFrame({'Message': ['No progress data available']})
        return df
    
    def _get_trainers(self) -> pd.DataFrame:
        df = pd.DataFrame({'Message': ['No trainers assigned']})
        return df
    
    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        stats = []
        
        participants_df = results.get('participants', pd.DataFrame())
        total_participants = len(participants_df) if 'full_name' in participants_df.columns else 0
        
        if total_participants == 0:
            stats.append({'Metric': 'Status', 'Value': 'No participant data'})
            return pd.DataFrame(stats)
        
        stats.append({'Metric': 'Total Participants Enrolled', 'Value': total_participants})
        
        if 'role' in participants_df.columns:
            role_counts = participants_df['role'].value_counts()
            for role, count in role_counts.items():
                stats.append({'Metric': f'  └─ {role}', 'Value': f"{count} ({round(count/total_participants*100, 1)}%)"})
        
        attendance_df = results.get('attendance_summary', pd.DataFrame())
        if not attendance_df.empty and 'attendance_rate' in attendance_df.columns:
            stats.append({'Metric': '', 'Value': ''})
            stats.append({'Metric': '📊 ATTENDANCE OVERVIEW', 'Value': ''})
            
            perfect = len(attendance_df[attendance_df['attendance_rate'] == 100])
            good = len(attendance_df[(attendance_df['attendance_rate'] >= 75) & (attendance_df['attendance_rate'] < 100)])
            moderate = len(attendance_df[(attendance_df['attendance_rate'] >= 50) & (attendance_df['attendance_rate'] < 75)])
            poor = len(attendance_df[(attendance_df['attendance_rate'] >= 25) & (attendance_df['attendance_rate'] < 50)])
            very_poor = len(attendance_df[attendance_df['attendance_rate'] < 25])
            
            stats.append({'Metric': '  Participant Attendance Distribution', 'Value': ''})
            stats.append({'Metric': f'    ├─ 100% (Perfect Attendance)', 'Value': f"{perfect} ({round(perfect/total_participants*100, 1)}%)"})
            stats.append({'Metric': f'    ├─ 75% - 99% (Good Attendance)', 'Value': f"{good} ({round(good/total_participants*100, 1)}%)"})
            stats.append({'Metric': f'    ├─ 50% - 74% (Moderate Attendance)', 'Value': f"{moderate} ({round(moderate/total_participants*100, 1)}%)"})
            stats.append({'Metric': f'    ├─ 25% - 49% (Poor Attendance)', 'Value': f"{poor} ({round(poor/total_participants*100, 1)}%)"})
            stats.append({'Metric': f'    └─ <25% (Very Poor Attendance)', 'Value': f"{very_poor} ({round(very_poor/total_participants*100, 1)}%)"})
        
        assignments_df = results.get('assignment_submissions', pd.DataFrame())
        if not assignments_df.empty and 'Message' not in assignments_df.columns:
            total_records = len(assignments_df)
            if total_records > 0:
                stats.append({'Metric': '', 'Value': ''})
                stats.append({'Metric': '📝 ASSIGNMENT OVERVIEW', 'Value': ''})
                
                not_submitted = len(assignments_df[assignments_df['submission_status'].str.contains('NOT SUBMITTED', na=False)])
                submitted = len(assignments_df[assignments_df['submission_status'].str.contains('SUBMITTED', na=False)])
                approved = len(assignments_df[assignments_df['submission_status'].str.contains('APPROVED', na=False)])
                
                stats.append({'Metric': '  Total Assignment Records', 'Value': total_records})
                stats.append({'Metric': f'    ├─ ❌ Not Submitted', 'Value': f"{not_submitted} ({round(not_submitted/total_records*100, 1)}%)"})
                stats.append({'Metric': f'    ├─ 📤 Submitted', 'Value': f"{submitted} ({round(submitted/total_records*100, 1)}%)"})
                stats.append({'Metric': f'    └─ ✅ Approved', 'Value': f"{approved} ({round(approved/total_records*100, 1)}%)"})
        
        if not stats:
            stats = [{'Metric': 'Status', 'Value': 'No data available'}]
        
        return pd.DataFrame(stats)
    
    
    def get_filename(self) -> str:
        batch_name = self.batch_info.get('batch_name', 'unknown')
        start_date = self.batch_info.get('start_date')
        clean_name = self._clean_filename(str(batch_name))
        if pd.notna(start_date):
            date_str = start_date.strftime('%Y%m%d')
        else:
            date_str = 'nodate'
        return f"{clean_name}_{date_str}.xlsx"
    
    def get_course_name(self) -> str:
        return self.batch_info.get('course_name', 'Unknown_Course')
