"""
LMS Comprehensive Report - Corrected for actual database schema
Based on discovered columns:
- batch: id, batch, location, start_date, enddate, batch_status_id, country_id, course_id
- country: id, country
- submissionstatus: id, submissionstatus
"""

import pandas as pd
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class LMSComprehensiveReport(BaseReportV2):
    """
    Comprehensive LMS Report with multiple sheets based on actual schema
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['batch_id', 'course_id', 'country']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all LMS report sheets"""
        
        results = {}
        
        # 1. BATCH SUMMARY
        results['batch_summary'] = self._get_batch_summary()
        
        # 2. ENROLLMENT SUMMARY
        results['enrollment_summary'] = self._get_enrollment_summary()
        
        # 3. PARTICIPANT DETAILS
        results['participant_details'] = self._get_participant_details()
        
        # 4. MODULE COMPLETION
        results['module_completion'] = self._get_module_completion()
        
        # 5. ASSIGNMENT STATUS
        results['assignment_status'] = self._get_assignment_status()
        
        # 6. ATTENDANCE SUMMARY
        results['attendance_summary'] = self._get_attendance_summary()
        
        # 7. SURVEY RESPONSES
        results['survey_responses'] = self._get_survey_responses()
        
        # 8. SUMMARY STATISTICS
        results['summary_stats'] = self._get_summary_stats(results)
        
        return results
    
    def _get_batch_summary(self) -> pd.DataFrame:
        """Get batch summary overview"""
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
        
        try:
            df = self.execute_query(query)
            print(f"✅ Batch summary: {len(df)} batches")
            return df
        except Exception as e:
            print(f"⚠️ Batch summary error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_enrollment_summary(self) -> pd.DataFrame:
        """Get enrollment summary by batch"""
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
        
        try:
            df = self.execute_query(query)
            print(f"✅ Enrollment summary: {len(df)} records")
            return df
        except Exception as e:
            print(f"⚠️ Enrollment summary error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_participant_details(self) -> pd.DataFrame:
        """Get detailed participant information"""
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
        
        try:
            df = self.execute_query(query)
            print(f"✅ Participant details: {len(df)} records")
            return df
        except Exception as e:
            print(f"⚠️ Participant details error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_module_completion(self) -> pd.DataFrame:
        """Get module completion status"""
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
        
        try:
            df = self.execute_query(query)
            if not df.empty and 'total_enrolled' in df.columns:
                df['attendance_rate'] = df.apply(
                    lambda row: round((row['attended_count'] / row['total_enrolled'] * 100), 1) 
                    if row['total_enrolled'] > 0 else 0, axis=1
                )
            print(f"✅ Module completion: {len(df)} module-batch combinations")
            return df
        except Exception as e:
            print(f"⚠️ Module completion error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_assignment_status(self) -> pd.DataFrame:
        """Get assignment submission status"""
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
        
        try:
            df = self.execute_query(query)
            print(f"✅ Assignment status: {len(df)} submissions")
            return df
        except Exception as e:
            print(f"⚠️ Assignment status error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_attendance_summary(self) -> pd.DataFrame:
        """Get attendance summary"""
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
        
        try:
            df = self.execute_query(query)
            print(f"✅ Attendance summary: {len(df)} records")
            return df
        except Exception as e:
            print(f"⚠️ Attendance summary error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_survey_responses(self) -> pd.DataFrame:
        """Get survey response data"""
        query = """
        SELECT 
            s.survey as survey_name,
            s.survey_type,
            r.link_id,
            r.link_type,
            r.batchid,
            r.role as respondent_role,
            p.firstname || ' ' || COALESCE(p.lastname, '') as participant_name,
            r.linkcomment as comment
        FROM response r
        LEFT JOIN survey s ON r.survey = s.id
        LEFT JOIN person p ON r.participant = p.id
        WHERE r.id IS NOT NULL
        ORDER BY r.id DESC
        LIMIT 1000
        """
        
        try:
            df = self.execute_query(query)
            print(f"✅ Survey responses: {len(df)} records")
            return df
        except Exception as e:
            print(f"⚠️ Survey responses error: {e}")
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_summary_stats(self, results: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Generate summary statistics"""
        summary = []
        
        # Batch stats
        if 'batch_summary' in results and not results['batch_summary'].empty:
            df = results['batch_summary']
            summary.append({'Metric': 'Total Batches', 'Value': len(df)})
            if 'total_enrollments' in df.columns:
                total = df['total_enrollments'].sum()
                summary.append({'Metric': 'Total Enrollments', 'Value': int(total) if not pd.isna(total) else 0})
        
        # Participant stats
        if 'participant_details' in results and not results['participant_details'].empty:
            df = results['participant_details']
            summary.append({'Metric': 'Total Participants', 'Value': len(df)})
            if 'gender' in df.columns:
                male_count = len(df[df['gender'] == 'Male'])
                female_count = len(df[df['gender'] == 'Female'])
                summary.append({'Metric': 'Male Participants', 'Value': male_count})
                summary.append({'Metric': 'Female Participants', 'Value': female_count})
        
        # Assignment stats
        if 'assignment_status' in results and not results['assignment_status'].empty:
            df = results['assignment_status']
            summary.append({'Metric': 'Total Submissions', 'Value': len(df)})
            if 'status_name' in df.columns:
                approved = len(df[df['status_name'] == 'Approved'])
                summary.append({'Metric': 'Approved Submissions', 'Value': approved})
        
        # Attendance stats
        if 'attendance_summary' in results and not results['attendance_summary'].empty:
            df = results['attendance_summary']
            if 'attendance_rate' in df.columns:
                valid_rates = df['attendance_rate'].dropna()
                if len(valid_rates) > 0:
                    avg_attendance = valid_rates.mean()
                    summary.append({'Metric': 'Average Attendance Rate', 'Value': f"{avg_attendance:.1f}%"})
        
        # Survey stats
        if 'survey_responses' in results and not results['survey_responses'].empty:
            df = results['survey_responses']
            summary.append({'Metric': 'Survey Responses', 'Value': len(df)})
        
        return pd.DataFrame(summary)
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'batch_summary': '1. Batch Summary',
            'enrollment_summary': '2. Enrollment Summary',
            'participant_details': '3. Participant Details',
            'module_completion': '4. Module Completion',
            'assignment_status': '5. Assignment Status',
            'attendance_summary': '6. Attendance Summary',
            'survey_responses': '7. Survey Responses',
            'summary_stats': '8. Summary Statistics'
        }
