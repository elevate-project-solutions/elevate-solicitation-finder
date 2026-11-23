from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DocumentStatus = Literal[
    "available",
    "incomplete",
    "access_required",
    "not_verified",
]

class SolicitationDashboardItem(BaseModel):
    id: int
    solicitation_number: str | None = None
    title: str
    agency: str | None = None
    status: str
    due_date: datetime | None = None
    source: str
    document_status: DocumentStatus = "not_verified"

class SolicitationListResponse(BaseModel):
    items: list[SolicitationDashboardItem]
    total: int
    page: int
    page_size: int

class SolicitationDocumentItem(BaseModel):
    id: int
    solicitation_id: int
    filename: str | None = None
    title: str | None = None
    document_type: str | None = None
    source_url: str | None = None
    retrieval_status: str = "not_verified"

class SolicitationDocumentResponse(BaseModel):
    items: list[SolicitationDashboardItem]
    total: int
    page: int
    page_size: int