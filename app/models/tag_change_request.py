"""
SQLAlchemy model for TagChangeRequest entity.

Represents a request to change a tag with voting workflow.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from enum import Enum
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight import Fight
    from app.models.tag_type import TagType
    from app.models.vote import Vote


class RequestStatus(str, Enum):
    """Status of a tag change request."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TagChangeRequest(Base):
    """
    TagChangeRequest entity for voting on tag changes.

    Attributes:
        id: UUID primary key
        fight_id: FK to fights table
        tag_type_id: FK to tag_types table
        proposed_value: The new value being proposed
        current_value: The current tag value (if any)
        status: pending, accepted, or rejected
        threshold: Number of votes needed to resolve
        votes_for: Count of upvotes
        votes_against: Count of downvotes
        created_at: Timestamp of request creation
        resolved_at: Timestamp when resolved (if resolved)
    """

    __tablename__ = "tag_change_requests"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    fight_id: Mapped[UUID] = mapped_column(
        ForeignKey("fights.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    tag_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("tag_types.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    proposed_value: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    current_value: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default=RequestStatus.PENDING.value,
        nullable=False
    )
    threshold: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False
    )
    votes_for: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    votes_against: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    is_deactivated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    # Relationships
    fight: Mapped["Fight"] = relationship("Fight", lazy="joined")
    tag_type: Mapped["TagType"] = relationship("TagType", lazy="joined")
    votes: Mapped[list["Vote"]] = relationship(
        "Vote",
        back_populates="tag_change_request"
    )

    def __repr__(self) -> str:
        return f"<TagChangeRequest(id={self.id}, status={self.status}, votes={self.votes_for}/{self.votes_against})>"
