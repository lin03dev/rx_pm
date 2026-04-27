"""
AG Drafting Monitoring Report - Consolidated report for all project types
Combines Bible, OBS, Literature, and Grammar metrics into single monitoring view
"""

import pandas as pd
import json
import re
from typing import Dict, Any
from reports.base_report import BaseReport


class AGDraftingMonitoringReport(BaseReport):
    """AG Drafting Monitoring Report - Complete project monitoring across all types"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['country', 'language', 'project_type']
    
    def _analyze_literature_content(self, content) -> Dict[str, int]:
        """Analyze literature content for each genre"""
        result = {
            'childrens_literature': {'total_blocks': 0, 'filled_blocks': 0},
            'formal_writing': {'total_blocks': 0, 'filled_blocks': 0},
            'history': {'total_blocks': 0, 'filled_blocks': 0},
            'narrative': {'total_blocks': 0, 'filled_blocks': 0},
            'poetry': {'total_blocks': 0, 'filled_blocks': 0},
            'literature': {'total_blocks': 0, 'filled_blocks': 0}
        }
        
        if content is None:
            return result
        
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            if 'content' in data and isinstance(data['content'], list):
                genre_type = data.get('metadata', {}).get('genre', '')
                if genre_type and genre_type in result:
                    blocks = data['content']
                    result[genre_type]['total_blocks'] = len(blocks)
                    filled = sum(1 for b in blocks if isinstance(b, dict) and b.get('content', '').strip())
                    result[genre_type]['filled_blocks'] = filled
        except:
            pass
        
        return result
    
    def _get_grammar_completion(self, project_id: str, grammar_type: str) -> Dict[str, int]:
        """Get grammar completion metrics"""
        result = {'total_items': 0, 'completed_items': 0}
        
        table_map = {
            'GRAMMAR_PHRASES': ('grammar_phrases_project_contents', 'grammar_phrases_projects', 'grammarPhrasesProjectId', 'phrase'),
            'GRAMMAR_PRONOUNS': ('grammar_pronouns_project_contents', 'grammar_pronouns_projects', 'grammarPronounsProjectId', 'pronoun'),
            'GRAMMAR_CONNECTIVES': ('grammar_connectives_project_contents', 'grammar_connectives_projects', 'grammarConnectivesProjectId', 'connective')
        }
        
        if grammar_type not in table_map:
            return result
        
        content_table, project_table, id_field, item_key = table_map[grammar_type]
        
        try:
            query = f"""
            SELECT gpc.content
            FROM {content_table} gpc
            JOIN {project_table} gp ON gpc."{id_field}" = gp.id
            WHERE gp."projectId" = '{project_id}'
              AND gpc.version > 1
            ORDER BY gpc.version DESC
            LIMIT 1
            """
            df = self.execute_query(query)
            
            if not df.empty and df['content'].iloc[0]:
                content = df['content'].iloc[0]
                if isinstance(content, str):
                    data = json.loads(content)
                else:
                    data = content
                
                if 'content' in data and isinstance(data['content'], list):
                    items = data['content']
                    result['total_items'] = len(items)
                    result['completed_items'] = sum(1 for i in items if isinstance(i, dict) and i.get(item_key, '').strip())
        except:
            pass
        
        return result
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate AG Drafting Monitoring Report"""
        
        # Get all distinct countries and languages with projects
        query = """
        SELECT DISTINCT 
            c.name as country,
            l.name as language,
            l."isoCode" as language_code
        FROM projects p
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE p."projectType" IN ('TEXT_TRANSLATION', 'OBS', 'LITERATURE', 'LITERATURE_PROJECT',
                                  'GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
          AND c.name IS NOT NULL
        ORDER BY c.name, l.name
        """
        
        try:
            locations_df = self.execute_query(query)
            print(f"✅ Retrieved {len(locations_df)} country-language combinations")
        except Exception as e:
            print(f"❌ Locations query failed: {e}")
            locations_df = pd.DataFrame()
        
        report_data = []
        
        for _, loc in locations_df.iterrows():
            country = loc['country']
            language = loc['language']
            
            # Get MTT names for this language
            lang_escaped = language.replace("'", "''")
            mtt_query = f"""
            SELECT DISTINCT COALESCE(NULLIF(u.name, ''), u.username) as mtt_name
            FROM users u
            JOIN users_to_projects utp ON u.id = utp."userId"
            JOIN projects p ON utp."projectId" = p.id
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
              AND utp.role = 'MTT'
            ORDER BY mtt_name
            """
            mtt_df = self.execute_query(mtt_query)
            mtt_names = ', '.join(mtt_df['mtt_name'].tolist()) if not mtt_df.empty else ''
            
            # Initialize row
            row = {
                'Country': country,
                'Language': language,
                'Cluster': '',
                'Language_dup': language,
                'Date of Report': '',
                'MTT Names': mtt_names,
                'OBS_Chapters_Assigned': 0,
                'OBS_Chapters_Completed': 0,
                'Bible_Verses_Assigned': 0,
                'Bible_Verse_Completion': 0,
                'Literature_Total_Blocks': 0,
                'Literature_Filled_Blocks': 0,
                'Childrens_Lit_Total': 0,
                'Childrens_Lit_Filled': 0,
                'Formal_Writing_Total': 0,
                'Formal_Writing_Filled': 0,
                'History_Total': 0,
                'History_Filled': 0,
                'Narrative_Total': 0,
                'Narrative_Filled': 0,
                'Poetry_Total': 0,
                'Poetry_Filled': 0,
                'Grammar_Pronouns_Total': 0,
                'Grammar_Pronouns_Completed': 0,
                'Grammar_Connectives_Total': 0,
                'Grammar_Connectives_Completed': 0,
                'Grammar_Phrases_Total': 0,
                'Grammar_Phrases_Completed': 0
            }
            
            # Get OBS project
            obs_query = f"""
            SELECT p.id as project_id
            FROM projects p
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
              AND p."projectType" = 'OBS'
            LIMIT 1
            """
            obs_df = self.execute_query(obs_query)
            
            if not obs_df.empty:
                project_id = obs_df['project_id'].iloc[0]
                
                assign_query = f"""
                SELECT COALESCE(SUM(array_length(string_to_array(COALESCE("obsChapters", ''), ','), 1)), 0) as total
                FROM users_to_projects
                WHERE "projectId" = '{project_id}'
                  AND role = 'MTT'
                """
                assign_df = self.execute_query(assign_query)
                row['OBS_Chapters_Assigned'] = assign_df['total'].iloc[0] if not assign_df.empty else 0
                
                complete_query = f"""
                SELECT COUNT(DISTINCT opc."chapterNo") as completed
                FROM obs_project_chapters opc
                JOIN obs_projects op ON opc."obsProjectId" = op.id
                WHERE op."projectId" = '{project_id}'
                  AND opc.version > 1
                  AND opc.data IS NOT NULL
                  AND opc.data::text != '{{}}'
                """
                complete_df = self.execute_query(complete_query)
                row['OBS_Chapters_Completed'] = complete_df['completed'].iloc[0] if not complete_df.empty else 0
            
            # Get Bible project
            bible_query = f"""
            SELECT p.id as project_id
            FROM projects p
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
              AND p."projectType" = 'TEXT_TRANSLATION'
            LIMIT 1
            """
            bible_df = self.execute_query(bible_query)
            
            if not bible_df.empty:
                project_id = bible_df['project_id'].iloc[0]
                
                assign_query = f"""
                SELECT COALESCE(SUM(array_length(string_to_array(COALESCE(verses, ''), ','), 1)), 0) as total
                FROM users_to_projects
                WHERE "projectId" = '{project_id}'
                  AND role = 'MTT'
                """
                assign_df = self.execute_query(assign_query)
                row['Bible_Verses_Assigned'] = assign_df['total'].iloc[0] if not assign_df.empty else 0
                
                complete_query = f"""
                SELECT COUNT(DISTINCT ttc.id) as completed
                FROM text_translation_chapters ttc
                JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
                JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
                WHERE tp."projectId" = '{project_id}'
                  AND ttc.version > 1
                """
                complete_df = self.execute_query(complete_query)
                row['Bible_Verse_Completion'] = complete_df['completed'].iloc[0] if not complete_df.empty else 0
            
            # Get Literature project
            lit_query = f"""
            SELECT lp."projectId"
            FROM literature_projects lp
            JOIN projects p ON lp."projectId" = p.id
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
            LIMIT 1
            """
            lit_df = self.execute_query(lit_query)
            
            if not lit_df.empty:
                project_id = lit_df['projectId'].iloc[0]
                
                content_query = f"""
                SELECT lpg.content
                FROM literature_project_genres_history lpg
                JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
                JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
                WHERE lp."projectId" = '{project_id}'
                  AND lpg.version > 1
                ORDER BY lpg.version DESC
                LIMIT 1
                """
                content_df = self.execute_query(content_query)
                
                if not content_df.empty and content_df['content'].iloc[0]:
                    content = content_df['content'].iloc[0]
                    analysis = self._analyze_literature_content(content)
                    
                    row['Literature_Total_Blocks'] = sum(g['total_blocks'] for g in analysis.values())
                    row['Literature_Filled_Blocks'] = sum(g['filled_blocks'] for g in analysis.values())
                    row['Childrens_Lit_Total'] = analysis['childrens_literature']['total_blocks']
                    row['Childrens_Lit_Filled'] = analysis['childrens_literature']['filled_blocks']
                    row['Formal_Writing_Total'] = analysis['formal_writing']['total_blocks']
                    row['Formal_Writing_Filled'] = analysis['formal_writing']['filled_blocks']
                    row['History_Total'] = analysis['history']['total_blocks']
                    row['History_Filled'] = analysis['history']['filled_blocks']
                    row['Narrative_Total'] = analysis['narrative']['total_blocks']
                    row['Narrative_Filled'] = analysis['narrative']['filled_blocks']
                    row['Poetry_Total'] = analysis['poetry']['total_blocks']
                    row['Poetry_Filled'] = analysis['poetry']['filled_blocks']
            
            # Get Grammar projects
            for grammar_type in ['GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES', 'GRAMMAR_PHRASES']:
                grammar_query = f"""
                SELECT p.id as project_id
                FROM projects p
                JOIN languages l ON p."languageId" = l.id
                WHERE l.name = '{lang_escaped}'
                  AND p."projectType" = '{grammar_type}'
                LIMIT 1
                """
                grammar_df = self.execute_query(grammar_query)
                
                if not grammar_df.empty:
                    project_id = grammar_df['project_id'].iloc[0]
                    completion = self._get_grammar_completion(project_id, grammar_type)
                    
                    if grammar_type == 'GRAMMAR_PRONOUNS':
                        row['Grammar_Pronouns_Total'] = completion['total_items']
                        row['Grammar_Pronouns_Completed'] = completion['completed_items']
                    elif grammar_type == 'GRAMMAR_CONNECTIVES':
                        row['Grammar_Connectives_Total'] = completion['total_items']
                        row['Grammar_Connectives_Completed'] = completion['completed_items']
                    elif grammar_type == 'GRAMMAR_PHRASES':
                        row['Grammar_Phrases_Total'] = completion['total_items']
                        row['Grammar_Phrases_Completed'] = completion['completed_items']
            
            report_data.append(row)
        
        report_df = pd.DataFrame(report_data)
        
        # Reorder columns
        column_order = [
            'Country', 'Language', 'Cluster', 'Language_dup', 'Date of Report', 'MTT Names',
            'OBS_Chapters_Assigned', 'OBS_Chapters_Completed',
            'Bible_Verses_Assigned', 'Bible_Verse_Completion',
            'Literature_Total_Blocks', 'Literature_Filled_Blocks',
            'Childrens_Lit_Total', 'Childrens_Lit_Filled',
            'Formal_Writing_Total', 'Formal_Writing_Filled',
            'History_Total', 'History_Filled',
            'Narrative_Total', 'Narrative_Filled',
            'Poetry_Total', 'Poetry_Filled',
            'Grammar_Pronouns_Total', 'Grammar_Pronouns_Completed',
            'Grammar_Connectives_Total', 'Grammar_Connectives_Completed',
            'Grammar_Phrases_Total', 'Grammar_Phrases_Completed'
        ]
        
        existing_columns = [col for col in column_order if col in report_df.columns]
        report_df = report_df[existing_columns]
        report_df = report_df.sort_values(['Country', 'Language'])
        
        # Summary statistics
        summary_data = []
        summary_data.append({'Metric': 'Total Languages/Countries', 'Value': len(report_df)})
        if 'OBS_Chapters_Assigned' in report_df.columns:
            summary_data.append({'Metric': 'Total OBS Chapters Assigned', 'Value': int(report_df['OBS_Chapters_Assigned'].sum())})
            summary_data.append({'Metric': 'Total OBS Chapters Completed', 'Value': int(report_df['OBS_Chapters_Completed'].sum())})
        if 'Bible_Verses_Assigned' in report_df.columns:
            summary_data.append({'Metric': 'Total Bible Verses Assigned', 'Value': int(report_df['Bible_Verses_Assigned'].sum())})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'monitoring_report': report_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'monitoring_report': 'AG Drafting Monitoring Report',
            'summary_stats': 'Summary Statistics'
        }
