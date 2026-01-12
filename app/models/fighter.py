"""
SQLAlchemy ORM model for Fighter entity.

Implements soft delete pattern with is_deleted flag.
Uses UUID primary keys and foreign key relationship to Team.
Eager loads team → country for 3-level hierarchy without N+1 queries.
"""

from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Import Base from country module to ensure single metadata instance
from app.models.country import Base

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.fight_participation import FightParticipation


class Fighter(Base):
    """
    Fighter entity with soft delete support and team relationship.

    Attributes:
        id: UUID primary key (auto-generated)
        name: Fighter name (max 100 characters)
        team_id: Foreign key to teams table (UUID)
        is_deleted: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated, UTC)

        team: Relationship to Team entity (eager loaded with country)
    """

    __tablename__ = "fighters"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id"),
        nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    team: Mapped["Team"] = relationship(
        "Team",
        lazy="joined",  # Eager load team (which eager loads country) to prevent N+1 queries
        foreign_keys=[team_id],
        back_populates="fighters"
    )
    participations: Mapped[list["FightParticipation"]] = relationship(
        "FightParticipation",
        back_populates="fighter"
    )

    def __init__(self, **kwargs):
        """
        Initialize Fighter with Python-level defaults.

        Ensures defaults are applied when creating instances programmatically.
        """
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self.id = uuid4()
        if 'is_deleted' not in kwargs:
            self.is_deleted = False
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<Fighter(id={self.id}, name='{self.name}', team_id={self.team_id}, is_deleted={self.is_deleted})>"
