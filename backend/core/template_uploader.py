"""
Template Uploader - Handles upload and processing of Excel templates
"""

import pandas as pd
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from config.excel_template_config import (
    TemplatePurpose,
    ExcelTemplate,
    TemplateSheet,
    get_excel_template_manager
)
from utils.excel_template_generator import get_excel_template_validator
from core.database_manager import DatabaseManager


class TemplateUploader:
    """Handle uploading and processing Excel template data"""
    
    def __init__(self, db_manager: DatabaseManager, upload_dir: str = "./output/uploads"):
        self.db_manager = db_manager
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.validator = get_excel_template_validator()
        self.template_manager = get_excel_template_manager()
    
    def upload_and_process(self, file_path: str, purpose: TemplatePurpose, 
                           dry_run: bool = False) -> Dict[str, Any]:
        """Upload and process an Excel file"""
        
        # Validate first
        validation_result = self.validator.validate_upload(file_path, purpose)
        
        if not validation_result["valid"]:
            return {
                "success": False,
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", [])
            }
        
        template = self.template_manager.get_template(purpose)
        if not template:
            return {"success": False, "errors": [f"Template not found: {purpose}"]}
        
        # Process each sheet
        results = []
        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        
        for sheet_config in template.sheets:
            sheet_result = self._process_sheet(
                file_path, sheet_config, template, dry_run
            )
            results.append(sheet_result)
            total_inserted += sheet_result.get("inserted", 0)
            total_updated += sheet_result.get("updated", 0)
            total_skipped += sheet_result.get("skipped", 0)
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved_path = self.upload_dir / f"{timestamp}_{Path(file_path).name}"
        import shutil
        shutil.copy(file_path, saved_path)
        
        return {
            "success": True,
            "dry_run": dry_run,
            "total_inserted": total_inserted,
            "total_updated": total_updated,
            "total_skipped": total_skipped,
            "sheets": results,
            "saved_file": str(saved_path),
            "validation": validation_result
        }
    
    def _process_sheet(self, file_path: str, sheet_config: TemplateSheet,
                       template: ExcelTemplate, dry_run: bool) -> Dict[str, Any]:
        """Process a single sheet"""
        
        df = pd.read_excel(file_path, sheet_name=sheet_config.sheet_name)
        
        inserted = 0
        updated = 0
        skipped = 0
        errors = []
        
        # Build column mapping
        col_map = {}
        for col in sheet_config.columns:
            col_map[col.display_name] = col
        
        for idx, row in df.iterrows():
            try:
                # Build record
                record = {}
                for col in sheet_config.columns:
                    value = row.get(col.display_name)
                    
                    # Skip empty optional fields
                    if pd.isna(value) or value == "":
                        if not col.required:
                            continue
                        else:
                            value = col.default_value if col.default_value else ""
                    
                    # Transform value
                    value = self._transform_value(value, col)
                    
                    # Map to database field
                    db_field = col.mapping_to_db or col.field_name
                    record[db_field] = value
                
                if dry_run:
                    # Just validate, don't insert
                    if self._validate_record(record, sheet_config):
                        inserted += 1
                    else:
                        skipped += 1
                else:
                    # Insert or update
                    result = self._upsert_record(record, sheet_config)
                    if result == "inserted":
                        inserted += 1
                    elif result == "updated":
                        updated += 1
                    else:
                        skipped += 1
                        
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
                skipped += 1
        
        return {
            "sheet_name": sheet_config.sheet_name,
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "errors": errors
        }
    
    def _transform_value(self, value: Any, col) -> Any:
        """Transform value based on field type and transform function"""
        
        # Handle NaN
        if pd.isna(value):
            return None
        
        # Type conversions
        if col.field_type.value == "integer":
            value = int(float(value)) if value else None
        elif col.field_type.value == "decimal":
            value = float(value) if value else None
        elif col.field_type.value == "boolean":
            if isinstance(value, str):
                value = value.lower() in ["true", "yes", "1", "y"]
            value = bool(value)
        elif col.field_type.value == "json":
            if isinstance(value, str):
                value = json.loads(value)
        
        # Apply transform function
        if col.transform_function:
            value = self._apply_transform(value, col.transform_function)
        
        return value
    
    def _apply_transform(self, value: Any, transform_function: str) -> Any:
        """Apply a transform function to the value"""
        
        if transform_function == "resolve_user_id":
            return self._resolve_user_id(value)
        elif transform_function == "resolve_project_id":
            return self._resolve_project_id(value)
        elif transform_function == "lookup_country_id":
            return self._lookup_country_id(value)
        elif transform_function == "lookup_language_id":
            return self._lookup_language_id(value)
        elif transform_function == "map_book_number":
            return self._map_book_number(value)
        elif transform_function == "validate_verse_ids":
            return self._validate_verse_ids(value)
        elif transform_function == "validate_obs_chapters":
            return self._validate_obs_chapters(value)
        elif transform_function == "format_bible_content":
            return self._format_bible_content(value)
        elif transform_function.startswith("resolve_grammar_"):
            return self._resolve_grammar_project_id(value, transform_function)
        
        return value
    
    def _resolve_user_id(self, identifier: str) -> str:
        """Resolve user ID from username or email"""
        if not identifier:
            return None
        
        # Check if it's already a UUID
        try:
            uuid.UUID(identifier)
            return identifier
        except:
            pass
        
        # Query by username or email
        query = """
        SELECT id FROM users 
        WHERE username = %s OR email = %s
        LIMIT 1
        """
        try:
            df = self.db_manager.execute_query(query, (identifier, identifier))
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        
        return identifier
    
    def _resolve_project_id(self, identifier: str) -> str:
        """Resolve project ID from project name"""
        if not identifier:
            return None
        
        try:
            uuid.UUID(identifier)
            return identifier
        except:
            pass
        
        query = "SELECT id FROM projects WHERE name = %s LIMIT 1"
        try:
            df = self.db_manager.execute_query(query, (identifier,))
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        
        return identifier
    
    def _lookup_country_id(self, country_name: str) -> str:
        """Look up country ID from country name"""
        if not country_name:
            return None
        
        query = "SELECT id FROM countries WHERE name ILIKE %s LIMIT 1"
        try:
            df = self.db_manager.execute_query(query, (f"%{country_name}%",))
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        
        return None
    
    def _lookup_language_id(self, language_name: str) -> str:
        """Look up language ID from language name"""
        if not language_name:
            return None
        
        query = "SELECT id FROM languages WHERE name ILIKE %s LIMIT 1"
        try:
            df = self.db_manager.execute_query(query, (f"%{language_name}%",))
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        
        return None
    
    def _map_book_number(self, book_no: int) -> int:
        """Map book number using book mapping config"""
        from config.book_mapping_config import map_book
        return map_book(int(book_no))
    
    def _validate_verse_ids(self, verse_ids: str) -> str:
        """Validate and clean verse IDs"""
        if not verse_ids:
            return None
        
        verses = [v.strip() for v in str(verse_ids).split(',')]
        valid_verses = [v for v in verses if v and len(v) >= 6 and v.isdigit()]
        return ','.join(valid_verses)
    
    def _validate_obs_chapters(self, chapters: str) -> str:
        """Validate OBS chapters (1-50)"""
        if not chapters:
            return None
        
        chapter_list = [c.strip() for c in str(chapters).split(',')]
        valid_chapters = [c for c in chapter_list if c and c.isdigit() and 1 <= int(c) <= 50]
        return ','.join(valid_chapters)
    
    def _format_bible_content(self, text: str) -> str:
        """Format Bible content as JSON"""
        if not text:
            return None
        
        return json.dumps({
            "version": 1,
            "content": [
                {
                    "start": 1,
                    "end": 1,
                    "text": text
                }
            ]
        })
    
    def _resolve_grammar_project_id(self, project_name: str, transform_function: str) -> str:
        """Resolve grammar project ID"""
        grammar_type = transform_function.replace("resolve_grammar_", "").replace("_project_id", "")
        
        table_map = {
            "phrases": "grammar_phrases_projects",
            "pronouns": "grammar_pronouns_projects",
            "connectives": "grammar_connectives_projects"
        }
        
        table = table_map.get(grammar_type)
        if not table:
            return project_name
        
        query = f"""
        SELECT gp.id 
        FROM {table} gp
        JOIN projects p ON gp."projectId" = p.id
        WHERE p.name = %s
        LIMIT 1
        """
        try:
            df = self.db_manager.execute_query(query, (project_name,))
            if not df.empty:
                return df['id'].iloc[0]
        except:
            pass
        
        return project_name
    
    def _validate_record(self, record: Dict[str, Any], sheet_config: TemplateSheet) -> bool:
        """Validate a record before insertion"""
        # Check primary keys
        for pk in sheet_config.primary_key_fields:
            if pk not in record or not record[pk]:
                return False
        return True
    
    def _upsert_record(self, record: Dict[str, Any], sheet_config: TemplateSheet) -> str:
        """Insert or update a record"""
        
        table = sheet_config.table_name
        if not table:
            return "skipped"
        
        # Check if record exists
        where_clause = " AND ".join([f'"{pk}" = %s' for pk in sheet_config.primary_key_fields])
        where_values = [record.get(pk) for pk in sheet_config.primary_key_fields]
        
        check_query = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
        
        try:
            df = self.db_manager.execute_query(check_query, tuple(where_values))
            exists = not df.empty
        except:
            exists = False
        
        if exists and sheet_config.update_mode in ["update", "upsert"]:
            # Update
            set_clause = ", ".join([f'"{k}" = %s' for k in record.keys() if k not in sheet_config.primary_key_fields])
            set_values = [v for k, v in record.items() if k not in sheet_config.primary_key_fields]
            update_query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            try:
                self.db_manager.execute_update(update_query, tuple(set_values + where_values))
                return "updated"
            except Exception as e:
                print(f"Update error: {e}")
                return "skipped"
        
        elif sheet_config.update_mode in ["insert", "upsert"]:
            # Insert
            columns = ", ".join([f'"{k}"' for k in record.keys()])
            placeholders = ", ".join(["%s"] * len(record))
            insert_query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            try:
                self.db_manager.execute_update(insert_query, tuple(record.values()))
                return "inserted"
            except Exception as e:
                print(f"Insert error: {e}")
                return "skipped"
        
        return "skipped"

    # ============================================================
