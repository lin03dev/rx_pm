"""
BT Academy Student Report

Standard master student list for BT Academy with Autographa IDs, validation status,
current status, and enrollment history. One row per student.
Language and Autographa IDs are enriched from AG when available.
Autographa IDs must be exactly 6 digits (AG-XXXXXX).
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from config.schema_registry import is_cross_db_enrichment_allowed
from core.schema_guard import SchemaGuard, SchemaViolationError
from reports.base_report_v2 import BaseReportV2


class BTAcademyStudentReport(BaseReportV2):
    """One row per BT Academy student with Autographa ID, roles, and enrollment status."""

    AUTOGRAPHA_ID_CANDIDATES = (
        "rollnumber",
        "autographa_id",
        "autographaid",
    )
    ENROLLMENT_DATE_CANDIDATES = (
        "enrollmentdate",
        "enrollment_date",
        "createdat",
        "created_at",
    )
    BATCH_START_DATE_CANDIDATES = (
        "start_date",
        "startdate",
    )
    ROLE_ALIASES = {
        "mtt": "MTT",
        "qc": "QC",
        "ict": "ICT",
        "lqc": "LQC",
        "trainer": "Trainer",
        "admin": "Admin",
        "student": "Student",
        "facilitator": "Facilitator",
        "mentor": "Mentor",
    }
    ROLE_PREFIX_PATTERN = re.compile(
        r"^(qc|mtt|ict|lqc|trainer|admin|facilitator|mentor|student)(\s|$|\()",
        re.IGNORECASE,
    )
    AG_ID_PATTERN = re.compile(r"^AG-?\d{6}$", re.IGNORECASE)
    AUTOGRAPHA_ID_DIGITS = 6
    EMPTY_VALUES = {"", "none", "nan", "not specified", "null", "n/a", "na"}

    def __init__(self, db_manager, **kwargs):
        super().__init__(db_manager, **kwargs)
        self._ag_enrichment_stats: Dict[str, int] = {}
        self._lms_source_stats: Dict[str, int] = {}

    def generate(self) -> Dict[str, pd.DataFrame]:
        roster, enrollment_details = self._get_student_roster()
        summary = self._get_summary_stats(roster)
        return {
            "student_roster": roster,
            "enrollment_details": enrollment_details,
            "summary_stats": summary,
        }


    def _table_columns(self, table_name: str) -> List[str]:
        return [name.lower() for name in self.schema.table_columns(table_name)]

    def _table_exists(self, table_name: str) -> bool:
        return self.schema.has_table(table_name)

    def _pick_column(self, columns: List[str], candidates: Tuple[str, ...]) -> Optional[str]:
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    def _table_columns_for_db(self, table_name: str, db_name: str) -> List[str]:
        guard = SchemaGuard(self.db_manager, db_name, self.report_id)
        return [name.lower() for name in guard.table_columns(table_name)]

    def _quoted_ident(self, column_name: str) -> str:
        if column_name.islower() and column_name.isidentifier():
            return column_name
        if column_name.isidentifier():
            return f'"{column_name}"'
        return f'"{column_name}"'

    def _quoted(self, column_name: str) -> str:
        return self._quoted_ident(column_name)

    def _pick_timestamp_expr(self, table_alias: str, columns: List[str]) -> str:
        if "updatedat" in columns:
            return f'{table_alias}."updatedAt"'
        if "createdat" in columns:
            return f'{table_alias}."createdAt"'
        return "NULL::timestamp"

    def _autographa_id_expr(self, person_columns: List[str]) -> str:
        parts = []
        for candidate in self.AUTOGRAPHA_ID_CANDIDATES:
            if candidate in person_columns:
                col = self._quoted(candidate)
                parts.append(f"NULLIF(TRIM(p.{col}::text), '')")
        if not parts:
            return "NULL"
        return f"COALESCE({', '.join(parts)})"

    @classmethod
    def _extract_id_digits(cls, value: object) -> str:
        text = re.sub(r"^AG-", "", str(value or "").strip(), flags=re.IGNORECASE)
        return re.sub(r"\D", "", text)

    @classmethod
    def _evaluate_autographa_candidate(cls, value: object) -> Tuple[Optional[str], Optional[str]]:
        """Return canonical AG-XXXXXX (6 digits) and optional issue note."""
        text = str(value or "").strip()
        if not text or text.lower() in cls.EMPTY_VALUES:
            return None, None
        if cls._looks_like_role(text):
            return None, None

        digits = cls._extract_id_digits(text)
        if not digits:
            return None, None
        if len(digits) == cls.AUTOGRAPHA_ID_DIGITS:
            return f"AG-{digits}", None
        if len(digits) < cls.AUTOGRAPHA_ID_DIGITS:
            return None, (
                f"Autographa ID incomplete ({len(digits)} digits, expected "
                f"{cls.AUTOGRAPHA_ID_DIGITS}) - LMS/AG data may be missing"
            )
        return None, (
            f"Autographa ID invalid ({len(digits)} digits, expected "
            f"{cls.AUTOGRAPHA_ID_DIGITS})"
        )

    @classmethod
    def _format_autographa_id(cls, value: object) -> str:
        canonical, _ = cls._evaluate_autographa_candidate(value)
        return canonical or "Not specified"

    @classmethod
    def _looks_like_role(cls, value: object) -> bool:
        text = str(value or "").strip()
        if not text:
            return False
        lowered = text.lower()
        if " in " in lowered or "language" in lowered:
            return True
        if cls.ROLE_PREFIX_PATTERN.match(lowered):
            compact = text.replace(" ", "")
            return not bool(cls.AG_ID_PATTERN.match(compact))
        if " " in text and not cls.AG_ID_PATTERN.match(text.replace(" ", "")):
            return True
        return False

    @classmethod
    def _is_valid_ag_id_candidate(cls, value: object) -> bool:
        canonical, _ = cls._evaluate_autographa_candidate(value)
        return canonical is not None

    @staticmethod
    def _normalize_name(value: object) -> str:
        text = str(value or "").strip().lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-z0-9' ]+", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _name_lookup_keys(cls, *names: object) -> List[str]:
        keys: set[str] = set()
        for name in names:
            normalized = cls._normalize_name(name)
            if not normalized:
                continue
            keys.add(normalized)
            tokens = sorted(set(normalized.split()))
            if len(tokens) >= 2:
                keys.add(" ".join(tokens))
                keys.add(f"{tokens[0]}|{tokens[-1]}")
                keys.add(f"{tokens[-1]}|{tokens[0]}")
        return sorted(keys)

    @staticmethod
    def _normalize_roll(value: object) -> str:
        digits = BTAcademyStudentReport._extract_id_digits(value)
        return digits if len(digits) == BTAcademyStudentReport.AUTOGRAPHA_ID_DIGITS else ""

    @staticmethod
    def _normalize_email(value: object) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _normalize_role(value: object) -> str:
        text = str(value or "").strip()
        if not text or text.lower() in BTAcademyStudentReport.EMPTY_VALUES:
            return ""
        lowered = text.lower()
        if lowered in BTAcademyStudentReport.ROLE_ALIASES:
            return BTAcademyStudentReport.ROLE_ALIASES[lowered]
        if text.isupper() and len(text) <= 4:
            return text
        return text[:1].upper() + text[1:]

    @staticmethod
    def _format_validation_status(value: object) -> str:
        text = str(value or "").strip()
        if not text or text.lower() in BTAcademyStudentReport.EMPTY_VALUES:
            return "Not specified"
        return text.title()

    def _derive_current_status(
        self,
        present_status: object,
        validation_status: object,
        leaving_date: object,
        reason: object,
    ) -> str:
        if pd.notna(leaving_date):
            return "Inactive"
        if pd.notna(reason) and str(reason).strip().lower() not in self.EMPTY_VALUES:
            return "Inactive"

        present = str(present_status or "").strip()
        present_lower = present.lower()
        validation = str(validation_status or "").strip().upper()

        if present_lower == "inactive":
            return "Inactive"
        if validation == "REJECTED":
            return "Inactive"
        if present_lower == "active":
            return "Active"
        if validation == "PENDING":
            return "Pending"
        if validation == "VALIDATED":
            return "Active"

        if present:
            return present
        return "Not specified"

    @staticmethod
    def _clean_field(value: object, default: str = "Not specified") -> str:
        text = str(value or "").strip()
        if not text or text.lower() in BTAcademyStudentReport.EMPTY_VALUES:
            return default
        return text

    def _build_country_expr(self, person_columns: List[str], batch_columns: List[str]) -> Tuple[str, List[str]]:
        joins: List[str] = []
        parts: List[str] = []

        if self._table_exists("country"):
            if "country_id" in person_columns:
                joins.append("LEFT JOIN country cnt_p ON p.country_id = cnt_p.id")
                parts.append("NULLIF(TRIM(cnt_p.country::text), '')")

            if batch_columns:
                if "country_id" in batch_columns or "country" in batch_columns:
                    batch_country_key = "COALESCE(b.country_id, b.country)" if (
                        "country_id" in batch_columns and "country" in batch_columns
                    ) else ("b.country_id" if "country_id" in batch_columns else "b.country")
                    joins.append(f"LEFT JOIN country cnt_b ON cnt_b.id = {batch_country_key}")
                    parts.append("NULLIF(TRIM(cnt_b.country::text), '')")

        if "country" in person_columns:
            parts.append("NULLIF(TRIM(p.country::text), '')")
        if "presentaddresscountry" in person_columns:
            parts.append("NULLIF(TRIM(p.presentaddresscountry::text), '')")

        expr = f"COALESCE({', '.join(parts)}, 'Not specified')" if parts else "'Not specified'"
        return expr, joins

    def _resolve_ag_database(self) -> Optional[str]:
        if not is_cross_db_enrichment_allowed(self.report_id or "bt-academy-students", "AG"):
            return None
        try:
            companion = self.schema.validate_companion_connection("AG")
            if not self.db_manager.config_manager.get_config(companion):
                return None
            return companion
        except SchemaViolationError:
            return None

    def _fetch_ag_user_profiles(self) -> Dict[str, Dict[str, Any]]:
        empty: Dict[str, Any] = {
            "by_email": {},
            "by_roll": {},
            "by_name": {},
            "all_profiles": [],
        }
        ag_db = self._resolve_ag_database()
        if not ag_db or not self.db_manager.table_exists("users", db_name=ag_db):
            self._ag_enrichment_stats = {"ag_users_indexed": 0, "ag_directory_loaded": 0}
            return empty

        directory = self._fetch_ag_user_directory(ag_db)
        if not directory:
            self._ag_enrichment_stats = {"ag_users_indexed": 0, "ag_directory_loaded": 0}
            return empty

        assignments_by_username = self._fetch_ag_language_assignments(ag_db)
        for username, profile in directory.items():
            profile["assignments"] = assignments_by_username.get(username, [])

        indexed = self._index_ag_profiles(directory.values())
        self._ag_enrichment_stats = {
            "ag_users_indexed": len(directory),
            "ag_directory_loaded": 1,
        }
        return indexed

    def _ag_users_person_join(self) -> str:
        """Join AG users to person; cast both sides to text to avoid type mismatches."""
        return 'LEFT JOIN person ap ON ap.id::text = trim(u."personId"::text)'

    def _fetch_ag_user_directory(self, ag_db: str) -> Dict[str, Dict[str, Any]]:
        """All AG users for ID matching — not limited to language-project members."""
        directory = self._query_ag_user_directory(ag_db, include_person=True)
        if not directory:
            directory = self._query_ag_user_directory(ag_db, include_person=False)
        return directory

    def _query_ag_user_directory(self, ag_db: str, include_person: bool) -> Dict[str, Dict[str, Any]]:
        person_join = ""
        roll_select = "NULL::text AS roll_number_raw"
        person_name_select = "NULL::text AS person_name_key"
        tables = ["users"]

        if include_person and self.db_manager.table_exists("person", db_name=ag_db):
            person_join = self._ag_users_person_join()
            roll_select = 'NULLIF(TRIM(ap."rollNumber"::text), \'\') AS roll_number_raw'
            person_name_select = """
            NULLIF(trim(regexp_replace(
                trim(COALESCE(ap."firstName", '') || ' ' || COALESCE(ap."lastName", '')),
                '\\s+', ' ', 'g'
            )), '') AS person_name_key
            """
            tables.append("person")

        query = f"""
        SELECT
            lower(trim(u.email)) AS email_key,
            u.username AS autographa_id,
            NULLIF(trim(regexp_replace(
                COALESCE(NULLIF(u.name, ''), u.username),
                '\\s+', ' ', 'g'
            )), '') AS display_name_raw,
            {roll_select},
            {person_name_select}
        FROM users u
        {person_join}
        WHERE u.role::text != 'SUPER_ADMIN'
          AND u.username IS NOT NULL
          AND trim(u.username::text) <> ''
        """
        try:
            ag_df = self.companion_schema_query("AG", query, tables)
        except (SchemaViolationError, Exception):
            return {}

        return self._directory_from_ag_df(ag_df)

    def _directory_from_ag_df(self, ag_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        directory: Dict[str, Dict[str, Any]] = {}
        for _, row in ag_df.iterrows():
            autographa_id = str(row.get("autographa_id") or "").strip()
            if not autographa_id or autographa_id.lower() in self.EMPTY_VALUES:
                continue
            if autographa_id not in directory:
                directory[autographa_id] = {
                    "autographa_id": autographa_id,
                    "email_key": str(row.get("email_key") or "").strip(),
                    "name_variants": set(),
                    "assignments": [],
                }
            profile = directory[autographa_id]
            for raw_name in (
                row.get("display_name_raw"),
                row.get("person_name_key"),
            ):
                for key in self._name_lookup_keys(raw_name):
                    profile["name_variants"].add(key)
            roll_raw = str(row.get("roll_number_raw") or "").strip()
            if roll_raw:
                profile["ag_roll_number_raw"] = roll_raw
        return directory

    def _fetch_ag_language_assignments(self, ag_db: str) -> Dict[str, List[Dict[str, Any]]]:
        """Language roles keyed by AG username."""
        if self.db_manager.table_exists("language_project_member_roles", db_name=ag_db):
            query = """
            SELECT
                u.username AS autographa_id,
                lang.name AS language_name,
                lpmr.role::text AS project_role,
                COALESCE(lpmr."assignedAt", lpm."createdAt") AS assignment_sort_date,
                lpmr."revokedAt" AS revoked_at
            FROM users u
            JOIN language_project_members lpm ON lpm."userId" = u.id
            JOIN language_projects lp ON lp.id = lpm."languageProjectId"
            LEFT JOIN languages lang ON lp."languageId" = lang.id
            JOIN language_project_member_roles lpmr ON lpmr."languageProjectMemberId" = lpm.id
            WHERE u.role::text != 'SUPER_ADMIN'
              AND lang.name IS NOT NULL
              AND trim(lang.name) <> ''
            ORDER BY u.username, lang.name, assignment_sort_date ASC NULLS LAST
            """
            tables = [
                "users",
                "language_project_members",
                "language_projects",
                "languages",
                "language_project_member_roles",
            ]
        else:
            utp_columns = self._table_columns_for_db("users_to_projects", ag_db)
            project_columns = self._table_columns_for_db("projects", ag_db)
            utp_sort_expr = self._pick_timestamp_expr("utp", utp_columns)
            project_sort_expr = self._pick_timestamp_expr("pj", project_columns)
            sort_expr = f"COALESCE({utp_sort_expr}, {project_sort_expr})"
            query = f"""
            SELECT
                u.username AS autographa_id,
                lang.name AS language_name,
                utp.role::text AS project_role,
                {sort_expr} AS assignment_sort_date,
                NULL::timestamp AS revoked_at
            FROM users u
            JOIN users_to_projects utp ON u.id = utp."userId"
            JOIN projects pj ON utp."projectId" = pj.id
            LEFT JOIN languages lang ON pj."languageId" = lang.id
            WHERE u.role::text != 'SUPER_ADMIN'
              AND lang.name IS NOT NULL
              AND trim(lang.name) <> ''
            ORDER BY u.username, lang.name, assignment_sort_date ASC NULLS LAST
            """
            tables = ["users", "users_to_projects", "projects", "languages"]

        try:
            ag_df = self.companion_schema_query("AG", query, tables)
        except (SchemaViolationError, Exception):
            return {}

        assignments_by_username: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for _, row in ag_df.iterrows():
            username = str(row.get("autographa_id") or "").strip()
            role = self._normalize_role(row.get("project_role"))
            language = self._clean_field(row.get("language_name"), default="")
            if not username or not language or not role:
                continue
            assignments_by_username[username].append({
                "language": language,
                "role": role,
                "sort_date": pd.to_datetime(row.get("assignment_sort_date"), errors="coerce"),
                "revoked_at": pd.to_datetime(row.get("revoked_at"), errors="coerce"),
            })
        return dict(assignments_by_username)

    def _index_ag_profiles(
        self,
        profiles: Any,
    ) -> Dict[str, Any]:
        by_email: Dict[str, Dict[str, Any]] = {}
        by_roll: Dict[str, Dict[str, Any]] = {}
        by_name: Dict[str, Dict[str, Any]] = {}
        all_profiles: List[Dict[str, Any]] = []

        for profile in profiles:
            all_profiles.append(profile)
            autographa_id = profile["autographa_id"]
            canonical, _ = self._evaluate_autographa_candidate(autographa_id)
            roll_keys = []
            if canonical:
                roll_keys.append(self._normalize_roll(canonical))
            roll_keys.append(self._normalize_roll(autographa_id))
            ag_roll = profile.get("ag_roll_number_raw")
            if ag_roll:
                roll_keys.append(self._normalize_roll(ag_roll))

            email_key = profile.get("email_key", "")
            self._register_profile_lookup(by_email, email_key, profile)
            for roll_key in roll_keys:
                self._register_profile_lookup(by_roll, roll_key, profile)
            for name_key in profile.get("name_variants", set()):
                self._register_profile_lookup(by_name, name_key, profile)

        return {
            "by_email": by_email,
            "by_roll": by_roll,
            "by_name": by_name,
            "all_profiles": all_profiles,
        }

    def _register_profile_lookup(
        self,
        index: Dict[str, Dict[str, Any]],
        key: str,
        profile: Dict[str, Any],
    ) -> None:
        if not key:
            return
        existing = index.get(key)
        if not existing:
            index[key] = profile
            return
        if self._profile_id_rank(profile) > self._profile_id_rank(existing):
            index[key] = profile

    @classmethod
    def _profile_id_rank(cls, profile: Dict[str, Any]) -> int:
        canonical, _ = cls._evaluate_autographa_candidate(profile.get("autographa_id"))
        if canonical:
            return 2
        digits = cls._extract_id_digits(profile.get("autographa_id"))
        if digits:
            return 1
        return 0

    def _lookup_ag_profile(
        self,
        profiles: Dict[str, Any],
        email: str,
        student_name: str,
        roll_candidates: List[str],
        firstname: str = "",
        lastname: str = "",
    ) -> Optional[Dict[str, Any]]:
        if email and email in profiles["by_email"]:
            return profiles["by_email"][email]

        for roll in roll_candidates:
            if roll and roll in profiles["by_roll"]:
                return profiles["by_roll"][roll]

        for key in self._name_lookup_keys(
            student_name,
            f"{firstname} {lastname}".strip(),
            f"{lastname} {firstname}".strip(),
        ):
            if key in profiles["by_name"]:
                return profiles["by_name"][key]

        return self._lookup_ag_profile_by_token_overlap(
            profiles.get("all_profiles", []),
            student_name,
            firstname,
            lastname,
        )

    def _lookup_ag_profile_by_token_overlap(
        self,
        all_profiles: List[Dict[str, Any]],
        student_name: str,
        firstname: str = "",
        lastname: str = "",
    ) -> Optional[Dict[str, Any]]:
        student_tokens = set()
        for key in self._name_lookup_keys(
            student_name,
            f"{firstname} {lastname}".strip(),
            f"{lastname} {firstname}".strip(),
        ):
            if "|" in key:
                student_tokens.update(key.split("|"))
            else:
                student_tokens.update(key.split())

        if len(student_tokens) < 2:
            return None

        best: Optional[Tuple[int, Dict[str, Any]]] = None
        for profile in all_profiles:
            ag_tokens: set[str] = set()
            for variant in profile.get("name_variants", set()):
                if "|" in variant:
                    ag_tokens.update(variant.split("|"))
                else:
                    ag_tokens.update(variant.split())
            if len(ag_tokens) < 2:
                continue

            overlap = student_tokens & ag_tokens
            required = max(2, min(len(student_tokens), len(ag_tokens)) - 1)
            if len(overlap) < required:
                continue

            score = len(overlap)
            if not best or score > best[0]:
                best = (score, profile)

        return best[1] if best else None

    def _build_id_remark(
        self,
        group: pd.DataFrame,
        ag_profile: Optional[Dict[str, Any]],
        id_remark: Optional[str],
    ) -> Optional[str]:
        if id_remark:
            return id_remark
        if ag_profile:
            return "AG username is not a valid 6-digit Autographa ID"

        stats = self._ag_enrichment_stats
        if not stats.get("ag_directory_loaded"):
            return "AG user directory not loaded; check AG database connection"

        first_row = group.iloc[0]
        has_email = bool(str(first_row.get("email_raw") or "").strip())
        has_roll = any(
            str(first_row.get(column) or "").strip()
            for column in ("rollnumber_raw", "autographa_id_raw", "user_login_raw")
        )
        if not has_email and not has_roll:
            return "No AG match; LMS email and roll number are empty"
        if not has_email:
            return "No AG match; LMS email is empty and name/roll did not match AG"
        return "No AG account matched (email, roll number, or name)"

    def _collect_emails(self, group: pd.DataFrame) -> List[str]:
        emails: List[str] = []
        for _, row in group.iterrows():
            email = self._normalize_email(row.get("email_raw"))
            if email and email not in emails:
                emails.append(email)
        return emails

    def _lookup_ag_profile_for_student(
        self,
        profiles: Dict[str, Any],
        group: pd.DataFrame,
        student_name: str,
        firstname: str,
        lastname: str,
    ) -> Optional[Dict[str, Any]]:
        roll_candidates = self._collect_roll_candidates(group)
        emails = self._collect_emails(group)
        for email in emails:
            match = self._lookup_ag_profile(
                profiles,
                email,
                student_name,
                roll_candidates,
                firstname=firstname,
                lastname=lastname,
            )
            if match:
                return match
        return self._lookup_ag_profile(
            profiles,
            "",
            student_name,
            roll_candidates,
            firstname=firstname,
            lastname=lastname,
        )

    def _summarize_language_roles(
        self,
        profile: Optional[Dict[str, Any]],
    ) -> Tuple[str, str, str]:
        """Return consolidated Language, Role, and role-history remarks for one student."""
        if not profile or not profile.get("assignments"):
            return "Not specified", "Not specified", ""

        by_language: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for assignment in profile["assignments"]:
            by_language[assignment["language"]].append(assignment)

        languages: List[str] = []
        role_parts: List[str] = []
        remark_parts: List[str] = []

        for language in sorted(by_language.keys()):
            assignments = sorted(
                by_language[language],
                key=lambda item: item.get("sort_date") or pd.Timestamp.min,
            )
            active_roles = [
                assignment for assignment in assignments
                if pd.isna(assignment.get("revoked_at"))
            ]
            if active_roles:
                current_role = active_roles[-1]["role"]
            elif assignments:
                current_role = assignments[-1]["role"]
            else:
                current_role = "Not specified"

            previous_roles: List[str] = []
            for assignment in assignments:
                role = assignment["role"]
                if role == current_role:
                    continue
                if role and role not in previous_roles:
                    previous_roles.append(role)

            languages.append(language)
            role_parts.append(f"{language}: {current_role}")
            if previous_roles:
                remark_parts.append(
                    f"{language} role(previous): {', '.join(previous_roles)}"
                )

        return ", ".join(languages), "; ".join(role_parts), "; ".join(remark_parts)

    def _resolve_autographa_id(
        self,
        group: pd.DataFrame,
        ag_profile: Optional[Dict[str, Any]],
    ) -> Tuple[str, Optional[str]]:
        id_remark: Optional[str] = None
        best_issue: Optional[str] = None

        if ag_profile and ag_profile.get("autographa_id"):
            canonical, issue = self._evaluate_autographa_candidate(ag_profile["autographa_id"])
            if canonical:
                return canonical, None
            if issue:
                id_remark = issue

        for _, row in group.iterrows():
            for column in ("rollnumber_raw", "autographa_id_raw", "username_raw", "user_login_raw"):
                candidate = row.get(column)
                canonical, issue = self._evaluate_autographa_candidate(candidate)
                if canonical:
                    return canonical, id_remark
                if issue and not best_issue:
                    best_issue = issue

        if not id_remark:
            id_remark = best_issue

        if not id_remark:
            id_remark = self._build_id_remark(group, ag_profile, id_remark)

        return "Not specified", id_remark

    @staticmethod
    def _merge_remarks(id_remark: Optional[str], role_remark: str) -> str:
        parts = [part for part in (id_remark, role_remark) if part]
        return "; ".join(parts)

    def _lms_roster_tables(self) -> List[str]:
        tables = ["enrollment", "person"]
        if self._table_exists("user") and self.schema.pick_column("user", ["personId", "personid"]):
            tables.append("user")
        if self._table_columns("batch"):
            tables.append("batch")
        if self._table_exists("country"):
            tables.append("country")
        return sorted(set(tables))

    def _build_query(self) -> str:
        person_columns = self._table_columns("person")
        enrollment_columns = self._table_columns("enrollment")
        batch_columns = self._table_columns("batch")

        if not person_columns or not enrollment_columns:
            return ""

        autographa_expr = self._autographa_id_expr(person_columns)
        country_expr, country_joins = self._build_country_expr(person_columns, batch_columns)

        rollnumber_expr = (
            f"NULLIF(TRIM(p.{self._quoted('rollnumber')}::text), '')"
            if "rollnumber" in person_columns else "NULL"
        )
        email_expr = (
            f"NULLIF(TRIM(p.{self._quoted('email')}::text), '')"
            if "email" in person_columns else "NULL"
        )
        username_expr = (
            f"NULLIF(TRIM(p.{self._quoted('username')}::text), '')"
            if "username" in person_columns
            else (
                f"NULLIF(TRIM(p.{self._quoted('user_name')}::text), '')"
                if "user_name" in person_columns else "NULL"
            )
        )
        user_join = ""
        user_login_expr = "NULL"
        if self._table_exists("user"):
            user_person_col = self.schema.pick_column("user", ["personId", "personid"])
            if user_person_col:
                lu_person = self.schema.quote_identifier(user_person_col, self.schema.system)
                user_join = f'LEFT JOIN "user" lu ON lu.{lu_person} = p.id'
                user_login_expr = "NULLIF(TRIM(lu.login::text), '')"

        enrollment_date_col = self._pick_column(enrollment_columns, self.ENROLLMENT_DATE_CANDIDATES)
        person_enrollment_date_col = self._pick_column(person_columns, self.ENROLLMENT_DATE_CANDIDATES)
        batch_start_col = self._pick_column(batch_columns, self.BATCH_START_DATE_CANDIDATES) if batch_columns else None

        enrollment_date_expr = (
            f"e.{self._quoted(enrollment_date_col)}"
            if enrollment_date_col else "NULL::timestamp"
        )
        person_enrollment_date_expr = (
            f"p.{self._quoted(person_enrollment_date_col)}"
            if person_enrollment_date_col else "NULL::timestamp"
        )
        batch_start_expr = (
            f"b.{self._quoted(batch_start_col)}"
            if batch_start_col else "NULL::timestamp"
        )

        batch_join = "LEFT JOIN batch b ON e.batch = b.id" if batch_columns else ""
        country_join_sql = "\n        ".join(dict.fromkeys(country_joins))

        has_date_of_leaving = "date_of_leaving" in person_columns
        reason_col = (
            "reasonofleaving" if "reasonofleaving" in person_columns
            else "reason_of_leaving" if "reason_of_leaving" in person_columns
            else None
        )
        leaving_expr = f"p.{self._quoted('date_of_leaving')}" if has_date_of_leaving else "NULL"
        reason_expr = f"p.{self._quoted(reason_col)}" if reason_col else "NULL"
        batch_name_expr = (
            "NULLIF(TRIM(b.batch::text), '')"
            if batch_columns and "batch" in batch_columns else "NULL"
        )
        enrollment_role_expr = (
            "NULLIF(TRIM(e.role::text), '')"
            if "role" in enrollment_columns else "NULL"
        )
        validation_status_expr = (
            f"NULLIF(TRIM(p.{self._quoted('validationstatus')}::text), '')"
            if "validationstatus" in person_columns else "NULL"
        )
        present_status_expr = (
            f"NULLIF(TRIM(p.{self._quoted('presentstatus')}::text), '')"
            if "presentstatus" in person_columns else "NULL"
        )

        return f"""
        SELECT
            p.id AS person_id,
            TRIM(COALESCE(p.firstname, '') || ' ' || COALESCE(p.lastname, '')) AS student_name,
            NULLIF(TRIM(p.firstname::text), '') AS firstname_raw,
            NULLIF(TRIM(p.lastname::text), '') AS lastname_raw,
            {autographa_expr} AS autographa_id_raw,
            {rollnumber_expr} AS rollnumber_raw,
            {email_expr} AS email_raw,
            {username_expr} AS username_raw,
            {user_login_expr} AS user_login_raw,
            {country_expr} AS country,
            {batch_name_expr} AS batch_name,
            {enrollment_role_expr} AS enrollment_role,
            {validation_status_expr} AS validation_status_raw,
            {present_status_expr} AS present_status_raw,
            {enrollment_date_expr} AS enrollment_record_date,
            {person_enrollment_date_expr} AS person_enrollment_date,
            {batch_start_expr} AS batch_start_date,
            e.id AS enrollment_id,
            {leaving_expr} AS date_of_leaving,
            {reason_expr} AS reason_of_leaving
        FROM enrollment e
        JOIN person p ON e.student = p.id
        {user_join}
        {batch_join}
        {country_join_sql}
        ORDER BY student_name, enrollment_record_date DESC NULLS LAST, batch_start_date DESC NULLS LAST, enrollment_id DESC
        """

    def _summarize_enrollments(self, group: pd.DataFrame) -> Tuple[int, str, str]:
        batches: List[str] = []
        lms_roles: List[str] = []
        for _, row in group.iterrows():
            batch = self._clean_field(row.get("batch_name"), default="")
            if batch and batch not in batches:
                batches.append(batch)
            role = self._clean_field(row.get("enrollment_role"), default="")
            if role and role not in lms_roles:
                lms_roles.append(role)
        batch_text = ", ".join(batches) if batches else "Not specified"
        role_text = ", ".join(lms_roles) if lms_roles else "Not specified"
        return len(group), batch_text, role_text

    def _build_enrollment_details(
        self,
        raw_df: pd.DataFrame,
        person_autographa: Dict[int, str],
    ) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for _, row in raw_df.iterrows():
            person_id = int(row["person_id"])
            rows.append({
                "Autographa id": person_autographa.get(person_id, "Not specified"),
                "Name of student": self._clean_field(row.get("student_name")),
                "Batch": self._clean_field(row.get("batch_name")),
                "LMS role": self._clean_field(row.get("enrollment_role")),
                "Validation Status": self._format_validation_status(row.get("validation_status_raw")),
                "Current Status": self._derive_current_status(
                    row.get("present_status_raw"),
                    row.get("validation_status_raw"),
                    row.get("date_of_leaving"),
                    row.get("reason_of_leaving"),
                ),
                "Country": self._clean_field(row.get("country")),
                "Enrollment record date": (
                    pd.to_datetime(row.get("enrollment_record_date"), errors="coerce").strftime("%Y-%m-%d")
                    if pd.notna(pd.to_datetime(row.get("enrollment_record_date"), errors="coerce"))
                    else "Not recorded"
                ),
                "Enrollment ID": row.get("enrollment_id"),
            })
        details = pd.DataFrame(rows)
        if details.empty:
            return details
        return self.schema_order_columns(
            "enrollment_details",
            details.sort_values(
                ["Name of student", "Batch"],
                ascending=[True, True],
            ).reset_index(drop=True),
        )

    def _get_student_roster(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        person_columns = self._table_columns("person")
        enrollment_columns = self._table_columns("enrollment")

        if not person_columns or not enrollment_columns:
            empty = pd.DataFrame({"Message": ["LMS person/enrollment tables not found"]})
            return empty, empty

        query = self._build_query()
        if not query:
            empty = pd.DataFrame({"Message": ["LMS person/enrollment tables not found"]})
            return empty, empty

        try:
            raw_df = self.schema_query(query, self._lms_roster_tables())
        except Exception as exc:
            return pd.DataFrame({"Error": [str(exc)]}), pd.DataFrame()

        if raw_df.empty:
            empty = pd.DataFrame({"Message": ["No BT Academy students found"]})
            return empty, empty

        self._lms_source_stats = {
            "enrollment_records": len(raw_df),
            "unique_students": int(raw_df["person_id"].nunique()),
        }

        roster, person_autographa = self._build_roster(raw_df)
        roster = self._apply_filters(roster)
        enrollment_details = self._build_enrollment_details(raw_df, person_autographa)
        return roster, enrollment_details

    def _collect_roll_candidates(self, group: pd.DataFrame) -> List[str]:
        candidates: List[str] = []
        for _, row in group.iterrows():
            for column in ("rollnumber_raw", "autographa_id_raw", "username_raw", "user_login_raw"):
                normalized = self._normalize_roll(row.get(column))
                if normalized and normalized not in candidates:
                    candidates.append(normalized)
        return candidates

    def _enrollment_sort_date(self, row: pd.Series) -> pd.Timestamp:
        for column in ("enrollment_record_date", "person_enrollment_date", "batch_start_date"):
            parsed = pd.to_datetime(row.get(column), errors="coerce")
            if pd.notna(parsed):
                return parsed
        return pd.NaT

    def _pick_best_field(self, group: pd.DataFrame, column: str) -> str:
        """Pick the first non-empty value across all enrollment rows for this student."""
        ordered = group.sort_values("sort_date", ascending=False, na_position="last")
        for _, row in ordered.iterrows():
            value = self._clean_field(row.get(column), default="")
            if value:
                return value
        return "Not specified"

    def _build_roster(self, raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[int, str]]:
        rows = []
        person_autographa: Dict[int, str] = {}
        ag_profiles = self._fetch_ag_user_profiles()
        date_columns = [
            "enrollment_record_date",
            "person_enrollment_date",
            "batch_start_date",
        ]
        for column in date_columns:
            raw_df[column] = pd.to_datetime(raw_df[column], errors="coerce")

        for person_id, group in raw_df.groupby("person_id", sort=False):
            group = group.copy()
            group["sort_date"] = group.apply(self._enrollment_sort_date, axis=1)

            first_row = group.iloc[0]
            student_name = self._pick_best_field(group, "student_name")
            firstname = self._pick_best_field(group, "firstname_raw")
            lastname = self._pick_best_field(group, "lastname_raw")
            if firstname == "Not specified":
                firstname = ""
            if lastname == "Not specified":
                lastname = ""

            ag_profile = self._lookup_ag_profile_for_student(
                ag_profiles,
                group,
                student_name,
                firstname,
                lastname,
            )

            autographa_id, id_remark = self._resolve_autographa_id(group, ag_profile)
            person_autographa[int(person_id)] = autographa_id
            country = self._pick_best_field(group, "country")
            language, role, role_remarks = self._summarize_language_roles(ag_profile)
            enrollment_count, batches, lms_roles = self._summarize_enrollments(group)

            enrollment_dates = group["sort_date"].dropna()
            first_enrollment = (
                enrollment_dates.min().strftime("%Y-%m-%d")
                if not enrollment_dates.empty
                else "Not recorded"
            )

            leaving_date = first_row.get("date_of_leaving")
            reason = first_row.get("reason_of_leaving")
            validation_status = self._format_validation_status(
                self._pick_best_field(group, "validation_status_raw")
                if "validation_status_raw" in group.columns
                else first_row.get("validation_status_raw")
            )

            present_raw = (
                self._pick_best_field(group, "present_status_raw")
                if "present_status_raw" in group.columns
                else first_row.get("present_status_raw")
            )

            current_status = self._derive_current_status(
                present_raw,
                first_row.get("validation_status_raw"),
                leaving_date,
                reason,
            )

            rows.append({
                "Autographa id": autographa_id,
                "Name of student": student_name,
                "Country": country,
                "Language": language,
                "Role": role,
                "LMS roles": lms_roles,
                "Enrollments": enrollment_count,
                "Batches": batches,
                "Validation Status": validation_status,
                "Current Status": current_status,
                "Remarks": self._merge_remarks(id_remark, role_remarks),
                "Date of enrolment": first_enrollment,
            })

        roster = pd.DataFrame(rows)
        roster = roster.sort_values(
            ["Current Status", "Name of student"],
            ascending=[True, True],
        )
        return self.schema_order_columns(
            "student_roster",
            roster.reset_index(drop=True),
        ), person_autographa

    def _apply_filters(self, roster: pd.DataFrame) -> pd.DataFrame:
        if roster.empty or "Message" in roster.columns or "Error" in roster.columns:
            return roster

        filtered = roster.copy()
        country = self.filters.get("country")
        role = self.filters.get("role")
        status = self.filters.get("status")

        if country:
            filtered = filtered[filtered["Country"].str.contains(str(country), case=False, na=False)]
        if role:
            filtered = filtered[
                filtered["Role"].str.contains(str(role), case=False, na=False)
                | filtered["LMS roles"].str.contains(str(role), case=False, na=False)
            ]
        if status:
            filtered = filtered[filtered["Current Status"].str.lower() == str(status).strip().lower()]
        validation = self.filters.get("validation_status")
        if validation:
            filtered = filtered[
                filtered["Validation Status"].str.contains(str(validation), case=False, na=False)
            ]

        return filtered.reset_index(drop=True)

    def _get_summary_stats(self, roster: pd.DataFrame) -> pd.DataFrame:
        if roster.empty or "Message" in roster.columns or "Error" in roster.columns:
            return pd.DataFrame({"Metric": ["Students"], "Value": [0]})

        summary = [
            {
                "Metric": "LMS enrollment records (all batch rows)",
                "Value": self._lms_source_stats.get("enrollment_records", len(roster)),
            },
            {
                "Metric": "Unique students (one roster row each)",
                "Value": self._lms_source_stats.get("unique_students", len(roster)),
            },
            {"Metric": "AG Users Indexed", "Value": self._ag_enrichment_stats.get("ag_users_indexed", 0)},
            {"Metric": "Students in roster", "Value": len(roster)},
            {
                "Metric": "Students With Valid Autographa ID (6 digits)",
                "Value": int(
                    roster["Autographa id"].str.match(r"^AG-\d{6}$", na=False).sum()
                ),
            },
            {
                "Metric": "Students Missing Autographa ID",
                "Value": int((roster["Autographa id"] == "Not specified").sum()),
            },
            {
                "Metric": "Students With ID Data Issues (see Remarks)",
                "Value": int(
                    roster["Remarks"].str.contains("Autographa ID", case=False, na=False).sum()
                ),
            },
            {"Metric": "Students Active", "Value": int((roster["Current Status"] == "Active").sum())},
            {"Metric": "Students Inactive", "Value": int((roster["Current Status"] == "Inactive").sum())},
            {"Metric": "Students Pending", "Value": int((roster["Current Status"] == "Pending").sum())},
            {"Metric": "Validation Validated", "Value": int((roster["Validation Status"] == "Validated").sum())},
            {"Metric": "Validation Pending", "Value": int((roster["Validation Status"] == "Pending").sum())},
            {"Metric": "Validation Rejected", "Value": int((roster["Validation Status"] == "Rejected").sum())},
            {"Metric": "Unique Countries", "Value": int(roster["Country"].nunique())},
            {"Metric": "Students With AG Language Assignments", "Value": int((roster["Language"] != "Not specified").sum())},
        ]
        return pd.DataFrame(summary)
