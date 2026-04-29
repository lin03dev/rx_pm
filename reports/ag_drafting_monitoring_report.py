"""
AG Drafting Monitoring Report - Consolidated report for all project types
PROJECT-LEVEL COMPLETION with proper metrics for Bible, OBS, Literature, and Grammar
"""

import pandas as pd
import json
from typing import Dict, Any, Set
from reports.base_report import BaseReport


class AGDraftingMonitoringReport(BaseReport):
    """AG Drafting Monitoring Report - PROJECT-LEVEL completion across all types"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['country', 'language', 'project_type']
        
        # Map assigned book numbers to standard Bible book numbers
        # OT: 101-166 → 1-66 (offset -100)
        # NT: 240-266 → 40-66 (offset -200)
        self.book_mapping = {}
        for i in range(101, 167):
            self.book_mapping[i] = i - 100
        for i in range(240, 267):
            self.book_mapping[i] = i - 200
        
        # OBS Completion Thresholds for translation
        self.obs_translation_thresholds = {
            'title_required': True,
            'bibleref_required': True,
            'paragraphs_required_percent': 100
        }
        
        # Literature genre mapping - standard order
        self.literature_genres = [
            'childrens_literature', 'formal_writing', 'history', 'literature', 'narrative', 'poetry'
        ]
        
        self.literature_genre_display = {
            'childrens_literature': "Children's Literature",
            'formal_writing': 'Formal Writing',
            'history': 'History',
            'literature': 'Literature',
            'narrative': 'Narrative',
            'poetry': 'Poetry'
        }
    
    def _map_assigned_verse(self, verse_id: str) -> tuple:
        """Map assigned verse ID to standard (book, chapter, verse)"""
        if not verse_id or len(verse_id) < 9:
            return None, None, None
        
        try:
            assigned_book = int(verse_id[:3])
            chapter = int(verse_id[3:6])
            verse = int(verse_id[6:9])
            
            if assigned_book in self.book_mapping:
                standard_book = self.book_mapping[assigned_book]
            else:
                standard_book = assigned_book
            
            return standard_book, chapter, verse
        except:
            return None, None, None
    
    def _is_obs_chapter_translated(self, data_text: str) -> bool:
        """Check if an OBS chapter is FULLY TRANSLATED based on thresholds"""
        try:
            if not data_text or data_text == '{}':
                return False
            
            data = json.loads(data_text)
            
            if self.obs_translation_thresholds['title_required']:
                title = data.get('title', '')
                if not title or not title.strip():
                    return False
            
            if self.obs_translation_thresholds['bibleref_required']:
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
            return completion_pct >= self.obs_translation_thresholds['paragraphs_required_percent']
            
        except:
            return False
    
    def _get_bible_verse_completion(self, project_id: str) -> Dict[str, Any]:
        """Get Bible verse completion with proper book mapping"""
        result = {
            'total_verses_assigned': 0,
            'verses_with_content': 0,
            'completion_pct': 0
        }
        
        try:
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
            
            assigned_verse_keys = set()
            chapter_verses_map = {}
            
            for _, row in assign_df.iterrows():
                verse_id = row['verse_id'].strip()
                if verse_id and len(verse_id) >= 9:
                    book, chapter, verse = self._map_assigned_verse(verse_id)
                    if book and chapter and verse:
                        assigned_verse_keys.add((book, chapter, verse))
                        key = (book, chapter)
                        if key not in chapter_verses_map:
                            chapter_verses_map[key] = set()
                        chapter_verses_map[key].add(verse)
            
            result['total_verses_assigned'] = len(assigned_verse_keys)
            
            content_query = f"""
            SELECT ttb."bookNo", ttc."chapterNo", ttc.content::text as content_text
            FROM text_translation_chapters ttc
            JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
            JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
            WHERE tp."projectId" = '{project_id}'
              AND ttc.version > 1
            """
            content_df = self.execute_query(content_query)
            
            verses_with_content = set()
            
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
                                        verses_with_content.add((book, chapter, verse_num_int))
                                        
                except Exception as e:
                    pass
            
            result['verses_with_content'] = len(verses_with_content)
            
            if result['total_verses_assigned'] > 0:
                result['completion_pct'] = round((result['verses_with_content'] / result['total_verses_assigned']) * 100, 1)
            
        except Exception as e:
            print(f"  Error in Bible completion: {e}")
        
        return result
    
    def _get_grammar_completion(self, project_id: str, grammar_type: str) -> Dict[str, Any]:
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
    
    def _get_literature_completion(self, project_id: str) -> Dict[str, Any]:
        """Get literature completion metrics - uses latest version per genre"""
        result = {
            'total_blocks': 0,
            'filled_blocks': 0,
            'completion_pct': 0,
            'genres': {}
        }
        
        try:
            # Get latest version per genre
            query = f"""
            SELECT DISTINCT ON (lg."genreId")
                lg."genreId",
                lg.name as genre_name,
                lpg.content,
                lpg.version
            FROM literature_project_genres_history lpg
            JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
            JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
            WHERE lp."projectId" = '{project_id}'
              AND lpg.version > 1
            ORDER BY lg."genreId", lpg.version DESC
            """
            df = self.execute_query(query)
            
            for _, row in df.iterrows():
                genre_id = row['genreId']
                genre_name = self.literature_genre_display.get(genre_id, genre_id)
                content = row['content']
                
                if content:
                    try:
                        if isinstance(content, str):
                            data = json.loads(content)
                        else:
                            data = content
                        
                        if 'content' in data and isinstance(data['content'], list):
                            blocks = data['content']
                            total = len(blocks)
                            filled = sum(1 for b in blocks if isinstance(b, dict) and b.get('content', '').strip())
                            
                            result['total_blocks'] += total
                            result['filled_blocks'] += filled
                            result['genres'][genre_name] = {
                                'total_blocks': total,
                                'filled_blocks': filled,
                                'completion_pct': round((filled / total * 100), 1) if total > 0 else 0
                            }
                    except:
                        pass
            
            if result['total_blocks'] > 0:
                result['completion_pct'] = round((result['filled_blocks'] / result['total_blocks']) * 100, 1)
                
        except Exception as e:
            print(f"  Error in Literature completion: {e}")
        
        return result
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate AG Drafting Monitoring Report - PROJECT LEVEL completion"""
        
        # Get all distinct countries and languages with projects
        query = """
        SELECT DISTINCT 
            c.name as country,
            l.name as language,
            COALESCE(NULLIF(l."isoCode", ''), 'NA') as cluster
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
            cluster = loc['cluster'] if loc['cluster'] else 'NA'
            date_of_report = ''
            
            # Get MTT names
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
                'Cluster': cluster,
                'Language_Dup': language,
                'Date of Report': date_of_report,
                'MTT Names': mtt_names,
                # OBS
                'OBS_Chapters_Assigned': 0,
                'OBS_Chapters_Translated': 0,
                # Bible
                'Bible_Verses_Assigned': 0,
                'Bible_Verses_Completed': 0,
                # Literature - Overall
                'Literature_Total_Blocks': 0,
                'Literature_Filled_Blocks': 0,
                # Literature - Genre Breakdown
                'Childrens_Lit_Total': 0,
                'Childrens_Lit_Filled': 0,
                'Formal_Writing_Total': 0,
                'Formal_Writing_Filled': 0,
                'History_Total': 0,
                'History_Filled': 0,
                'Literature_Genre_Total': 0,
                'Literature_Genre_Filled': 0,
                'Narrative_Total': 0,
                'Narrative_Filled': 0,
                'Poetry_Total': 0,
                'Poetry_Filled': 0,
                # Grammar
                'Grammar_Pronouns_Total': 0,
                'Grammar_Pronouns_Completed': 0,
                'Grammar_Connectives_Total': 0,
                'Grammar_Connectives_Completed': 0,
                'Grammar_Phrases_Total': 0,
                'Grammar_Phrases_Completed': 0
            }
            
            # ============================================================
            # OBS
            # ============================================================
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
                
                translated_chapters = set()
                for _, r in complete_df.iterrows():
                    chapter_no = r['chapterNo']
                    data_text = r['data_text']
                    if self._is_obs_chapter_translated(data_text):
                        translated_chapters.add(chapter_no)
                
                row['OBS_Chapters_Translated'] = len([ch for ch in assigned_chapters if ch in translated_chapters])
            
            # ============================================================
            # Bible
            # ============================================================
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
            
            # ============================================================
            # Literature
            # ============================================================
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
                lit_completion = self._get_literature_completion(project_id)
                
                # Overall Literature
                row['Literature_Total_Blocks'] = lit_completion['total_blocks']
                row['Literature_Filled_Blocks'] = lit_completion['filled_blocks']
                
                # Genre Breakdown
                for genre_name, data in lit_completion['genres'].items():
                    if genre_name == "Children's Literature":
                        row['Childrens_Lit_Total'] = data['total_blocks']
                        row['Childrens_Lit_Filled'] = data['filled_blocks']
                    elif genre_name == "Formal Writing":
                        row['Formal_Writing_Total'] = data['total_blocks']
                        row['Formal_Writing_Filled'] = data['filled_blocks']
                    elif genre_name == "History":
                        row['History_Total'] = data['total_blocks']
                        row['History_Filled'] = data['filled_blocks']
                    elif genre_name == "Literature":
                        row['Literature_Genre_Total'] = data['total_blocks']
                        row['Literature_Genre_Filled'] = data['filled_blocks']
                    elif genre_name == "Narrative":
                        row['Narrative_Total'] = data['total_blocks']
                        row['Narrative_Filled'] = data['filled_blocks']
                    elif genre_name == "Poetry":
                        row['Poetry_Total'] = data['total_blocks']
                        row['Poetry_Filled'] = data['filled_blocks']
            
            # ============================================================
            # Grammar
            # ============================================================
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
            'Country', 'Language', 'Cluster', 'Language_Dup', 'Date of Report', 'MTT Names',
            'OBS_Chapters_Assigned', 'OBS_Chapters_Translated',
            'Bible_Verses_Assigned', 'Bible_Verses_Completed',
            'Literature_Total_Blocks', 'Literature_Filled_Blocks',
            'Childrens_Lit_Total', 'Childrens_Lit_Filled',
            'Formal_Writing_Total', 'Formal_Writing_Filled',
            'History_Total', 'History_Filled',
            'Literature_Genre_Total', 'Literature_Genre_Filled',
            'Narrative_Total', 'Narrative_Filled',
            'Poetry_Total', 'Poetry_Filled',
            'Grammar_Pronouns_Total', 'Grammar_Pronouns_Completed',
            'Grammar_Connectives_Total', 'Grammar_Connectives_Completed',
            'Grammar_Phrases_Total', 'Grammar_Phrases_Completed'
        ]
        
        existing_columns = [col for col in column_order if col in report_df.columns]
        report_df = report_df[existing_columns]
        
        if not report_df.empty:
            report_df = report_df.sort_values(['Country', 'Language'])
        
        return {
            'monitoring_report': report_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'monitoring_report': 'AG Drafting Monitoring Report'
        }
