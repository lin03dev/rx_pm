"""Schema enforcement for report queries against AG, LMS, and Telios."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from config.schema_registry import (
    get_companion_connection,
    get_cross_db_report_config,
    get_report_project_binding,
    get_system_for_connection,
    list_system_tables,
)
from core.database_manager import DatabaseManager

TABLE_PATTERN = re.compile(
    r'\b(?:FROM|JOIN)\s+"?([a-zA-Z_][a-zA-Z0-9_]*)"?',
    re.IGNORECASE,
)


class SchemaViolationError(ValueError):
    """Raised when a report violates schema or database binding rules."""


class SchemaGuard:
    """Validate database bindings and confine queries to registered tables."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        db_name: Optional[str],
        report_id: Optional[str] = None,
    ):
        self.db_manager = db_manager
        self.db_name = db_name
        self.report_id = report_id
        self.system = get_system_for_connection(db_name) if db_name else None
        self._column_cache: Dict[str, List[str]] = {}

    @property
    def allowed_tables(self) -> set[str]:
        if not self.system:
            return set()
        return set(list_system_tables(self.system).keys())

    def validate_primary_connection(self) -> None:
        if not self.db_name:
            raise SchemaViolationError("No database selected for report generation")
        if not self.system:
            raise SchemaViolationError(
                f"Connection '{self.db_name}' is not mapped to AG, LMS, or Telios in schema_registry.yaml"
            )
        if not self.report_id:
            return

        binding = get_report_project_binding(self.report_id)
        if not binding:
            return

        if binding == "Utility":
            return

        cross_db = get_cross_db_report_config(self.report_id)
        allowed_systems = {binding}
        if cross_db:
            allowed_systems.add(cross_db.get("primary", binding))
            for enrichment in cross_db.get("enrichments", []):
                if enrichment.get("system"):
                    allowed_systems.add(enrichment["system"])

        if self.system not in allowed_systems:
            raise SchemaViolationError(
                f"Report '{self.report_id}' must run against {sorted(allowed_systems)}; "
                f"got '{self.db_name}' ({self.system})"
            )

    def validate_companion_connection(self, target_system: str) -> str:
        if not self.db_name:
            raise SchemaViolationError("No primary database selected")
        companion = get_companion_connection(self.db_name, target_system)
        if not companion:
            raise SchemaViolationError(
                f"No {target_system} companion connection configured for '{self.db_name}'"
            )
        cross_db = get_cross_db_report_config(self.report_id or "")
        if cross_db:
            allowed = {item.get("system") for item in cross_db.get("enrichments", [])}
            if target_system not in allowed:
                raise SchemaViolationError(
                    f"Report '{self.report_id}' is not allowed to enrich from {target_system}"
                )
        return companion

    def tables_exist(self, *tables: str) -> bool:
        return all(self.has_table(table) for table in tables)

    def has_table(self, table: str) -> bool:
        if table not in self.allowed_tables:
            return False
        return self.db_manager.table_exists(table, db_name=self.db_name)

    def require_tables(self, *tables: str) -> None:
        if not self.system:
            raise SchemaViolationError(f"Unknown schema system for connection '{self.db_name}'")
        missing_registry = [table for table in tables if table not in self.allowed_tables]
        if missing_registry:
            raise SchemaViolationError(
                f"Tables {missing_registry} are not registered for {self.system} in schema_registry.yaml"
            )
        missing_db = [table for table in tables if not self.db_manager.table_exists(table, db_name=self.db_name)]
        if missing_db:
            raise SchemaViolationError(
                f"Tables {missing_db} do not exist in database '{self.db_name}'"
            )

    def table_columns(self, table: str) -> List[str]:
        if table not in self._column_cache:
            if table not in self.allowed_tables:
                self._column_cache[table] = []
            else:
                query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND lower(table_name) = lower(%s)
                """
                try:
                    conn = self.db_manager._get_connection(self.db_name)
                    with conn.cursor() as cursor:
                        cursor.execute(query, (table,))
                        rows = cursor.fetchall()
                    self._column_cache[table] = [str(row[0]).lower() for row in rows]
                except Exception:
                    self._column_cache[table] = []
        return self._column_cache[table]

    @staticmethod
    def quote_identifier(column_name: str, system: Optional[str]) -> str:
        if system == "AG" and any(ch.isupper() for ch in column_name):
            return f'"{column_name}"'
        if column_name.islower() and column_name.isidentifier():
            return column_name
        return f'"{column_name}"'

    def pick_column(self, table: str, candidates: Sequence[str]) -> Optional[str]:
        columns = self.table_columns(table)
        for candidate in candidates:
            if candidate.lower() in columns:
                registry_columns = list_system_tables(self.system).get(table, {}).get("columns", [])
                for registry_name in registry_columns:
                    if registry_name.lower() == candidate.lower():
                        return registry_name
                return candidate
        return None

    def pick_foreign_key(self, table: str, base_name: str) -> str:
        columns = self.table_columns(table)
        id_name = f"{base_name}_id"
        if id_name in columns:
            return f"{table[:1]}.{id_name}" if len(table) == 1 else f"b.{id_name}" if table == "batch" else f"{table}.{id_name}"
        if base_name in columns:
            alias = "b" if table == "batch" else table[0]
            return f"{alias}.{base_name}"
        return f"b.{id_name}" if table == "batch" else f"{table}.{id_name}"

    def batch_course_join(self, batch_alias: str = "b", course_alias: str = "c") -> str:
        columns = self.table_columns("batch")
        if "course_id" in columns:
            return f"{batch_alias}.course_id = {course_alias}.id"
        if "course" in columns:
            return f"{batch_alias}.course = {course_alias}.id"
        raise SchemaViolationError("batch table has no course_id/course foreign key")

    def batch_country_join(self, batch_alias: str = "b", country_alias: str = "cnt") -> str:
        columns = self.table_columns("batch")
        if "country_id" in columns:
            return f"{batch_alias}.country_id = {country_alias}.id"
        if "country" in columns:
            return f"{batch_alias}.country = {country_alias}.id"
        raise SchemaViolationError("batch table has no country_id/country foreign key")

    def extract_tables(self, query: str) -> List[str]:
        return [match.lower() for match in TABLE_PATTERN.findall(query)]

    def extract_schema_tables(self, query: str) -> List[str]:
        """Return only table names registered for the active schema system."""
        candidates = sorted(set(self.extract_tables(query)))
        if not self.system:
            return candidates
        allowed = self.allowed_tables
        return [name for name in candidates if name in allowed]

    def assert_query_tables(self, query: str, explicit_tables: Optional[Iterable[str]] = None) -> None:
        tables = sorted(set(explicit_tables or self.extract_tables(query)))
        if not tables:
            raise SchemaViolationError("Query does not declare any schema tables")
        self.require_tables(*tables)

    def query(
        self,
        query: str,
        tables: Sequence[str],
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        self.assert_query_tables(query, tables)
        return self.db_manager.execute_query(query, params, db_name=self.db_name)

    def query_optional(
        self,
        query: str,
        tables: Sequence[str],
        params: Optional[dict] = None,
        message: str = "Data not available",
    ) -> pd.DataFrame:
        try:
            if not self.tables_exist(*tables):
                return self.message_frame(message)
            return self.query(query, tables, params=params)
        except SchemaViolationError as exc:
            return self.message_frame(str(exc))

    @staticmethod
    def message_frame(message: str) -> pd.DataFrame:
        return pd.DataFrame({"Message": [message]})

    def companion_query(
        self,
        target_system: str,
        query: str,
        tables: Sequence[str],
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        companion_db = self.validate_companion_connection(target_system)
        companion = SchemaGuard(self.db_manager, companion_db, self.report_id)
        return companion.query(query, tables, params=params)
