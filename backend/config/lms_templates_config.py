"""
LMS Templates Configuration - Dynamic template definitions for LMS data
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum


class LMSTemplateType(Enum):
    """LMS template types"""
    BATCH_IMPORT = "batch_import"
    ENROLLMENT_IMPORT = "enrollment_import"
    MODULE_IMPORT = "module_import"
    SESSION_IMPORT = "session_import"
    ATTENDANCE_IMPORT = "attendance_import"
    ASSIGNMENT_IMPORT = "assignment_import"
    SUBMISSION_IMPORT = "submission_import"
    SURVEY_IMPORT = "survey_import"
    TRAINER_IMPORT = "trainer_import"


@dataclass
class TemplateColumn:
    """Template column definition"""
    name: str
    display_name: str
    field_type: str  # text, integer, date, boolean, email, json
    required: bool = False
    validation: Dict = field(default_factory=dict)
    example: str = ""
    help_text: str = ""


@dataclass
class LMSTemplate:
    """LMS template definition"""
    template_type: LMSTemplateType
    name: str
    display_name: str
    description: str
    sheets: List[Dict[str, Any]]
    version: str = "1.0"


# ============================================================
# Template Definitions
# ============================================================

def get_batch_import_template() -> LMSTemplate:
    """Template for importing/updating batches"""
    return LMSTemplate(
        template_type=LMSTemplateType.BATCH_IMPORT,
        name="batch_import",
        display_name="Batch Import Template",
        description="Import or update batch information",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Batches",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True, 
                     "help": "Unique batch identifier", "example": "BATCH_2024_001"},
                    {"name": "course_name", "display": "Course Name", "type": "text", "required": False,
                     "help": "Course title", "example": "Bible Translation Principles"},
                    {"name": "location", "display": "Location", "type": "text", "required": False,
                     "help": "Training location", "example": "Bangalore, India"},
                    {"name": "country", "display": "Country", "type": "text", "required": False,
                     "help": "Country name", "example": "India"},
                    {"name": "start_date", "display": "Start Date (YYYY-MM-DD)", "type": "date", "required": False,
                     "help": "Batch start date", "example": "2024-01-15"},
                    {"name": "end_date", "display": "End Date (YYYY-MM-DD)", "type": "date", "required": False,
                     "help": "Batch end date", "example": "2024-03-15"},
                    {"name": "status", "display": "Status", "type": "text", "required": False,
                     "help": "Planning, Active, Completed, Cancelled", "example": "Active"},
                ],
                "description": "Import batch information"
            }
        ]
    )


def get_enrollment_import_template() -> LMSTemplate:
    """Template for enrolling participants into batches"""
    return LMSTemplate(
        template_type=LMSTemplateType.ENROLLMENT_IMPORT,
        name="enrollment_import",
        display_name="Enrollment Import Template",
        description="Enroll participants into batches",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Enrollments",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "participant_email", "display": "Participant Email *", "type": "email", "required": True,
                     "help": "Email address of participant", "example": "john@example.com"},
                    {"name": "participant_name", "display": "Participant Name", "type": "text", "required": False,
                     "help": "Full name", "example": "John Doe"},
                    {"name": "role", "display": "Role", "type": "text", "required": False,
                     "help": "MTT, QC, ICT, Trainer, Admin", "example": "MTT"},
                    {"name": "enrollment_date", "display": "Enrollment Date", "type": "date", "required": False,
                     "help": "Date of enrollment", "example": "2024-01-10"},
                ],
                "description": "Enroll participants in batches"
            },
            {
                "sheet_name": "New_Participants",
                "columns": [
                    {"name": "email", "display": "Email *", "type": "email", "required": True,
                     "help": "Unique email address", "example": "newuser@example.com"},
                    {"name": "first_name", "display": "First Name *", "type": "text", "required": True,
                     "help": "First name", "example": "John"},
                    {"name": "last_name", "display": "Last Name", "type": "text", "required": False,
                     "help": "Last name", "example": "Doe"},
                    {"name": "phone", "display": "Phone Number", "type": "text", "required": False,
                     "help": "Contact number", "example": "+1234567890"},
                    {"name": "gender", "display": "Gender", "type": "text", "required": False,
                     "help": "Male, Female, Other", "example": "Male"},
                    {"name": "country", "display": "Country", "type": "text", "required": False,
                     "help": "Country name", "example": "India"},
                ],
                "description": "Add new participants (will be created automatically)"
            }
        ]
    )


def get_attendance_import_template() -> LMSTemplate:
    """Template for recording attendance"""
    return LMSTemplate(
        template_type=LMSTemplateType.ATTENDANCE_IMPORT,
        name="attendance_import",
        display_name="Attendance Import Template",
        description="Record participant attendance for sessions",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Attendance",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "participant_email", "display": "Participant Email *", "type": "email", "required": True,
                     "help": "Email of participant", "example": "john@example.com"},
                    {"name": "session_name", "display": "Session/Module Name *", "type": "text", "required": True,
                     "help": "Session or module name", "example": "Introduction to Translation"},
                    {"name": "session_date", "display": "Session Date", "type": "date", "required": False,
                     "help": "Date of session", "example": "2024-01-15"},
                    {"name": "attendance_status", "display": "Attendance Status *", "type": "text", "required": True,
                     "help": "Present, Absent, Late, Excused", "example": "Present"},
                ],
                "description": "Record attendance for each participant per session"
            }
        ]
    )


def get_module_session_import_template() -> LMSTemplate:
    """Template for importing modules/sessions for a batch"""
    return LMSTemplate(
        template_type=LMSTemplateType.SESSION_IMPORT,
        name="session_import",
        display_name="Session/Module Import Template",
        description="Assign modules/sessions to batches",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Sessions",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "session_name", "display": "Session/Module Name *", "type": "text", "required": True,
                     "help": "Name of session/module", "example": "Introduction to Translation"},
                    {"name": "module_description", "display": "Description", "type": "text", "required": False,
                     "help": "Session description", "example": "Basic translation concepts"},
                    {"name": "session_date", "display": "Session Date", "type": "date", "required": False,
                     "help": "Date of session", "example": "2024-01-15"},
                    {"name": "order", "display": "Order", "type": "integer", "required": False,
                     "help": "Display order", "example": "1"},
                ],
                "description": "Assign modules/sessions to batches"
            }
        ]
    )


def get_assignment_import_template() -> LMSTemplate:
    """Template for creating assignments"""
    return LMSTemplate(
        template_type=LMSTemplateType.ASSIGNMENT_IMPORT,
        name="assignment_import",
        display_name="Assignment Import Template",
        description="Create assignments for modules",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Assignments",
                "columns": [
                    {"name": "module_name", "display": "Module Name *", "type": "text", "required": True,
                     "help": "Module to which assignment belongs", "example": "Introduction to Translation"},
                    {"name": "assignment_name", "display": "Assignment Name *", "type": "text", "required": True,
                     "help": "Assignment title", "example": "Week 1 Quiz"},
                    {"name": "description", "display": "Description", "type": "text", "required": False,
                     "help": "Assignment details", "example": "Answer 10 questions"},
                    {"name": "due_date", "display": "Due Date", "type": "date", "required": False,
                     "help": "Submission deadline", "example": "2024-01-20"},
                    {"name": "max_score", "display": "Max Score", "type": "integer", "required": False,
                     "help": "Maximum possible score", "example": "100"},
                ],
                "description": "Create assignments for modules"
            }
        ]
    )


def get_submission_import_template() -> LMSTemplate:
    """Template for recording assignment submissions"""
    return LMSTemplate(
        template_type=LMSTemplateType.SUBMISSION_IMPORT,
        name="submission_import",
        display_name="Submission Import Template",
        description="Record assignment submissions and grades",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Submissions",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "participant_email", "display": "Participant Email *", "type": "email", "required": True,
                     "help": "Email of participant", "example": "john@example.com"},
                    {"name": "assignment_name", "display": "Assignment Name *", "type": "text", "required": True,
                     "help": "Assignment identifier", "example": "Week 1 Quiz"},
                    {"name": "submission_status", "display": "Status *", "type": "text", "required": True,
                     "help": "Submitted, Approved, Redo Required, Rejected", "example": "Submitted"},
                    {"name": "score", "display": "Score", "type": "integer", "required": False,
                     "help": "Score obtained", "example": "85"},
                    {"name": "feedback", "display": "Feedback", "type": "text", "required": False,
                     "help": "Instructor feedback", "example": "Good work"},
                    {"name": "submission_date", "display": "Submission Date", "type": "date", "required": False,
                     "help": "Date submitted", "example": "2024-01-19"},
                ],
                "description": "Record assignment submissions and grades"
            }
        ]
    )


def get_survey_import_template() -> LMSTemplate:
    """Template for importing survey responses"""
    return LMSTemplate(
        template_type=LMSTemplateType.SURVEY_IMPORT,
        name="survey_import",
        display_name="Survey Response Import Template",
        description="Import survey responses from participants",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Survey_Responses",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "participant_email", "display": "Participant Email *", "type": "email", "required": True,
                     "help": "Email of participant", "example": "john@example.com"},
                    {"name": "participant_role", "display": "Role", "type": "text", "required": False,
                     "help": "MTT, QC, ICT", "example": "MTT"},
                    {"name": "survey_name", "display": "Survey Name *", "type": "text", "required": True,
                     "help": "Name of the survey", "example": "Course Feedback"},
                    {"name": "question", "display": "Question Text", "type": "text", "required": False,
                     "help": "The survey question", "example": "How would you rate the course?"},
                    {"name": "answer", "display": "Answer", "type": "text", "required": False,
                     "help": "Participant's answer", "example": "Excellent"},
                ],
                "description": "Import survey responses"
            }
        ]
    )


def get_trainer_import_template() -> LMSTemplate:
    """Template for assigning trainers to batches"""
    return LMSTemplate(
        template_type=LMSTemplateType.TRAINER_IMPORT,
        name="trainer_import",
        display_name="Trainer Assignment Template",
        description="Assign trainers to batches",
        version="1.0",
        sheets=[
            {
                "sheet_name": "Trainers",
                "columns": [
                    {"name": "batch_name", "display": "Batch Name *", "type": "text", "required": True,
                     "help": "Batch identifier", "example": "BATCH_2024_001"},
                    {"name": "trainer_email", "display": "Trainer Email *", "type": "email", "required": True,
                     "help": "Email of trainer", "example": "trainer@example.com"},
                    {"name": "trainer_name", "display": "Trainer Name", "type": "text", "required": False,
                     "help": "Full name", "example": "Dr. Smith"},
                    {"name": "trainer_role", "display": "Role", "type": "text", "required": False,
                     "help": "Lead Trainer, Assistant Trainer", "example": "Lead Trainer"},
                ],
                "description": "Assign trainers to batches"
            }
        ]
    )


# Template registry
LMS_TEMPLATES = {
    LMSTemplateType.BATCH_IMPORT: get_batch_import_template,
    LMSTemplateType.ENROLLMENT_IMPORT: get_enrollment_import_template,
    LMSTemplateType.ATTENDANCE_IMPORT: get_attendance_import_template,
    LMSTemplateType.SESSION_IMPORT: get_module_session_import_template,
    LMSTemplateType.ASSIGNMENT_IMPORT: get_assignment_import_template,
    LMSTemplateType.SUBMISSION_IMPORT: get_submission_import_template,
    LMSTemplateType.SURVEY_IMPORT: get_survey_import_template,
    LMSTemplateType.TRAINER_IMPORT: get_trainer_import_template,
}


def get_lms_template(template_type: LMSTemplateType) -> LMSTemplate:
    """Get a specific LMS template"""
    if template_type in LMS_TEMPLATES:
        return LMS_TEMPLATES[template_type]()
    return None


def get_all_lms_templates() -> List[LMSTemplate]:
    """Get all LMS templates"""
    return [get_lms_template(t) for t in LMSTemplateType]
