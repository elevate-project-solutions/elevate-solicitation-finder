from typing import Annotated

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

@router.get(
    "",
    response_model=SolicitationListResponse,
)
def list_solicitations(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
):
    total = db.scalar(
        select(func.count()).select_from(Solicitation)
    ) or 0

    offset = (page - 1) * page_size

    records = db.scalars(
        select(Solicitation)
        .order_by(
            Solicitation.due_at.asc().nulls_last(),
            Solicitation.id.desc(),
        )
        .offset(offset)
        .limit(page_size)
    ).all()

    # Have not yet established verified document
    # retrieval or package completeness.
    # Please do not infer availability from a stored URL

    items = [
        SoliciationDashboardItem(
            id=item.id,
            solicitation_number=item.solicitation_number,
            title=item.title,
            agency=item.agency,
            status=item.status,
            due_date=item.due_at,
            source=item.source,
            document_status="not_verified",
        )
        for item in records
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