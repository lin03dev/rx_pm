"""
User Assignment Report - Complete user assignments across all projects
Shows: User details, assigned projects, roles, languages, countries
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport


class UserAssignmentReport(BaseReport):
    """User Assignment Report - Complete user and project assignment details"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['user_id', 'username', 'role', 'country', 'project_type']
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate comprehensive user assignment report"""
        
        # ============================================================
        # Main Query: Users with their assignments and project details
        # ============================================================
        main_query = """
        SELECT 
            -- User Information
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            u.role::text as system_role,
            
            -- Person Information (for gender)
            p.gender,
            
            -- Project Assignment Information
            utp."projectId" as project_id,
            pj.name as project_name,
            pj."projectType" as project_type,
            pj.stage as project_stage,
            utp.role as project_role,
            
            -- Location Information (from Project)
            c.name as country,
            l.name as language_name,
            l."isoCode" as language_code
            
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        LEFT JOIN users_to_projects utp ON u.id = utp."userId"
        LEFT JOIN projects pj ON utp."projectId" = pj.id
        LEFT JOIN countries c ON pj."countryId" = c.id
        LEFT JOIN languages l ON pj."languageId" = l.id
        WHERE u.role::text != 'SUPER_ADMIN'
        ORDER BY u.username, pj.name
        """
        
        try:
            main_df = self.execute_query(main_query)
            print(f"✅ Retrieved {len(main_df)} assignment records")
        except Exception as e:
            print(f"❌ Main query failed: {e}")
            main_df = pd.DataFrame()
        
        # ============================================================
        # 1. User Summary Sheet (One row per user)
        # ============================================================
        user_summary = []
        
        if not main_df.empty:
            for user_id in main_df['user_id'].unique():
                user_data = main_df[main_df['user_id'] == user_id]
                first_row = user_data.iloc[0]
                
                # Get all projects for this user
                projects_list = []
                project_types = set()
                project_roles = set()
                countries = set()
                languages = set()
                
                for _, row in user_data.iterrows():
                    if pd.notna(row.get('project_name')):
                        projects_list.append(f"{row['project_name']} ({row.get('project_role', 'N/A')})")
                        project_types.add(row.get('project_type', 'Unknown'))
                        project_roles.add(row.get('project_role', 'Unknown'))
                        if pd.notna(row.get('country')):
                            countries.add(row['country'])
                        if pd.notna(row.get('language_name')):
                            languages.add(row['language_name'])
                
                user_summary.append({
                    'User ID': user_id,
                    'Username': first_row.get('username', ''),
                    'Full Name': first_row.get('full_name', first_row.get('username', '')),
                    'Email': first_row.get('email', ''),
                    'System Role': first_row.get('system_role', ''),
                    'Gender': first_row.get('gender', 'Not Specified') if pd.notna(first_row.get('gender')) else 'Not Specified',
                    'Countries': ', '.join(sorted(countries)) if countries else 'Not Assigned',
                    'Languages': ', '.join(sorted(languages)) if languages else 'Not Assigned',
                    'Number of Projects': len([p for p in projects_list if p]),
                    'Project Types': ', '.join(sorted(project_types)) if project_types else 'None',
                    'Project Roles': ', '.join(sorted(project_roles)) if project_roles else 'None',
                    'Projects': ' | '.join(projects_list[:10]) + ('...' if len(projects_list) > 10 else '')
                })
        
        user_summary_df = pd.DataFrame(user_summary)
        if not user_summary_df.empty:
            user_summary_df = user_summary_df.sort_values(['Full Name'])
        
        # ============================================================
        # 2. Detailed Assignments Sheet (One row per assignment)
        # ============================================================
        if not main_df.empty:
            detailed_df = main_df[[
                'username', 'full_name', 'email', 'system_role', 'gender',
                'project_name', 'project_type', 'project_stage', 'project_role',
                'country', 'language_name', 'language_code'
            ]].copy()
            
            # Clean up display
            detailed_df['gender'] = detailed_df['gender'].fillna('Not Specified')
            detailed_df['country'] = detailed_df['country'].fillna('Not Specified')
            detailed_df['language_name'] = detailed_df['language_name'].fillna('Not Specified')
            detailed_df['project_stage'] = detailed_df['project_stage'].fillna('Not Specified')
            
            # Rename columns for better display
            detailed_df.columns = [
                'Username', 'Full Name', 'Email', 'System Role', 'Gender',
                'Project Name', 'Project Type', 'Project Stage', 'Project Role',
                'Country', 'Language', 'Language Code'
            ]
        else:
            detailed_df = pd.DataFrame({'Message': ['No data available']})
        
        # ============================================================
        # 3. Users with No Assignments
        # ============================================================
        all_users_query = """
        SELECT 
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            u.role::text as system_role,
            p.gender
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        WHERE u.role::text != 'SUPER_ADMIN'
        ORDER BY u.username
        """
        
        try:
            all_users_df = self.execute_query(all_users_query)
            if not main_df.empty:
                users_with_assignments = set(main_df[main_df['project_id'].notna()]['user_id'].unique())
                no_assignments_df = all_users_df[~all_users_df['user_id'].isin(users_with_assignments)].copy()
                no_assignments_df = no_assignments_df[['user_id', 'username', 'full_name', 'email', 'system_role', 'gender']]
                no_assignments_df['gender'] = no_assignments_df['gender'].fillna('Not Specified')
                no_assignments_df['Status'] = 'No Projects Assigned'
            else:
                no_assignments_df = all_users_df.copy()
                no_assignments_df['gender'] = no_assignments_df['gender'].fillna('Not Specified')
                no_assignments_df['Status'] = 'No Projects Assigned'
            print(f"✅ Found {len(no_assignments_df)} users with no assignments")
        except Exception as e:
            print(f"❌ Users query failed: {e}")
            no_assignments_df = pd.DataFrame()
        
        # ============================================================
        # 4. Summary Statistics
        # ============================================================
        summary_data = []
        
        if not main_df.empty:
            total_users = main_df['user_id'].nunique()
            total_assignments = len(main_df[main_df['project_id'].notna()])
            total_projects = main_df['project_id'].nunique()
            
            summary_data.append({'Metric': 'Total Users', 'Value': total_users})
            summary_data.append({'Metric': 'Total Project Assignments', 'Value': total_assignments})
            summary_data.append({'Metric': 'Total Projects', 'Value': total_projects})
            summary_data.append({'Metric': 'Avg Projects per User', 'Value': round(total_assignments / total_users, 1) if total_users > 0 else 0})
            
            # Role distribution
            if 'project_role' in main_df.columns:
                role_dist = main_df[main_df['project_role'].notna()]['project_role'].value_counts()
                for role, count in role_dist.items():
                    summary_data.append({'Metric': f'  - {role} assignments', 'Value': count})
            
            # Gender distribution
            if 'gender' in main_df.columns:
                gender_dist = main_df[main_df['gender'].notna()]['gender'].value_counts()
                for gender, count in gender_dist.items():
                    if gender and gender != 'None':
                        summary_data.append({'Metric': f'Gender: {gender}', 'Value': count})
            
            # Country distribution (from projects)
            country_dist = main_df[main_df['country'].notna()]['country'].value_counts().head(10)
            for country, count in country_dist.items():
                if country and country != 'None':
                    summary_data.append({'Metric': f'Projects in {country}', 'Value': count})
        
        if not no_assignments_df.empty:
            summary_data.append({'Metric': 'Users with No Assignments', 'Value': len(no_assignments_df)})
        
        summary_df = pd.DataFrame(summary_data)
        
        # ============================================================
        # 5. Project Type Breakdown by User
        # ============================================================
        if not main_df.empty and 'project_type' in main_df.columns:
            project_type_breakdown = main_df[main_df['project_id'].notna()].groupby(
                ['username', 'full_name', 'project_type']
            ).size().reset_index(name='count')
            project_type_breakdown = project_type_breakdown.pivot_table(
                index=['username', 'full_name'],
                columns='project_type',
                values='count',
                fill_value=0
            ).reset_index()
        else:
            project_type_breakdown = pd.DataFrame()
        
        return {
            'user_summary': user_summary_df,
            'detailed_assignments': detailed_df,
            'users_no_assignments': no_assignments_df,
            'project_type_breakdown': project_type_breakdown,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'user_summary': '1. User Summary',
            'detailed_assignments': '2. Detailed Assignments',
            'users_no_assignments': '3. Users with No Projects',
            'project_type_breakdown': '4. Project Type by User',
            'summary_stats': '5. Summary Statistics'
        }
