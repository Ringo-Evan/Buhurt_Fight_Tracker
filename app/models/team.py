"""
SQLAlchemy ORM model for Team entity.

Implements soft delete pattern with is_deactivated flag.
Uses UUID primary keys and foreign key relationship to Country.
Follows same patterns as Country model for consistency.
"""

from datetime import datetime, UTC
from uuid import UUID, uuid4
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Import Base from country module to ensure single metadata instance
from app.models.country import Base

# Type checking import to avoid circular import at runtime
if TYPE_CHECKING:
    from app.models.country import Country
    from app.models.fighter import Fighter


class Team(Base):
    """
    Team entity with soft delete support and country relationship.

    A team represents a group of fighters that compete together in Buhurt fights.
    Each team must be associated with exactly one country via foreign key.

    Attributes:
        id: UUID primary key (auto-generated)
        name: Team name (max 100 characters, required)
        country_id: Foreign key to countries table (UUID, required)
        is_deactivated: Soft delete flag (defaults to False)
        created_at: Timestamp of creation (auto-generated, UTC)

        country: Relationship to Country entity (eager loaded by default)

    Relationships:
        - country: Many-to-One with Country (lazy="joined" for eager loading)
        - Prevents N+1 query problem when retrieving teams

    Database Constraints:
        - FK: country_id references countries.id (CASCADE on update, RESTRICT on delete)
        - NOT NULL: name, country_id must be provided
        - Default: is_deactivated = False, created_at = now()

    Soft Delete Behavior:
        - Deactivated teams are filtered from default queries
        - Country relationship preserved even when soft deleted
        - Admin can retrieve deactivated teams with include_deactivated=True

    Example:
        ```python
        # Create team with country relationship
        team = Team(
            name="Team USA",
            country_id=usa_country_id
        )
        session.add(team)
        await session.commit()

        # Retrieve with eager-loaded country
        team = await repository.get_by_id(team.id)
        assert team.country.code == "USA"  # No additional query!
        ```
    """
    __tablename__ = "teams"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    country_id: Mapped[UUID] = mapped_column(
        ForeignKey("countries.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        index=True  # Optimize filtering by country
    )

    is_deactivated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True  # Optimize soft delete filtering
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False
    )

    # Relationships
    country: Mapped["Country"] = relationship(
        "Country",
        lazy="joined",  # Eager load by default to avoid N+1 queries
        foreign_keys=[country_id],
        back_populates="teams"  # Will be added to Country model
    )

    fighters: Mapped[List["Fighter"]] = relationship(
        "Fighter",
        back_populates="team",
        lazy="select",  # Not eager-loaded by default (fighters load team eagerly instead)
        cascade="all, delete-orphan"  # Cascade operations to fighters
    )

    def __init__(self, **kwargs):
        """
        Initialize Team with Python-level defaults.

        This ensures defaults are applied when creating instances programmatically
        (not just when inserting to database), making the model work correctly in
        tests, mocks, and outside database context.

        Rationale: Prefer explicit Python defaults over relying solely on database
        defaults. This makes the model portable and easier to test.

        Args:
            **kwargs: Field values for the team

        Example:
            ```python
            team = Team(name="Team USA", country_id=usa_id)
            assert team.id is not None  # Auto-generated
            assert team.is_deactivated is False  # Python default applied
            ```
        """
        super().__init__(**kwargs)

        # Apply Python defaults if not provided
        # Database defaults (in mapped_column) will override these on insert
        if 'id' not in kwargs:
            self.id = uuid4()
        if 'is_deactivated' not in kwargs:
            self.is_deactivated = False
        if 'created_at' not in kwargs:
            self.created_at = datetime.now(UTC)

    def __repr__(self) -> str:
        """
        String representation of Team for debugging.

        Returns:
            str: Human-readable representation with key attributes
        """
        return (
            f"<Team(id={self.id}, name='{self.name}', "
            f"country_id={self.country_id}, is_deactivated={self.is_deactivated})>"
        )
