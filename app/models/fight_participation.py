"""
SQLAlchemy ORM model for FightParticipation entity (junction table).

Links fighters to fights with side assignment and role.
Enforces unique constraint: one fighter can only participate once per fight.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from enum import Enum as PyEnum
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight import Fight
    from app.models.fighter import Fighter


class ParticipationRole(PyEnum):
    """
    Enumeration of possible participation roles in a fight.

    - fighter: Standard participant
    - captain: Team captain/leader
    - alternate: Reserve/substitute fighter
    - coach: Coach/instructor (non-fighting)
    """
    FIGHTER = "fighter"
    CAPTAIN = "captain"
    ALTERNATE = "alternate"
    COACH = "coach"


class FightParticipation(Base):
    """
    Junction table linking fighters to fights with side and role.

    Attributes:
        id: UUID primary key (auto-generated)
        fight_id: Foreign key to fights table (UUID)
        fighter_id: Foreign key to fighters table (UUID)
        side: Side assignment (1 or 2)
        role: Participation role (fighter, captain, alternate, coach)
        created_at: Timestamp of creation (auto-generated, UTC)

        fight: Relationship to Fight entity
        fighter: Relationship to Fighter entity (eager loaded)

    Constraints:
        - Unique (fight_id, fighter_id): One fighter can only participate once per fight
        - Check side IN (1, 2): Side must be 1 or 2
    """

    __tablename__ = "fight_participations"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    fight_id: Mapped[UUID] = mapped_column(
        ForeignKey("fights.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # For queries by fight
    )

    fighter_id: Mapped[UUID] = mapped_column(
        ForeignKey("fighters.id", ondelete="RESTRICT"),
        nullable=False,
        index=True  # For queries by fighter
    )

    side: Mapped[int] = mapped_column(
        Integer,
        nullable=False  # 1 or 2
        # Check constraint added in migration: side IN (1, 2)
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ParticipationRole.FIGHTER.value
        # Check constraint added in migration: role IN ('fighter', 'captain', 'alternate', 'coach')
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    fight: Mapped["Fight"] = relationship(
        "Fight",
        back_populates="participations"
    )

    fighter: Mapped["Fighter"] = relationship(
        "Fighter",
        back_populates="participations",
        lazy="joined"  # Eager load fighter (which eager loads team → country)
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint('fight_id', 'fighter_id', name='uq_fight_fighter'),
    )

    def __init__(self, **kwargs):
        """
        Initialize FightParticipation with Python-level defaults.

        Ensures defaults are applied when creating instances programmatically.
        """
        super().__init__(**kwargs)

        if 'id' not in kwargs:
            self.id = uuid4()
        if 'role' not in kwargs:
            self.role = ParticipationRole.FIGHTER.value
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"<FightParticipation(id={self.id}, fight_id={self.fight_id}, fighter_id={self.fighter_id}, side={self.side}, role='{self.role}')>"
