"""API request/response schemas."""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class GenerateReportRequest(BaseModel):
    report_id: str = Field(..., min_length=1)
    database: str = Field(..., min_length=1)
    output_format: str = Field(default="excel", pattern="^(excel|csv|json)$")
    filters: Optional[Dict[str, str]] = None


class GenerateReportResponse(BaseModel):
    report_id: str
    database: str
    output_format: str
    output_file: str
