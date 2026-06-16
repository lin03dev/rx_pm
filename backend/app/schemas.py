"""API request/response schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    report_id: str = Field(..., min_length=1)
    database: Optional[str] = None
    databases: Optional[List[str]] = None
    output_format: str = Field(default="excel", pattern="^(excel|csv|json)$")
    filters: Optional[Dict[str, str]] = None


class GenerateReportOutput(BaseModel):
    report_id: str
    database: str
    output_format: str
    output_file: str


class GenerateReportResponse(BaseModel):
    report_id: str
    output_format: str
    outputs: List[GenerateReportOutput]
    output_file: Optional[str] = None
    database: Optional[str] = None


class PreviewReportRequest(BaseModel):
    report_id: str = Field(..., min_length=1)
    database: Optional[str] = None
    databases: Optional[List[str]] = None
    filters: Optional[Dict[str, str]] = None
    limit: int = Field(default=500, ge=1, le=5000)


class PreviewSheetData(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
    truncated: bool


class PreviewReportResponse(BaseModel):
    report_id: str
    database: Optional[str] = None
    databases: List[str] = Field(default_factory=list)
    sheets: Dict[str, PreviewSheetData] = Field(default_factory=dict)
    results: Dict[str, Dict[str, PreviewSheetData]] = Field(default_factory=dict)


class DatabaseConnectionRequest(BaseModel):
    name: str = Field(..., min_length=1)
    host: str = Field(..., min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    password: str = Field(default="")
    ssl_mode: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = "production"
    project: Optional[str] = None
    category: Optional[str] = None
    active: bool = True


class DatabaseConnectionUpdateRequest(BaseModel):
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: Optional[str] = None
    description: Optional[str] = None
    environment: Optional[str] = None
    project: Optional[str] = None
    category: Optional[str] = None


class DatabaseTestRequest(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(default=5432, ge=1, le=65535)
    database: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    password: str = Field(default="")
    ssl_mode: Optional[str] = None


class ActiveDatabasesRequest(BaseModel):
    active: List[str] = Field(..., min_length=1)
    primary: Optional[str] = None


class DatabaseSelectionRequest(BaseModel):
    project: str = Field(..., min_length=1)
    database: str = Field(..., min_length=1)


class DatabaseConnectionsResponse(BaseModel):
    databases: List[Dict[str, Any]]
    active: List[str]
    primary: Optional[str] = None
    selected_by_project: Dict[str, str] = Field(default_factory=dict)


class DashboardInsightMetric(BaseModel):
    id: str
    label: str
    description: str = ""
    format: str = "text"
    value: Optional[Any] = None
    display_value: str = "—"
    status: str = "ok"
    error: Optional[str] = None
    source_report_id: Optional[str] = None
    navigate: Dict[str, Any] = Field(default_factory=dict)


class DashboardInsightsResponse(BaseModel):
    project: str
    database: str
    metrics: List[DashboardInsightMetric]
    updated_at: str
    cached: bool = False
