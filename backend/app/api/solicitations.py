from typing import Annotated
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.db.dependencies import get_db
from app.models.solicitation import Solicitation
from app.schemas.dashboard import (
    SolicitationDashboardItem,
    SolicitationListResponse,
    SolicitationDocumentItem,
    SolicitationDocumentResponse,
)

router = APIRouter(
    prefix="/api/solicitations",
    tags=["solicitations"],
)

DbSession = Annotated[Session, Depends(get_db)]

@router.get(
    "",
    response_model=SolicitationListResponse,
)
def list_solicitations(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    now = datetime.now(timezone.utc)

    # Shows solicitations whose deadlines have not passed
    active_filter = Solicitation.due_at > now

    # Counts only future dated opportunities
    total = db.scalar(
        select(func.count(Solicitation.id))
        .where(active_filter)
    ) or 0

    # Retrieves future dated opportunities, earliest deadline first.
    query = (
        select(Solicitation)
        .where(active_filter)
        .order_by(
            Solicitation.due_at.asc(),
            Solicitation.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    solicitations = db.scalars(query).all()

    items = [
        SolicitationDashboardItem(
            id=item.id,
            solicitation_number=item.solicitation_number,
            title=item.title,
            agency=item.agency,
            status=item.status,
            due_date=item.due_at,
            source=item.source,
            document_status="not_verified",
        )
        for item in solicitations
    ]

    return SolicitationListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )

@router.get(
    "/{solicitation_id}/documents",
    response_model=SolicitationDocumentResponse,
)
def list_solicitation_documents(
    solicitation_id: int,
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    solicitation = db.get(Solicitation, solicitation_id)

    if solicitation is None:
        raise HTTPException(
            status_code=404,
            detail="Solicitation not found",
        )

    total = db.execute(
        text("""
            SELECT COUNT (*)
            FROM document_versions dv
            JOIN solicitation_documents sd
                ON sd.id = dv.document_id
            WHERE sd.solicitation_id = :solicitation_id
        """),
        {"solicitation_id": solicitation_id},
    ).scalar_one()

    offset = (page - 1) * page_size

    rows = db.execute(
        text("""
            SELECT
                dv.id,
                sd.solicitation_id,
                sd.title,
                sd.document_type,
                dv.file_name AS filename,
                dv.source_url
            FROM solicitation_documents sd
            JOIN document_versions dv
                ON dv.document_id = sd.id
            WHERE sd.solicitation_id = :solicitation_id
            ORDER BY
                sd.id,
                dv.version_number DESC
            LIMIT :page_size
            OFFSET :offset
        """),
        {
            "solicitation_id": solicitation_id,
            "page_size": page_size,
            "offset": offset,
        },
    ).mappings().all()

    items = [
        SolicitationDocumentItem(
            id=row["id"],
            solicitation_id=row["solicitation_id"],
            title=row["title"],
            document_type=row["document_type"],
            filename=row["filename"],
            source_url=row["source_url"],
            retrieval_status="not_verified",
        )
        for row in rows
    ]

    return SolicitationDocumentResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )