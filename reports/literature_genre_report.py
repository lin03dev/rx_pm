"""
Literature Genre Report - Complete report with genre-level details
Includes: Projects Overview, MTT Assignments, Project Status, MTT Performance, Genre Details, Summary Statistics
"""

import pandas as pd
import json
import re
from typing import Dict, Any, List
from reports.base_report import BaseReport


class LiteratureGenreReport(BaseReport):
    """Literature Genre Report - Complete report with genre-level breakdown"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'country']
    
    def _count_sentences(self, text: str) -> int:
        """Count number of sentences in text"""
        if not text:
            return 0
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _analyze_genre_content(self, content) -> Dict[str, Any]:
        """Analyze content for a single genre"""
        result = {
            'total_sections': 0,
            'sections_completed': 0,
            'section_completion_pct': 0,
            'total_sentences': 0,
            'total_words': 0,
            'total_characters': 0,
            'has_content': False
        }
        
        if content is None:
            return result
        
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            if 'content' in data and isinstance(data['content'], list):
                sections = data['content']
                result['total_sections'] = len(sections)
                
                total_sentences = 0
                total_words = 0
                total_chars = 0
                sections_completed = 0
                
                for section in sections:
                    if isinstance(section, dict):
                        text = section.get('content', '')
                        if text and text.strip():
                            sections_completed += 1
                            sentences = self._count_sentences(text)
                            total_sentences += sentences
                            total_words += len(text.split())
                            total_chars += len(text)
                
                result['sections_completed'] = sections_completed
                result['total_sentences'] = total_sentences
                result['total_words'] = total_words
                result['total_characters'] = total_chars
                result['has_content'] = sections_completed > 0
                
                if result['total_sections'] > 0:
                    result['section_completion_pct'] = (sections_completed / result['total_sections'] * 100)
        except:
            pass
        
        return result
    
    def _get_performance_rating(self, section_pct: float, sentence_count: int) -> str:
        if section_pct >= 100 and sentence_count >= 200:
            return "🏆 Excellent (High Quality)"
        elif section_pct >= 100 and sentence_count >= 100:
            return "✅ Good (Completed)"
        elif section_pct >= 100:
            return "⚠️ Completed (Low Content)"
        elif section_pct >= 75:
            return "👍 Almost Complete"
        elif section_pct >= 50:
            return "⭐ Half Complete"
        elif section_pct >= 25:
            return "🔨 In Progress"
        elif section_pct > 0:
            return "📝 Just Started"
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
        """Generate complete literature report with genre-level details"""
        
        # ============================================================
        # Sheet 1 - All Literature Projects Overview
        # ============================================================
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
        WHERE p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
        ORDER BY p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} Literature projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 2 - MTT Assignments
        # ============================================================
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
            utp."literatureGenres" as assigned_genres_raw,
            array_length(string_to_array(COALESCE(utp."literatureGenres", ''), ','), 1) as genres_assigned_count,
            utp.role as project_role
        FROM users_to_projects utp
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users u ON utp."userId" = u.id
        WHERE utp."literatureGenres" IS NOT NULL 
          AND utp."literatureGenres" != ''
          AND p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
          AND utp.role = 'MTT'
        ORDER BY p.name, u.username
        """
        
        try:
            mtt_assignments_df = self.execute_query(mtt_assignments_query)
            print(f"✅ Retrieved {len(mtt_assignments_df)} MTT assignment records")
        except Exception as e:
            print(f"❌ MTT assignments query failed: {e}")
            mtt_assignments_df = pd.DataFrame()
        
        # ============================================================
        # Sheet 3 - Project Status (Aggregated)
        # ============================================================
        project_status_query = """
        SELECT DISTINCT ON (lp."projectId")
            lp."projectId",
            lpg.version,
            lpg.content,
            lpg."userId" as completed_by,
            lpg."updatedAt" as last_updated
        FROM literature_project_genres_history lpg
        JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
        JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
        WHERE lpg.version > 1
        ORDER BY lp."projectId", lpg.version DESC
        """
        
        try:
            project_content_df = self.execute_query(project_status_query)
            print(f"✅ Retrieved {len(project_content_df)} projects with completion data")
            
            project_completion = {}
            for _, row in project_content_df.iterrows():
                project_id = row['projectId']
                content = row['content']
                version = row['version']
                completed_by = row.get('completed_by')
                
                # Get completed by name
                completed_by_name = completed_by
                if completed_by:
                    try:
                        name_query = f"""
                        SELECT COALESCE(NULLIF(u.name, ''), u.username) as name
                        FROM users u
                        WHERE u.id = '{completed_by}'
                        """
                        name_df = self.execute_query(name_query)
                        if not name_df.empty and name_df['name'].iloc[0]:
                            completed_by_name = name_df['name'].iloc[0]
                    except:
                        pass
                
                metrics = self._analyze_genre_content(content)
                
                project_completion[project_id] = {
                    'has_content': metrics['has_content'],
                    'version': version,
                    'completed_by': completed_by_name,
                    'total_sections': metrics['total_sections'],
                    'sections_completed': metrics['sections_completed'],
                    'section_completion_pct': metrics['section_completion_pct'],
                    'total_sentences': metrics['total_sentences'],
                    'total_words': metrics['total_words'],
                    'last_updated': row['last_updated']
                }
        except Exception as e:
            print(f"⚠️ Project status query: {e}")
            project_completion = {}
        
        # Build project status dataframe
        project_status_data = []
        for _, project in projects_df.iterrows():
            project_id = project['project_id']
            completion = project_completion.get(project_id, {})
            
            mtt_info = mtt_assignments_df[mtt_assignments_df['projectId'] == project_id]
            mtt_count = mtt_info['user_id'].nunique() if not mtt_info.empty else 0
            mtt_names = ', '.join(mtt_info['full_name'].unique()) if not mtt_info.empty else ''
            
            section_pct = completion.get('section_completion_pct', 0)
            status = self._get_status(section_pct)
            
            project_status_data.append({
                'Project ID': project_id,
                'Project Name': project['project_name'],
                'Project Type': project['project_type'],
                'Language': project['language_name'] or 'N/A',
                'Country': project['country'] or 'N/A',
                'MTTs Assigned': mtt_count,
                'MTT Names': mtt_names[:300] if mtt_names else '',
                'Has Content': 'Yes' if completion.get('has_content', False) else 'No',
                'Total Sections': completion.get('total_sections', 0),
                'Sections Completed': completion.get('sections_completed', 0),
                'Section Completion %': round(completion.get('section_completion_pct', 0), 2),
                'Total Sentences': completion.get('total_sentences', 0),
                'Total Words': completion.get('total_words', 0),
                'Version': completion.get('version', 0),
                'Completed By': completion.get('completed_by', ''),
                'Status': status
            })
        
        project_status_df = pd.DataFrame(project_status_data)
        
        # ============================================================
        # Sheet 4 - MTT Performance
        # ============================================================
        mtt_performance_data = []
        if not mtt_assignments_df.empty:
            for _, row in mtt_assignments_df.iterrows():
                project_id = row['projectId']
                completion = project_completion.get(project_id, {})
                
                mtt_performance_data.append({
                    'Project ID': project_id,
                    'Project Name': row['project_name'],
                    'Language': row['language_name'] or 'N/A',
                    'Country': row['country'] or 'N/A',
                    'MTT User ID': row['user_id'],
                    'MTT Username': row['username'],
                    'MTT Full Name': row['full_name'],
                    'MTT Email': row['email'],
                    'Genres Assigned': row['genres_assigned_count'],
                    'Has Content': 'Yes' if completion.get('has_content', False) else 'No',
                    'Total Sections': completion.get('total_sections', 0),
                    'Sections Completed': completion.get('sections_completed', 0),
                    'Section Completion %': round(completion.get('section_completion_pct', 0), 2),
                    'Total Sentences': completion.get('total_sentences', 0),
                    'Total Words': completion.get('total_words', 0),
                    'Status': self._get_status(completion.get('section_completion_pct', 0))
                })
        
        mtt_performance_df = pd.DataFrame(mtt_performance_data)
        
        # ============================================================
        # Sheet 5 - Genre Details (1 row per genre)
        # ============================================================
        genre_details_query = """
        SELECT DISTINCT ON (lpg."literatureProjectGenreId")
            p.id as project_id,
            p.name as project_name,
            p."projectType" as project_type,
            l.name as language_name,
            c.name as country,
            lg."genreId" as genre_type,
            lg.name as genre_name,
            lpg.version,
            lpg.content,
            lpg."userId" as completed_by_user_id,
            lpg."updatedAt" as last_updated
        FROM literature_project_genres_history lpg
        JOIN literature_project_genres lg ON lpg."literatureProjectGenreId" = lg.id
        JOIN literature_projects lp ON lg."literatureProjectId" = lp.id
        JOIN projects p ON lp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
          AND lpg.version > 1
        ORDER BY lpg."literatureProjectGenreId", lpg.version DESC
        """
        
        try:
            genre_df = self.execute_query(genre_details_query)
            print(f"✅ Retrieved {len(genre_df)} genre records")
        except Exception as e:
            print(f"⚠️ Genre details query: {e}")
            genre_df = pd.DataFrame()
        
        genre_details_data = []
        for _, row in genre_df.iterrows():
            content_analysis = self._analyze_genre_content(row['content'])
            
            completed_by = row['completed_by_user_id']
            completed_by_name = ''
            if completed_by:
                try:
                    name_query = f"""
                    SELECT COALESCE(NULLIF(u.name, ''), u.username) as name
                    FROM users u
                    WHERE u.id = '{completed_by}'
                    """
                    name_df = self.execute_query(name_query)
                    if not name_df.empty and name_df['name'].iloc[0]:
                        completed_by_name = name_df['name'].iloc[0]
                except:
                    completed_by_name = str(completed_by)[:8] if completed_by else ''
            
            genre_details_data.append({
                'Project ID': row['project_id'],
                'Project Name': row['project_name'],
                'Project Type': row['project_type'],
                'Language': row['language_name'] if row['language_name'] else 'N/A',
                'Country': row['country'] if row['country'] else 'N/A',
                'Genre ID': row['genre_type'],
                'Genre Name': row['genre_name'] if row['genre_name'] else row['genre_type'],
                'Total Sections': content_analysis['total_sections'],
                'Sections Completed': content_analysis['sections_completed'],
                'Section Completion %': round(content_analysis['section_completion_pct'], 2),
                'Total Sentences': content_analysis['total_sentences'],
                'Total Words': content_analysis['total_words'],
                'Total Characters': content_analysis['total_characters'],
                'Version': row['version'],
                'Completed By': completed_by_name,
                'Last Updated': row['last_updated'] if pd.notna(row['last_updated']) else '',
                'Status': self._get_status(content_analysis['section_completion_pct'])
            })
        
        genre_details_df = pd.DataFrame(genre_details_data)
        
        # ============================================================
        # Sheet 6 - Summary Statistics
        # ============================================================
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total Literature Projects', 'Value': len(projects_df)})
            summary_data.append({'Metric': '  - LITERATURE type', 'Value': len(projects_df[projects_df['project_type'] == 'LITERATURE'])})
            summary_data.append({'Metric': '  - LITERATURE_PROJECT type', 'Value': len(projects_df[projects_df['project_type'] == 'LITERATURE_PROJECT'])})
        
        if not project_status_df.empty:
            with_content = len(project_status_df[project_status_df['Has Content'] == 'Yes'])
            completed = len(project_status_df[project_status_df['Status'] == 'Completed'])
            in_progress = len(project_status_df[project_status_df['Status'] == 'In Progress'])
            not_started = len(project_status_df[project_status_df['Status'] == 'Not Started'])
            
            summary_data.append({'Metric': 'Projects with Content', 'Value': with_content})
            summary_data.append({'Metric': 'Completed Projects', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Projects', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Projects', 'Value': not_started})
        
        if not genre_details_df.empty:
            summary_data.append({'Metric': 'Total Genres', 'Value': len(genre_details_df)})
            summary_data.append({'Metric': 'Genres with Content', 'Value': len(genre_details_df[genre_details_df['Sections Completed'] > 0])})
            summary_data.append({'Metric': 'Completed Genres', 'Value': len(genre_details_df[genre_details_df['Status'] == 'Completed'])})
            summary_data.append({'Metric': 'In Progress Genres', 'Value': len(genre_details_df[genre_details_df['Status'] == 'In Progress'])})
            summary_data.append({'Metric': 'Not Started Genres', 'Value': len(genre_details_df[genre_details_df['Status'] == 'Not Started'])})
            summary_data.append({'Metric': 'Total Sections', 'Value': genre_details_df['Total Sections'].sum()})
            summary_data.append({'Metric': 'Sections Completed', 'Value': genre_details_df['Sections Completed'].sum()})
            summary_data.append({'Metric': 'Total Sentences', 'Value': genre_details_df['Total Sentences'].sum()})
            summary_data.append({'Metric': 'Total Words', 'Value': genre_details_df['Total Words'].sum()})
        
        if not mtt_assignments_df.empty:
            summary_data.append({'Metric': 'Total MTTs Assigned', 'Value': mtt_assignments_df['user_id'].nunique()})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'projects_overview': projects_df,
            'mtt_assignments': mtt_assignments_df,
            'project_status': project_status_df,
            'mtt_performance': mtt_performance_df,
            'genre_details': genre_details_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'projects_overview': '1 - All Literature Projects',
            'mtt_assignments': '2 - MTT Assignments',
            'project_status': '3 - Project Status',
            'mtt_performance': '4 - MTT Performance',
            'genre_details': '5 - Genre Details (1 row per genre)',
            'summary_stats': '6 - Summary Statistics'
        }
