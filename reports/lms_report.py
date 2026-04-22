"""
LMS Report - Learning Management System reports for Telios
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport


class LMSReport(BaseReport):
    """LMS Report - Course enrollment, attendance, and survey analytics"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['course_id', 'batch_id', 'country', 'role']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate comprehensive LMS reports"""
        
        results = {}
        
        # First, check if tables exist and have data
        try:
            # Check if batch table exists and has data
            check_query = "SELECT COUNT(*) as count FROM batch"
            count_df = self.execute_query(check_query)
            has_data = count_df['count'].iloc[0] > 0 if not count_df.empty else False
            
            if not has_data:
                print("⚠️ No data found in LMS tables")
                results['batch_summary'] = pd.DataFrame({'Message': ['No batch data available']})
                results['enrollments'] = pd.DataFrame({'Message': ['No enrollment data available']})
                results['attendance'] = pd.DataFrame({'Message': ['No attendance data available']})
                results['summary_stats'] = pd.DataFrame({'Message': ['No data available']})
                return results
        except Exception as e:
            print(f"⚠️ LMS tables may not exist: {e}")
            results['batch_summary'] = pd.DataFrame({'Message': ['LMS tables not found or empty']})
            results['enrollments'] = pd.DataFrame({'Message': ['LMS tables not found or empty']})
            results['attendance'] = pd.DataFrame({'Message': ['LMS tables not found or empty']})
            results['summary_stats'] = pd.DataFrame({'Message': ['LMS tables not found or empty']})
            return results
        
        # 1. Batch Summary (using correct column names)
        try:
            # First get column names from batch table
            columns_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'batch'
            """
            columns_df = self.execute_query(columns_query)
            batch_columns = columns_df['column_name'].tolist() if not columns_df.empty else []
            print(f"Batch table columns: {batch_columns}")
            
            # Build query dynamically based on available columns
            select_fields = ["b.id as batch_id", "b.batch as batch_name"]
            
            if 'location' in batch_columns:
                select_fields.append("b.location")
            if 'startdate' in batch_columns or 'startDate' in batch_columns:
                date_field = 'startdate' if 'startdate' in batch_columns else '"startDate"'
                select_fields.append(f"b.{date_field} as start_date")
            if 'enddate' in batch_columns or 'endDate' in batch_columns:
                date_field = 'enddate' if 'enddate' in batch_columns else '"endDate"'
                select_fields.append(f"b.{date_field} as end_date")
            
            batch_query = f"""
            SELECT 
                {', '.join(select_fields)},
                COUNT(DISTINCT e.id) as total_enrollments
            FROM batch b
            LEFT JOIN enrollment e ON b.id = e.batch
            GROUP BY b.id, b.batch
            ORDER BY b.batch
            """
            
            results['batch_summary'] = self.execute_query(batch_query)
            print(f"✅ Batch summary: {len(results['batch_summary'])} rows")
        except Exception as e:
            print(f"⚠️ Batch query: {e}")
            results['batch_summary'] = pd.DataFrame({'Error': [str(e)]})
        
        # 2. Enrollments
        try:
            enrollment_query = """
            SELECT 
                b.batch as batch_name,
                e.role,
                COUNT(e.id) as enrollment_count
            FROM enrollment e
            LEFT JOIN batch b ON e.batch = b.id
            GROUP BY b.batch, e.role
            ORDER BY b.batch, e.role
            """
            results['enrollments'] = self.execute_query(enrollment_query)
            print(f"✅ Enrollments: {len(results['enrollments'])} rows")
        except Exception as e:
            print(f"⚠️ Enrollment query: {e}")
            results['enrollments'] = pd.DataFrame({'Error': [str(e)]})
        
        # 3. Summary Statistics
        summary_data = []
        if not results['batch_summary'].empty and 'Error' not in results['batch_summary'].columns:
            summary_data.append({'Metric': 'Total Batches', 'Value': len(results['batch_summary'])})
            summary_data.append({'Metric': 'Total Enrollments', 'Value': results['batch_summary']['total_enrollments'].sum() if 'total_enrollments' in results['batch_summary'].columns else 0})
        
        if not results['enrollments'].empty and 'Error' not in results['enrollments'].columns:
            summary_data.append({'Metric': 'Unique Roles', 'Value': results['enrollments']['role'].nunique() if 'role' in results['enrollments'].columns else 0})
        
        results['summary_stats'] = pd.DataFrame(summary_data) if summary_data else pd.DataFrame({'Message': ['No summary data available']})
        
        return results
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'batch_summary': 'Batch Summary',
            'enrollments': 'Enrollments',
            'attendance': 'Attendance',
            'summary_stats': 'Summary Statistics'
        }
