"""
Batch Detail Report - Complete details for a specific batch
Generates a workbook with the batch name and start date as filename
Includes ALL batch-related information across multiple sheets
"""

import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from reports.base_report_v2 import BaseReportV2


class BatchDetailReport(BaseReportV2):
    """
    Comprehensive Batch Detail Report
    Filename format: {batch_name}_{start_date}_Batch_Report.xlsx
    
    Sheets included:
    1. Executive Summary - Key metrics at a glance
    2. Batch Information - Basic batch details
    3. Participant List - All participants with details
    4. Participant Performance - Individual metrics
    5. Attendance Details - Daily attendance records
    6. Attendance Summary - Per participant summary
    7. Module Progress - Module completion status
    8. Assignment Status - All submissions
    9. Assignment Grades - Graded assignments
    10. Survey Responses - All survey feedback
    11. Daily Updates - Session-wise updates
    12. Timetable/Sessions - Schedule
    13. Trainers & Mentors - Assigned staff
    14. Batch Comparisons - Compare with other batches
    """
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['batch_id', 'batch_name']
        self.batch_id = kwargs.get('batch_id')
        self.batch_name = kwargs.get('batch_name')
        self.batch_info = None
    
    def set_batch(self, batch_id: Optional[int] = None, batch_name: Optional[str] = None):
        """Set which batch to report on"""
        self.batch_id = batch_id
        self.batch_name = batch_name
        self._load_batch_info()
    
    def _load_batch_info(self):
        """Load batch information"""
        if self.batch_id:
            query = f"""
            SELECT 
                b.id, b.batch, b.location, b.start_date, b.enddate,
                c.title as course_name,
                cnt.country as country_name,
                b.batch_status_id
            FROM batch b
            LEFT JOIN course c ON b.course_id = c.id
            LEFT JOIN country cnt ON b.country_id = cnt.id
            WHERE b.id = {self.batch_id}
            """
        elif self.batch_name:
            query = f"""
            SELECT 
                b.id, b.batch, b.location, b.start_date, b.enddate,
                c.title as course_name,
                cnt.country as country_name,
                b.batch_status_id
            FROM batch b
            LEFT JOIN course c ON b.course_id = c.id
            LEFT JOIN country cnt ON b.country_id = cnt.id
            WHERE b.batch = '{self.batch_name}'
            """
        else:
            # Get most recent batch
            query = """
            SELECT 
                b.id, b.batch, b.location, b.start_date, b.enddate,
                c.title as course_name,
                cnt.country as country_name,
                b.batch_status_id
            FROM batch b
            LEFT JOIN course c ON b.course_id = c.id
            LEFT JOIN country cnt ON b.country_id = cnt.id
            ORDER BY b.start_date DESC
            LIMIT 1
            """
        
        try:
            df = self.execute_query(query)
            if not df.empty:
                self.batch_info = df.iloc[0].to_dict()
                self.batch_id = self.batch_info['id']
                self.batch_name = self.batch_info['batch']
                print(f"✅ Loaded batch: {self.batch_name}")
        except Exception as e:
            print(f"⚠️ Error loading batch info: {e}")
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate all batch detail sheets"""
        
        if not self.batch_id and not self.batch_name:
            self._load_batch_info()
        
        if not self.batch_id:
            return {'error': pd.DataFrame({'Error': ['No batch selected']})}
        
        results = {}
        
        # 1. Executive Summary
        results['executive_summary'] = self._get_executive_summary()
        
        # 2. Batch Information
        results['batch_information'] = self._get_batch_information()
        
        # 3. Participant List
        results['participant_list'] = self._get_participant_list()
        
        # 4. Participant Performance
        results['participant_performance'] = self._get_participant_performance()
        
        # 5. Attendance Details
        results['attendance_details'] = self._get_attendance_details()
        
        # 6. Attendance Summary
        results['attendance_summary'] = self._get_attendance_summary()
        
        # 7. Module Progress
        results['module_progress'] = self._get_module_progress()
        
        # 8. Assignment Status
        results['assignment_status'] = self._get_assignment_status()
        
        # 9. Assignment Grades
        results['assignment_grades'] = self._get_assignment_grades()
        
        # 10. Survey Responses
        results['survey_responses'] = self._get_survey_responses()
        
        # 11. Daily Updates
        results['daily_updates'] = self._get_daily_updates()
        
        # 12. Timetable/Sessions
        results['timetable'] = self._get_timetable()
        
        # 13. Trainers & Mentors
        results['trainers_mentors'] = self._get_trainers_mentors()
        
        # 14. Batch Comparisons
        results['batch_comparisons'] = self._get_batch_comparisons()
        
        return results
    
    def _get_executive_summary(self) -> pd.DataFrame:
        """Get executive summary with key metrics"""
        query = f"""
        WITH stats AS (
            SELECT 
                COUNT(DISTINCT e.id) as total_enrolled,
                COUNT(DISTINCT CASE WHEN e.role = 'MTT' THEN e.id END) as mtt_count,
                COUNT(DISTINCT CASE WHEN e.role = 'trainer' THEN e.id END) as trainer_count,
                COUNT(DISTINCT p.id) as unique_participants,
                COUNT(DISTINCT a.id) as total_attendance_records,
                SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) as total_present,
                COUNT(DISTINCT asub.id) as total_submissions,
                COUNT(DISTINCT CASE WHEN ss.submissionstatus = 'Approved' THEN asub.id END) as approved_submissions,
                COUNT(DISTINCT m.id) as total_modules,
                COUNT(DISTINCT bm.id) as assigned_modules
            FROM batch b
            LEFT JOIN enrollment e ON b.id = e.batch
            LEFT JOIN person p ON e.student = p.id
            LEFT JOIN attendance a ON e.id = a.enrollment
            LEFT JOIN assignmentsubmission asub ON e.id = asub.enrollment
            LEFT JOIN submissionstatus ss ON asub.submissionstatus = ss.id
            LEFT JOIN batchmodule bm ON b.id = bm.batchid
            LEFT JOIN module m ON bm.moduleid = m.id
            WHERE b.id = {self.batch_id}
        )
        SELECT 
            'Total Enrolled' as metric,
            total_enrolled as value
        FROM stats
        UNION ALL SELECT 'MTTs', mtt_count FROM stats
        UNION ALL SELECT 'Trainers', trainer_count FROM stats
        UNION ALL SELECT 'Unique Participants', unique_participants FROM stats
        UNION ALL SELECT 'Total Attendance Records', total_attendance_records FROM stats
        UNION ALL SELECT 'Present Count', total_present FROM stats
        UNION ALL SELECT 'Attendance Rate', 
            ROUND(100.0 * total_present / NULLIF(total_attendance_records, 0), 1) FROM stats
        UNION ALL SELECT 'Total Submissions', total_submissions FROM stats
        UNION ALL SELECT 'Approved Submissions', approved_submissions FROM stats
        UNION ALL SELECT 'Approval Rate', 
            ROUND(100.0 * approved_submissions / NULLIF(total_submissions, 0), 1) FROM stats
        UNION ALL SELECT 'Total Modules', total_modules FROM stats
        UNION ALL SELECT 'Assigned Modules', assigned_modules FROM stats
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_batch_information(self) -> pd.DataFrame:
        """Get basic batch information"""
        query = f"""
        SELECT 
            b.batch as "Batch Name",
            b.location as "Location",
            TO_CHAR(b.start_date, 'YYYY-MM-DD') as "Start Date",
            TO_CHAR(b.enddate, 'YYYY-MM-DD') as "End Date",
            EXTRACT(DAY FROM (b.enddate - b.start_date)) + 1 as "Duration (Days)",
            c.title as "Course Name",
            cnt.country as "Country",
            bs.status as "Batch Status",
            CASE 
                WHEN b.enddate < CURRENT_DATE THEN 'Completed'
                WHEN b.start_date > CURRENT_DATE THEN 'Upcoming'
                ELSE 'Ongoing'
            END as "Current Status"
        FROM batch b
        LEFT JOIN course c ON b.course_id = c.id
        LEFT JOIN country cnt ON b.country_id = cnt.id
        LEFT JOIN batchstatus bs ON b.batch_status_id = bs.id
        WHERE b.id = {self.batch_id}
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_participant_list(self) -> pd.DataFrame:
        """Get all participants with their details"""
        query = f"""
        SELECT 
            p.id as "Person ID",
            p.firstname as "First Name",
            p.lastname as "Last Name",
            p.email as "Email",
            p.phone as "Phone",
            p.gender as "Gender",
            cnt.country as "Country",
            p.state as "State",
            p.region as "Region",
            p.enrollmentdate as "Enrollment Date",
            e.role as "Role",
            TO_CHAR(p.date_of_joining, 'YYYY-MM-DD') as "Date of Joining",
            p.reasonofleaving as "Reason for Leaving"
        FROM enrollment e
        JOIN person p ON e.student = p.id
        LEFT JOIN country cnt ON p.country_id = cnt.id
        WHERE e.batch = {self.batch_id}
        ORDER BY e.role, p.firstname, p.lastname
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_participant_performance(self) -> pd.DataFrame:
        """Get individual participant performance metrics"""
        query = f"""
        SELECT 
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant Name",
            e.role as "Role",
            COUNT(DISTINCT a.id) as "Total Sessions",
            SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) as "Present",
            ROUND(100.0 * SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) as "Attendance %",
            COUNT(DISTINCT asub.id) as "Assignments Submitted",
            COUNT(DISTINCT CASE WHEN ss.submissionstatus = 'Approved' THEN asub.id END) as "Assignments Approved",
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN ss.submissionstatus = 'Approved' THEN asub.id END) / NULLIF(COUNT(DISTINCT asub.id), 0), 1) as "Approval Rate",
            ROUND(AVG(CAST(asub.score AS FLOAT)), 1) as "Average Score"
        FROM enrollment e
        JOIN person p ON e.student = p.id
        LEFT JOIN attendance a ON e.id = a.enrollment
        LEFT JOIN assignmentsubmission asub ON e.id = asub.enrollment
        LEFT JOIN submissionstatus ss ON asub.submissionstatus = ss.id
        WHERE e.batch = {self.batch_id}
        GROUP BY p.firstname, p.lastname, e.role
        ORDER BY "Attendance %" DESC, "Approval Rate" DESC
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_attendance_details(self) -> pd.DataFrame:
        """Get detailed attendance records"""
        query = f"""
        SELECT 
            TO_CHAR(a.date, 'YYYY-MM-DD') as "Date",
            m.module as "Module",
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant",
            e.role as "Role",
            CASE WHEN a.ispresent = true THEN 'Present' ELSE 'Absent' END as "Status"
        FROM attendance a
        JOIN enrollment e ON a.enrollment = e.id
        JOIN person p ON e.student = p.id
        JOIN module m ON a.module = m.id
        WHERE e.batch = {self.batch_id}
        ORDER BY a.date, m.module, p.firstname
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_attendance_summary(self) -> pd.DataFrame:
        """Get attendance summary by participant and module"""
        query = f"""
        SELECT 
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant Name",
            m.module as "Module",
            COUNT(a.id) as "Total Sessions",
            SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) as "Present",
            ROUND(100.0 * SUM(CASE WHEN a.ispresent = true THEN 1 ELSE 0 END) / NULLIF(COUNT(a.id), 0), 1) as "Attendance %"
        FROM enrollment e
        JOIN person p ON e.student = p.id
        JOIN attendance a ON e.id = a.enrollment
        JOIN module m ON a.module = m.id
        WHERE e.batch = {self.batch_id}
        GROUP BY p.firstname, p.lastname, m.module
        ORDER BY p.firstname, m.module
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_module_progress(self) -> pd.DataFrame:
        """Get module completion progress"""
        query = f"""
        SELECT 
            m.module as "Module Name",
            m.description as "Description",
            COUNT(DISTINCT e.id) as "Total Enrolled",
            COUNT(DISTINCT a.id) as "Attendance Records",
            COUNT(DISTINCT CASE WHEN a.ispresent = true THEN e.id END) as "Attended Count",
            ROUND(100.0 * COUNT(DISTINCT CASE WHEN a.ispresent = true THEN e.id END) / NULLIF(COUNT(DISTINCT e.id), 0), 1) as "Completion %"
        FROM batchmodule bm
        JOIN module m ON bm.moduleid = m.id
        LEFT JOIN enrollment e ON bm.batchid = e.batch
        LEFT JOIN attendance a ON e.id = a.enrollment AND a.module = m.id
        WHERE bm.batchid = {self.batch_id}
        GROUP BY m.module, m.description
        ORDER BY bm.id
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_assignment_status(self) -> pd.DataFrame:
        """Get assignment submission status"""
        query = f"""
        SELECT 
            a.assignment as "Assignment Name",
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant Name",
            ss.submissionstatus as "Status",
            TO_CHAR(asub.submissiondate, 'YYYY-MM-DD') as "Submission Date",
            asub.comment as "Feedback",
            asub.file_url as "File URL"
        FROM assignmentsubmission asub
        JOIN enrollment e ON asub.enrollment = e.id
        JOIN person p ON e.student = p.id
        LEFT JOIN assignment a ON asub.assignment = a.id
        LEFT JOIN submissionstatus ss ON asub.submissionstatus = ss.id
        WHERE e.batch = {self.batch_id}
        ORDER BY a.assignment, p.firstname
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_assignment_grades(self) -> pd.DataFrame:
        """Get graded assignments with scores"""
        query = f"""
        SELECT 
            a.assignment as "Assignment Name",
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant Name",
            asub.score as "Score",
            ss.submissionstatus as "Status",
            asub.comment as "Feedback"
        FROM assignmentsubmission asub
        JOIN enrollment e ON asub.enrollment = e.id
        JOIN person p ON e.student = p.id
        LEFT JOIN assignment a ON asub.assignment = a.id
        LEFT JOIN submissionstatus ss ON asub.submissionstatus = ss.id
        WHERE e.batch = {self.batch_id}
          AND asub.score IS NOT NULL
        ORDER BY a.assignment, asub.score DESC
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_survey_responses(self) -> pd.DataFrame:
        """Get all survey responses for this batch"""
        query = f"""
        SELECT 
            s.survey as "Survey Name",
            s.survey_type as "Survey Type",
            p.firstname || ' ' || COALESCE(p.lastname, '') as "Participant Name",
            r.role as "Respondent Role",
            r.linkcomment as "Comment",
            r.batchid as "Batch ID"
        FROM response r
        LEFT JOIN survey s ON r.survey = s.id
        LEFT JOIN person p ON r.participant = p.id
        WHERE r.batchid = {self.batch_id}
        ORDER BY s.survey, p.firstname
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_daily_updates(self) -> pd.DataFrame:
        """Get daily updates/session details"""
        query = f"""
        SELECT 
            TO_CHAR(du.date, 'YYYY-MM-DD') as "Date",
            du.description as "Daily Update",
            m.module as "Module",
            COUNT(DISTINCT du.id) as "Total Updates"
        FROM dailyupdate du
        LEFT JOIN module m ON du.module = m.id
        WHERE du.batch = {self.batch_id}
        GROUP BY du.date, du.description, m.module
        ORDER BY du.date DESC
        LIMIT 100
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_timetable(self) -> pd.DataFrame:
        """Get timetable/sessions for this batch"""
        query = f"""
        SELECT 
            TO_CHAR(s.date, 'YYYY-MM-DD') as "Date",
            m.module as "Module",
            s.session as "Session Name",
            s.start_time as "Start Time",
            s.end_time as "End Time",
            t.name as "Trainer Name"
        FROM sessions s
        LEFT JOIN module m ON s.module = m.id
        LEFT JOIN trainer t ON s.trainer = t.id
        WHERE s.batch = {self.batch_id}
        ORDER BY s.date, s.start_time
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_trainers_mentors(self) -> pd.DataFrame:
        """Get trainers and mentors for this batch"""
        query = f"""
        SELECT 
            'Trainer' as "Type",
            t.name as "Name",
            t.email as "Email",
            t.phone as "Phone"
        FROM batchtrainer bt
        JOIN trainer t ON bt.trainer = t.id
        WHERE bt.batch = {self.batch_id}
        UNION ALL
        SELECT 
            'Mentor' as "Type",
            m.name as "Name",
            m.email as "Email",
            m.phone as "Phone"
        FROM batchmentor bm
        JOIN mentor m ON bm.mentor = m.id
        WHERE bm.batch = {self.batch_id}
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def _get_batch_comparisons(self) -> pd.DataFrame:
        """Compare this batch with other similar batches"""
        query = f"""
        WITH this_batch AS (
            SELECT 
                b.batch,
                b.start_date,
                COUNT(DISTINCT e.id) as enrollments,
                COUNT(DISTINCT a.id) as attendance_records,
                COUNT(DISTINCT asub.id) as submissions
            FROM batch b
            LEFT JOIN enrollment e ON b.id = e.batch
            LEFT JOIN attendance a ON e.id = a.enrollment
            LEFT JOIN assignmentsubmission asub ON e.id = asub.enrollment
            WHERE b.id = {self.batch_id}
            GROUP BY b.batch, b.start_date
        ),
        other_batches AS (
            SELECT 
                b.batch,
                b.start_date,
                COUNT(DISTINCT e.id) as enrollments,
                COUNT(DISTINCT a.id) as attendance_records,
                COUNT(DISTINCT asub.id) as submissions
            FROM batch b
            LEFT JOIN enrollment e ON b.id = e.batch
            LEFT JOIN attendance a ON e.id = a.enrollment
            LEFT JOIN assignmentsubmission asub ON e.id = asub.enrollment
            WHERE b.id != {self.batch_id}
              AND b.course_id = (SELECT course_id FROM batch WHERE id = {self.batch_id})
            GROUP BY b.batch, b.start_date
            ORDER BY b.start_date DESC
            LIMIT 5
        )
        SELECT * FROM this_batch
        UNION ALL
        SELECT * FROM other_batches
        """
        
        try:
            df = self.execute_query(query)
            return df
        except Exception as e:
            return pd.DataFrame({'Error': [str(e)]})
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'executive_summary': '1. Executive Summary',
            'batch_information': '2. Batch Information',
            'participant_list': '3. Participant List',
            'participant_performance': '4. Participant Performance',
            'attendance_details': '5. Attendance Details',
            'attendance_summary': '6. Attendance Summary',
            'module_progress': '7. Module Progress',
            'assignment_status': '8. Assignment Status',
            'assignment_grades': '9. Assignment Grades',
            'survey_responses': '10. Survey Responses',
            'daily_updates': '11. Daily Updates',
            'timetable': '12. Timetable/Sessions',
            'trainers_mentors': '13. Trainers & Mentors',
            'batch_comparisons': '14. Batch Comparisons'
        }


# Convenience function to generate batch report from command line
def generate_batch_report(db_manager, batch_id=None, batch_name=None, output_dir="./output/reports/LMS"):
    """Generate a batch report with proper filename"""
    from pathlib import Path
    from datetime import datetime
    
    report = BatchDetailReport(db_manager, batch_id=batch_id, batch_name=batch_name)
    report._load_batch_info()
    
    if not report.batch_info:
        print("❌ Batch not found!")
        return None
    
    # Generate filename with batch name and start date
    batch_name_clean = report.batch_name.replace('/', '_').replace(' ', '_')
    start_date = report.batch_info.get('start_date')
    if start_date:
        start_date_str = pd.to_datetime(start_date).strftime('%Y%m%d')
    else:
        start_date_str = datetime.now().strftime('%Y%m%d')
    
    filename = f"{batch_name_clean}_{start_date_str}_Batch_Report.xlsx"
    output_path = Path(output_dir) / filename
    
    # Generate the report
    data = report.generate()
    
    # Save to Excel
    from utils.excel_formatter import ExcelFormatter
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in data.items():
            sheet_display = report.get_sheet_names().get(sheet_name, sheet_name)
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_display[:31], index=False)
                if sheet_display[:31] in writer.sheets:
                    ExcelFormatter.format_worksheet(writer.sheets[sheet_display[:31]])
    
    print(f"✅ Batch report generated: {output_path}")
    return output_path
