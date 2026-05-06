"""
Consolidated Report - Dynamic version with correct column names
"""

import pandas as pd
from typing import Dict, Any

from reports.base_report_v2 import BaseReportV2


class ConsolidatedReportDynamic(BaseReportV2):
    """Consolidated project report using dynamic features"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_type', 'country', 'language']
        
        # Correct column names per table
        self.content_columns = {
            'TEXT_TRANSLATION': {'table': 'text_translation_chapters', 'content_col': 'content', 'version_col': 'version'},
            'OBS': {'table': 'obs_project_chapters', 'content_col': 'data', 'version_col': 'version'},
            'LITERATURE': {'table': 'literature_project_genres', 'content_col': 'content', 'version_col': 'version'},
            'LITERATURE_PROJECT': {'table': 'literature_project_genres', 'content_col': 'content', 'version_col': 'version'},
            'GRAMMAR_PHRASES': {'table': 'grammar_phrases_project_contents', 'content_col': 'content', 'version_col': 'version'},
            'GRAMMAR_PRONOUNS': {'table': 'grammar_pronouns_project_contents', 'content_col': 'content', 'version_col': 'version'},
            'GRAMMAR_CONNECTIVES': {'table': 'grammar_connectives_project_contents', 'content_col': 'content', 'version_col': 'version'},
        }
    
    def _get_project_completion(self, project_id: str, project_type: str) -> Dict[str, Any]:
        """Get completion for a project using correct column names"""
        col_config = self.content_columns.get(project_type)
        if not col_config:
            return {'total': 0, 'completed': 0, 'pct': 0}
        
        content_col = col_config['content_col']
        version_col = col_config['version_col']
        table_name = col_config['table']
        
        # Handle different table structures
        if project_type == 'OBS':
            # OBS uses obsProjectId to link to projects
            query = f"""
            SELECT opc.{content_col} as content, opc.{version_col} as version
            FROM {table_name} opc
            JOIN obs_projects op ON opc."obsProjectId" = op.id
            WHERE op."projectId" = '{project_id}'
              AND opc.{version_col} > 1
            ORDER BY opc.{version_col} DESC
            LIMIT 1
            """
        elif project_type in ['LITERATURE', 'LITERATURE_PROJECT']:
            # Literature uses a history table
            query = f"""
            SELECT lpg.{content_col} as content, lpg.{version_col} as version
            FROM literature_project_genres_history lpg
            JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
            JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
            WHERE lp."projectId" = '{project_id}'
              AND lpg.{version_col} > 1
            ORDER BY lpg.{version_col} DESC
            LIMIT 1
            """
        elif project_type.startswith('GRAMMAR_'):
            # Grammar projects
            grammar_table_map = {
                'GRAMMAR_PHRASES': ('grammar_phrases_projects', 'grammarPhrasesProjectId'),
                'GRAMMAR_PRONOUNS': ('grammar_pronouns_projects', 'grammarPronounsProjectId'),
                'GRAMMAR_CONNECTIVES': ('grammar_connectives_projects', 'grammarConnectivesProjectId'),
            }
            project_table, id_field = grammar_table_map.get(project_type, (None, None))
            if not project_table:
                return {'total': 0, 'completed': 0, 'pct': 0}
            
            query = f"""
            SELECT gpc.{content_col} as content, gpc.{version_col} as version
            FROM {table_name} gpc
            JOIN {project_table} gp ON gpc."{id_field}" = gp.id
            WHERE gp."projectId" = '{project_id}'
              AND gpc.{version_col} > 1
            ORDER BY gpc.{version_col} DESC
            LIMIT 1
            """
        else:
            # Bible translation
            query = f"""
            SELECT ttc.{content_col} as content, ttc.{version_col} as version
            FROM {table_name} ttc
            JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
            JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
            WHERE tp."projectId" = '{project_id}'
              AND ttc.{version_col} > 1
            ORDER BY ttc.{version_col} DESC
            LIMIT 1
            """
        
        try:
            df = self.execute_query(query)
            if not df.empty:
                content = df['content'].iloc[0]
                metrics = self.analyze_content(content, project_type)
                return {
                    'total': metrics.total_items,
                    'completed': metrics.completed_items,
                    'pct': metrics.completion_pct,
                    'has_content': metrics.has_content,
                    'metadata': metrics.metadata
                }
        except Exception as e:
            # Silent fail for individual queries
            pass
        
        return {'total': 0, 'completed': 0, 'pct': 0, 'has_content': False}
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate consolidated report"""
        
        # Get all projects
        projects_df = self.get_all_projects()
        print(f"✅ Retrieved {len(projects_df)} projects")
        
        # Get MTT assignments
        mtt_df = self.get_mtt_assignments()
        print(f"✅ Retrieved {len(mtt_df)} MTT assignments")
        
        # Build project status
        project_status = []
        
        for _, project in projects_df.iterrows():
            project_id = project['project_id']
            project_name = project['project_name']
            project_type = project['project_type']
            language = project.get('language_name', 'N/A')
            country = project.get('country', 'N/A')
            
            # Get MTT info
            project_mtts = mtt_df[mtt_df['projectId'] == project_id]
            mtt_count = len(project_mtts)
            mtt_names = ', '.join(project_mtts['full_name'].unique()) if not project_mtts.empty else ''
            
            # Get completion
            completion = self._get_project_completion(project_id, project_type)
            completion_pct = completion['pct']
            
            status = self.get_completion_status(completion_pct, mtt_count > 0)
            rating = self.get_performance_rating(completion_pct)
            
            # Format item count display
            total_items_display = f"{completion['total']:,}" if completion['total'] > 0 else '0'
            completed_items_display = f"{completion['completed']:,}" if completion['completed'] > 0 else '0'
            
            # Add extra metadata for specific project types
            extra_info = ''
            if completion.get('metadata'):
                if 'total_sentences' in completion['metadata']:
                    extra_info = f" | {completion['metadata']['total_sentences']} sentences"
                elif 'total_paras' in completion['metadata']:
                    extra_info = f" | {completion['metadata']['completed_paras']}/{completion['metadata']['total_paras']} paragraphs"
            
            project_status.append({
                'Project Name': project_name,
                'Project Type': project_type,
                'Language': language,
                'Country': country,
                'MTTs Assigned': mtt_count,
                'MTT Names': mtt_names[:300] if len(mtt_names) > 300 else mtt_names,
                'Total Items': total_items_display,
                'Completed Items': completed_items_display,
                'Completion %': round(completion_pct, 1),
                'Performance': rating,
                'Status': status,
                'Details': extra_info.strip(' | ')
            })
        
        status_df = pd.DataFrame(project_status)
        if not status_df.empty:
            status_df = status_df.sort_values(['Project Type', 'Completion %'], ascending=[True, False])
        
        # Summary stats
        summary_data = []
        summary_data.append({'Metric': 'Total Projects', 'Value': len(projects_df)})
        
        if not status_df.empty:
            for ptype in status_df['Project Type'].unique():
                count = len(status_df[status_df['Project Type'] == ptype])
                summary_data.append({'Metric': f'  - {ptype}', 'Value': count})
            
            completed = len(status_df[status_df['Status'].str.contains('Completed', na=False)])
            in_progress = len(status_df[status_df['Status'].str.contains('Progress', na=False)])
            not_started = len(status_df[status_df['Status'].str.contains('Not Started', na=False)])
            no_mtt = len(status_df[status_df['Status'].str.contains('No MTT', na=False)])
            
            summary_data.append({'Metric': 'Completed Projects', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Projects', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Projects', 'Value': not_started})
            summary_data.append({'Metric': 'Projects Without MTTs', 'Value': no_mtt})
            
            # Calculate total items (convert string to int for sum)
            total_items_sum = 0
            completed_items_sum = 0
            for _, row in status_df.iterrows():
                try:
                    total_items_sum += int(row['Total Items'].replace(',', '')) if row['Total Items'] != '0' else 0
                    completed_items_sum += int(row['Completed Items'].replace(',', '')) if row['Completed Items'] != '0' else 0
                except:
                    pass
            
            summary_data.append({'Metric': 'Total Items Across All Projects', 'Value': f"{total_items_sum:,}"})
            summary_data.append({'Metric': 'Total Completed Items', 'Value': f"{completed_items_sum:,}"})
            
            if total_items_sum > 0:
                overall_pct = (completed_items_sum / total_items_sum) * 100
                summary_data.append({'Metric': 'Overall Completion Rate', 'Value': f"{overall_pct:.1f}%"})
        
        # MTT summary
        if not mtt_df.empty:
            unique_mtts = mtt_df['user_id'].nunique()
            summary_data.append({'Metric': 'Unique MTTs Assigned', 'Value': unique_mtts})
            
            # MTTs by project type
            mtt_by_type = mtt_df.groupby('project_type')['user_id'].nunique()
            for ptype, count in mtt_by_type.items():
                summary_data.append({'Metric': f'  MTTs in {ptype}', 'Value': count})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'project_status': status_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'project_status': '1. Project Status',
            'summary_stats': '2. Summary Statistics'
        }
