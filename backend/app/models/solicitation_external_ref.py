from datetime import datetime

from sqlalchemy import (
    BigInteger, DateTime, ForeignKey, Identity,
    Index, Text, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class SolicitationExternalRef(Base):
    __tablename__ = "solicitation_external_refs"

    __table_args__ = (
        UniqueConstraint(
            "source_id", "external_url",
            name="external_refs_source_url_unique",
        ),
        Index(
            "idx_external_refs_source_external_id",
            "source_id", "external_id",
            unique=True,
            postgresql_where=text("external_id IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), primary_key=True
    )

    solicitation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solicitations.id", ondelete="CASCADE"),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(Text)
    external_url: Mapped[str] = mapped_column(Text, nullable=False)

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    source_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("solicitation_sources.id"),
        nullable=False,
    )