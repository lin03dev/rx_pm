"""
OBS Project Completion Report - Fixed to check actual paragraph content
"""

import pandas as pd
import json
from typing import Dict, Any, Set, Tuple
from reports.base_report import BaseReport
from config.obs_mapping_config import get_obs_mapping_config


class OBSProjectCompletionReport(BaseReport):
    """OBS Project Completion Report - Track assigned vs completed with actual content check"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'role', 'country']
        self.obs_config = get_obs_mapping_config()
    
    def _has_actual_content(self, data_text: str) -> Tuple[bool, int, int]:
        """Check if chapter has actual paragraph content, not just version"""
        try:
            if data_text and data_text != '{}':
                data = json.loads(data_text)
                paras = data.get('paras', [])
                if paras:
                    # Check if any paragraph has actual content
                    for para in paras:
                        if para.get('content') and para['content'].strip():
                            total_paras = len(paras)
                            completed_paras = sum(1 for p in paras if p.get('content') and p['content'].strip())
                            return True, total_paras, completed_paras
        except:
            pass
        return False, 0, 0
    
    def _count_chapter_completion(self, data_text: str) -> Tuple[int, int, int, int, int, int]:
        """Count completed items in a chapter - only count if content exists"""
        try:
            if data_text and data_text != '{}':
                data = json.loads(data_text)
                
                # Check title - only count if not empty
                title_completed = 1 if data.get('title') and data['title'].strip() else 0
                
                # Check bibleRef - only count if not empty
                bibleref_completed = 1 if data.get('bibleRef') and data['bibleRef'].strip() else 0
                
                # Check paragraphs - only count those with actual content
                paras = data.get('paras', [])
                total_paras = len(paras)
                completed_paras = sum(1 for p in paras if p.get('content') and p['content'].strip())
                
                total_items = 2 + total_paras
                completed_items = title_completed + bibleref_completed + completed_paras
                
                return title_completed, bibleref_completed, total_paras, completed_paras, total_items, completed_items
        except:
            pass
        return 0, 0, 0, 0, 0, 0
    
    def _get_chapter_paragraph_count(self, chapter_no: int) -> int:
        return self.obs_config.get_chapter_paragraph_count(chapter_no)
    
    def _get_performance_rating(self, completion_pct: float) -> str:
        rating = self.obs_config.get_mtt_performance_rating(completion_pct)
        return f"{rating['icon']} {rating['label']}"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate OBS project completion report with actual content checking"""
        
        # 1. All OBS Projects Overview
        projects_query = """
        SELECT 
            p.id as project_id,
            p.name as project_name,
            l.name as language_name,
            c.name as country
        FROM projects p
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE p."projectType" = 'OBS'
        ORDER BY p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} OBS projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # 2. Get UNIQUE assigned chapters per project
        project_assigned_chapters = {}
        
        for _, project_row in projects_df.iterrows():
            project_id = project_row['project_id']
            try:
                chap_query = f"""
                SELECT DISTINCT trim(unnest(string_to_array(COALESCE(utp."obsChapters", ''), ','))) as chapter_num
                FROM users_to_projects utp
                WHERE utp."projectId" = '{project_id}'
                  AND utp.role = 'MTT'
                  AND utp."obsChapters" IS NOT NULL
                """
                chap_df = self.execute_query(chap_query)
                chapters = set()
                for _, row in chap_df.iterrows():
                    try:
                        ch = int(row['chapter_num'].strip())
                        if 1 <= ch <= 50:
                            chapters.add(ch)
                    except:
                        pass
                if chapters:
                    project_assigned_chapters[project_id] = chapters
            except Exception as e:
                print(f"  Warning: Could not get chapters for {project_id}: {e}")
        
        print(f"✅ Found assigned chapters for {len(project_assigned_chapters)} projects")
        
        # 3. Get MTT assignments per project with proper full names
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
            utp."obsChapters" as assigned_chapters_raw,
            array_length(string_to_array(COALESCE(utp."obsChapters", ''), ','), 1) as chapters_assigned_count
        FROM users_to_projects utp
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users u ON utp."userId" = u.id
        WHERE utp."obsChapters" IS NOT NULL 
          AND utp."obsChapters" != ''
          AND p."projectType" = 'OBS'
          AND utp.role = 'MTT'
        ORDER BY p.name, u.username
        """
        
        try:
            mtt_assignments_df = self.execute_query(mtt_assignments_query)
            print(f"✅ Retrieved {len(mtt_assignments_df)} MTT assignment records")
        except Exception as e:
            print(f"❌ MTT assignments query failed: {e}")
            mtt_assignments_df = pd.DataFrame()
        
        # 4. ACTUAL COMPLETED WORK - ONLY COUNT CHAPTERS WITH ACTUAL PARAGRAPH CONTENT
        completed_work_query = """
        SELECT 
            op."projectId",
            opc."chapterNo",
            opc.version,
            opc.data::text as data_text
        FROM obs_project_chapters opc
        LEFT JOIN obs_projects op ON opc."obsProjectId" = op.id
        WHERE opc.version > 1
        """
        
        try:
            completed_df = self.execute_query(completed_work_query)
            print(f"✅ Retrieved {len(completed_df)} chapters with version > 1")
            
            project_completed = {}
            for _, row in completed_df.iterrows():
                project_id = row['projectId']
                chapter_no = row['chapterNo']
                data_text = row['data_text']
                
                # Check if this chapter has ACTUAL content (not just version)
                has_content, total_paras, completed_paras = self._has_actual_content(data_text)
                
                if not has_content:
                    # Skip this chapter - it has version but no actual content
                    continue
                
                if project_id not in project_completed:
                    project_completed[project_id] = {
                        'completed_chapters': set(),
                        'completed_titles': 0,
                        'completed_biblerefs': 0,
                        'completed_paragraphs': 0,
                        'total_paragraphs': 0,
                        'completed_items': 0,
                        'total_items': 0
                    }
                
                project_completed[project_id]['completed_chapters'].add(chapter_no)
                
                # Count items only for chapters with actual content
                title_comp, bibleref_comp, total_paras, comp_paras, total_items, comp_items = self._count_chapter_completion(data_text)
                project_completed[project_id]['completed_titles'] += title_comp
                project_completed[project_id]['completed_biblerefs'] += bibleref_comp
                project_completed[project_id]['completed_paragraphs'] += comp_paras
                project_completed[project_id]['total_paragraphs'] += total_paras
                project_completed[project_id]['completed_items'] += comp_items
                project_completed[project_id]['total_items'] += total_items
            
            print(f"✅ Processed completion for {len(project_completed)} projects (with actual content)")
        except Exception as e:
            print(f"❌ Completed work query failed: {e}")
            project_completed = {}
        
        # 5. TITLE AUDIO COMPLETION DATA
        title_audio_query = """
        SELECT 
            op."projectId",
            opc."chapterNo",
            1 as has_title_audio
        FROM obs_audio_recordings oar
        LEFT JOIN obs_project_chapters opc ON oar."obsProjectChapterId" = opc.id
        LEFT JOIN obs_projects op ON opc."obsProjectId" = op.id
        WHERE oar."recordingId" IS NOT NULL
          AND oar.type = 'title'
        GROUP BY op."projectId", opc."chapterNo"
        """
        
        try:
            title_audio_df = self.execute_query(title_audio_query)
            title_audio_lookup = {}
            for _, row in title_audio_df.iterrows():
                project_id = row['projectId']
                chapter_no = row['chapterNo']
                if project_id and chapter_no:
                    title_audio_lookup[(project_id, chapter_no)] = True
            print(f"✅ Processed title audio for {len(title_audio_lookup)} chapters")
        except Exception as e:
            print(f"❌ Title audio query failed: {e}")
            title_audio_lookup = {}
        
        # 6. PARAGRAPH AUDIO COMPLETION DATA
        para_audio_query = """
        SELECT 
            op."projectId",
            opc."chapterNo",
            COUNT(DISTINCT oar."paraIndex") as para_audio_count
        FROM obs_audio_recordings oar
        LEFT JOIN obs_project_chapters opc ON oar."obsProjectChapterId" = opc.id
        LEFT JOIN obs_projects op ON opc."obsProjectId" = op.id
        WHERE oar."recordingId" IS NOT NULL
          AND oar.type = 'para'
        GROUP BY op."projectId", opc."chapterNo"
        """
        
        try:
            para_audio_df = self.execute_query(para_audio_query)
            para_audio_lookup = {}
            for _, row in para_audio_df.iterrows():
                project_id = row['projectId']
                chapter_no = row['chapterNo']
                para_count = row['para_audio_count']
                if project_id and chapter_no:
                    para_audio_lookup[(project_id, chapter_no)] = para_count
            print(f"✅ Processed paragraph audio for {len(para_audio_lookup)} chapters")
        except Exception as e:
            print(f"❌ Paragraph audio query failed: {e}")
            para_audio_lookup = {}
        
        # 7. PROJECT-LEVEL STATUS
        project_status = []
        
        for project_id, assigned_chapters in project_assigned_chapters.items():
            project_info = projects_df[projects_df['project_id'] == project_id]
            project_name = project_info.iloc[0]['project_name'] if not project_info.empty else 'Unknown'
            language = project_info.iloc[0]['language_name'] if not project_info.empty else ''
            country = project_info.iloc[0]['country'] if not project_info.empty else ''
            
            mtt_info = mtt_assignments_df[mtt_assignments_df['projectId'] == project_id]
            mtt_count = mtt_info['user_id'].nunique() if not mtt_info.empty else 0
            mtt_names = ', '.join(mtt_info['full_name'].unique()) if not mtt_info.empty else ''
            
            chapters_assigned = len(assigned_chapters)
            paragraphs_assigned = sum(self._get_chapter_paragraph_count(ch) for ch in assigned_chapters)
            total_items_assigned = (chapters_assigned * 2) + paragraphs_assigned
            
            completed = project_completed.get(project_id, {})
            chapters_completed = len([ch for ch in assigned_chapters if ch in completed.get('completed_chapters', set())])
            titles_completed = completed.get('completed_titles', 0)
            biblerefs_completed = completed.get('completed_biblerefs', 0)
            paragraphs_completed = completed.get('completed_paragraphs', 0)
            total_items_completed = completed.get('completed_items', 0)
            
            chapters_with_title_audio = 0
            total_para_audio_count = 0
            for chapter in assigned_chapters:
                if title_audio_lookup.get((project_id, chapter), False):
                    chapters_with_title_audio += 1
                total_para_audio_count += para_audio_lookup.get((project_id, chapter), 0)
            
            chapter_pct = min((chapters_completed / chapters_assigned * 100) if chapters_assigned > 0 else 0, 100)
            title_pct = min((titles_completed / chapters_assigned * 100) if chapters_assigned > 0 else 0, 100)
            para_pct = min((paragraphs_completed / paragraphs_assigned * 100) if paragraphs_assigned > 0 else 0, 100)
            overall_pct = min((total_items_completed / total_items_assigned * 100) if total_items_assigned > 0 else 0, 100)
            title_audio_pct = min((chapters_with_title_audio / chapters_assigned * 100) if chapters_assigned > 0 else 0, 100)
            para_audio_pct = min((total_para_audio_count / paragraphs_assigned * 100) if paragraphs_assigned > 0 else 0, 100)
            
            thresholds = self.obs_config.get_completion_thresholds()
            translation_threshold = thresholds.get('translation', 100)
            audio_threshold = thresholds.get('audio', 100)
            
            # Determine status based on ACTUAL content, not just version
            if overall_pct >= translation_threshold and title_audio_pct >= audio_threshold and para_audio_pct >= audio_threshold:
                status = 'Complete (Translation + Audio)'
            elif overall_pct >= translation_threshold:
                status = 'Translation Complete, Audio Pending'
            elif overall_pct > 0:
                status = 'Translation In Progress'
            else:
                status = 'Not Started'
            
            project_status.append({
                'Project ID': project_id, 'Project Name': project_name, 'Language': language, 'Country': country,
                'MTTs Assigned': mtt_count, 'MTT Names': mtt_names[:300],
                'Chapters Assigned': chapters_assigned, 'Chapters Completed': chapters_completed,
                'Chapter Completion %': round(chapter_pct, 2),
                'Titles Completed': titles_completed, 'Title Completion %': round(title_pct, 2),
                'Paragraphs Assigned': paragraphs_assigned, 'Paragraphs Completed': paragraphs_completed,
                'Paragraph Completion %': round(para_pct, 2),
                'Total Items Assigned': total_items_assigned, 'Total Items Completed': total_items_completed,
                'Overall Completion %': round(overall_pct, 2),
                'Chapters with Title Audio': chapters_with_title_audio, 'Title Audio %': round(title_audio_pct, 2),
                'Paragraphs with Audio': total_para_audio_count, 'Paragraph Audio %': round(para_audio_pct, 2),
                'Status': status
            })
        
        project_status_df = pd.DataFrame(project_status)
        if not project_status_df.empty:
            project_status_df = project_status_df.sort_values('Overall Completion %', ascending=False)
        
        # 8. MTT-LEVEL PERFORMANCE
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
                assigned_chapters_raw = row['assigned_chapters_raw']
                
                assigned_chapters = set()
                for ch in assigned_chapters_raw.split(','):
                    ch = ch.strip()
                    if ch and ch.isdigit():
                        assigned_chapters.add(int(ch))
                
                chapters_assigned = len(assigned_chapters)
                paragraphs_assigned = sum(self._get_chapter_paragraph_count(ch) for ch in assigned_chapters)
                total_items_assigned = (chapters_assigned * 2) + paragraphs_assigned
                
                completed = project_completed.get(project_id, {})
                chapters_completed = len([ch for ch in assigned_chapters if ch in completed.get('completed_chapters', set())])
                
                titles_completed = 0
                biblerefs_completed = 0
                paragraphs_completed = 0
                
                for chapter in assigned_chapters:
                    if chapter in completed.get('completed_chapters', set()):
                        titles_completed += 1
                        biblerefs_completed += 1
                        paragraphs_completed += self._get_chapter_paragraph_count(chapter)
                
                total_items_completed = titles_completed + biblerefs_completed + paragraphs_completed
                
                chapter_pct = min((chapters_completed / chapters_assigned * 100) if chapters_assigned > 0 else 0, 100)
                para_pct = min((paragraphs_completed / paragraphs_assigned * 100) if paragraphs_assigned > 0 else 0, 100)
                overall_pct = min((total_items_completed / total_items_assigned * 100) if total_items_assigned > 0 else 0, 100)
                
                mtt_status = self.obs_config.get_mtt_status(overall_pct)
                performance_rating = self._get_performance_rating(overall_pct)
                
                mtt_performance.append({
                    'Project ID': project_id,
                    'Project Name': project_name,
                    'Language': language,
                    'Country': country,
                    'MTT User ID': user_id,
                    'MTT Username': username,
                    'MTT Full Name': full_name,
                    'MTT Email': email,
                    'Chapters Assigned': chapters_assigned,
                    'Chapters Completed': chapters_completed,
                    'Chapter Completion %': round(chapter_pct, 2),
                    'Paragraphs Assigned': paragraphs_assigned,
                    'Paragraphs Completed': paragraphs_completed,
                    'Paragraph Completion %': round(para_pct, 2),
                    'Total Items Assigned': total_items_assigned,
                    'Total Items Completed': total_items_completed,
                    'Overall Completion %': round(overall_pct, 2),
                    'Performance Rating': performance_rating,
                    'Status': mtt_status
                })
        
        mtt_performance_df = pd.DataFrame(mtt_performance)
        if not mtt_performance_df.empty:
            mtt_performance_df = mtt_performance_df.sort_values('Overall Completion %', ascending=False)
        
        # 9. Summary Statistics
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total OBS Projects', 'Value': len(projects_df)})
        
        if not project_status_df.empty:
            summary_data.append({'Metric': 'Projects with MTTs', 'Value': len(project_status_df)})
            summary_data.append({'Metric': 'Total Chapters Assigned', 'Value': project_status_df['Chapters Assigned'].sum()})
            summary_data.append({'Metric': 'Total Chapters Completed (with content)', 'Value': project_status_df['Chapters Completed'].sum()})
            summary_data.append({'Metric': 'Total Paragraphs Assigned', 'Value': project_status_df['Paragraphs Assigned'].sum()})
            summary_data.append({'Metric': 'Total Paragraphs Completed (with content)', 'Value': project_status_df['Paragraphs Completed'].sum()})
            
            total_chapters = project_status_df['Chapters Assigned'].sum()
            total_paragraphs = project_status_df['Paragraphs Assigned'].sum()
            
            if total_chapters > 0:
                summary_data.append({'Metric': 'Overall Chapter Completion Rate', 'Value': f"{(project_status_df['Chapters Completed'].sum()/total_chapters*100):.1f}%"})
            if total_paragraphs > 0:
                summary_data.append({'Metric': 'Overall Paragraph Completion Rate', 'Value': f"{(project_status_df['Paragraphs Completed'].sum()/total_paragraphs*100):.1f}%"})
            
            # Count projects by status
            complete = len(project_status_df[project_status_df['Status'].str.contains('Complete', na=False)])
            in_progress = len(project_status_df[project_status_df['Status'] == 'Translation In Progress'])
            not_started = len(project_status_df[project_status_df['Status'] == 'Not Started'])
            
            summary_data.append({'Metric': 'Fully Complete Projects', 'Value': complete})
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
            'projects_overview': '1. All OBS Projects',
            'mtt_assignments': '2. MTT Assignments',
            'project_status': '3. Assigned vs Completed',
            'mtt_performance': '4. MTT Performance',
            'summary_stats': '5. Summary Statistics'
        }
