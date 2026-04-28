"""
AG Drafting Monitoring Report - Consolidated report for all project types
PROJECT-LEVEL COMPLETION with proper metrics
"""

import pandas as pd
import json
import re
from typing import Dict, Any, Set, Tuple
from reports.base_report import BaseReport


class AGDraftingMonitoringReport(BaseReport):
    """AG Drafting Monitoring Report - PROJECT-LEVEL completion across all types"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['country', 'language', 'project_type']
        
        # OBS Completion Thresholds
        self.obs_thresholds = {
            'title_required': True,
            'bibleref_required': True,
            'paragraphs_required_percent': 100
        }
    
    def _is_obs_chapter_complete(self, data_text: str) -> bool:
        """Check if an OBS chapter is COMPLETE based on thresholds"""
        try:
            if not data_text or data_text == '{}':
                return False
            
            data = json.loads(data_text)
            
            if self.obs_thresholds['title_required']:
                title = data.get('title', '')
                if not title or not title.strip():
                    return False
            
            if self.obs_thresholds['bibleref_required']:
                bibleref = data.get('bibleRef', '')
                if not bibleref or not bibleref.strip():
                    return False
            
            paras = data.get('paras', [])
            if not paras:
                return False
            
            completed_paras = 0
            for para in paras:
                content = para.get('content', '')
                if content and content.strip():
                    completed_paras += 1
            
            required_paras = len(paras)
            if required_paras == 0:
                return False
            
            completion_pct = (completed_paras / required_paras) * 100
            return completion_pct >= self.obs_thresholds['paragraphs_required_percent']
            
        except:
            return False
    
    def _get_bible_verse_completion(self, project_id: str) -> Dict[str, Any]:
        """Get Bible verse completion - count verses with ACTUAL TEXT CONTENT"""
        result = {
            'total_verses_assigned': 0,
            'verses_with_content': 0,
            'completion_pct': 0,
            'total_chapters_assigned': 0,
            'chapters_completed': 0
        }
        
        try:
            # Get all assigned verses for this project
            assign_query = f"""
            SELECT DISTINCT trim(unnest(string_to_array(COALESCE(verses, ''), ','))) as verse_id
            FROM users_to_projects
            WHERE "projectId" = '{project_id}'
              AND role = 'MTT'
              AND verses IS NOT NULL
            """
            assign_df = self.execute_query(assign_query)
            
            if assign_df.empty:
                return result
            
            # Parse assigned verses
            assigned_verses = set()
            chapter_verses_map = {}
            book_chapter_map = {}
            
            for _, row in assign_df.iterrows():
                verse_id = row['verse_id'].strip()
                if verse_id and len(verse_id) >= 9 and verse_id.isdigit():
                    assigned_verses.add(verse_id)
                    book = int(verse_id[:3])
                    chapter = int(verse_id[3:6])
                    verse = int(verse_id[6:9])
                    key = (book, chapter)
                    if key not in chapter_verses_map:
                        chapter_verses_map[key] = set()
                        book_chapter_map[key] = set()
                    chapter_verses_map[key].add(verse)
                    book_chapter_map[key].add(verse_id)
            
            result['total_verses_assigned'] = len(assigned_verses)
            result['total_chapters_assigned'] = len(chapter_verses_map)
            
            # Get completed content
            content_query = f"""
            SELECT ttb."bookNo", ttc."chapterNo", ttc.content::text as content_text
            FROM text_translation_chapters ttc
            JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
            JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
            WHERE tp."projectId" = '{project_id}'
              AND ttc.version > 1
            """
            content_df = self.execute_query(content_query)
            
            # Track verses with actual content
            verses_with_content = set()
            chapters_with_all_verses = set()
            
            for _, row in content_df.iterrows():
                book = row['bookNo']
                chapter = row['chapterNo']
                content_text = row['content_text']
                
                key = (book, chapter)
                if key not in chapter_verses_map:
                    continue
                
                try:
                    data = json.loads(content_text) if isinstance(content_text, str) else content_text
                    
                    if 'content' in data and isinstance(data['content'], list):
                        for item in data['content']:
                            verse_text = item.get('text', '')
                            if verse_text and verse_text.strip():
                                verse_num = item.get('start') or item.get('end')
                                if verse_num:
                                    verse_num_int = int(verse_num)
                                    if verse_num_int in chapter_verses_map[key]:
                                        verse_id = f"{book:03d}{chapter:03d}{verse_num_int:03d}"
                                        verses_with_content.add(verse_id)
                    
                    chapter_assigned = chapter_verses_map[key]
                    chapter_completed = set()
                    for verse_num in chapter_assigned:
                        verse_id = f"{book:03d}{chapter:03d}{verse_num:03d}"
                        if verse_id in verses_with_content:
                            chapter_completed.add(verse_num)
                    
                    if chapter_assigned == chapter_completed:
                        chapters_with_all_verses.add(key)
                        
                except Exception as e:
                    pass
            
            result['verses_with_content'] = len(verses_with_content)
            result['chapters_completed'] = len(chapters_with_all_verses)
            
            if result['total_verses_assigned'] > 0:
                result['completion_pct'] = round((result['verses_with_content'] / result['total_verses_assigned']) * 100, 1)
            
        except Exception as e:
            print(f"  Error in Bible completion: {e}")
        
        return result
    
    def _get_grammar_completion(self, project_id: str, grammar_type: str) -> Dict[str, int]:
        """Get grammar completion metrics - PROJECT LEVEL"""
        result = {'total_items': 0, 'completed_items': 0, 'completion_pct': 0}
        
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
                    if result['total_items'] > 0:
                        result['completion_pct'] = round((result['completed_items'] / result['total_items']) * 100, 1)
        except:
            pass
        
        return result
    
    def _analyze_literature_content(self, content) -> Dict[str, int]:
        """Analyze literature content for each genre"""
        result = {
            'childrens_literature': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0},
            'formal_writing': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0},
            'history': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0},
            'narrative': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0},
            'poetry': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0},
            'literature': {'total_blocks': 0, 'filled_blocks': 0, 'completion_pct': 0}
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
                    if len(blocks) > 0:
                        result[genre_type]['completion_pct'] = round((filled / len(blocks)) * 100, 1)
                else:
                    blocks = data['content']
                    result['literature']['total_blocks'] += len(blocks)
                    filled = sum(1 for b in blocks if isinstance(b, dict) and b.get('content', '').strip())
                    result['literature']['filled_blocks'] += filled
                    if result['literature']['total_blocks'] > 0:
                        result['literature']['completion_pct'] = round((result['literature']['filled_blocks'] / result['literature']['total_blocks']) * 100, 1)
        except:
            pass
        
        return result
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate AG Drafting Monitoring Report - PROJECT LEVEL completion"""
        
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
            
            row = {
                'Country': country,
                'Language': language,
                'MTT Names': mtt_names,
                'OBS_Chapters_Assigned': 0,
                'OBS_Chapters_Completed': 0,
                'OBS_Completion_%': 0,
                'Bible_Verses_Assigned': 0,
                'Bible_Verses_Completed': 0,
                'Bible_Completion_%': 0,
                'Literature_Fill_%': 0,
                'Grammar_Pronouns_%': 0,
                'Grammar_Connectives_%': 0,
                'Grammar_Phrases_%': 0
            }
            
            # OBS Completion
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
                SELECT DISTINCT trim(unnest(string_to_array(COALESCE("obsChapters", ''), ','))) as chapter_num
                FROM users_to_projects
                WHERE "projectId" = '{project_id}'
                  AND role = 'MTT'
                  AND "obsChapters" IS NOT NULL
                """
                assign_df = self.execute_query(assign_query)
                assigned_chapters = set()
                for _, r in assign_df.iterrows():
                    try:
                        ch = int(r['chapter_num'].strip())
                        if 1 <= ch <= 50:
                            assigned_chapters.add(ch)
                    except:
                        pass
                
                row['OBS_Chapters_Assigned'] = len(assigned_chapters)
                
                complete_query = f"""
                SELECT opc."chapterNo", opc.data::text as data_text
                FROM obs_project_chapters opc
                JOIN obs_projects op ON opc."obsProjectId" = op.id
                WHERE op."projectId" = '{project_id}'
                  AND opc.version > 1
                """
                complete_df = self.execute_query(complete_query)
                
                completed_chapters = set()
                for _, r in complete_df.iterrows():
                    chapter_no = r['chapterNo']
                    data_text = r['data_text']
                    if self._is_obs_chapter_complete(data_text):
                        completed_chapters.add(chapter_no)
                
                row['OBS_Chapters_Completed'] = len([ch for ch in assigned_chapters if ch in completed_chapters])
                if row['OBS_Chapters_Assigned'] > 0:
                    row['OBS_Completion_%'] = round((row['OBS_Chapters_Completed'] / row['OBS_Chapters_Assigned']) * 100, 1)
            
            # Bible Completion
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
                bible_completion = self._get_bible_verse_completion(project_id)
                
                row['Bible_Verses_Assigned'] = bible_completion['total_verses_assigned']
                row['Bible_Verses_Completed'] = bible_completion['verses_with_content']
                row['Bible_Completion_%'] = bible_completion['completion_pct']
            
            # Literature Completion
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
                    row['Literature_Fill_%'] = analysis['literature']['completion_pct']
            
            # Grammar Completion
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
                        row['Grammar_Pronouns_%'] = completion['completion_pct']
                    elif grammar_type == 'GRAMMAR_CONNECTIVES':
                        row['Grammar_Connectives_%'] = completion['completion_pct']
                    elif grammar_type == 'GRAMMAR_PHRASES':
                        row['Grammar_Phrases_%'] = completion['completion_pct']
            
            report_data.append(row)
        
        report_df = pd.DataFrame(report_data)
        
        column_order = [
            'Country', 'Language', 'MTT Names',
            'OBS_Chapters_Assigned', 'OBS_Chapters_Completed', 'OBS_Completion_%',
            'Bible_Verses_Assigned', 'Bible_Verses_Completed', 'Bible_Completion_%',
            'Literature_Fill_%',
            'Grammar_Pronouns_%', 'Grammar_Connectives_%', 'Grammar_Phrases_%'
        ]
        
        existing_columns = [col for col in column_order if col in report_df.columns]
        report_df = report_df[existing_columns]
        report_df = report_df.sort_values(['Country', 'Language'])
        
        summary_data = []
        summary_data.append({'Metric': 'Total Languages/Countries', 'Value': len(report_df)})
        
        if 'OBS_Completion_%' in report_df.columns:
            avg_obs = report_df[report_df['OBS_Chapters_Assigned'] > 0]['OBS_Completion_%'].mean()
            summary_data.append({'Metric': 'Average OBS Completion %', 'Value': f"{round(avg_obs, 1)}%"})
        
        if 'Bible_Completion_%' in report_df.columns:
            avg_bible = report_df[report_df['Bible_Verses_Assigned'] > 0]['Bible_Completion_%'].mean()
            summary_data.append({'Metric': 'Average Bible Completion %', 'Value': f"{round(avg_bible, 1)}%"})
        
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
