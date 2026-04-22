"""
Grammar Project Completion Report - Enhanced with detailed item tracking
Includes item-level breakdown per MTT (1 row per grammar item)
"""

import pandas as pd
import json
from typing import Dict, Any, Tuple, List
from reports.base_report import BaseReport


class GrammarProjectCompletionReport(BaseReport):
    """Grammar Project Completion Report - Track items with detailed breakdown per MTT"""
    
    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self.available_filters = ['project_id', 'user_id', 'role', 'country']
    
    def _extract_items(self, content, grammar_type: str) -> Tuple[int, int, List[Dict]]:
        """Extract items and return detailed list"""
        total = 0
        completed = 0
        items = []
        
        if content is None:
            return 0, 0, []
        
        try:
            if isinstance(content, str):
                data = json.loads(content)
            else:
                data = content
            
            # Determine item key
            item_key = {
                'phrases': 'phrase',
                'pronouns': 'pronoun',
                'connectives': 'connective'
            }.get(grammar_type, 'text')
            
            content_items = []
            if 'content' in data and isinstance(data['content'], list):
                content_items = data['content']
            elif isinstance(data, list):
                content_items = data
            
            total = len(content_items)
            for idx, item in enumerate(content_items):
                if isinstance(item, dict):
                    value = item.get(item_key, '')
                    is_completed = bool(value and len(str(value).strip()) > 0)
                    if is_completed:
                        completed += 1
                    
                    items.append({
                        'item_num': idx + 1,
                        'value': value if value else '',
                        'has_content': is_completed,
                        'preview': (str(value)[:50] + '...') if value and len(str(value)) > 50 else (str(value) if value else '')
                    })
                elif isinstance(item, str):
                    is_completed = bool(item.strip())
                    if is_completed:
                        completed += 1
                    items.append({
                        'item_num': idx + 1,
                        'value': item,
                        'has_content': is_completed,
                        'preview': item[:50] + '...' if len(item) > 50 else item
                    })
            
            return total, completed, items
        except:
            return 0, 0, []
    
    def _has_content(self, content, grammar_type: str) -> bool:
        total, completed, _ = self._extract_items(content, grammar_type)
        return completed > 0
    
    def _get_completion_pct(self, content, grammar_type: str) -> float:
        total, completed, _ = self._extract_items(content, grammar_type)
        if total > 0:
            return (completed / total * 100)
        return 0
    
    def _get_performance_rating(self, completion_pct: float) -> str:
        if completion_pct >= 100:
            return "🏆 Excellent"
        elif completion_pct >= 75:
            return "👍 Good"
        elif completion_pct >= 50:
            return "⭐ Average"
        elif completion_pct >= 25:
            return "⚠️ Needs Improvement"
        elif completion_pct > 0:
            return "🔨 In Progress"
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
        """Generate enhanced Grammar project completion report with item-level details"""
        
        grammar_configs = [
            ('GRAMMAR_PHRASES', 'phrases', 'grammar_phrases_project_contents', 'grammar_phrases_projects', 'grammarPhrasesProjectId'),
            ('GRAMMAR_PRONOUNS', 'pronouns', 'grammar_pronouns_project_contents', 'grammar_pronouns_projects', 'grammarPronounsProjectId'),
            ('GRAMMAR_CONNECTIVES', 'connectives', 'grammar_connectives_project_contents', 'grammar_connectives_projects', 'grammarConnectivesProjectId')
        ]
        
        # ============================================================
        # 1. All Grammar Projects Overview
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
        WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
        ORDER BY p."projectType", p.name
        """
        
        try:
            projects_df = self.execute_query(projects_query)
            print(f"✅ Retrieved {len(projects_df)} Grammar projects")
        except Exception as e:
            print(f"❌ Projects query failed: {e}")
            projects_df = pd.DataFrame()
        
        # ============================================================
        # 2. Get MTT assignments with proper full names
        # ============================================================
        mtt_assignments_query = """
        SELECT 
            utp."projectId",
            p.name as project_name,
            p."projectType" as project_type,
            l.name as language_name,
            c.name as country,
            u.id as user_id,
            u.username,
            COALESCE(NULLIF(u.name, ''), u.username) as full_name,
            u.email,
            utp.role as project_role
        FROM users_to_projects utp
        LEFT JOIN projects p ON utp."projectId" = p.id
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN users u ON utp."userId" = u.id
        WHERE p."projectType" IN ('GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
          AND utp.role = 'MTT'
        ORDER BY p."projectType", p.name, u.username
        """
        
        try:
            mtt_assignments_df = self.execute_query(mtt_assignments_query)
            print(f"✅ Retrieved {len(mtt_assignments_df)} MTT assignment records")
        except Exception as e:
            print(f"❌ MTT assignments query failed: {e}")
            mtt_assignments_df = pd.DataFrame()
        
        # ============================================================
        # 3. Get completion data with item-level details
        # ============================================================
        project_completion = {}
        item_details_by_project = {}  # For detailed item sheet
        
        for grammar_enum, grammar_key, content_table, project_table, id_field in grammar_configs:
            try:
                query = f"""
                SELECT DISTINCT ON (gp."projectId")
                    gp."projectId",
                    gpc.version,
                    gpc.content
                FROM {content_table} gpc
                JOIN {project_table} gp ON gpc."{id_field}" = gp.id
                WHERE gpc.version > 1
                ORDER BY gp."projectId", gpc.version DESC
                """
                
                content_df = self.execute_query(query)
                print(f"✅ {grammar_enum}: Found {len(content_df)} projects with content")
                
                for _, row in content_df.iterrows():
                    project_id = row['projectId']
                    content = row['content']
                    version = row['version']
                    
                    total_items, completed_items, items = self._extract_items(content, grammar_key)
                    has_content = self._has_content(content, grammar_key)
                    completion_pct = self._get_completion_pct(content, grammar_key)
                    
                    if project_id not in project_completion:
                        project_completion[project_id] = {
                            'grammar_type': grammar_enum,
                            'has_content': has_content,
                            'version': version,
                            'total_items': total_items,
                            'completed_items': completed_items,
                            'completion_pct': completion_pct
                        }
                    elif version > project_completion[project_id]['version']:
                        project_completion[project_id].update({
                            'grammar_type': grammar_enum,
                            'has_content': has_content,
                            'version': version,
                            'total_items': total_items,
                            'completed_items': completed_items,
                            'completion_pct': completion_pct
                        })
                    
                    # Store item details for detailed sheet
                    item_details_by_project[project_id] = {
                        'items': items,
                        'grammar_type': grammar_enum
                    }
            except Exception as e:
                print(f"⚠️ {grammar_enum} query error: {e}")
        
        print(f"✅ Found {len(project_completion)} grammar projects with content")
        
        # ============================================================
        # 4. PROJECT-LEVEL STATUS
        # ============================================================
        project_status = []
        
        for _, row in projects_df.iterrows():
            project_id = row['project_id']
            project_name = row['project_name']
            project_type = row['project_type']
            language = row['language_name'] or 'N/A'
            country = row['country'] or 'N/A'
            
            mtt_info = mtt_assignments_df[mtt_assignments_df['projectId'] == project_id]
            mtt_count = mtt_info['user_id'].nunique() if not mtt_info.empty else 0
            mtt_names = ', '.join(mtt_info['full_name'].unique()) if not mtt_info.empty else ''
            
            completion = project_completion.get(project_id, {})
            has_content = completion.get('has_content', False)
            version = completion.get('version', 0)
            completion_pct = completion.get('completion_pct', 0)
            total_items = completion.get('total_items', 0)
            completed_items = completion.get('completed_items', 0)
            grammar_type = completion.get('grammar_type', '')
            
            status = self._get_status(completion_pct)
            performance = self._get_performance_rating(completion_pct)
            
            project_status.append({
                'Project ID': project_id,
                'Project Name': project_name,
                'Project Type': project_type,
                'Language': language,
                'Country': country,
                'MTTs Assigned': mtt_count,
                'MTT Names': mtt_names[:300],
                'Grammar Type': grammar_type,
                'Has Content': 'Yes' if has_content else 'No',
                'Total Items': total_items,
                'Items Completed': completed_items,
                'Completion %': round(completion_pct, 2),
                'Version': version,
                'Performance Rating': performance,
                'Status': status
            })
        
        project_status_df = pd.DataFrame(project_status)
        if not project_status_df.empty:
            project_status_df = project_status_df.sort_values('Completion %', ascending=False)
        
        # ============================================================
        # 5. MTT-LEVEL PERFORMANCE
        # ============================================================
        mtt_performance = []
        
        if not mtt_assignments_df.empty:
            for _, row in mtt_assignments_df.iterrows():
                project_id = row['projectId']
                user_id = row['user_id']
                username = row['username']
                full_name = row['full_name']
                email = row['email']
                project_name = row['project_name']
                project_type = row['project_type']
                language = row['language_name']
                country = row['country']
                
                completion = project_completion.get(project_id, {})
                has_content = completion.get('has_content', False)
                completion_pct = completion.get('completion_pct', 0)
                total_items = completion.get('total_items', 0)
                completed_items = completion.get('completed_items', 0)
                
                performance_rating = self._get_performance_rating(completion_pct)
                mtt_status = self._get_status(completion_pct)
                
                mtt_performance.append({
                    'Project ID': project_id,
                    'Project Name': project_name,
                    'Project Type': project_type,
                    'Language': language,
                    'Country': country,
                    'MTT User ID': user_id,
                    'MTT Username': username,
                    'MTT Full Name': full_name,
                    'MTT Email': email,
                    'Has Content': 'Yes' if has_content else 'No',
                    'Total Items': total_items,
                    'Items Completed': completed_items,
                    'Completion %': round(completion_pct, 2),
                    'Version': completion.get('version', 0),
                    'Performance Rating': performance_rating,
                    'Status': mtt_status
                })
        
        mtt_performance_df = pd.DataFrame(mtt_performance)
        if not mtt_performance_df.empty:
            mtt_performance_df = mtt_performance_df.sort_values('Completion %', ascending=False)
        
        # ============================================================
        # 6. ITEM-LEVEL DETAILS (1 row per grammar item)
        # ============================================================
        item_details = []
        
        for project_id, item_data in item_details_by_project.items():
            project_info = projects_df[projects_df['project_id'] == project_id]
            project_name = project_info.iloc[0]['project_name'] if not project_info.empty else 'Unknown'
            grammar_type = item_data.get('grammar_type', '')
            
            # Get MTTs for this project
            project_mtts = mtt_assignments_df[mtt_assignments_df['projectId'] == project_id]
            mtt_names_list = project_mtts['full_name'].tolist() if not project_mtts.empty else ['No MTT Assigned']
            
            for mtt_name in mtt_names_list:
                for item in item_data.get('items', []):
                    item_details.append({
                        'Project Name': project_name,
                        'Grammar Type': grammar_type,
                        'MTT Full Name': mtt_name,
                        'Item #': item['item_num'],
                        'Content': item['preview'] if item['preview'] else '(empty)',
                        'Has Content': '✅' if item['has_content'] else '❌',
                        'Full Value': item['value'][:100] if item['value'] else ''
                    })
        
        item_details_df = pd.DataFrame(item_details)
        
        # ============================================================
        # 7. Summary Statistics
        # ============================================================
        summary_data = []
        
        if not projects_df.empty:
            summary_data.append({'Metric': 'Total Grammar Projects', 'Value': len(projects_df)})
            for gtype in ['GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES']:
                count = len(projects_df[projects_df['project_type'] == gtype])
                summary_data.append({'Metric': f'  - {gtype}', 'Value': count})
        
        if not project_status_df.empty:
            with_content = len(project_status_df[project_status_df['Has Content'] == 'Yes'])
            completed = len(project_status_df[project_status_df['Status'] == 'Completed'])
            in_progress = len(project_status_df[project_status_df['Status'] == 'In Progress'])
            not_started = len(project_status_df[project_status_df['Status'] == 'Not Started'])
            
            summary_data.append({'Metric': 'Projects with Content', 'Value': with_content})
            summary_data.append({'Metric': 'Completed Projects', 'Value': completed})
            summary_data.append({'Metric': 'In Progress Projects', 'Value': in_progress})
            summary_data.append({'Metric': 'Not Started Projects', 'Value': not_started})
            summary_data.append({'Metric': 'Average Completion %', 'Value': f"{round(project_status_df['Completion %'].mean(), 1)}%"})
        
        if not mtt_assignments_df.empty:
            summary_data.append({'Metric': 'Total MTTs Assigned', 'Value': mtt_assignments_df['user_id'].nunique()})
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'projects_overview': projects_df,
            'mtt_assignments': mtt_assignments_df,
            'project_status': project_status_df,
            'mtt_performance': mtt_performance_df,
            'item_details': item_details_df,
            'summary_stats': summary_df
        }
    
    def get_sheet_names(self) -> Dict[str, str]:
        return {
            'projects_overview': '1. All Grammar Projects',
            'mtt_assignments': '2. MTT Assignments',
            'project_status': '3. Assigned vs Completed',
            'mtt_performance': '4. MTT Performance',
            'item_details': '5. Item Details (per MTT)',
            'summary_stats': '6. Summary Statistics'
        }
