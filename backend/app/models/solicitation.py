from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Solicitation(Base):
    __tablename__ = "solicitations"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "source_record_id",
            name="uq_solicitations_source_record_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_record_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    agency: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)

    solicitation_number: Mapped[str | None] = mapped_column(Text)

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="unknown"
    )

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
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )