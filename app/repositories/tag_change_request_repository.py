"""
Repository for TagChangeRequest entity data access.

Implements data access layer for tag change voting workflow.
"""

from typing import Dict, Any
from uuid import UUID
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.tag_change_request import TagChangeRequest, RequestStatus


class TagChangeRequestRepository:
    """
    Data access layer for TagChangeRequest entity.

    Handles all database operations for tag change requests.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, request_data: Dict[str, Any]) -> TagChangeRequest:
        """Create a new tag change request."""
        try:
            request = TagChangeRequest(**request_data)
            self.session.add(request)
            await self.session.commit()
            await self.session.refresh(request)
            return request
        except Exception as e:
            await self.session.rollback()
            raise e

    async def get_by_id(self, request_id: UUID) -> TagChangeRequest | None:
        """Get request by ID with eager-loaded relationships."""
        query = select(TagChangeRequest).options(
            joinedload(TagChangeRequest.fight),
            joinedload(TagChangeRequest.tag_type)
        ).where(TagChangeRequest.id == request_id)
        result = await self.session.execute(query)
        return result.unique().scalar_one_or_none()

    async def list_pending(self) -> list[TagChangeRequest]:
        """List all pending requests."""
        query = select(TagChangeRequest).options(
            joinedload(TagChangeRequest.fight),
            joinedload(TagChangeRequest.tag_type)
        ).where(
            TagChangeRequest.status == RequestStatus.PENDING.value,
            TagChangeRequest.is_deleted == False
        )
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def list_by_fight(self, fight_id: UUID) -> list[TagChangeRequest]:
        """List all requests for a specific fight."""
        query = select(TagChangeRequest).options(
            joinedload(TagChangeRequest.tag_type)
        ).where(
            TagChangeRequest.fight_id == fight_id,
            TagChangeRequest.is_deleted == False
        )
        result = await self.session.execute(query)
        return list(result.unique().scalars().all())

    async def get_pending_for_fight_and_type(
        self,
        fight_id: UUID,
        tag_type_id: UUID
    ) -> TagChangeRequest | None:
        """Get the pending request for a fight and tag type (only one allowed)."""
        query = select(TagChangeRequest).where(
            TagChangeRequest.fight_id == fight_id,
            TagChangeRequest.tag_type_id == tag_type_id,
            TagChangeRequest.status == RequestStatus.PENDING.value,
            TagChangeRequest.is_deleted == False
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_vote_counts(
        self,
        request_id: UUID,
        votes_for: int,
        votes_against: int
    ) -> TagChangeRequest:
        """Update the vote counts for a request."""
        request = await self.get_by_id(request_id)
        if request is None:
            raise ValueError("Request not found")

        request.votes_for = votes_for
        request.votes_against = votes_against
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def resolve(
        self,
        request_id: UUID,
        status: RequestStatus
    ) -> TagChangeRequest:
        """Resolve a request with the given status."""
        request = await self.get_by_id(request_id)
        if request is None:
            raise ValueError("Request not found")

        request.status = status.value
        request.resolved_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(request)
        return request
