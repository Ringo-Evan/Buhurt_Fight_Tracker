"""
SQLAlchemy model for TagType entity.

Reference data for tag categories.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from sqlalchemy import String, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.tag import Tag


class TagType(Base):
    """
    TagType entity representing categories of tags.

    Examples: category, subcategory, weapon, gender, rule_set, league, custom

    Attributes:
        id: UUID primary key
        name: Type name (unique)
        is_privileged: If True, changes require voting
        display_order: Order for display purposes
        is_deleted: Soft delete flag
        created_at: Timestamp of record creation
    """

    __tablename__ = "tag_types"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )
    is_privileged: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    display_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
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
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="tag_type"
    )

    def __repr__(self) -> str:
        return f"<TagType(id={self.id}, name={self.name})>"
