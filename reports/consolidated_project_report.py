"""
Consolidated Project Report - Combines all project types with proper completion status
"""

import pandas as pd
import json
import re
from typing import Dict, Any, Tuple
from reports.base_report import BaseReport


class ConsolidatedProjectReport(BaseReport):
    """Consolidated Project Report - All project types with completion status"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_type', 'country', 'language']
    
    def _get_project_completion(self, project_id: str, project_type: str) -> Dict[str, Any]:
        """Get overall project completion percentage"""
        try:
            if project_type == 'TEXT_TRANSLATION':
                # Get Bible project completion from chapters
                query = f"""
                SELECT COUNT(DISTINCT ttc.id) as completed
                FROM text_translation_chapters ttc
                JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
                JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
                WHERE tp."projectId" = '{project_id}'
                  AND ttc.version > 1
                """
                df = self.execute_query(query)
                completed = df['completed'].iloc[0] if not df.empty else 0
                # Get total assigned verses
                query2 = f"""
                SELECT SUM(array_length(string_to_array(COALESCE(verses, ''), ','), 1)) as total
                FROM users_to_projects
                WHERE "projectId" = '{project_id}'
                  AND role = 'MTT'
                """
                df2 = self.execute_query(query2)
                total = df2['total'].iloc[0] if not df2.empty else 0
                return {'completion_pct': (completed / total * 100) if total > 0 else 0}
                
            elif project_type == 'OBS':
                query = f"""
                SELECT COUNT(DISTINCT opc."chapterNo") as completed
                FROM obs_project_chapters opc
                JOIN obs_projects op ON opc."obsProjectId" = op.id
                WHERE op."projectId" = '{project_id}'
                  AND opc.version > 1
                """
                df = self.execute_query(query)
                completed = df['completed'].iloc[0] if not df.empty else 0
                query2 = f"""
                SELECT SUM(array_length(string_to_array(COALESCE("obsChapters", ''), ','), 1)) as total
                FROM users_to_projects
                WHERE "projectId" = '{project_id}'
                  AND role = 'MTT'
                """
                df2 = self.execute_query(query2)
                total = df2['total'].iloc[0] if not df2.empty else 0
                return {'completion_pct': (completed / total * 100) if total > 0 else 0}
                
            elif project_type in ['LITERATURE', 'LITERATURE_PROJECT']:
                query = f"""
                SELECT lpg.version
                FROM literature_project_genres_history lpg
                JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
                JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
                WHERE lp."projectId" = '{project_id}'
                  AND lpg.version > 1
                ORDER BY lpg.version DESC
                LIMIT 1
                """
                df = self.execute_query(query)
                has_content = not df.empty
                return {'completion_pct': 100 if has_content else 0}
                
            elif project_type == 'GRAMMAR_PHRASES':
                query = f"""
                SELECT gpc.version
                FROM grammar_phrases_project_contents gpc
                JOIN grammar_phrases_projects gp ON gpc."grammarPhrasesProjectId" = gp.id
                WHERE gp."projectId" = '{project_id}'
                  AND gpc.version > 1
                ORDER BY gpc.version DESC
                LIMIT 1
                """
                df = self.execute_query(query)
                has_content = not df.empty
                return {'completion_pct': 100 if has_content else 0}
                
            elif project_type == 'GRAMMAR_PRONOUNS':
                query = f"""
                SELECT gpc.version
                FROM grammar_pronouns_project_contents gpc
                JOIN grammar_pronouns_projects gp ON gpc."grammarPronounsProjectId" = gp.id
                WHERE gp."projectId" = '{project_id}'
                  AND gpc.version > 1
                ORDER BY gpc.version DESC
                LIMIT 1
                """
                df = self.execute_query(query)
                has_content = not df.empty
                return {'completion_pct': 100 if has_content else 0}
                
            elif project_type == 'GRAMMAR_CONNECTIVES':
                query = f"""
                SELECT gpc.version
                FROM grammar_connectives_project_contents gpc
                JOIN grammar_connectives_projects gp ON gpc."grammarConnectivesProjectId" = gp.id
                WHERE gp."projectId" = '{project_id}'
                  AND gpc.version > 1
                ORDER BY gpc.version DESC
                LIMIT 1
                """
                df = self.execute_query(query)
                has_content = not df.empty
                return {'completion_pct': 100 if has_content else 0}
                
            else:
                return {'completion_pct': 0}
        except Exception as e:
            # Silent fail for individual project errors
            return {'completion_pct': 0}
    
    def _get_status(self, completion_pct: float) -> str:
        """Get status based on completion percentage"""
        if completion_pct >= 100:
            return "✅ Completed"
        elif completion_pct >= 75:
            return "🟢 Almost Complete"
        elif completion_pct >= 50:
            return "🟡 Half Complete"
        elif completion_pct >= 25:
            return "🟠 In Progress"
        elif completion_pct > 0:
            return "🔵 Just Started"
        else:
            return "⚪ Not Started"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate consolidated project report with proper completion status"""
        
        # Get all projects with their basic info
        projects_query = """
        SELECT 
            p.id as project_id,
            p.name as project_name,
            p."projectType" as project_type,
            l.name as language_name,
            c.name as country
        FROM projects p
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE p."projectType" IN ('TEXT_TRANSLATION', 'OBS', 'LITERATURE', 'LITERATURE_PROJECT', 
                                  'GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
        ORDER BY p."projectType", p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # Get MTT assignments per project
        mtt_query = """
        SELECT DISTINCT
            utp."projectId",
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            utp.verses,
            utp."obsChapters",
            utp."literatureGenres"
        FROM users_to_projects utp
        JOIN users u ON utp."userId" = u.id
        WHERE utp.role = 'MTT'
        ORDER BY utp."projectId", u.username
        """
        
        try:
            mtt_df = self.execute_query(mtt_query)
            print(f"✅ Retrieved {len(mtt_df)} MTT assignments")
        except Exception as e:
            print(f"❌ MTT query failed: {e}")
            mtt_df = pd.DataFrame()
        
        # Calculate project completion percentages
        project_completion = {}
        for _, project in projects_df.iterrows():
            project_id = project['project_id']
            project_type = project['project_type']
            completion = self._get_project_completion(project_id, project_type)
            project_completion[project_id] = completion['completion_pct']
        
        # Build Project Summary sheet
        project_summary_data = []
        
        for _, project in projects_df.iterrows():
            project_id = project['project_id']
            project_name = project['project_name']
            project_type = project['project_type']
            language = project['language_name'] or 'N/A'
            country = project['country'] or 'N/A'
            
            # Get MTTs for this project
            project_mtts = mtt_df[mtt_df['projectId'] == project_id]
            mtt_count = len(project_mtts)
            mtt_names = ', '.join(project_mtts['full_name'].unique()) if not project_mtts.empty else 'No MTT Assigned'
            
            completion_pct = project_completion.get(project_id, 0)
            status = self._get_status(completion_pct)
            
            project_summary_data.append({
                'Project Name': project_name,
                'Project Type': project_type,
                'Language': language,
                'Country': country,
                'MTTs Assigned': mtt_count,
                'MTT Names': mtt_names[:500] if len(mtt_names) > 500 else mtt_names,
                'Completion %': round(completion_pct, 1),
                'Status': status
            })
        
        project_summary_df = pd.DataFrame(project_summary_data)
        
        # Build MTT Details sheet with proper status
        mtt_detail_data = []
        
        for _, mtt in mtt_df.iterrows():
            project_id = mtt['projectId']
            project_info = projects_df[projects_df['project_id'] == project_id]
            
            if project_info.empty:
                continue
                
            project_name = project_info.iloc[0]['project_name']
            project_type = project_info.iloc[0]['project_type']
            language = project_info.iloc[0]['language_name'] or 'N/A'
            country = project_info.iloc[0]['country'] or 'N/A'
            
            # Get project completion percentage
            completion_pct = project_completion.get(project_id, 0)
            status = self._get_status(completion_pct)
            
            # Get assignment counts
            verses_assigned = 0
            obs_assigned = 0
            lit_assigned = 0
            
            if mtt.get('verses') and project_type == 'TEXT_TRANSLATION':
                verses_assigned = len([v for v in str(mtt['verses']).split(',') if v.strip()])
            if mtt.get('obsChapters') and project_type == 'OBS':
                obs_assigned = len([c for c in str(mtt['obsChapters']).split(',') if c.strip().isdigit()])
            if mtt.get('literatureGenres') and project_type in ['LITERATURE', 'LITERATURE_PROJECT']:
                lit_assigned = len([g for g in str(mtt['literatureGenres']).split(',') if g.strip()])
            
            assigned_items = verses_assigned or obs_assigned or lit_assigned
            assigned_display = str(assigned_items) if assigned_items > 0 else 'N/A'
            
            mtt_detail_data.append({
                'Project Name': project_name,
                'Project Type': project_type,
                'Language': language,
                'Country': country,
                'MTT User ID': mtt['user_id'],
                'MTT Username': mtt['username'],
                'MTT Full Name': mtt['full_name'],
                'MTT Email': mtt['email'],
                'Items Assigned': assigned_display,
                'Project Completion %': round(completion_pct, 1),
                'Status': status
            })
        
        mtt_detail_df = pd.DataFrame(mtt_detail_data)
        
        # Summary statistics
        summary_data = []
        summary_data.append({'Metric': 'Total Projects', 'Value': len(project_summary_df)})
        
        for ptype in project_summary_df['Project Type'].unique():
            count = len(project_summary_df[project_summary_df['Project Type'] == ptype])
            summary_data.append({'Metric': f'  - {ptype}', 'Value': count})
        
        summary_data.append({'Metric': 'Total MTT Assignments', 'Value': len(mtt_detail_df)})
        summary_data.append({'Metric': 'Unique MTTs', 'Value': mtt_detail_df['MTT User ID'].nunique() if not mtt_detail_df.empty else 0})
        summary_data.append({'Metric': 'Projects with MTTs', 'Value': len(project_summary_df[project_summary_df['MTTs Assigned'] > 0])})
        
        # Count by status
        status_counts = project_summary_df['Status'].value_counts()
        for status, count in status_counts.items():
            summary_data.append({'Metric': f'  Status: {status}', 'Value': count})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'project_summary': project_summary_df,
            'mtt_details': mtt_detail_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'project_summary': '1. Project Summary',
            'mtt_details': '2. MTT Details (per project)',
            'summary_stats': '3. Summary Statistics'
        }
