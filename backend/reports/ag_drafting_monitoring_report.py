"""
AG Drafting Monitoring Report - Consolidated report for all project types
PROJECT-LEVEL COMPLETION with proper metrics for Bible, OBS, Literature, and Grammar
Uses BaseReportV3 for dynamic dialect/ROLV support
"""

import pandas as pd
import json
from typing import Dict, Any, Set
from reports.base_report_v3 import BaseReportV3


class AGDraftingMonitoringReport(BaseReportV3):
    """AG Drafting Monitoring Report - PROJECT-LEVEL completion across all types"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        
        # Map assigned book numbers to standard Bible book numbers
        self.book_mapping = {}
        for i in range(101, 167):
            self.book_mapping[i] = i - 100
        for i in range(240, 267):
            self.book_mapping[i] = i - 200
        
        # OBS Completion Thresholds for translation
        # Title and bibleRef are optional; only paragraph completion is required.
        self.obs_translation_thresholds = {
            'title_required': False,
            'bibleref_required': False,
            'paragraphs_required_percent': 100
        }
        
        # Literature genre mapping - standard order
        self.literature_genre_display = {
            'childrens_literature': "Children's Literature",
            'formal_writing': 'Formal Writing',
            'history': 'History',
            'literature': 'Literature',
            'narrative': 'Narrative',
            'poetry': 'Poetry'
        }
        
        # Include languages without dialects in the report
        self.include_null_dialects = True
    
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
        """Generate AG Drafting Monitoring Report with one row per language-dialect-project combination"""
        
        project_types = [
            'TEXT_TRANSLATION', 'OBS', 'LITERATURE', 'LITERATURE_PROJECT',
            'GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES'
        ]
        projects_df = self.get_all_projects(project_types=project_types, include_dialect_info=True)
        
        if projects_df.empty:
            print("❌ No AG Drafting projects found")
            return {'monitoring_report': pd.DataFrame({'Message': ['No data available']})}
        
        print(f"✅ Retrieved {len(projects_df)} projects for AG Drafting report")
        
        report_data = []
        
        for _, proj in projects_df.iterrows():
            country = proj['country'] if proj['country'] else ''
            language = proj['language_name'] if proj['language_name'] else ''
            dialect_name = proj['dialect_name'] if proj['dialect_name'] else ''
            rolv_code = proj['rolv_code'] if proj['rolv_code'] else ''
            cluster = proj['language_code'] if proj['language_code'] else 'NA'
            project_id = proj['project_id']
            project_type = proj['project_type']
            project_name = proj['project_name'] if proj['project_name'] else ''
            mtt_count, mtt_names = self.get_mtt_names_for_project(project_id)
            
            row = {
                'Country': country,
                'Language': language,
                'Dialect': dialect_name,
                'ROLV Code': rolv_code,
                'lan_iso_code': cluster,
                'Date of Report': '',
                'Project Type': project_type,
                'Project Name': project_name,
                'MTT Names': mtt_names,
                'Project Count': 1,
                'Project Names': project_name,
                'OBS_Chapters_Assigned': 0,
                'OBS_Chapters_Translated': 0,
                'Bible_Verses_Assigned': 0,
                'Bible_Verses_Completed': 0,
                'Literature_Total_Blocks': 0,
                'Literature_Filled_Blocks': 0,
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
                'Grammar_Pronouns_Total': 0,
                'Grammar_Pronouns_Completed': 0,
                'Grammar_Connectives_Total': 0,
                'Grammar_Connectives_Completed': 0,
                'Grammar_Phrases_Total': 0,
                'Grammar_Phrases_Completed': 0
            }
            
            if project_type == 'OBS':
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
                
                row['OBS_Chapters_Assigned'] += len(assigned_chapters)
                
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
                
                row['OBS_Chapters_Translated'] += len([ch for ch in assigned_chapters if ch in translated_chapters])
            
            elif project_type == 'TEXT_TRANSLATION':
                bible_completion = self._get_bible_verse_completion(project_id)
                row['Bible_Verses_Assigned'] += bible_completion['total_verses_assigned']
                row['Bible_Verses_Completed'] += bible_completion['verses_with_content']
            
            elif project_type in ('LITERATURE', 'LITERATURE_PROJECT'):
                lit_completion = self._get_literature_completion(project_id)
                
                row['Literature_Total_Blocks'] += lit_completion['total_blocks']
                row['Literature_Filled_Blocks'] += lit_completion['filled_blocks']
                
                for genre_name, data in lit_completion['genres'].items():
                    if genre_name == "Children's Literature":
                        row['Childrens_Lit_Total'] += data['total_blocks']
                        row['Childrens_Lit_Filled'] += data['filled_blocks']
                    elif genre_name == "Formal Writing":
                        row['Formal_Writing_Total'] += data['total_blocks']
                        row['Formal_Writing_Filled'] += data['filled_blocks']
                    elif genre_name == "History":
                        row['History_Total'] += data['total_blocks']
                        row['History_Filled'] += data['filled_blocks']
                    elif genre_name == "Literature":
                        row['Literature_Genre_Total'] += data['total_blocks']
                        row['Literature_Genre_Filled'] += data['filled_blocks']
                    elif genre_name == "Narrative":
                        row['Narrative_Total'] += data['total_blocks']
                        row['Narrative_Filled'] += data['filled_blocks']
                    elif genre_name == "Poetry":
                        row['Poetry_Total'] += data['total_blocks']
                        row['Poetry_Filled'] += data['filled_blocks']
            
            elif project_type == 'GRAMMAR_PRONOUNS':
                completion = self._get_grammar_completion(project_id, 'GRAMMAR_PRONOUNS')
                row['Grammar_Pronouns_Total'] += completion['total_items']
                row['Grammar_Pronouns_Completed'] += completion['completed_items']
            elif project_type == 'GRAMMAR_CONNECTIVES':
                completion = self._get_grammar_completion(project_id, 'GRAMMAR_CONNECTIVES')
                row['Grammar_Connectives_Total'] += completion['total_items']
                row['Grammar_Connectives_Completed'] += completion['completed_items']
            elif project_type == 'GRAMMAR_PHRASES':
                completion = self._get_grammar_completion(project_id, 'GRAMMAR_PHRASES')
                row['Grammar_Phrases_Total'] += completion['total_items']
                row['Grammar_Phrases_Completed'] += completion['completed_items']
            
            report_data.append(row)
        
        report_df = pd.DataFrame(report_data)
        
        # Column order
        column_order = [
            'Country', 'Language', 'Dialect', 'ROLV Code', 'lan_iso_code', 'Date of Report',
            'Project Type', 'Project Name', 'MTT Names', 'Project Count', 'Project Names',
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
            report_df = report_df.sort_values(['Country', 'Language', 'Dialect', 'Project Name'])
        
        rows_with_dialect = len(report_df[report_df['Dialect'] != ''])
        rows_without_dialect = len(report_df[report_df['Dialect'] == ''])
        
        print(f"✅ Generated report with {len(report_df)} rows")
        print(f"   - Rows with dialect: {rows_with_dialect}")
        print(f"   - Rows WITHOUT dialect (NULL dialectId): {rows_without_dialect}")
        
        # Build the legacy aggregated sheet by language-dialect
        aggregated_df = self._build_language_dialect_summary()
        
        return {
            'project_level': report_df,
            'language_dialect_summary': aggregated_df
        }
    
    def _build_language_dialect_summary(self) -> pd.DataFrame:
        """Build a secondary sheet with one row per language-dialect combination"""
        combinations_df = self.get_all_language_dialect_combinations()
        
        if combinations_df.empty:
            return pd.DataFrame()
        
        report_data = []
        for _, combo in combinations_df.iterrows():
            country = combo['country']
            language = combo['language']
            dialect_name = combo['dialect_name'] if combo['dialect_name'] else ''
            rolv_code = combo['rolv_code'] if combo['rolv_code'] else ''
            cluster = combo['lan_iso_code'] if combo['lan_iso_code'] else 'NA'
            
            projects_df = self.get_projects_by_language_dialect(language, dialect_name if dialect_name else None)
            mtt_names = self.get_mtt_names_for_language_dialect(language, dialect_name if dialect_name else None)
            
            row = {
                'Country': country,
                'Language': language,
                'Dialect': dialect_name,
                'ROLV Code': rolv_code,
                'lan_iso_code': cluster,
                'Date of Report': '',
                'MTT Names': mtt_names,
                'Project Count': 0,
                'Project Names': '',
                'OBS_Chapters_Assigned': 0,
                'OBS_Chapters_Translated': 0,
                'Bible_Verses_Assigned': 0,
                'Bible_Verses_Completed': 0,
                'Literature_Total_Blocks': 0,
                'Literature_Filled_Blocks': 0,
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
                'Grammar_Pronouns_Total': 0,
                'Grammar_Pronouns_Completed': 0,
                'Grammar_Connectives_Total': 0,
                'Grammar_Connectives_Completed': 0,
                'Grammar_Phrases_Total': 0,
                'Grammar_Phrases_Completed': 0
            }
            
            project_names = []
            for _, proj in projects_df.iterrows():
                project_names.append(proj['project_name'])
                project_id = proj['project_id']
                project_type = proj['project_type']
                
                if project_type == 'OBS':
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
                    
                    row['OBS_Chapters_Assigned'] += len(assigned_chapters)
                    
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
                    
                    row['OBS_Chapters_Translated'] += len([ch for ch in assigned_chapters if ch in translated_chapters])
                elif project_type == 'TEXT_TRANSLATION':
                    bible_completion = self._get_bible_verse_completion(project_id)
                    row['Bible_Verses_Assigned'] += bible_completion['total_verses_assigned']
                    row['Bible_Verses_Completed'] += bible_completion['verses_with_content']
                elif project_type in ('LITERATURE', 'LITERATURE_PROJECT'):
                    lit_completion = self._get_literature_completion(project_id)
                    row['Literature_Total_Blocks'] += lit_completion['total_blocks']
                    row['Literature_Filled_Blocks'] += lit_completion['filled_blocks']
                    for genre_name, data in lit_completion['genres'].items():
                        if genre_name == "Children's Literature":
                            row['Childrens_Lit_Total'] += data['total_blocks']
                            row['Childrens_Lit_Filled'] += data['filled_blocks']
                        elif genre_name == "Formal Writing":
                            row['Formal_Writing_Total'] += data['total_blocks']
                            row['Formal_Writing_Filled'] += data['filled_blocks']
                        elif genre_name == "History":
                            row['History_Total'] += data['total_blocks']
                            row['History_Filled'] += data['filled_blocks']
                        elif genre_name == "Literature":
                            row['Literature_Genre_Total'] += data['total_blocks']
                            row['Literature_Genre_Filled'] += data['filled_blocks']
                        elif genre_name == "Narrative":
                            row['Narrative_Total'] += data['total_blocks']
                            row['Narrative_Filled'] += data['filled_blocks']
                        elif genre_name == "Poetry":
                            row['Poetry_Total'] += data['total_blocks']
                            row['Poetry_Filled'] += data['filled_blocks']
                elif project_type == 'GRAMMAR_PRONOUNS':
                    completion = self._get_grammar_completion(project_id, 'GRAMMAR_PRONOUNS')
                    row['Grammar_Pronouns_Total'] += completion['total_items']
                    row['Grammar_Pronouns_Completed'] += completion['completed_items']
                elif project_type == 'GRAMMAR_CONNECTIVES':
                    completion = self._get_grammar_completion(project_id, 'GRAMMAR_CONNECTIVES')
                    row['Grammar_Connectives_Total'] += completion['total_items']
                    row['Grammar_Connectives_Completed'] += completion['completed_items']
                elif project_type == 'GRAMMAR_PHRASES':
                    completion = self._get_grammar_completion(project_id, 'GRAMMAR_PHRASES')
                    row['Grammar_Phrases_Total'] += completion['total_items']
                    row['Grammar_Phrases_Completed'] += completion['completed_items']
            
            row['Project Count'] = len(project_names)
            row['Project Names'] = ', '.join(project_names)
            report_data.append(row)
        
        aggregated_df = pd.DataFrame(report_data)
        column_order = [
            'Country', 'Language', 'Dialect', 'ROLV Code', 'lan_iso_code', 'Date of Report',
            'MTT Names', 'Project Count', 'Project Names',
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
        existing_columns = [col for col in column_order if col in aggregated_df.columns]
        aggregated_df = aggregated_df[existing_columns]
        if not aggregated_df.empty:
            aggregated_df = aggregated_df.sort_values(['Country', 'Language', 'Dialect'])
        return aggregated_df
    
