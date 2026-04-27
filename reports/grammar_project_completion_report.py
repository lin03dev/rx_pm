"""
Grammar Project Completion Report - Simplified to meaningful metrics
Focus on project-level completion (what's actually done)
"""

import pandas as pd
import json
from typing import Dict, Any, Tuple
from reports.base_report import BaseReport


class GrammarProjectCompletionReport(BaseReport):
    """Grammar Project Completion Report - Project-level completion only"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'role', 'country']
    
    def _extract_items_from_content(self, content, grammar_type: str) -> Tuple[int, int]:
        """Extract items from content and count completed ones"""
        total = 0
        completed = 0
        
        if content is None:
            return 0, 0
        
        item_key = {
            'phrases': 'phrase',
            'pronouns': 'pronoun',
            'connectives': 'connective'
        }.get(grammar_type, 'text')
        
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            if 'content' in data and isinstance(data['content'], list):
                items = data['content']
                total = len(items)
                for item in items:
                    if isinstance(item, dict):
                        value = item.get(item_key, '')
                        if value and value.strip():
                            completed += 1
            return total, completed
        except:
            return 0, 0
    
    def _get_performance_rating(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return "🏆 Complete"
        elif completion_pct >= 75:
            return "✅ Almost Complete"
        elif completion_pct >= 50:
            return "⭐ Halfway"
        elif completion_pct >= 25:
            return "📝 In Progress"
        elif completion_pct > 0:
            return "🔨 Just Started"
        else:
            return "❌ Not Started"
    
    def _get_status(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return "Completed"
        elif completion_pct > 0:
            return "In Progress"
        else:
            return "Not Started"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate grammar report - meaningful metrics only"""
        
        grammar_configs = [
            ('GRAMMAR_PHRASES', 'phrases', 'grammar_phrases_project_contents', 'grammar_phrases_projects', 'grammarPhrasesProjectId'),
            ('GRAMMAR_PRONOUNS', 'pronouns', 'grammar_pronouns_project_contents', 'grammar_pronouns_projects', 'grammarPronounsProjectId'),
            ('GRAMMAR_CONNECTIVES', 'connectives', 'grammar_connectives_project_contents', 'grammar_connectives_projects', 'grammarConnectivesProjectId')
        ]
        
        # ============================================================
        # Sheet 1: All Grammar Projects Overview
        # ============================================================
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
        WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
        ORDER BY p."projectType", p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} Grammar projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 2: MTT Assignments (Who is assigned - for reference only)
        # ============================================================
        mtt_assignments_query = """
        SELECT 
            p.name as project_name,
            p."projectType" as project_type,
            l.name as language_name,
            c.name as country,
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email
        FROM users_to_projects utp
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users u ON utp."userId" = u.id
        WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
          AND utp.role = 'MTT'
        ORDER BY p."projectType", p.name, u.username
        """
        
        try:
            mtt_assignments_df = self.execute_query(mtt_assignments_query)
            print(f"✅ Retrieved {len(mtt_assignments_df)} MTT assignment records")
        except Exception as e:
            print(f"❌ MTT assignments query failed: {e}")
            mtt_assignments_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 3: Project Status (PROJECT-LEVEL completion) - MAIN SHEET
        # ============================================================
        project_status_data = []
        
        for grammar_type, grammar_key, content_table, project_table, id_field in grammar_configs:
            try:
                query = f"""
                SELECT DISTINCT ON (gp."projectId")
                    p.name as project_name,
                    p."projectType" as project_type,
                    l.name as language_name,
                    c.name as country,
                    gp."projectId",
                    gpc.version,
                    gpc.content
                FROM {content_table} gpc
                JOIN {project_table} gp ON gpc."{id_field}" = gp.id
                JOIN projects p ON gp."projectId" = p.id
                LEFT JOIN languages l ON p."languageId" = l.id
                LEFT JOIN countries c ON p."countryId" = c.id
                WHERE gpc.version > 1
                ORDER BY gp."projectId", gpc.version DESC
                """
                
                content_df = self.execute_query(query)
                print(f"✅ {grammar_type}: Found {len(content_df)} projects with content")
                
                for _, row in content_df.iterrows():
                    total_items, completed_items = self._extract_items_from_content(row['content'], grammar_key)
                    completion_pct = (completed_items / total_items * 100) if total_items > 0 else 0
                    status = self._get_status(completion_pct)
                    performance = self._get_performance_rating(completion_pct)
                    
                    # Get MTTs assigned to this project
                    mtts = mtt_assignments_df[mtt_assignments_df['project_name'] == row['project_name']]
                    mtt_count = len(mtts)
                    mtt_names = ', '.join(mtts['full_name'].unique()) if not mtts.empty else 'No MTTs Assigned'
                    
                    project_status_data.append({
                        'Project Name': row['project_name'],
                        'Grammar Type': row['project_type'],
                        'Language': row['language_name'] or 'N/A',
                        'Country': row['country'] or 'N/A',
                        'MTTs Assigned': mtt_count,
                        'MTT Names': mtt_names[:300] if len(mtt_names) > 300 else mtt_names,
                        'Total Items': total_items,
                        'Items Completed': completed_items,
                        'Completion %': round(completion_pct, 1),
                        'Version': row['version'],
                        'Performance': performance,
                        'Status': status
                    })
            except Exception as e:
                print(f"⚠️ {grammar_type} query: {e}")
        
        # Also include projects with no content (version 0 or null)
        for _, project in projects_df.iterrows():
            if not any(p['Project Name'] == project['project_name'] for p in project_status_data):
                mtts = mtt_assignments_df[mtt_assignments_df['project_name'] == project['project_name']]
                mtt_count = len(mtts)
                mtt_names = ', '.join(mtts['full_name'].unique()) if not mtts.empty else 'No MTTs Assigned'
                
                project_status_data.append({
                    'Project Name': project['project_name'],
                    'Grammar Type': project['project_type'],
                    'Language': project['language_name'] or 'N/A',
                    'Country': project['country'] or 'N/A',
                    'MTTs Assigned': mtt_count,
                    'MTT Names': mtt_names[:300] if len(mtt_names) > 300 else mtt_names,
                    'Total Items': 0,
                    'Items Completed': 0,
                    'Completion %': 0,
                    'Version': 0,
                    'Performance': '❌ Not Started',
                    'Status': 'Not Started'
                })
        
        project_status_df = pd.DataFrame(project_status_data)
        if not project_status_df.empty:
            project_status_df = project_status_df.sort_values(['Grammar Type', 'Completion %'], ascending=[True, False])
        
        # ============================================================
        # Sheet 4: Summary Statistics
        # ============================================================
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total Grammar Projects', 'Value': len(projects_df)})
            for gtype in ['GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES']:
                count = len(projects_df[projects_df['project_type'] == gtype])
                summary_data.append({'Metric': f'  - {gtype}', 'Value': count})
        
        if not project_status_df.empty:
            with_content = len(project_status_df[project_status_df['Items Completed'] > 0])
            completed = len(project_status_df[project_status_df['Status'] == 'Completed'])
            in_progress = len(project_status_df[project_status_df['Status'] == 'In Progress'])
            not_started = len(project_status_df[project_status_df['Status'] == 'Not Started'])
            
            summary_data.append({'Metric': 'Projects with Content', 'Value': with_content})
            summary_data.append({'Metric': 'Completed Projects', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Projects', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Projects', 'Value': not_started})
            summary_data.append({'Metric': 'Total Items Across All Projects', 'Value': project_status_df['Total Items'].sum()})
            summary_data.append({'Metric': 'Total Completed Items', 'Value': project_status_df['Items Completed'].sum()})
            if project_status_df['Total Items'].sum() > 0:
                summary_data.append({'Metric': 'Overall Completion Rate', 'Value': f"{(project_status_df['Items Completed'].sum() / project_status_df['Total Items'].sum() * 100):.1f}%"})
        
        if not mtt_assignments_df.empty and 'user_id' in mtt_assignments_df.columns:
            summary_data.append({'Metric': 'Total MTTs Assigned', 'Value': mtt_assignments_df['user_id'].nunique()})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'projects_overview': projects_df,
            'mtt_assignments': mtt_assignments_df,
            'project_status': project_status_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'projects_overview': '1 - All Grammar Projects',
            'mtt_assignments': '2 - MTT Assignments (Reference)',
            'project_status': '3 - Project Status (Completion)',
            'summary_stats': '4 - Summary Statistics'
        }
