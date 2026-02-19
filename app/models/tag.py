"""
SQLAlchemy model for Tag entity.

Represents tags applied to fights with hierarchical support.
"""

from datetime import datetime, UTC
from uuid import uuid4, UUID
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.models.country import Base

if TYPE_CHECKING:
    from app.models.fight import Fight
    from app.models.tag_type import TagType


class Tag(Base):
    """
    Tag entity representing a tag applied to a fight.

    Tags have a hierarchical structure through parent_tag_id for
    cascading relationships (e.g., Category -> Subcategory -> Weapon).

    Attributes:
        id: UUID primary key
        fight_id: FK to fights table
        tag_type_id: FK to tag_types table
        value: The tag value (e.g., "Singles", "Longsword")
        parent_tag_id: Optional FK to parent tag (for hierarchy)
        is_deactivated: Deactivated flag
        created_at: Timestamp of record creation
    """

    __tablename__ = "tags"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )
    fight_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("fights.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True  # Optional for now - will be required when Fight is implemented
    )
    tag_type_id: Mapped[UUID] = mapped_column(
        ForeignKey("tag_types.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False
    )
    value: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    parent_tag_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("tags.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True
    )
    is_deactivated: Mapped[bool] = mapped_column(
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
    fight: Mapped["Fight | None"] = relationship(
        "Fight",
        back_populates="tags"
    )
    tag_type: Mapped["TagType"] = relationship(
        "TagType",
        back_populates="tags",
        lazy="joined"
    )
    parent_tag: Mapped["Tag | None"] = relationship(
        "Tag",
        remote_side=[id],
        back_populates="child_tags"
    )
    child_tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        back_populates="parent_tag"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, type={self.tag_type_id}, value={self.value})>"
