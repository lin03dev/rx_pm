"""
User Activity Report - Tracks user details, Autographa ID, start date, and last use date
Shows project-specific roles (MTT, QC, ICT, etc.) from users_to_projects
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any
from reports.base_report import BaseReport


class UserActivityReport(BaseReport):
    """User Activity Report - User details with project roles (MTT, QC, ICT, etc.)"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['role', 'country', 'has_activity']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate user activity report with project roles"""
        
        # ============================================================
        # Main Query: Users with their details and activity
        # Uses string_agg with proper casting for PostgreSQL
        # ============================================================
        query = """
        SELECT 
            -- User Information
            u.id as user_id,
            u.username as autographa_id,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            u."createdAt" as start_date,
            u."updatedAt" as last_updated,
            
            -- Project-specific roles (from users_to_projects) - cast to text
            STRING_AGG(DISTINCT utp.role::text, ', ') as project_roles,
            
            -- Person Information
            p."firstName",
            p."lastName",
            p.phone,
            p.gender,
            p.state,
            
            -- Country Information
            c.name as country,
            c."countryCode" as country_code,
            
            -- Language Information (from projects they are assigned to)
            STRING_AGG(DISTINCT l.name::text, ', ') as languages,
            
            -- Project names they are assigned to
            STRING_AGG(DISTINCT pj.name::text, ', ') as project_names,
            
            -- Last activity from worklogs
            (
                SELECT MAX(w."endDate") 
                FROM worklogs w 
                WHERE w."userId" = u.id AND w."noWork" = false
            ) as last_use_date,
            
            -- First activity date
            (
                SELECT MIN(w."startDate") 
                FROM worklogs w 
                WHERE w."userId" = u.id AND w."noWork" = false
            ) as first_use_date,
            
            -- Worklog statistics
            (
                SELECT COUNT(*) 
                FROM worklogs w 
                WHERE w."userId" = u.id AND w."noWork" = false
            ) as total_work_sessions,
            
            -- Projects assigned count
            COUNT(DISTINCT utp."projectId") as projects_assigned_count
            
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users_to_projects utp ON u.id = utp."userId"
        LEFT JOIN projects pj ON utp."projectId" = pj.id
        LEFT JOIN languages l ON pj."languageId" = l.id
        WHERE u.role::text != 'SUPER_ADMIN'
        GROUP BY u.id, u.username, u.name, u.email, u."createdAt", u."updatedAt", 
                 p."firstName", p."lastName", p.phone, p.gender, p.state,
                 c.name, c."countryCode"
        ORDER BY u."createdAt" DESC
        """
        
        try:
            df = self.execute_query(query)
            print(f"✅ Retrieved {len(df)} users")
        except Exception as e:
            print(f"❌ Query failed: {e}")
            df = pd.DataFrame()
        
        # Clean up and format the data
        if not df.empty:
            # Format dates
            df['start_date'] = pd.to_datetime(df['start_date']).dt.strftime('%Y-%m-%d')
            
            # Handle last_use_date
            df['last_use_date'] = pd.to_datetime(df['last_use_date']).dt.strftime('%Y-%m-%d') if df['last_use_date'].notna().any() else df['last_use_date']
            df['first_use_date'] = pd.to_datetime(df['first_use_date']).dt.strftime('%Y-%m-%d') if df['first_use_date'].notna().any() else df['first_use_date']
            df['last_updated'] = pd.to_datetime(df['last_updated']).dt.strftime('%Y-%m-%d')
            
            # Handle nulls
            df['last_use_date'] = df['last_use_date'].fillna('Never used')
            df['first_use_date'] = df['first_use_date'].fillna('Never used')
            df['languages'] = df['languages'].fillna('None assigned')
            df['project_roles'] = df['project_roles'].fillna('No role assigned')
            df['project_names'] = df['project_names'].fillna('No projects')
            df['total_work_sessions'] = df['total_work_sessions'].fillna(0).astype(int)
            df['projects_assigned_count'] = df['projects_assigned_count'].fillna(0).astype(int)
            df['phone'] = df['phone'].fillna('')
            df['gender'] = df['gender'].fillna('Not specified')
            df['state'] = df['state'].fillna('')
            df['country'] = df['country'].fillna('Not specified')
            
            # Calculate days since last use
            df['days_inactive'] = df.apply(
                lambda row: (datetime.now() - datetime.strptime(row['last_use_date'], '%Y-%m-%d')).days 
                if row['last_use_date'] != 'Never used' else None, axis=1
            )
            
            # Add activity status
            df['activity_status'] = df.apply(
                lambda row: 'Active' if row['total_work_sessions'] > 0 else 'Inactive (No worklogs)',
                axis=1
            )
        
        # ============================================================
        # Sheet 1: All Users (with project roles)
        # ============================================================
        if not df.empty:
            report_df = df[[
                'full_name',
                'languages',
                'project_roles',
                'autographa_id',
                'start_date',
                'last_use_date',
                'total_work_sessions',
                'activity_status',
                'project_names'
            ]].copy()
            
            # Rename columns
            report_df.columns = [
                'Name of the user',
                'Language name',
                'Role (in project)',
                'Autographa id',
                'Start date in Autographa',
                'Last use date in Autographa',
                'Work Sessions',
                'Status',
                'Projects Assigned'
            ]
        else:
            report_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 2: Active Users (with worklogs)
        # ============================================================
        if not df.empty:
            active_df = df[df['total_work_sessions'] > 0][[
                'full_name',
                'languages',
                'project_roles',
                'autographa_id',
                'start_date',
                'first_use_date',
                'last_use_date',
                'total_work_sessions',
                'projects_assigned_count',
                'days_inactive',
                'project_names'
            ]].copy()
            
            active_df.columns = [
                'Name of the user',
                'Language name',
                'Role (in project)',
                'Autographa id',
                'Start date',
                'First use date',
                'Last use date',
                'Work Sessions',
                'Projects Assigned',
                'Days Inactive',
                'Project Names'
            ]
        else:
            active_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 3: Inactive Users (never used)
        # ============================================================
        if not df.empty:
            inactive_df = df[df['total_work_sessions'] == 0][[
                'full_name',
                'languages',
                'project_roles',
                'autographa_id',
                'start_date',
                'projects_assigned_count',
                'project_names'
            ]].copy()
            
            inactive_df.columns = [
                'Name of the user',
                'Language name',
                'Role (in project)',
                'Autographa id',
                'Start date',
                'Projects Assigned',
                'Project Names'
            ]
        else:
            inactive_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 4: Role Distribution
        # ============================================================
        role_distribution = []
        if not df.empty:
            # Split comma-separated roles and count
            all_roles = []
            for roles in df['project_roles']:
                if roles and roles != 'No role assigned':
                    for role in roles.split(', '):
                        all_roles.append(role)
            
            from collections import Counter
            role_counts = Counter(all_roles)
            
            for role, count in role_counts.most_common():
                role_distribution.append({'Role': role, 'User Count': count})
        
        role_df = pd.DataFrame(role_distribution)
        
        # ============================================================
        # Sheet 5: Summary Statistics
        # ============================================================
        summary_data = []
        
        if not df.empty:
            summary_data.append({'Metric': 'Total Users', 'Value': len(df)})
            
            # Active vs Inactive
            active_count = len(df[df['total_work_sessions'] > 0])
            inactive_count = len(df[df['total_work_sessions'] == 0])
            summary_data.append({'Metric': 'Active Users (have worklogs)', 'Value': active_count})
            summary_data.append({'Metric': 'Inactive Users (no worklogs)', 'Value': inactive_count})
            
            # Users who never used Autographa
            never_used = len(df[df['last_use_date'] == 'Never used'])
            summary_data.append({'Metric': 'Never Used Autographa', 'Value': never_used})
            
            # Users with activity in last 30 days
            recently_active = len(df[df['days_inactive'].notna() & (df['days_inactive'] <= 30)])
            summary_data.append({'Metric': 'Active in Last 30 Days', 'Value': recently_active})
            
            # Average work sessions
            avg_sessions = df['total_work_sessions'].mean()
            summary_data.append({'Metric': 'Average Work Sessions per User', 'Value': f"{avg_sessions:.1f}"})
            
            # Users by country
            country_counts = df[df['country'] != 'Not specified']['country'].value_counts().head(10)
            for country, count in country_counts.items():
                summary_data.append({'Metric': f'Users in {country}', 'Value': count})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'all_users': report_df,
            'active_users': active_df,
            'inactive_users': inactive_df,
            'role_distribution': role_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'all_users': '1 - All Users',
            'active_users': '2 - Active Users (with work)',
            'inactive_users': '3 - Inactive Users (no work)',
            'role_distribution': '4 - Role Distribution',
            'summary_stats': '5 - Summary Statistics'
        }
