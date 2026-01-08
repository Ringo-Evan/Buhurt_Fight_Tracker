"""
SQLAlchemy ORM model for Country entity.

Implements soft delete pattern with is_deleted flag.
Uses UUID primary keys and SQLAlchemy 2.0 mapped_column style.
"""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class Country(Base):
    """
    Country entity with soft delete support.

    Attributes:
        id: UUID primary key (auto-generated)
        name: Country name (max 100 characters)
        code: ISO 3166-1 alpha-3 country code (3 uppercase letters)
        is_deleted: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated)
    """
    __tablename__ = "countries"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    code: Mapped[str] = mapped_column(
        String(3),
        nullable=False
    )

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<Country(id={self.id}, name='{self.name}', code='{self.code}', is_deleted={self.is_deleted})>"