# LMS Transform Functions
# ============================================================

def _resolve_course_id(self, identifier: str) -> str:
    """Resolve course ID from course title"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    # Check if it's a title
    query = "SELECT id FROM course WHERE title = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    # If not found, we'll create it - return the title as marker
    return identifier


def _resolve_batch_id(self, identifier: str) -> str:
    """Resolve batch ID from batch name"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    query = "SELECT id FROM batch WHERE batch = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return identifier


def _resolve_participant_id(self, identifier: str) -> str:
    """Resolve participant/person ID from email, username, or ID"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    # Try by email
    query = "SELECT id FROM person WHERE email = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    # Try by username in users table
    query = """
    SELECT p.id FROM person p
    JOIN users u ON u."personId"::text = p.id
    WHERE u.username = %s LIMIT 1
    """
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return identifier


def _resolve_module_id(self, identifier: str) -> str:
    """Resolve module ID from module name"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    query = "SELECT id FROM module WHERE module = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return identifier


def _resolve_assignment_id(self, identifier: str) -> str:
    """Resolve assignment ID from assignment name"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    query = "SELECT id FROM assignment WHERE assignment = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return identifier


def _resolve_survey_id(self, identifier: str) -> str:
    """Resolve survey ID from survey name"""
    if not identifier:
        return None
    
    try:
        uuid.UUID(identifier)
        return identifier
    except:
        pass
    
    query = "SELECT id FROM survey WHERE survey = %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (identifier,))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return identifier


def _resolve_batch_status_id(self, status_name: str) -> str:
    """Resolve batch status ID from status name"""
    if not status_name:
        return None
    
    status_map = {
        "PLANNING": 1,
        "ACTIVE": 2,
        "COMPLETED": 3,
        "CANCELLED": 4,
        "ON_HOLD": 5
    }
    
    return status_map.get(status_name.upper(), 1)


def _lookup_lms_country_id(self, country_name: str) -> str:
    """Look up country ID from country name in LMS database"""
    if not country_name:
        return None
    
    query = "SELECT id FROM country WHERE country ILIKE %s LIMIT 1"
    try:
        df = self.db_manager.execute_query(query, (f"%{country_name}%",))
        if not df.empty:
            return df['id'].iloc[0]
    except:
        pass
    
    return None


def _generate_username_if_empty(self, value: str, email: str = None) -> str:
    """Generate username from email if empty"""
    if value and value.strip():
        return value
    
    if email:
        # Generate username from email
        username = email.split('@')[0].lower()
        # Remove special characters
        import re
        username = re.sub(r'[^a-z0-9_]', '_', username)
        return username
    
    return None