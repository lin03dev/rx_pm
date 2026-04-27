"""
Literature Project Completion Report - Shows assigned vs completed per MTT
Handles cases where MTT assignments may not be recorded
"""

import pandas as pd
import json
import re
from typing import Dict, Any, List
from reports.base_report import BaseReport


class LiteratureProjectCompletionReport(BaseReport):
    """Literature Project Completion Report - Assigned vs Completed per MTT"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'country']
    
    def _count_sentences(self, text: str) -> int:
        """Count number of sentences in text"""
        if not text:
            return 0
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _analyze_content(self, content) -> Dict[str, Any]:
        """Analyze literature content"""
        result = {
            'total_blocks': 0,
            'filled_blocks': 0,
            'fill_rate': 0,
            'total_sentences': 0,
            'total_words': 0,
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
                blocks = data['content']
                result['total_blocks'] = len(blocks)
                
                filled_blocks = 0
                total_sentences = 0
                total_words = 0
                
                for block in blocks:
                    if isinstance(block, dict):
                        text = block.get('content', '')
                        if text and text.strip():
                            filled_blocks += 1
                            total_sentences += self._count_sentences(text)
                            total_words += len(text.split())
                
                result['filled_blocks'] = filled_blocks
                result['total_sentences'] = total_sentences
                result['total_words'] = total_words
                result['has_content'] = filled_blocks > 0
                
                if result['total_blocks'] > 0:
                    result['fill_rate'] = (filled_blocks / result['total_blocks'] * 100)
        except:
            pass
        
        return result
    
    def _get_status(self, fill_rate: float) -> str:
        if fill_rate >= 100:
            return "✅ Completed"
        elif fill_rate >= 75:
            return "🟢 Almost Complete"
        elif fill_rate >= 50:
            return "🟡 Half Complete"
        elif fill_rate >= 25:
            return "🟠 In Progress"
        elif fill_rate > 0:
            return "🔵 Just Started"
        else:
            return "⚪ Not Started"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate literature report with assigned vs completed per MTT"""
        
        # ============================================================
        # Sheet 1: All Literature Projects Overview
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
        # Sheet 2: MTT Assignments (What was assigned to each MTT)
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
        WHERE p."projectType" IN ('LITERATURE', 'LITERATURE_PROJECT')
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
        # Sheet 3: Genre Details (1 row per genre - from completed work)
        # This is the main sheet - shows actual completed work per genre
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
            print(f"✅ Retrieved {len(genre_df)} genre records with completed work")
        except Exception as e:
            print(f"⚠️ Genre details query: {e}")
            genre_df = pd.DataFrame()
        
        genre_details_data = []
        for _, row in genre_df.iterrows():
            content_analysis = self._analyze_content(row['content'])
            fill_rate = content_analysis['fill_rate']
            
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
                'Project Name': row['project_name'],
                'Language': row['language_name'] if row['language_name'] else 'N/A',
                'Country': row['country'] if row['country'] else 'N/A',
                'Genre': row['genre_name'] if row['genre_name'] else row['genre_type'],
                'Total Blocks': content_analysis['total_blocks'],
                'Filled Blocks': content_analysis['filled_blocks'],
                'Fill Rate %': round(fill_rate, 1),
                'Total Sentences': content_analysis['total_sentences'],
                'Total Words': content_analysis['total_words'],
                'Version': row['version'],
                'Completed By': completed_by_name,
                'Last Updated': row['last_updated'] if pd.notna(row['last_updated']) else '',
                'Status': self._get_status(fill_rate)
            })
        
        genre_details_df = pd.DataFrame(genre_details_data)
        
        # ============================================================
        # Sheet 4: MTT Performance (Who completed what)
        # Shows which MTT completed which genres
        # ============================================================
        mtt_performance_data = []
        
        if not genre_df.empty:
            for _, row in genre_df.iterrows():
                content_analysis = self._analyze_content(row['content'])
                fill_rate = content_analysis['fill_rate']
                
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
                        else:
                            completed_by_name = completed_by[:8] + '...' if len(str(completed_by)) > 8 else str(completed_by)
                    except:
                        completed_by_name = str(completed_by)[:8] + '...' if len(str(completed_by)) > 8 else str(completed_by)
                else:
                    completed_by_name = 'Unknown'
                
                mtt_performance_data.append({
                    'Project Name': row['project_name'],
                    'Language': row['language_name'] if row['language_name'] else 'N/A',
                    'Country': row['country'] if row['country'] else 'N/A',
                    'Genre': row['genre_name'] if row['genre_name'] else row['genre_type'],
                    'Completed By': completed_by_name,
                    'Filled Blocks': content_analysis['filled_blocks'],
                    'Total Blocks': content_analysis['total_blocks'],
                    'Fill Rate %': round(fill_rate, 1),
                    'Sentences': content_analysis['total_sentences'],
                    'Words': content_analysis['total_words'],
                    'Version': row['version'],
                    'Last Updated': row['last_updated'] if pd.notna(row['last_updated']) else '',
                    'Status': self._get_status(fill_rate)
                })
        
        mtt_performance_df = pd.DataFrame(mtt_performance_data)
        
        # ============================================================
        # Sheet 5: Summary Statistics
        # ============================================================
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total Literature Projects', 'Value': len(projects_df)})
            summary_data.append({'Metric': '  - LITERATURE type', 'Value': len(projects_df[projects_df['project_type'] == 'LITERATURE'])})
            summary_data.append({'Metric': '  - LITERATURE_PROJECT type', 'Value': len(projects_df[projects_df['project_type'] == 'LITERATURE_PROJECT'])})
        
        if not genre_details_df.empty:
            with_content = len(genre_details_df[genre_details_df['Filled Blocks'] > 0])
            completed = len(genre_details_df[genre_details_df['Fill Rate %'] >= 100])
            in_progress = len(genre_details_df[(genre_details_df['Fill Rate %'] > 0) & (genre_details_df['Fill Rate %'] < 100)])
            not_started = len(genre_details_df[genre_details_df['Fill Rate %'] == 0])
            
            summary_data.append({'Metric': 'Genres with Content', 'Value': with_content})
            summary_data.append({'Metric': 'Completed Genres (100%)', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Genres', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Genres', 'Value': not_started})
            summary_data.append({'Metric': 'Total Blocks', 'Value': genre_details_df['Total Blocks'].sum()})
            summary_data.append({'Metric': 'Filled Blocks', 'Value': genre_details_df['Filled Blocks'].sum()})
            summary_data.append({'Metric': 'Overall Fill Rate', 'Value': f"{(genre_details_df['Filled Blocks'].sum() / genre_details_df['Total Blocks'].sum() * 100):.1f}%" if genre_details_df['Total Blocks'].sum() > 0 else "0%"})
            summary_data.append({'Metric': 'Total Sentences', 'Value': genre_details_df['Total Sentences'].sum()})
            summary_data.append({'Metric': 'Total Words', 'Value': genre_details_df['Total Words'].sum()})
        
        if not mtt_performance_df.empty:
            summary_data.append({'Metric': 'MTTs with Completed Work', 'Value': mtt_performance_df['Completed By'].nunique()})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'projects_overview': projects_df,
            'mtt_assignments': mtt_assignments_df,
            'genre_details': genre_details_df,
            'mtt_performance': mtt_performance_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'projects_overview': '1 - All Literature Projects',
            'mtt_assignments': '2 - MTT Assignments',
            'genre_details': '3 - Genre Details (Completed Work)',
            'mtt_performance': '4 - MTT Performance (Who Completed What)',
            'summary_stats': '5 - Summary Statistics'
        }
