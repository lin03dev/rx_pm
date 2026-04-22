"""
User Report - User management and assignments
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport

class UserReport(BaseReport):
    """User Report - Complete user management information"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['role', 'country']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate user report"""
        
        query = """
        SELECT 
            u.id as user_id,
            u.username,
            u.email,
            u.role::text as user_role,
            u.name as display_name,
            u."createdAt",
            p."firstName",
            p."lastName",
            p."firstName" || ' ' || COALESCE(p."lastName", '') as full_name,
            p.phone,
            p.gender,
            p.state,
            c.name as country,
            c."countryCode" as country_code
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE 1=1
        """
        
        params = {}
        param_count = 0
        
        if 'role' in self.filters and self.filters['role']:
            param_count += 1
            query += f" AND u.role::text = %(role_{param_count})s"
            params[f"role_{param_count}"] = self.filters['role']
        
        if 'country' in self.filters and self.filters['country']:
            param_count += 1
            query += f" AND c.name = %(country_{param_count})s"
            params[f"country_{param_count}"] = self.filters['country']
        
        query += " ORDER BY c.name, u.username"
        
        try:
            user_df = self.execute_query(query, params)
            print(f"✅ Retrieved {len(user_df)} users")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            user_df = pd.DataFrame({'Error': [str(e)]})
        
        # Role summary
        if not user_df.empty and 'Error' not in user_df.columns:
            role_summary = user_df.groupby(['user_role']).agg({
                'user_id': 'count'
            }).reset_index()
            role_summary.columns = ['Role', 'Count']
            role_summary = role_summary.sort_values('Count', ascending=False)
        else:
            role_summary = pd.DataFrame()
        
        return {
            'user_details': user_df,
            'role_summary': role_summary
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'user_details': 'User Details',
            'role_summary': 'Role Summary'
        }