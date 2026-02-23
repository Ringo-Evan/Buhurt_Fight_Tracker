"""
Repository for FightParticipation entity data access.

Implements data access layer for the fight-fighter junction table.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.fight_participation import FightParticipation


class FightParticipationRepository:
    """
    Data access layer for FightParticipation entity.

    Handles all database operations for fight participations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def create(self, participation_data: Dict[str, Any]) -> FightParticipation:
        """
        Create a new fight participation.

        Args:
            participation_data: Dictionary with participation fields

        Returns:
            Created FightParticipation instance
        """
        try:
            participation = FightParticipation(**participation_data)
            self.session.add(participation)  # add() is synchronous
            await self.session.commit()
            await self.session.refresh(participation)
            return participation
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(
        self,
        participation_id: UUID
    ) -> FightParticipation | None:
        """
        Retrieve a participation by ID with eager-loaded fighter.

        Args:
            participation_id: UUID of the participation

        Returns:
            FightParticipation instance or None if not found
        """
        query = select(FightParticipation).options(
            joinedload(FightParticipation.fighter)
        ).where(FightParticipation.id == participation_id)

        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_by_fight(
        self,
        fight_id: UUID
    ) -> list[FightParticipation]:
        """
        List all participations for a specific fight.

        Args:
            fight_id: UUID of the fight

        Returns:
            List of FightParticipation instances
        """
        query = select(FightParticipation).options(
            joinedload(FightParticipation.fighter)
        ).where(FightParticipation.fight_id == fight_id).order_by(
            FightParticipation.side,
            FightParticipation.role
        )

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_fighter(
        self,
        fighter_id: UUID
    ) -> list[FightParticipation]:
        """
        List all fight participations for a specific fighter.

        Args:
            fighter_id: UUID of the fighter

        Returns:
            List of FightParticipation instances
        """
        query = select(FightParticipation).options(
            joinedload(FightParticipation.fight)
        ).where(FightParticipation.fighter_id == fighter_id)

        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def delete(self, participation_id: UUID) -> bool:
        """
        Hard delete a participation (junction tables use hard delete, not soft delete).

        Args:
            participation_id: UUID of the participation to delete

        Returns:
            True if deleted, False if not found
        """
        participation = await self.get_by_id(participation_id)
        if participation is None:
            return False

        self.session.delete(participation)  # delete() is synchronous
        await self.session.commit()
        return True

    async def check_fighter_participation(
        self,
        fight_id: UUID,
        fighter_id: UUID
    ) -> bool:
        """
        Check if a fighter is already participating in the fight.

        Args:
            fight_id: UUID of the fight
            fighter_id: UUID of the fighter

        Returns:
            True if fighter already has a participation, False otherwise
        """
        query = select(FightParticipation).where(
            FightParticipation.fight_id == fight_id,
            FightParticipation.fighter_id == fighter_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None
