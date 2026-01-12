"""
SQLAlchemy model for Vote entity.

Represents an anonymous vote on a tag change request.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.tag_change_request import TagChangeRequest


class Vote(Base):
    """
    Vote entity for anonymous voting on tag changes.

    Uses session_id instead of user_id for anonymous voting.
    One vote per session per request enforced by unique constraint.

    Attributes:
        id: UUID primary key
        tag_change_request_id: FK to tag_change_requests table
        session_id: UUID identifying the voting session
        is_upvote: True for upvote, False for downvote
        created_at: Timestamp of vote
    """

    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("tag_change_request_id", "session_id", name="uq_request_session"),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    tag_change_request_id: Mapped[UUID] = mapped_column(
        ForeignKey("tag_change_requests.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )
    session_id: Mapped[UUID] = mapped_column(
        nullable=False
    )
    is_upvote: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    tag_change_request: Mapped["TagChangeRequest"] = relationship(
        "TagChangeRequest",
        back_populates="votes"
    )

    def __repr__(self) -> str:
        vote_type = "upvote" if self.is_upvote else "downvote"
        return f"<Vote(id={self.id}, {vote_type}, session={self.session_id})>"
