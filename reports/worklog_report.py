"""
Worklog Report - Translation work tracking
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport

class WorklogReport(BaseReport):
    """Worklog Report - Translation work tracking"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['role', 'stage', 'software', 'project_type']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate worklog report"""
        
        query = """
        SELECT 
            w.id,
            w."projectId",
            p.name as project_name,
            p."projectType" as project_type,
            w.role,
            w."userId",
            u.username,
            u.email,
            w."startDate",
            w."endDate",
            w.description,
            w."translationSoftware",
            w."bookNo",
            w."startChapter",
            w."startVerse",
            w."endChapter",
            w."endVerse",
            w."noWork",
            w.stage,
            w."obsStartChapter",
            w."obsEndChapter",
            w."obsStartPara",
            w."obsEndPara",
            w."literatureGenre",
            w."createdAt",
            w."updatedAt"
        FROM worklogs w
        LEFT JOIN users u ON w."userId" = u.id
        LEFT JOIN projects p ON w."projectId" = p.id
        WHERE 1=1
        """
        
        params = {}
        param_count = 0
        
        if 'role' in self.filters:
            param_count += 1
            query += f" AND w.role = %(role_{param_count})s"
            params[f"role_{param_count}"] = self.filters['role']
        
        if 'stage' in self.filters:
            param_count += 1
            query += f" AND w.stage = %(stage_{param_count})s"
            params[f"stage_{param_count}"] = self.filters['stage']
        
        if 'software' in self.filters:
            param_count += 1
            query += f" AND w.\"translationSoftware\" = %(software_{param_count})s"
            params[f"software_{param_count}"] = self.filters['software']
        
        query += " ORDER BY w.\"startDate\" DESC LIMIT 5000"
        
        try:
            worklog_df = self.execute_query(query, params)
            print(f"✅ Retrieved {len(worklog_df)} worklog records")
            
            if not worklog_df.empty:
                worklog_df['startDate'] = pd.to_datetime(worklog_df['startDate'])
                worklog_df['endDate'] = pd.to_datetime(worklog_df['endDate'])
                worklog_df['days_worked'] = (worklog_df['endDate'] - worklog_df['startDate']).dt.days + 1
        except Exception as e:
            print(f"❌ Worklog query failed: {e}")
            worklog_df = pd.DataFrame({'Error': [str(e)]})
        
        # Role summary
        if not worklog_df.empty and 'Error' not in worklog_df.columns:
            role_summary = worklog_df.groupby(['role']).agg({
                'id': 'count',
                'days_worked': 'sum'
            }).reset_index()
            role_summary.columns = ['Role', 'Work Sessions', 'Total Days']
            role_summary = role_summary.sort_values('Work Sessions', ascending=False)
        else:
            role_summary = pd.DataFrame()
        
        return {
            'worklog_details': worklog_df,
            'role_summary': role_summary
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'worklog_details': 'Worklog Details',
            'role_summary': 'Role Summary'
        }