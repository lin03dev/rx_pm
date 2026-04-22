"""
Individual Performance Report - Track assigned vs completed work per person
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport


class IndividualPerformanceReport(BaseReport):
    """Individual Performance Report - Track assigned vs completed work for each person"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['user_id', 'username', 'role', 'country', 'language']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate comprehensive individual performance report"""
        
        # 1. Get all users with person details - properly join to get actual names
        users_query = """
        SELECT 
            u.id as user_id,
            u.username,
            u.email,
            u.role::text as user_role,
            p."firstName",
            p."lastName",
            CASE 
                WHEN p."firstName" IS NOT NULL AND p."firstName" != '' 
                     AND p."lastName" IS NOT NULL AND p."lastName" != ''
                THEN p."firstName" || ' ' || p."lastName"
                ELSE u.username
            END as full_name,
            p.phone,
            p.gender,
            p.state,
            c.name as country,
            c."countryCode" as country_code
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE u.role::text != 'SUPER_ADMIN'
        ORDER BY c.name, p."firstName", p."lastName"
        """
        
        try:
            users_df = self.execute_query(users_query)
            print(f"✅ Retrieved {len(users_df)} users")
        except Exception as e:
            print(f"❌ Users query failed: {e}")
            users_df = pd.DataFrame()
        
        # 2. Get assignments with project details
        assignments_query = """
        SELECT 
            u.id as user_id,
            u.username,
            u.role::text as user_role,
            utp."projectId",
            p.name as project_name,
            p."projectType",
            p.stage as project_stage,
            l.name as language_name,
            l."isoCode" as language_code,
            utp.role as project_role,
            utp.verses,
            utp."obsChapters",
            utp."literatureGenres",
            array_length(string_to_array(COALESCE(utp.verses, ''), ','), 1) as verses_assigned_count,
            array_length(string_to_array(COALESCE(utp."obsChapters", ''), ','), 1) as obs_assigned_count,
            array_length(string_to_array(COALESCE(utp."literatureGenres", ''), ','), 1) as literature_assigned_count
        FROM users_to_projects utp
        LEFT JOIN users u ON utp."userId" = u.id
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        WHERE utp.verses IS NOT NULL 
           OR utp."obsChapters" IS NOT NULL 
           OR utp."literatureGenres" IS NOT NULL
        ORDER BY u.username, p.name
        """
        
        try:
            assignments_df = self.execute_query(assignments_query)
            print(f"✅ Retrieved {len(assignments_df)} assignment records")
        except Exception as e:
            print(f"❌ Assignments query failed: {e}")
            assignments_df = pd.DataFrame()
        
        # 3. Individual summary with proper full names
        individual_summary = []
        
        if not users_df.empty:
            for _, user in users_df.iterrows():
                user_id = user['user_id']
                username = user.get('username', '')
                full_name = user.get('full_name', username)
                user_role = user.get('user_role', 'USER')
                
                user_assignments = assignments_df[assignments_df['user_id'] == user_id] if not assignments_df.empty else pd.DataFrame()
                
                individual_summary.append({
                    'User ID': user_id,
                    'Username': username,
                    'Full Name': full_name,
                    'Role': user_role,
                    'Email': user.get('email', ''),
                    'Phone': user.get('phone', ''),
                    'Gender': user.get('gender', ''),
                    'State': user.get('state', ''),
                    'Country': user.get('country', ''),
                    'Country Code': user.get('country_code', ''),
                    'Total Projects Assigned': len(user_assignments) if not user_assignments.empty else 0,
                    'Total Verses Assigned': int(user_assignments['verses_assigned_count'].fillna(0).sum()) if not user_assignments.empty else 0,
                    'Total OBS Chapters Assigned': int(user_assignments['obs_assigned_count'].fillna(0).sum()) if not user_assignments.empty else 0,
                    'Total Literature Genres Assigned': int(user_assignments['literature_assigned_count'].fillna(0).sum()) if not user_assignments.empty else 0
                })
        
        individual_summary_df = pd.DataFrame(individual_summary)
        if not individual_summary_df.empty:
            individual_summary_df = individual_summary_df[individual_summary_df['Total Projects Assigned'] > 0]
        
        # 4. Summary statistics
        summary_stats = []
        
        if not individual_summary_df.empty:
            summary_stats.append({'Metric': 'Total Users with Assignments', 'Value': len(individual_summary_df)})
            summary_stats.append({'Metric': 'Total Bible Verses Assigned', 'Value': int(individual_summary_df['Total Verses Assigned'].sum())})
            summary_stats.append({'Metric': 'Total OBS Chapters Assigned', 'Value': int(individual_summary_df['Total OBS Chapters Assigned'].sum())})
            summary_stats.append({'Metric': 'Total Literature Genres Assigned', 'Value': int(individual_summary_df['Total Literature Genres Assigned'].sum())})
        
        summary_stats_df = pd.DataFrame(summary_stats)
        
        return {
            'individual_summary': individual_summary_df,
            'summary_stats': summary_stats_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'individual_summary': '1. Individual Summary',
            'summary_stats': '2. Summary Statistics'
        }
