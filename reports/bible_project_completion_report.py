"""
Bible Text Project Completion Report - Track assigned vs completed work for Bible Translation projects
"""

import pandas as pd
import json
from typing import Dict, Any, Set, Tuple
from reports.base_report import BaseReport
from config.book_mapping_config import get_book_mapping_config


class BibleProjectCompletionReport(BaseReport):
    """Bible Text Project Completion Report - Track assigned vs completed for Bible projects"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'role', 'country', 'language']
        self.book_mapping = get_book_mapping_config()
    
    def _extract_verses_from_content(self, content_text: str, book: int, chapter: int) -> Set[str]:
        completed = set()
        try:
            if content_text and content_text != '{}':
                data = json.loads(content_text) if isinstance(content_text, str) else content_text
                if 'content' in data:
                    for item in data['content']:
                        verse_text = item.get('text', '')
                        if verse_text and verse_text.strip():
                            verse_num = item.get('start') or item.get('end')
                            if verse_num:
                                verse_id = f"{book:03d}{chapter:03d}{int(verse_num):03d}"
                                completed.add(verse_id)
        except:
            pass
        return completed
    
    def _parse_assigned_verse(self, verse_id: str) -> Tuple[int, int, int]:
        try:
            if verse_id and len(verse_id) >= 9:
                book = int(verse_id[:3])
                chapter = int(verse_id[3:6])
                verse = int(verse_id[6:9])
                return book, chapter, verse
        except:
            pass
        return None, None, None
    
    def _map_assigned_verse(self, verse_id: str) -> str:
        try:
            if len(verse_id) >= 9:
                book = int(verse_id[:3])
                chapter = int(verse_id[3:6])
                verse = int(verse_id[6:9])
                mapped_book = self.book_mapping.map_book(book)
                return f"{mapped_book:03d}{chapter:03d}{verse:03d}"
        except:
            pass
        return verse_id
    
    def _get_performance_rating(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return "🏆 Excellent"
        elif completion_pct >= 75:
            return "👍 Good"
        elif completion_pct >= 50:
            return "⭐ Average"
        elif completion_pct >= 25:
            return "⚠️ Needs Improvement"
        else:
            return "❌ Poor"
    
    def _get_status(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return "Completed"
        elif completion_pct > 0:
            return "In Progress"
        else:
            return "Not Started"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate Bible project completion report"""
        
        projects_query = """
        SELECT 
            p.id as project_id,
            p.name as project_name,
            p."projectType" as project_type,
            l.name as language_name,
            l."isoCode" as language_code,
            c.name as country,
            c."countryCode" as country_code
        FROM projects p
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE p."projectType" = 'TEXT_TRANSLATION'
        ORDER BY p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} Bible translation projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # MTT assignments with proper name from users.name
        mtt_assignments_query = """
        SELECT 
            utp."projectId",
            p.name as project_name,
            l.name as language_name,
            c.name as country,
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            utp.verses as assigned_verses_raw,
            array_length(string_to_array(COALESCE(utp.verses, ''), ','), 1) as verses_assigned_count,
            utp.role as project_role
        FROM users_to_projects utp
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users u ON utp."userId" = u.id
        WHERE utp.verses IS NOT NULL 
          AND utp.verses != ''
          AND p."projectType" = 'TEXT_TRANSLATION'
          AND utp.role = 'MTT'
        ORDER BY p.name, u.username
        """
        
        try:
            mtt_assignments_df = self.execute_query(mtt_assignments_query)
            print(f"✅ Retrieved {len(mtt_assignments_df)} MTT assignment records")
        except Exception as e:
            print(f"❌ MTT assignments query failed: {e}")
            mtt_assignments_df = pd.DataFrame()
        
        # Get UNIQUE assigned verses per project
        project_assigned_verses = {}
        project_assigned_chapters = {}
        
        for _, project_row in projects_df.iterrows():
            project_id = project_row['project_id']
            try:
                verses_query = f"""
                SELECT DISTINCT trim(unnest(string_to_array(COALESCE(utp.verses, ''), ','))) as verse_id
                FROM users_to_projects utp
                WHERE utp."projectId" = '{project_id}'
                  AND utp.role = 'MTT'
                  AND utp.verses IS NOT NULL
                """
                verses_df = self.execute_query(verses_query)
                verses = set()
                chapters = set()
                for _, row in verses_df.iterrows():
                    verse_id = row['verse_id'].strip()
                    if verse_id and len(verse_id) >= 6:
                        verses.add(verse_id)
                        book, chapter, verse = self._parse_assigned_verse(verse_id)
                        if book and chapter:
                            mapped_book = self.book_mapping.map_book(book)
                            chapters.add((mapped_book, chapter))
                if verses:
                    project_assigned_verses[project_id] = verses
                    project_assigned_chapters[project_id] = chapters
            except Exception as e:
                print(f"  Warning: Could not get verses for {project_id}: {e}")
        
        print(f"✅ Found assigned verses for {len(project_assigned_verses)} projects")
        
        completed_work_query = """
        SELECT 
            tp."projectId",
            ttb."bookNo",
            ttc."chapterNo",
            ttc.version,
            ttc.content::text as content_text
        FROM text_translation_chapters ttc
        LEFT JOIN text_translation_books ttb ON ttc."textTranslationBookId" = ttb.id
        LEFT JOIN text_translation_projects tp ON ttb."textTranslationProjectId" = tp.id
        WHERE ttc.version > 1
          AND ttc.content IS NOT NULL
        """
        
        try:
            completed_df = self.execute_query(completed_work_query)
            print(f"✅ Retrieved {len(completed_df)} chapters with completion data")
            
            project_completed_chapters = {}
            project_completed_verses = {}
            
            for _, row in completed_df.iterrows():
                project_id = row['projectId']
                book = int(row['bookNo'])
                chapter = int(row['chapterNo'])
                content_text = row['content_text']
                
                if project_id not in project_completed_chapters:
                    project_completed_chapters[project_id] = set()
                    project_completed_verses[project_id] = set()
                
                project_completed_chapters[project_id].add((book, chapter))
                
                if content_text:
                    verses = self._extract_verses_from_content(content_text, book, chapter)
                    for verse_id in verses:
                        project_completed_verses[project_id].add(verse_id)
            
            print(f"✅ Processed completion for {len(project_completed_chapters)} projects")
        except Exception as e:
            print(f"❌ Completed work query failed: {e}")
            project_completed_chapters = {}
            project_completed_verses = {}
        
        # PROJECT-LEVEL STATUS
        project_status = []
        
        for project_id, assigned_verses in project_assigned_verses.items():
            project_info = projects_df[projects_df['project_id'] == project_id]
            project_name = project_info.iloc[0]['project_name'] if not project_info.empty else 'Unknown'
            language = project_info.iloc[0]['language_name'] if not project_info.empty else ''
            country = project_info.iloc[0]['country'] if not project_info.empty else ''
            
            mtt_info = mtt_assignments_df[mtt_assignments_df['projectId'] == project_id]
            mtt_count = mtt_info['user_id'].nunique() if not mtt_info.empty else 0
            mtt_names = ', '.join(mtt_info['full_name'].unique()) if not mtt_info.empty else ''
            
            total_verses_assigned = len(assigned_verses)
            total_chapters_assigned = len(project_assigned_chapters.get(project_id, set()))
            
            completed_chapters = len([ch for ch in project_assigned_chapters.get(project_id, set()) 
                                      if ch in project_completed_chapters.get(project_id, set())])
            
            mapped_assigned_verses = set()
            for verse_id in assigned_verses:
                mapped_assigned_verses.add(self._map_assigned_verse(verse_id))
            
            completed_verses = len([v for v in mapped_assigned_verses 
                                    if v in project_completed_verses.get(project_id, set())])
            
            chapter_pct = (completed_chapters / total_chapters_assigned * 100) if total_chapters_assigned > 0 else 0
            verse_pct = (completed_verses / total_verses_assigned * 100) if total_verses_assigned > 0 else 0
            
            chapter_pct = min(chapter_pct, 100)
            verse_pct = min(verse_pct, 100)
            
            status = self._get_status(verse_pct)
            
            project_status.append({
                'Project ID': project_id,
                'Project Name': project_name,
                'Language': language,
                'Country': country,
                'MTTs Assigned': mtt_count,
                'MTT Names': mtt_names[:300],
                'Verses Assigned': total_verses_assigned,
                'Verses Completed': completed_verses,
                'Verse Completion %': round(verse_pct, 2),
                'Chapters Assigned': total_chapters_assigned,
                'Chapters Completed': completed_chapters,
                'Chapter Completion %': round(chapter_pct, 2),
                'Status': status
            })
        
        project_status_df = pd.DataFrame(project_status)
        if not project_status_df.empty:
            project_status_df = project_status_df.sort_values('Verse Completion %', ascending=False)
        
        # MTT-LEVEL PERFORMANCE
        mtt_performance = []
        
        if not mtt_assignments_df.empty:
            for _, row in mtt_assignments_df.iterrows():
                project_id = row['projectId']
                user_id = row['user_id']
                username = row['username']
                full_name = row['full_name']
                email = row['email']
                project_name = row['project_name']
                language = row['language_name']
                country = row['country']
                assigned_verses_raw = row['assigned_verses_raw']
                
                assigned_verses = set()
                assigned_chapters = set()
                for verse_id in assigned_verses_raw.split(','):
                    verse_id = verse_id.strip()
                    if verse_id and len(verse_id) >= 6:
                        assigned_verses.add(verse_id)
                        book, chapter, verse = self._parse_assigned_verse(verse_id)
                        if book and chapter:
                            mapped_book = self.book_mapping.map_book(book)
                            assigned_chapters.add((mapped_book, chapter))
                
                verses_assigned = len(assigned_verses)
                chapters_assigned = len(assigned_chapters)
                
                mapped_verses = set()
                for verse_id in assigned_verses:
                    mapped_verses.add(self._map_assigned_verse(verse_id))
                
                completed_verses = len([v for v in mapped_verses 
                                        if v in project_completed_verses.get(project_id, set())])
                
                completed_chapters = len([ch for ch in assigned_chapters 
                                          if ch in project_completed_chapters.get(project_id, set())])
                
                chapter_pct = (completed_chapters / chapters_assigned * 100) if chapters_assigned > 0 else 0
                verse_pct = (completed_verses / verses_assigned * 100) if verses_assigned > 0 else 0
                
                chapter_pct = min(chapter_pct, 100)
                verse_pct = min(verse_pct, 100)
                
                mtt_status = self._get_status(verse_pct)
                performance_rating = self._get_performance_rating(verse_pct)
                
                mtt_performance.append({
                    'Project ID': project_id,
                    'Project Name': project_name,
                    'Language': language,
                    'Country': country,
                    'MTT User ID': user_id,
                    'MTT Username': username,
                    'MTT Full Name': full_name,
                    'MTT Email': email,
                    'Verses Assigned': verses_assigned,
                    'Verses Completed': completed_verses,
                    'Verse Completion %': round(verse_pct, 2),
                    'Chapters Assigned': chapters_assigned,
                    'Chapters Completed': completed_chapters,
                    'Chapter Completion %': round(chapter_pct, 2),
                    'Performance Rating': performance_rating,
                    'Status': mtt_status
                })
        
        mtt_performance_df = pd.DataFrame(mtt_performance)
        if not mtt_performance_df.empty:
            mtt_performance_df = mtt_performance_df.sort_values('Verse Completion %', ascending=False)
        
        # Summary Statistics
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total Bible Translation Projects', 'Value': len(projects_df)})
        
        if not project_status_df.empty:
            summary_data.append({'Metric': 'Projects with MTTs', 'Value': len(project_status_df)})
            summary_data.append({'Metric': 'Total Verses Assigned', 'Value': project_status_df['Verses Assigned'].sum()})
            summary_data.append({'Metric': 'Total Verses Completed', 'Value': project_status_df['Verses Completed'].sum()})
            summary_data.append({'Metric': 'Total Chapters Assigned', 'Value': project_status_df['Chapters Assigned'].sum()})
            summary_data.append({'Metric': 'Total Chapters Completed', 'Value': project_status_df['Chapters Completed'].sum()})
            
            total_verses = project_status_df['Verses Assigned'].sum()
            if total_verses > 0:
                summary_data.append({'Metric': 'Overall Verse Completion Rate', 'Value': f"{(project_status_df['Verses Completed'].sum()/total_verses*100):.1f}%"})
            
            completed = len(project_status_df[project_status_df['Status'] == 'Completed'])
            in_progress = len(project_status_df[project_status_df['Status'] == 'In Progress'])
            not_started = len(project_status_df[project_status_df['Status'] == 'Not Started'])
            
            summary_data.append({'Metric': 'Fully Completed Projects', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Projects', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Projects', 'Value': not_started})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'projects_overview': projects_df,
            'mtt_assignments': mtt_assignments_df,
            'project_status': project_status_df,
            'mtt_performance': mtt_performance_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'projects_overview': '1. All Bible Projects',
            'mtt_assignments': '2. MTT Assignments',
            'project_status': '3. Assigned vs Completed',
            'mtt_performance': '4. MTT Performance',
            'summary_stats': '5. Summary Statistics'
        }
