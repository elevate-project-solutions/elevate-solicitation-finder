"""Standarizes results for procurement portal adapters"""

from dataclasses import dataclass, field

@dataclass(frozen=True)
class PortalDocument:
    name: str
    url: str

@dataclass(frozen=True)
class PortalOpportunity:
    reference_number: str
    title: str
    url: str

@dataclass(frozen=True)
class PortalInspection:
    provider: str
    source_url: str
    destination_url: str | None
    access_status: str

    project_url: str | None = None
    project_title: str | None = None
    project_number: str | None = None

    documents: list[PortalDocument] = field(
        default_factory=list
    )

    access_evidence: str | None = None
    error_message: str | None = None

    project_match_method: str | None
    document_status: str = "not_checked"