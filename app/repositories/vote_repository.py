"""
Repository for Vote entity data access.

Implements data access layer for anonymous voting.
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vote import Vote


class VoteRepository:
    """
    Data access layer for Vote entity.

    Handles all database operations for votes.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, vote_data: Dict[str, Any]) -> Vote:
        """Create a new vote."""
        try:
            vote = Vote(**vote_data)
            self.session.add(vote)
            await self.session.commit()
            await self.session.refresh(vote)
            return vote
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, vote_id: UUID) -> Vote | None:
        """Get vote by ID."""
        query = select(Vote).where(Vote.id == vote_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_request_and_session(
        self,
        request_id: UUID,
        session_id: UUID
    ) -> Vote | None:
        """Check if a session has already voted on a request."""
        query = select(Vote).where(
            Vote.tag_change_request_id == request_id,
            Vote.session_id == session_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def count_by_request(self, request_id: UUID) -> tuple[int, int]:
        """Count votes for and against a request."""
        query_for = select(func.count(Vote.id)).where(
            Vote.tag_change_request_id == request_id,
            Vote.is_upvote == True
        )
        query_against = select(func.count(Vote.id)).where(
            Vote.tag_change_request_id == request_id,
            Vote.is_upvote == False
        )

        result_for = await self.session.execute(query_for)
        result_against = await self.session.execute(query_against)

        return (result_for.scalar() or 0, result_against.scalar() or 0)

    async def list_by_request(self, request_id: UUID) -> list[Vote]:
        """List all votes for a request."""
        query = select(Vote).where(Vote.tag_change_request_id == request_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())
