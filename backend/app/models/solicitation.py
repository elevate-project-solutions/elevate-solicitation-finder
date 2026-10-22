from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class Solicitation(Base):
    __tablename__ = "solicitations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(always=True),
        primary_key=True,
    )

    source: Mapped[str] = mapped_column(Text, nullable=False)
    agency: Mapped[str] = mapped_column(Text, nullable=False)
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