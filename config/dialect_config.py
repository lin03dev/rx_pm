"""
Dynamic Dialect Configuration - Centralized handling of dialects/ROLV codes
Supports both languages with and without dialects
"""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
from dataclasses import dataclass, field


@dataclass
class DialectInfo:
    """Information about a dialect"""
    dialect_id: Optional[str]
    dialect_name: str
    rolv_code: str
    is_null: bool = False
    
    def __post_init__(self):
        if self.dialect_id is None:
            self.is_null = True
            self.dialect_name = ""
            self.rolv_code = ""


class DialectManager:
    """Centralized manager for dialect/ROLV information"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._dialects_cache: Dict[str, List[DialectInfo]] = {}
        self._language_dialects_cache: Dict[str, List[DialectInfo]] = {}
    
    def get_dialects_for_language(self, language_id: str) -> List[DialectInfo]:
        """Get all dialects for a specific language"""
        if language_id in self._language_dialects_cache:
            return self._language_dialects_cache[language_id]
        
        query = f"""
        SELECT id, name, "rolvCode"
        FROM dialects 
        WHERE "languageId" = {language_id}
        ORDER BY name
        """
        try:
            df = self.db_manager.execute_query(query)
            dialects = []
            for _, row in df.iterrows():
                dialects.append(DialectInfo(
                    dialect_id=row['id'],
                    dialect_name=row['name'],
                    rolv_code=row.get('rolvCode', '') or ''
                ))
            self._language_dialects_cache[language_id] = dialects
            return dialects
        except:
            return []
    
    def get_project_dialect(self, project_id: str) -> DialectInfo:
        """Get dialect information for a specific project"""
        query = f"""
        SELECT 
            d.id as dialect_id,
            COALESCE(d.name, '') as dialect_name,
            COALESCE(d."rolvCode", '') as rolv_code
        FROM projects p
        LEFT JOIN dialects d ON p."dialectId" = d.id
        WHERE p.id = '{project_id}'
        LIMIT 1
        """
        try:
            df = self.db_manager.execute_query(query)
            if not df.empty:
                row = df.iloc[0]
                return DialectInfo(
                    dialect_id=row['dialect_id'] if pd.notna(row['dialect_id']) else None,
                    dialect_name=row['dialect_name'] if pd.notna(row['dialect_name']) else '',
                    rolv_code=row['rolv_code'] if pd.notna(row['rolv_code']) else ''
                )
        except:
            pass
        return DialectInfo(dialect_id=None, dialect_name='', rolv_code='')
    
    def get_language_dialect_combinations(self, country: str = None, language: str = None) -> pd.DataFrame:
        """
        Get all language-dialect combinations including NULL dialect
        Returns a DataFrame with columns: country, language, dialect_id, dialect_name, rolv_code
        """
        query = """
        SELECT DISTINCT 
            c.name as country,
            l.id as language_id,
            l.name as language,
            l."isoCode" as lan_iso_code,
            d.id as dialect_id,
            COALESCE(d.name, '') as dialect_name,
            COALESCE(d."rolvCode", '') as rolv_code
        FROM projects p
        LEFT JOIN languages l ON p."languageId" = l.id
        LEFT JOIN countries c ON p."countryId" = c.id
        LEFT JOIN dialects d ON p."dialectId" = d.id
        WHERE p."projectType" IN ('TEXT_TRANSLATION', 'OBS', 'LITERATURE', 'LITERATURE_PROJECT',
                                  'GRAMMAR_PHRASES', 'GRAMMAR_PRONOUNS', 'GRAMMAR_CONNECTIVES')
          AND c.name IS NOT NULL
          AND c.name NOT ILIKE '%deleted%'
          AND c.name NOT ILIKE '%test%'
        """
        
        if country:
            query += f" AND c.name = '{country}'"
        if language:
            query += f" AND l.name = '{language}'"
        
        query += " ORDER BY c.name, l.name, COALESCE(d.name, '')"
        
        try:
            df = self.db_manager.execute_query(query)
            # Add a special row for NULL dialect if needed
            return df
        except Exception as e:
            print(f"Error getting language-dialect combinations: {e}")
            return pd.DataFrame()
    
    def get_mtts_for_language_dialect(self, language: str, dialect_name: str = None) -> List[str]:
        """Get MTT names for a specific language and dialect"""
        lang_escaped = language.replace("'", "''")
        
        if dialect_name:
            dialect_escaped = dialect_name.replace("'", "''")
            query = f"""
            SELECT DISTINCT COALESCE(NULLIF(u.name, ''), u.username) as mtt_name
            FROM users u
            JOIN users_to_projects utp ON u.id = utp."userId"
            JOIN projects p ON utp."projectId" = p.id
            JOIN languages l ON p."languageId" = l.id
            LEFT JOIN dialects d ON p."dialectId" = d.id
            WHERE l.name = '{lang_escaped}'
              AND d.name = '{dialect_escaped}'
              AND utp.role = 'MTT'
            """
        else:
            query = f"""
            SELECT DISTINCT COALESCE(NULLIF(u.name, ''), u.username) as mtt_name
            FROM users u
            JOIN users_to_projects utp ON u.id = utp."userId"
            JOIN projects p ON utp."projectId" = p.id
            JOIN languages l ON p."languageId" = l.id
            WHERE l.name = '{lang_escaped}'
              AND (p."dialectId" IS NULL OR p."dialectId" = '')
              AND utp.role = 'MTT'
            """
        
        try:
            df = self.db_manager.execute_query(query)
            return df['mtt_name'].tolist() if not df.empty else []
        except:
            return []
    
    def get_dialect_display(self, dialect_info: DialectInfo) -> Tuple[str, str]:
        """Get display values for dialect (name and ROLV code)"""
        if dialect_info.is_null:
            return "", ""
        return dialect_info.dialect_name, dialect_info.rolv_code
    
    def clear_cache(self):
        """Clear all caches"""
        self._dialects_cache.clear()
        self._language_dialects_cache.clear()


# Singleton instance
_dialect_manager = None

def get_dialect_manager(db_manager) -> DialectManager:
    """Get singleton instance of DialectManager"""
    global _dialect_manager
    if _dialect_manager is None:
        _dialect_manager = DialectManager(db_manager)
    return _dialect_manager
