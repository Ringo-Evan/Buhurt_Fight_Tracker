"""
SQLAlchemy ORM model for Fight entity.

Implements soft delete pattern with is_deleted flag.
Uses UUID primary keys and one-to-many relationship to FightParticipation.
Eager loads participations to prevent N+1 queries.
"""

from datetime import datetime, date, UTC
from uuid import uuid4, UUID
from sqlalchemy import String, Date, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight_participation import FightParticipation
    from app.models.tag import Tag


class Fight(Base):
    """
    Fight entity with soft delete support and participation relationships.

    Attributes:
        id: UUID primary key (auto-generated)
        date: Date the fight occurred (cannot be in future)
        location: Location where fight took place (max 200 characters)
        video_url: Optional URL to fight video recording
        winner_side: Optional side that won (1 or 2, null for draw/undecided)
        notes: Optional notes about the fight
        is_deleted: Deactivated flag (defaults to False)
        created_at: Timestamp of creation (auto-generated, UTC)

        participations: Relationship to FightParticipation entities (eager loaded)
    """

    __tablename__ = "fights"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        index=True  # For date range queries
    )

    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    video_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    winner_side: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True  # None = draw or unknown
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    is_deactivated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True  # For filtering deactivated fights
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    participations: Mapped[list["FightParticipation"]] = relationship(
        "FightParticipation",
        back_populates="fight",
        lazy="joined",  # Eager load participations to prevent N+1 queries
        cascade="all, delete-orphan"  # Delete participations when fight deleted
    )

    # Phase 3: Tag system relationship (not yet implemented in Phase 2)
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="fight",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize Fight with Python-level defaults.

        Ensures defaults are applied when creating instances programmatically.
        """
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self.id = uuid4()
        if 'is_deactivated' not in kwargs:
            self.is_deactivated = False
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<Fight(id={self.id}, date={self.date}, location='{self.location}', is_deactivated={self.is_deactivated})>"
