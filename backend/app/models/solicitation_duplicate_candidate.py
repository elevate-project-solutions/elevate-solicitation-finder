from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SolicitationDuplicateCandidate(Base):
    __tablename__ = "solicitation_duplicate_candidates"

    __table_args__ = (
        UniqueConstraint(
            "solicitation_id_1",
            "solicitation_id_2",
            name="duplicate_candidates_unique_pair",
        ),
        CheckConstraint(
            "solicitation_id_1 < solicitation_id_2",
            name="duplicate_candidates_different_records",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR "
            "confidence_score BETWEEN 0 AND 1",
            name="duplicate_candidates_status_check",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    solicitation_id_1: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solicitations.id", ondelete="CASCADE"),
        nullable=False,
    )

    solicitation_id_2: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solicitations.id", ondelete="CASCADE"),
        nullable=False,
    )

    match_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 4)
    )

    review_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="pending"
    )

    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("app_users.id", ondelete="SET NULL"),
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    review_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )