"""
SQLAlchemy model for FightParticipation entity.

Junction table linking Fighters to Fights with side and role information.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from enum import Enum
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight import Fight
    from app.models.fighter import Fighter


class ParticipationRole(str, Enum):
    """Enum for fighter roles in a fight."""
    FIGHTER = "fighter"
    CAPTAIN = "captain"
    ALTERNATE = "alternate"
    COACH = "coach"


class FightParticipation(Base):
    """
    Junction table for Fight-Fighter many-to-many relationship.

    Tracks which fighters participated in which fights, on which side,
    and in what role.

    Attributes:
        id: UUID primary key
        fight_id: FK to fights table
        fighter_id: FK to fighters table
        side: Which side the fighter was on (1 or 2)
        role: The fighter's role (fighter, captain, alternate, coach)
        is_deleted: Soft delete flag
        created_at: Timestamp of record creation
    """

    __tablename__ = "fight_participations"
    __table_args__ = (
        UniqueConstraint("fight_id", "fighter_id", name="uq_fight_fighter"),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    fight_id: Mapped[UUID] = mapped_column(
        ForeignKey("fights.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    fighter_id: Mapped[UUID] = mapped_column(
        ForeignKey("fighters.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    side: Mapped[int] = mapped_column(
        Integer,
        nullable=False  # 1 or 2
    )
    role: Mapped[str] = mapped_column(
        String(20),
        default=ParticipationRole.FIGHTER.value,
        nullable=False
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
    fight: Mapped["Fight"] = relationship(
        "Fight",
        back_populates="participations"
    )
    fighter: Mapped["Fighter"] = relationship(
        "Fighter",
        back_populates="participations",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<FightParticipation(fight_id={self.fight_id}, fighter_id={self.fighter_id}, side={self.side})>"
