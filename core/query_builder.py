"""
Query Builder - SQL query construction utilities
"""

from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import re

class ConditionOperator(Enum):
    """SQL operators for WHERE conditions"""
    EQ = "="
    NE = "!="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    LIKE = "LIKE"
    ILIKE = "ILIKE"
    IN = "IN"
    NOT_IN = "NOT IN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    BETWEEN = "BETWEEN"

@dataclass
class QueryCondition:
    """Represents a single WHERE condition"""
    field: str
    operator: ConditionOperator
    value: Any
    param_name: Optional[str] = None

class QueryBuilder:
    """Builds SQL queries with proper parameterization"""
    
    def __init__(self, base_query: str = None):
        self.base_query = base_query or ""
        self.conditions: List[QueryCondition] = []
        self.params: Dict[str, Any] = {}
        self.order_by: List[str] = []
        self.limit_val: Optional[int] = None
        self.offset_val: Optional[int] = None
        self.group_by: List[str] = []
        self.having_conditions: List[QueryCondition] = []
        self.joins: List[str] = []
        self.select_fields: List[str] = []
        self.param_counter = 0
    
    def select(self, fields: List[str]) -> 'QueryBuilder':
        """Set SELECT fields"""
        self.select_fields = fields
        return self
    
    def from_table(self, table: str, alias: str = None) -> 'QueryBuilder':
        """Set FROM table"""
        self.base_query = f"SELECT * FROM {table}"
        if alias:
            self.base_query += f" AS {alias}"
        return self
    
    def join(self, join_type: str, table: str, condition: str, alias: str = None) -> 'QueryBuilder':
        """Add a JOIN clause"""
        join_str = f"{join_type} JOIN {table}"
        if alias:
            join_str += f" AS {alias}"
        join_str += f" ON {condition}"
        self.joins.append(join_str)
        return self
    
    def where(self, field: str, operator: ConditionOperator, value: Any, param_name: str = None) -> 'QueryBuilder':
        """Add a WHERE condition"""
        if param_name is None:
            self.param_counter += 1
            param_name = f"p_{self.param_counter}"
        
        self.conditions.append(QueryCondition(field, operator, value, param_name))
        self.params[param_name] = value
        return self
    
    def where_raw(self, condition: str, params: Dict[str, Any] = None) -> 'QueryBuilder':
        """Add raw WHERE condition"""
        self.conditions.append(QueryCondition(condition, ConditionOperator.EQ, None, None))
        if params:
            self.params.update(params)
        return self
    
    def order_by_field(self, field: str, direction: str = 'ASC') -> 'QueryBuilder':
        """Add ORDER BY clause"""
        self.order_by.append(f"{field} {direction}")
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """Set LIMIT"""
        self.limit_val = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """Set OFFSET"""
        self.offset_val = offset
        return self
    
    def group_by_field(self, field: str) -> 'QueryBuilder':
        """Add GROUP BY clause"""
        self.group_by.append(field)
        return self
    
    def having(self, field: str, operator: ConditionOperator, value: Any) -> 'QueryBuilder':
        """Add HAVING condition"""
        self.having_conditions.append(QueryCondition(field, operator, value, None))
        return self
    
    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build the complete SQL query"""
        parts = []
        
        # SELECT clause
        if self.select_fields:
            parts.append(f"SELECT {', '.join(self.select_fields)}")
        elif self.base_query:
            parts.append(self.base_query)
        else:
            parts.append("SELECT *")
        
        # FROM and JOINs
        if self.joins:
            # Extract base table from first join or use existing
            if not self.base_query:
                parts[0] = "SELECT *"
            parts.extend(self.joins)
        
        # WHERE clause
        if self.conditions:
            where_clauses = []
            for cond in self.conditions:
                if cond.operator in [ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL]:
                    where_clauses.append(f"{cond.field} {cond.operator.value}")
                elif cond.operator in [ConditionOperator.IN, ConditionOperator.NOT_IN]:
                    placeholders = ','.join([f'%({cond.param_name}_{i})s' for i in range(len(cond.value))])
                    for i, v in enumerate(cond.value):
                        self.params[f"{cond.param_name}_{i}"] = v
                    where_clauses.append(f"{cond.field} {cond.operator.value} ({placeholders})")
                elif cond.operator == ConditionOperator.BETWEEN:
                    where_clauses.append(f"{cond.field} BETWEEN %({cond.param_name}_start)s AND %({cond.param_name}_end)s")
                    self.params[f"{cond.param_name}_start"] = cond.value[0]
                    self.params[f"{cond.param_name}_end"] = cond.value[1]
                elif cond.param_name:
                    where_clauses.append(f"{cond.field} {cond.operator.value} %({cond.param_name})s")
                else:
                    where_clauses.append(cond.field)
            
            parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # GROUP BY
        if self.group_by:
            parts.append(f"GROUP BY {', '.join(self.group_by)}")
        
        # HAVING
        if self.having_conditions:
            having_clauses = [f"{cond.field} {cond.operator.value} {cond.value}" for cond in self.having_conditions]
            parts.append(f"HAVING {' AND '.join(having_clauses)}")
        
        # ORDER BY
        if self.order_by:
            parts.append(f"ORDER BY {', '.join(self.order_by)}")
        
        # LIMIT and OFFSET
        if self.limit_val is not None:
            parts.append(f"LIMIT {self.limit_val}")
        if self.offset_val is not None:
            parts.append(f"OFFSET {self.offset_val}")
        
        query = "\n".join(parts)
        return query, self.params
    
    def build_count_query(self) -> Tuple[str, Dict[str, Any]]:
        """Build a COUNT query with same conditions"""
        # Store original select fields
        original_select = self.select_fields
        self.select_fields = ["COUNT(*) as total"]
        
        query, params = self.build()
        
        # Restore select fields
        self.select_fields = original_select
        
        return query, params


class AdvancedQueryBuilder(QueryBuilder):
    """Extended query builder with advanced features"""
    
    def __init__(self, base_query: str = None):
        super().__init__(base_query)
        self.subqueries: List[Tuple[str, str]] = []  # (subquery, alias)
        self.window_functions: List[str] = []
        self.ctes: List[Tuple[str, str]] = []  # Common Table Expressions
    
    def with_cte(self, name: str, query: str) -> 'AdvancedQueryBuilder':
        """Add a Common Table Expression"""
        self.ctes.append((name, query))
        return self
    
    def add_subquery(self, subquery: str, alias: str) -> 'AdvancedQueryBuilder':
        """Add a subquery in FROM clause"""
        self.subqueries.append((subquery, alias))
        return self
    
    def row_number(self, partition_by: List[str], order_by: List[str], alias: str = 'row_num') -> 'AdvancedQueryBuilder':
        """Add ROW_NUMBER window function"""
        partition = f"PARTITION BY {', '.join(partition_by)}" if partition_by else ""
        order = f"ORDER BY {', '.join(order_by)}" if order_by else ""
        self.window_functions.append(f"ROW_NUMBER() OVER ({partition} {order}) as {alias}")
        return self
    
    def build(self) -> Tuple[str, Dict[str, Any]]:
        """Build advanced query with CTEs and subqueries"""
        parts = []
        
        # CTEs
        if self.ctes:
            cte_parts = [f"{name} AS ({query})" for name, query in self.ctes]
            parts.append(f"WITH {', '.join(cte_parts)}")
        
        # Main SELECT
        if self.select_fields:
            all_fields = self.select_fields.copy()
            all_fields.extend(self.window_functions)
            parts.append(f"SELECT {', '.join(all_fields)}")
        elif self.base_query:
            parts.append(self.base_query)
        else:
            parts.append("SELECT *")
        
        # FROM with subqueries
        if self.subqueries:
            from_parts = []
            for subquery, alias in self.subqueries:
                from_parts.append(f"({subquery}) AS {alias}")
            parts.append(f"FROM {', '.join(from_parts)}")
        elif self.joins:
            parts.extend(self.joins)
        
        # WHERE clause
        if self.conditions:
            where_clauses = []
            for cond in self.conditions:
                if cond.operator in [ConditionOperator.IS_NULL, ConditionOperator.IS_NOT_NULL]:
                    where_clauses.append(f"{cond.field} {cond.operator.value}")
                elif cond.param_name:
                    where_clauses.append(f"{cond.field} {cond.operator.value} %({cond.param_name})s")
                    self.params[cond.param_name] = cond.value
                else:
                    where_clauses.append(cond.field)
            parts.append(f"WHERE {' AND '.join(where_clauses)}")
        
        # GROUP BY
        if self.group_by:
            parts.append(f"GROUP BY {', '.join(self.group_by)}")
        
        # HAVING
        if self.having_conditions:
            having_clauses = [f"{cond.field} {cond.operator.value} {cond.value}" for cond in self.having_conditions]
            parts.append(f"HAVING {' AND '.join(having_clauses)}")
        
        # ORDER BY
        if self.order_by:
            parts.append(f"ORDER BY {', '.join(self.order_by)}")
        
        # LIMIT and OFFSET
        if self.limit_val is not None:
            parts.append(f"LIMIT {self.limit_val}")
        if self.offset_val is not None:
            parts.append(f"OFFSET {self.offset_val}")
        
        query = "\n".join(parts)
        return query, self.params


class QueryTemplate:
    """Pre-defined query templates"""
    
    @staticmethod
    def get_user_details() -> str:
        """Template for user details query"""
        return """
        SELECT 
            u.id,
            u.username,
            u.email,
            u.role::text as user_role,
            u.name as display_name,
            u."isActive",
            u.created_at,
            p."firstName",
            p."lastName",
            p.phone,
            p.organisation,
            p.gender,
            p.state,
            p.city,
            c.name as country
        FROM users u
        LEFT JOIN person p ON u."personId"::text = p.id
        LEFT JOIN countries c ON p."countryId" = c.id
        WHERE 1=1
        """
    
    @staticmethod
    def get_project_summary() -> str:
        """Template for project summary query"""
        return """
        SELECT 
            p.id as project_id,
            p.name as project_name,
            l.name as language,
            p.project_type,
            p.stage,
            COUNT(DISTINCT utp."userId") as assigned_users,
            COUNT(DISTINCT CASE WHEN utp.verses IS NOT NULL THEN 1 END) as has_verse_assignments
        FROM projects p
        LEFT JOIN languages l ON p.languageId = l.id
        LEFT JOIN users_to_projects utp ON p.id = utp."projectId"
        GROUP BY p.id, p.name, l.name, p.project_type, p.stage
        ORDER BY p.name
        """
    
    @staticmethod
    def get_worklog_summary() -> str:
        """Template for worklog summary query"""
        return """
        SELECT 
            w.role,
            w."translationSoftware",
            COUNT(*) as total_sessions,
            SUM(EXTRACT(DAY FROM (w."endDate" - w."startDate")) + 1) as total_days,
            COUNT(DISTINCT w."userId") as unique_users,
            COUNT(DISTINCT w."projectId") as projects_worked
        FROM worklogs w
        WHERE w."noWork" = false
        GROUP BY w.role, w."translationSoftware"
        ORDER BY total_sessions DESC
        """
    
    @staticmethod
    def get_obs_progress() -> str:
        """Template for OBS progress query"""
        return """
        SELECT 
            p.name as project_name,
            COUNT(DISTINCT opc.id) as total_chapters,
            COUNT(DISTINCT CASE WHEN opc.version > 1 THEN opc.id END) as translated_chapters,
            COUNT(DISTINCT oar.id) as audio_recordings
        FROM projects p
        JOIN obs_projects op ON p.id = op."projectId"
        LEFT JOIN obs_project_chapters opc ON op.id = opc."obsProjectId"
        LEFT JOIN obs_audio_recordings oar ON opc.id = oar."obsProjectChapterId"
        GROUP BY p.name
        """
    
    @staticmethod
    def get_language_stats() -> str:
        """Template for language statistics query"""
        return """
        SELECT 
            l.name as language_name,
            l.iso_code,
            COUNT(DISTINCT p.id) as project_count,
            COUNT(DISTINCT utp."userId") as user_count
        FROM languages l
        LEFT JOIN projects p ON l.id = p.languageId
        LEFT JOIN users_to_projects utp ON p.id = utp."projectId"
        GROUP BY l.name, l.iso_code
        ORDER BY project_count DESC
        """
    
    @staticmethod
    def get_assignment_summary() -> str:
        """Template for assignment summary query"""
        return """
        SELECT 
            u.username,
            u.role::text as user_role,
            COUNT(DISTINCT utp."projectId") as assigned_projects,
            SUM(array_length(string_to_array(COALESCE(utp.verses, ''), ','), 1)) as total_verses,
            SUM(array_length(string_to_array(COALESCE(utp."obsChapters", ''), ','), 1)) as total_obs
        FROM users u
        LEFT JOIN users_to_projects utp ON u.id = utp."userId"
        WHERE utp."projectId" IS NOT NULL
        GROUP BY u.username, u.role
        ORDER BY total_verses DESC NULLS LAST
        """