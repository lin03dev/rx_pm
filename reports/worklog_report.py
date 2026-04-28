"""
Worklog Report - Translation work tracking
"""

import pandas as pd
from typing import Dict, Any
from reports.base_report import BaseReport

class WorklogReport(BaseReport):
    """Worklog Report - Translation work tracking"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['role', 'stage', 'software', 'project_type']
        
        # Map numeric stage codes (stored as strings) to human-readable names
        self.stage_code_map = {
            '1': "1.1 Recruitment / Benched",
            '2': "1.2 Preparation of Translation brief",
            '3': "1.3 Training and Drafting",
            '4': "2.1 Exegetical Checking",
            '5': "2.2 Basic and Advanced PT Checks",
            '6': "2.3 Projector/ Team Check",
            '7': "2.4 Back Translation",
            '8': "3.1 Community Checking",
            '9': "4.1 Update Back Translation",
            '10': "4.2 Consultant Checking",
            '11': "5.1 Read Aloud",
            '12': "5.3 Church / Community Leader Checking",
            '13': "5.4 Final Checks, publishing, engagement",
            '14': "5.2 Draft Recording"
        }
        
        # Map project type stages to cleaner names
        self.project_stage_map = {
            'obs.drafting': 'OBS - Drafting',
            'obs.community_checking': 'OBS - Community Checking',
            'obs.qa_check': 'OBS - QA Check',
            'obs.read_aloud': 'OBS - Read Aloud',
            'obs.recording': 'OBS - Recording',
            'grammar.drafting': 'Grammar - Drafting',
            'lit.drafting': 'Literature - Drafting',
            'literature.drafting': 'Literature Project - Drafting'
        }
        
        # Map literature genre IDs to human-readable names
        self.literature_genre_map = {
            '0c8f4016a8': 'General 2',
            '95d918a497': 'General 1',
            'childrens_literature': "Children's Literature",
            'formal_writing': 'Formal Writing',
            'history': 'History',
            'literature': 'Literature',
            'narrative': 'Narrative',
            'poetry': 'Poetry'
        }
        
        # Map translation software codes to names
        self.software_map = {
            'autographa': 'Autographa',
            'paratext': 'ParaText',
            'others': 'Others'
        }
    
    def _get_stage_name(self, stage) -> str:
        """Get human-readable stage name"""
        if pd.isna(stage) or stage is None:
            return "Unknown"
        
        stage_str = str(stage).strip()
        
        if stage_str in self.stage_code_map:
            return self.stage_code_map[stage_str]
        
        if stage_str in self.project_stage_map:
            return self.project_stage_map[stage_str]
        
        return stage_str
    
    def _get_genre_name(self, genre_id) -> str:
        """Convert genre ID to human-readable name"""
        if pd.isna(genre_id) or genre_id is None or genre_id == '':
            return ""
        
        genre_str = str(genre_id).strip()
        
        # Check if it's a known genre ID
        if genre_str in self.literature_genre_map:
            return self.literature_genre_map[genre_str]
        
        # Return as-is with underscores replaced
        return genre_str.replace('_', ' ').title()
    
    def _get_book_name(self, book_no) -> str:
        """Get Bible book name from book number"""
        if pd.isna(book_no) or book_no == 0 or book_no is None:
            return ""
        
        book_names = {
            1: "Genesis", 2: "Exodus", 3: "Leviticus", 4: "Numbers", 5: "Deuteronomy",
            6: "Joshua", 7: "Judges", 8: "Ruth", 9: "1 Samuel", 10: "2 Samuel",
            11: "1 Kings", 12: "2 Kings", 13: "1 Chronicles", 14: "2 Chronicles",
            15: "Ezra", 16: "Nehemiah", 17: "Esther", 18: "Job", 19: "Psalms",
            20: "Proverbs", 21: "Ecclesiastes", 22: "Song of Solomon", 23: "Isaiah",
            24: "Jeremiah", 25: "Lamentations", 26: "Ezekiel", 27: "Daniel",
            28: "Hosea", 29: "Joel", 30: "Amos", 31: "Obadiah", 32: "Jonah",
            33: "Micah", 34: "Nahum", 35: "Habakkuk", 36: "Zephaniah", 37: "Haggai",
            38: "Zechariah", 39: "Malachi", 40: "Matthew", 41: "Mark", 42: "Luke",
            43: "John", 44: "Acts", 45: "Romans", 46: "1 Corinthians", 47: "2 Corinthians",
            48: "Galatians", 49: "Ephesians", 50: "Philippians", 51: "Colossians",
            52: "1 Thessalonians", 53: "2 Thessalonians", 54: "1 Timothy", 55: "2 Timothy",
            56: "Titus", 57: "Philemon", 58: "Hebrews", 59: "James", 60: "1 Peter",
            61: "2 Peter", 62: "1 John", 63: "2 John", 64: "3 John", 65: "Jude", 66: "Revelation"
        }
        try:
            return book_names.get(int(book_no), f"Book {book_no}")
        except:
            return ""
    
    def _make_description(self, row):
        """Create a meaningful work description based on project type"""
        project_type = row.get('project_type', '')
        
        # Bible Translation work
        if project_type == 'TEXT_TRANSLATION':
            if row.get('book_name') and pd.notna(row.get('startChapter')) and row.get('startChapter', 0) > 0:
                start_v = int(row['startVerse']) if pd.notna(row.get('startVerse')) else 1
                end_v = int(row['endVerse']) if pd.notna(row.get('endVerse')) else start_v
                return f"Bible: {row['book_name']} {int(row['startChapter'])}:{start_v}-{int(row['endChapter'])}:{end_v}"
            return "Bible: Work session"
        
        # OBS work
        elif project_type == 'OBS':
            if pd.notna(row.get('obsStartChapter')) and row.get('obsStartChapter', 0) > 0:
                return f"OBS: Chapters {int(row['obsStartChapter'])}-{int(row['obsEndChapter'])}"
            return "OBS: Work session"
        
        # Literature work
        elif project_type in ['LITERATURE', 'LITERATURE_PROJECT']:
            genre_name = self._get_genre_name(row.get('literatureGenre'))
            if genre_name:
                return f"Literature: {genre_name}"
            return "Literature: Work session"
        
        # Grammar work
        elif project_type in ['GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES']:
            grammar_type = project_type.replace('GRAMMAR_', '').title()
            return f"Grammar: {grammar_type} work session"
        
        # Fallback to description
        if row.get('description') and row['description'] != '':
            return row['description']
        
        return "Work session"
    
    def generate(self) -> Dict[str, pd.DataFrame]:
        """Generate worklog report with human-readable values"""
        
        query = """
        SELECT 
            w.id,
            w."projectId",
            p.name as project_name,
            p."projectType" as project_type,
            w.role,
            w."userId",
            u.username,
            u.email,
            w."startDate",
            w."endDate",
            w.description,
            w."translationSoftware",
            w."bookNo",
            w."startChapter",
            w."startVerse",
            w."endChapter",
            w."endVerse",
            w."noWork",
            w.stage,
            w."obsStartChapter",
            w."obsEndChapter",
            w."obsStartPara",
            w."obsEndPara",
            w."literatureGenre",
            w."createdAt",
            w."updatedAt"
        FROM worklogs w
        LEFT JOIN users u ON w."userId" = u.id
        LEFT JOIN projects p ON w."projectId" = p.id
        WHERE 1=1
        ORDER BY w."startDate" DESC
        """
        
        try:
            worklog_df = self.execute_query(query)
            print(f"✅ Retrieved {len(worklog_df)} worklog records")
            
            if not worklog_df.empty:
                # Convert dates
                worklog_df['startDate'] = pd.to_datetime(worklog_df['startDate'])
                worklog_df['endDate'] = pd.to_datetime(worklog_df['endDate'])
                worklog_df['days_worked'] = (worklog_df['endDate'] - worklog_df['startDate']).dt.days + 1
                
                # Convert stage to human-readable
                worklog_df['stage_name'] = worklog_df['stage'].apply(self._get_stage_name)
                
                # Convert book numbers to book names
                worklog_df['book_name'] = worklog_df['bookNo'].apply(self._get_book_name)
                
                # Convert literature genre to readable name
                worklog_df['genre_name'] = worklog_df['literatureGenre'].apply(self._get_genre_name)
                
                # Convert software codes to names
                worklog_df['software_name'] = worklog_df['translationSoftware'].str.lower().map(self.software_map).fillna(worklog_df['translationSoftware'])
                
                # Create work description
                worklog_df['work_description'] = worklog_df.apply(self._make_description, axis=1)
                
                # For Bible projects, add specific fields
                worklog_df['bible_reference'] = worklog_df.apply(
                    lambda row: f"{row['book_name']} {int(row['startChapter'])}:{int(row['startVerse'])}-{int(row['endChapter'])}:{int(row['endVerse'])}"
                    if row['project_type'] == 'TEXT_TRANSLATION' and row['book_name'] and pd.notna(row['startChapter']) and row['startChapter'] > 0
                    else "", axis=1
                )
                
                # For OBS projects, add chapter range
                worklog_df['obs_chapters'] = worklog_df.apply(
                    lambda row: f"Chapters {int(row['obsStartChapter'])}-{int(row['obsEndChapter'])}"
                    if row['project_type'] == 'OBS' and pd.notna(row['obsStartChapter']) and row['obsStartChapter'] > 0
                    else "", axis=1
                )
                
                # Select and reorder columns
                display_columns = [
                    'startDate', 'endDate', 'days_worked', 'project_name', 'project_type',
                    'role', 'username', 'email', 'stage_name', 'software_name',
                    'work_description', 'bible_reference', 'obs_chapters', 'genre_name',
                    'noWork', 'description'
                ]
                
                # Only include columns that exist
                existing_cols = [col for col in display_columns if col in worklog_df.columns]
                worklog_details = worklog_df[existing_cols].copy()
                
        except Exception as e:
            print(f"❌ Worklog query failed: {e}")
            import traceback
            traceback.print_exc()
            worklog_details = pd.DataFrame({'Error': [str(e)]})
        
        # Role summary
        if not worklog_details.empty and 'Error' not in worklog_details.columns:
            role_summary = worklog_details.groupby(['role']).agg(
                Work_Sessions=('role', 'count'),
                Total_Days=('days_worked', 'sum')
            ).reset_index()
            role_summary.columns = ['Role', 'Work Sessions', 'Total Days']
            role_summary['Role'] = role_summary['Role'].map({
                'MTT': 'Mother Tongue Translator',
                'ICT': 'ICT Support',
                'QC': 'Quality Checker',
                'ADMIN': 'Administrator'
            }).fillna(role_summary['Role'])
            role_summary = role_summary.sort_values('Work Sessions', ascending=False)
        else:
            role_summary = pd.DataFrame()
        
        # Project type summary
        if not worklog_details.empty and 'Error' not in worklog_details.columns and 'project_type' in worklog_details.columns:
            project_summary = worklog_details.groupby(['project_type']).agg(
                Work_Sessions=('project_type', 'count'),
                Total_Days=('days_worked', 'sum')
            ).reset_index()
            project_summary.columns = ['Project Type', 'Work Sessions', 'Total Days']
            project_summary['Project Type'] = project_summary['Project Type'].map({
                'TEXT_TRANSLATION': 'Bible Translation',
                'OBS': 'Open Bible Stories',
                'LITERATURE': 'Literature',
                'LITERATURE_PROJECT': 'Literature Project',
                'GRAMMAR_PHRASES': 'Grammar - Phrases',
                'GRAMMAR_PRONOUNS': 'Grammar - Pronouns',
                'GRAMMAR_CONNECTIVES': 'Grammar - Connectives'
            }).fillna(project_summary['Project Type'])
            project_summary = project_summary.sort_values('Work Sessions', ascending=False)
        else:
            project_summary = pd.DataFrame()
        
        # Stage summary
        if not worklog_details.empty and 'Error' not in worklog_details.columns and 'stage_name' in worklog_details.columns:
            stage_summary = worklog_details.groupby(['stage_name']).agg(
                Work_Sessions=('stage_name', 'count'),
                Total_Days=('days_worked', 'sum')
            ).reset_index()
            stage_summary.columns = ['Stage', 'Work Sessions', 'Total Days']
            stage_summary = stage_summary.sort_values('Work Sessions', ascending=False)
        else:
            stage_summary = pd.DataFrame()
        
        # Monthly summary
        if not worklog_details.empty and 'Error' not in worklog_details.columns:
            worklog_details['year_month'] = worklog_details['startDate'].dt.strftime('%Y-%m')
            monthly_summary = worklog_details.groupby(['year_month']).agg(
                Work_Sessions=('year_month', 'count'),
                Total_Days=('days_worked', 'sum')
            ).reset_index()
            monthly_summary.columns = ['Year-Month', 'Work Sessions', 'Total Days']
            monthly_summary = monthly_summary.sort_values('Year-Month', ascending=False)
        else:
            monthly_summary = pd.DataFrame()
        
        return {
            'worklog_details': worklog_details,
            'role_summary': role_summary,
            'project_summary': project_summary,
            'stage_summary': stage_summary,
            'monthly_summary': monthly_summary
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'worklog_details': 'Worklog Details',
            'role_summary': 'Role Summary',
            'project_summary': 'Project Type Summary',
            'stage_summary': 'Stage Summary',
            'monthly_summary': 'Monthly Summary'
        }
