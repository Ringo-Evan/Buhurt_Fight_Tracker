"""
SQLAlchemy model for Fight entity.

Represents a recorded fight/match between fighters or teams.
"""

from datetime import datetime, date, UTC
from uuid import uuid4, UUID
from sqlalchemy import String, Date, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight_participation import FightParticipation
    from app.models.tag import Tag


class Fight(Base):
    """
    Fight entity representing a recorded match.

    Attributes:
        id: UUID primary key
        date: Date of the fight
        location: Location/event name (e.g., "IMCF Worlds 2024, Warsaw")
        video_url: URL to fight video
        winner_side: Which side won (1, 2, or None for draw/unknown)
        is_deleted: Soft delete flag
        created_at: Timestamp of record creation
    """

    __tablename__ = "fights"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    video_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )
    winner_side: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True  # None = draw or unknown
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    participations: Mapped[list["FightParticipation"]] = relationship(
        "FightParticipation",
        back_populates="fight",
        lazy="selectin"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="fight",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Fight(id={self.id}, date={self.date}, location={self.location})>"
