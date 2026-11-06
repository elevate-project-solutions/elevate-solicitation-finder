from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Solicitation,
    SolicitationDuplicateCandidate,
    SolicitationExternalRef,
    SolicitationSource,
)


@dataclass(frozen=True)
class ImportResult:
    outcome: str
    solicitation_id: int | None

def normalized(value: str | None) -> str:
    return " ".join((value or "").casefold().split())

def find_extract_reference(
    session: Session,
    source_id: int,
    external_id: str | None,
    external_url: str,
) -> SolicitationExternalRef | None:
    by_id = None

    if external_id:
        by_id = session.scalar(
            select(SolicitationExternalRef).where(
                SolicitationExternalRef.source_id == source_id,
                SolicitationExternalRef.external_id == external_id,
            )
        )

    by_url = session.scalar(
        select(SolicitationExternalRef).where(
            SolicitationExternalRef.source_id == source_id,
            SolicitationExternalRef.external_url == external_url,
        )
    )

    if by_id and by_url and by_id.id != by_url.id:
        raise ValueError(
            "Identifier conflict: external ID and URL "
            "belong to different references"
        )

    if by_id and by_id.external_url != external_url:
        raise ValueError(
            "Identifier conflict: known external ID has a "
            "different URL; manual review required"
        )

    if by_url and external_id:
        if by_url.external_id not in (None, external_id):
            raise ValueError(
                "Identifier conflict: URL has a different external ID"
            )

    return by_id or by_url

def add_duplicate_candidate(
        session: Session,
        first_id: int,
        second_id: int,
        reason: str,
) -> None:
    smaller, larger = sorted((first_id, second_id))

    if smaller == larger:
        return

    existing = session.scalar(
        select(SolicitationDuplicateCandidate).where(
            SolicitationDuplicateCandidate.solicitation_id_1 == smaller,
            SolicitationDuplicateCandidate.solicitation_id_2 == larger,
        )
    )

    if existing is None:
        session.add(
            SolicitationDuplicateCandidate(
                solicitation_id_1=smaller,
                solicitation_id_2=larger,
                match_reason=reason,
                confidence_score=Decimal("0.8000"),
                review_status="pending",
            )
        )

def find_exact_reference(
        session: Session,
        source_id: int,
        external_id: str | None,
        external_url: str,
) -> SolicitationExternalRef | None:
    by_id = None

    if external_id:
        by_id = session.scalar(
            select(SolicitationExternalRef).where(
                SolicitationExternalRef.source_id == source_id,
                SolicitationExternalRef.external_id == external_id,
            )
        )

    by_url = session.scalar(
        select(SolicitationExternalRef).where(
            SolicitationExternalRef.source_id == source_id,
            SolicitationExternalRef.external_id == external_url,
        )
    )

    if by_id and by_url and by_id.id != by_url.id:
        raise ValueError(
            "Identifier conflict: external ID and URL "
            "belong to different references"
        )

    if by_id and by_id.external_url != external_url:
        raise ValueError(
            "Identifier conflict: known external ID has a "
            "different URL; manual review required"
        )

    if by_url and external_id:
        if by_url.external_id not in (None, external_id):
            raise ValueError(
                "Identifier conflict: URL has a different external ID"
            )

    return by_id or by_url

def import_solicitation(
        session: Session,
        *,
        source_key: str,
        agency: str,
        title: str,
        source_url: str,
        external_url: str,
        solicitation_number: str | None = None,
        external_id: str | None = None,
) -> ImportResult:
    """
    Import one solicitation without committing the transaction.
    
    The caller owns commit/rollback.
    """
    if not all(
        value and value.strip()
        for value in (
            source_key, agency, title, source_url, external_url
        )
    ):
        raise ValueError("Required import fields cannot be blank")

    external_id = (external_id or "").strip() or None
    external_url = external_url.strip()
    source_url = source_url.strip()
    solicitation_number = (
        (solicitation_number or "").strip() or None
    )

    source = session.scalar(
        select(SolicitationSource).where(
            SolicitationSource.source_key == source_key
        )
    )

    if source is None:
        raise ValueError(f"Unknown source: {source_key}")

    reference = find_exact_reference(
        session, source.id, external_id, external_url
    )

    if reference is not None:
        if reference.external_id is None and external_id:
            reference.external_id = external_id

        reference.last_seen_at = func.now()

        solicitation = session.get(
            Solicitation, reference.solicitation_id
        )
        solicitation.last_seen_at = func.now()

        session.flush()

        return ImportResult(
            "existing", reference.solicitation_id
        )

    #Canonical URL already exists in database
    #Reuses solicitation instead of violating global source_url uniqueness contraint.
    solicitation = session.scalar(
        select(Solicitation).where(
            Solicitation.source_url == source_url
        )
    )

    if solicitation is not None:
        session.add(
            SolicitationExternalRef(
                solicitation_id=solicitation.id,
                source_id=source.id,
                external_id=external_id,
                external_url=external_url,
            )
        )
        solicitation.last_seen_at = func.now()
        session.flush()

        return ImportResult(
            "existing_url", solicitation.id
        )

    #Compares agency and solicitation numbers
    #Just a candidate signal, not necessarily proof of duplication
    possible_matches = []

    if solicitation_number:
        possible_matches = list(
            session.scalars(
                select(Solicitation).where(
                    func.lower(func.trim(Solicitation.agency))
                    == agency.strip().lower(),
                    func.lower(
                        func.trim(Solicitation.solicitation_number)
                    )
                    == solicitation_number.lower(),
                )
            )
        )

    solicitation = Solicitation(
        source=source_key,
        agency=agency.strip(),
        title=title.strip(),
        solicitation_number=solicitation_number,
        source_url=source_url,
        status="unknown",
    )

    session.add(solicitation)
    session.flush()

    session.add(
        SolicitationExternalRef(
            solicitation_id=solicitation.id,
            source_id=source.id,
            external_id=external_id,
            external_url=external_url,
        )
    )

    for match in possible_matches:
        add_duplicate_candidate(
            session,
            match.id,
            solicitation.id,
            "Same agency and solicitation number",
        )

    session.flush()

    return ImportResult(
        "review_required" if possible_matches else "created",
        solicitation.id,
    )