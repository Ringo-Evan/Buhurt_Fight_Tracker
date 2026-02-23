"""
Service layer for Fight entity business logic.

Implements validation and business rules for fight operations.
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import date

from app.repositories.fight_repository import FightRepository
from app.repositories.fight_participation_repository import FightParticipationRepository
from app.repositories.fighter_repository import FighterRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.tag_type_repository import TagTypeRepository
from app.models.fight import Fight
from app.models.tag import Tag
from app.exceptions import (
    FightNotFoundError,
    ValidationError,
    MissingParentTagError,
    InvalidTagError,
    InvalidTagValueError,
    InvalidParticipantCountError,
)
from app.core.constants import VALID_WEAPONS, VALID_LEAGUES, VALID_RULESETS, TEAM_SIZE_RULES


class FightService:
    """
    Business logic layer for Fight entity.

    Handles validation and business rules for fight operations.
    """

    def __init__(
        self,
        fight_repository: FightRepository,
        participation_repository: Optional[FightParticipationRepository] = None,
        fighter_repository: Optional[FighterRepository] = None,
        tag_repository: Optional[TagRepository] = None,
        tag_type_repository: Optional[TagTypeRepository] = None
    ):
        """
        Initialize service with repositories.

        Args:
            fight_repository: Repository for fight data access
            participation_repository: Optional repository for participation data access
            fighter_repository: Optional repository for fighter data access
            tag_repository: Optional repository for tag data access
            tag_type_repository: Optional repository for tag type data access
        """
        self.fight_repository = fight_repository
        self.participation_repository = participation_repository
        self.fighter_repository = fighter_repository
        self.tag_repository = tag_repository
        self.tag_type_repository = tag_type_repository

    def _validate_fight_data(self, fight_data: Dict[str, Any], is_update: bool = False) -> None:
        """
        Validate fight data.

        Args:
            fight_data: Dictionary with fight fields
            is_update: If True, validation is for update operation

        Raises:
            ValidationError: If validation fails
        """
        # Validate date (not in future)
        if "date" in fight_data and fight_data["date"]:
            if fight_data["date"] > date.today():
                raise ValidationError("Fight date cannot be in the future")

        # Validate location
        if "location" in fight_data:
            location = fight_data.get("location", "")
            if is_update and (location is None or (isinstance(location, str) and location.strip() == "")):
                raise ValidationError("Location cannot be empty")
            elif not is_update and (not location or not location.strip()):
                raise ValidationError("Location is required")

        # Validate winner_side (must be 1, 2, or None)
        if "winner_side" in fight_data:
            winner_side = fight_data.get("winner_side")
            if winner_side is not None and winner_side not in (1, 2):
                raise ValidationError("Winner side must be 1, 2, or null")

    async def create(self, fight_data: Dict[str, Any]) -> Fight:
        """
        Create a new fight.

        Args:
            fight_data: Dictionary with fight fields

        Returns:
            Created Fight instance

        Raises:
            ValidationError: If validation fails
        """
        self._validate_fight_data(fight_data, is_update=False)
        return await self.fight_repository.create(fight_data)

    async def _validate_participations(
        self,
        participations_data: List[Dict[str, Any]],
        supercategory: Optional[str] = None
    ) -> None:
        """
        Validate participation data before creating fight.

        Args:
            participations_data: List of participation dictionaries

        Raises:
            ValidationError: If validation fails
        """
        if not participations_data:
            return

        # Check minimum 2 participants
        if len(participations_data) < 2:
            raise ValidationError("Fight must have at least 2 participants")

        # Check both sides have participants
        sides = {p["side"] for p in participations_data}
        if sides != {1, 2}:
            raise ValidationError("Fight must have participants on both sides")

        # Check for duplicate fighters
        fighter_ids = [p["fighter_id"] for p in participations_data]
        if len(fighter_ids) != len(set(fighter_ids)):
            raise ValidationError("Cannot have duplicate fighter in the same fight")

        # Check max 1 captain per side
        for side in [1, 2]:
            captains = [p for p in participations_data if p["side"] == side and p.get("role") == "captain"]
            if len(captains) > 1:
                raise ValidationError(f"Cannot have multiple captains on side {side}")

        # Check all fighters exist
        if self.fighter_repository:
            for participation in participations_data:
                fighter = await self.fighter_repository.get_by_id(participation["fighter_id"])
                if not fighter:
                    raise ValidationError(f"Fighter with ID {participation['fighter_id']} not found")

        # Format-dependent validation
        if supercategory:
            # Count fighters (not alternates/coaches) per side
            side_1_fighters = [p for p in participations_data if p["side"] == 1 and p.get("role") == "fighter"]
            side_2_fighters = [p for p in participations_data if p["side"] == 2 and p.get("role") == "fighter"]

            if supercategory == "singles":
                if len(side_1_fighters) != 1 or len(side_2_fighters) != 1:
                    raise ValidationError("Singles fights require exactly 1 fighter per side")
            elif supercategory == "melee":
                if len(side_1_fighters) < 5 or len(side_2_fighters) < 5:
                    raise ValidationError("Melee fights require at least 5 fighters per side")

    async def create_with_participants(
        self,
        fight_data: Dict[str, Any],
        supercategory: str,
        participations_data: List[Dict[str, Any]]
    ) -> Fight:
        """
        Create a fight with participants and supercategory tag atomically.

        Args:
            fight_data: Dictionary with fight fields
            supercategory: Supercategory of the fight ("singles" or "melee")
            participations_data: List of participation dictionaries

        Returns:
            Created Fight instance with participations

        Raises:
            ValidationError: If validation fails
        """
        self._validate_fight_data(fight_data, is_update=False)
        await self._validate_participations(participations_data, supercategory)

        # Create the fight first
        fight = await self.fight_repository.create(fight_data)

        # Create supercategory tag linked to this fight
        if self.tag_repository and self.tag_type_repository:
            supercategory_tag_type = await self.tag_type_repository.get_by_name("supercategory")
            if not supercategory_tag_type:
                raise ValidationError("supercategory TagType not found")

            await self.tag_repository.create({
                "fight_id": fight.id,
                "tag_type_id": supercategory_tag_type.id,
                "value": supercategory
            })

        # Create each participation
        for participation_data in participations_data:
            await self.participation_repository.create({
                "fight_id": fight.id,
                "fighter_id": participation_data["fighter_id"],
                "side": participation_data["side"],
                "role": participation_data.get("role", "fighter")
            })

        # Refresh the fight to load the newly created participations
        await self.fight_repository.refresh_session(fight)
        return fight

    async def delete_tag(self, fight_id: UUID, tag_id: UUID) -> None:
        """
        Hard delete a tag from a fight.

        DD-012: Rejects with ValidationError if tag has active children.

        Args:
            fight_id: UUID of the fight owning the tag
            tag_id: UUID of the tag to delete

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If tag not on this fight, or has active children
        """
        # 1. Validate fight exists
        fight = await self.fight_repository.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        # 2. Validate tag exists and belongs to this fight
        tag = await self.tag_repository.get_by_id(tag_id, include_deactivated=True)
        if tag is None or tag.fight_id != fight_id:
            raise ValidationError(f"Tag with ID {tag_id} not found on fight {fight_id}")

        # 3. DD-012: Reject if active children exist
        active_children = await self.tag_repository.list_active_children(tag_id)
        if active_children:
            raise ValidationError(
                f"Cannot delete tag '{tag_id}': it has {len(active_children)} active child tag(s). "
                f"Deactivate or delete children first."
            )

        # 4. Hard delete
        await self.tag_repository.delete(tag_id)

    async def update_tag(self, fight_id: UUID, tag_id: UUID, new_value: str) -> Tag:
        """
        Update the value of a tag on a fight.

        DD-011: Supercategory tags are immutable after creation.

        Args:
            fight_id: UUID of the fight owning the tag
            tag_id: UUID of the tag to update
            new_value: New tag value

        Returns:
            Updated Tag instance

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If tag not on this fight, supercategory tag, or invalid new value
        """
        # 1. Validate fight exists
        fight = await self.fight_repository.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        # 2. Validate tag exists and belongs to this fight
        tag = await self.tag_repository.get_by_id(tag_id, include_deactivated=False)
        if tag is None or tag.fight_id != fight_id:
            raise ValidationError(f"Tag with ID {tag_id} not found on fight {fight_id}")

        # 3. DD-011: Supercategory is immutable
        if tag.tag_type and tag.tag_type.name == "supercategory":
            raise ValidationError(
                "Cannot update supercategory tag: supercategory is immutable after fight creation."
            )

        # 4. Validate new value for this tag type
        if tag.tag_type:
            self._validate_tag_value(tag.tag_type.name, new_value, fight)

        # 5. DD-015: Validate team size if category is changing
        if tag.tag_type and tag.tag_type.name == "category":
            self._validate_team_size_for_category(fight, new_value)

        # 6. DD-014: Cascade-delete children when category changes
        if tag.tag_type and tag.tag_type.name == "category":
            await self.tag_repository.cascade_deactivate_children(tag_id)

        # 7. Update
        updated = await self.tag_repository.update(tag_id, {"value": new_value})
        return updated

    # Allowed tag values per tag type
    _SUPERCATEGORY_VALUES = {"singles", "melee"}
    _CATEGORY_VALUES = {
        "singles": {"duel", "profight"},
        "melee": {"3s", "5s", "10s", "12s", "16s", "21s", "30s", "mass"},
    }
    _GENDER_VALUES = {"male", "female", "mixed"}
    # custom: any non-empty string up to 200 chars
    # Tag types that allow only one active instance per fight
    _ONE_PER_FIGHT_TYPES = {"supercategory", "category", "gender", "weapon", "league", "ruleset"}

    async def add_tag(
        self,
        fight_id: UUID,
        tag_type_name: str,
        value: str,
        parent_tag_id: Optional[UUID] = None
    ) -> Tag:
        """
        Add a tag to a fight.

        Args:
            fight_id: UUID of the fight
            tag_type_name: Name of the tag type (supercategory, category, gender, custom)
            value: Tag value (validated per type)
            parent_tag_id: Optional parent tag UUID (for hierarchy)

        Returns:
            Created Tag instance

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If tag_type_name unknown, value invalid, or business rules violated
        """
        # 1. Validate fight exists and is active
        fight = await self.fight_repository.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        # 2. Validate tag type exists
        tag_type = await self.tag_type_repository.get_by_name(tag_type_name)
        if tag_type is None:
            raise ValidationError(f"Unknown tag type: '{tag_type_name}'")

        # 3. Validate value is allowed for this tag type
        self._validate_tag_value(tag_type_name, value, fight)

        # 4. Enforce one-per-type rule (not for custom)
        if tag_type_name in self._ONE_PER_FIGHT_TYPES:
            active_tags_of_type = [
                t for t in fight.tags
                if not t.is_deactivated and t.tag_type_id == tag_type.id
            ]
            if active_tags_of_type:
                raise ValidationError(
                    f"Fight already has an active {tag_type_name} tag. "
                    f"Deactivate it before adding a new one."
                )

        # 5. Auto-link to parent tag (hierarchy)
        if parent_tag_id is None:
            if tag_type_name == "category":
                # Category links to supercategory
                sc_tag = next(
                    (t for t in fight.tags if not t.is_deactivated
                     and t.tag_type and t.tag_type.name == "supercategory"),
                    None
                )
                if sc_tag:
                    parent_tag_id = sc_tag.id
            elif tag_type_name in ("weapon", "league", "ruleset"):
                # Weapon/league/ruleset link to category
                cat_tag = next(
                    (t for t in fight.tags if not t.is_deactivated
                     and t.tag_type and t.tag_type.name == "category"),
                    None
                )
                if cat_tag:
                    parent_tag_id = cat_tag.id

        # 6. Create tag
        return await self.tag_repository.create({
            "fight_id": fight_id,
            "tag_type_id": tag_type.id,
            "value": value,
            "parent_tag_id": parent_tag_id,
        })

    async def deactivate_tag(self, fight_id: UUID, tag_id: UUID) -> Tag:
        """
        Deactivate a tag on a fight. Cascades deactivation to child tags.

        Args:
            fight_id: UUID of the fight owning the tag
            tag_id: UUID of the tag to deactivate

        Returns:
            Deactivated Tag instance

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If tag does not belong to this fight
        """
        # 1. Validate fight exists
        fight = await self.fight_repository.get_by_id(fight_id, include_deactivated=False)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        # 2. Validate tag exists and belongs to this fight
        tag = await self.tag_repository.get_by_id(tag_id, include_deactivated=True)
        if tag is None or tag.fight_id != fight_id:
            raise ValidationError(f"Tag with ID {tag_id} not found on fight {fight_id}")

        # 3. Deactivate tag
        await self.tag_repository.deactivate(tag_id)

        # 4. Cascade deactivation to children (e.g., category tags when supercategory deactivated)
        await self.tag_repository.cascade_deactivate_children(tag_id)

        # 5. Return the deactivated tag
        return await self.tag_repository.get_by_id(tag_id, include_deactivated=True)

    def _validate_tag_value(self, tag_type_name: str, value: str, fight: Fight) -> None:
        """
        Validate that value is allowed for the given tag type on this fight.

        Args:
            tag_type_name: Tag type name
            value: Proposed tag value
            fight: The fight (needed to check supercategory for category validation)

        Raises:
            ValidationError: If value is invalid
        """
        if tag_type_name == "supercategory":
            if value not in self._SUPERCATEGORY_VALUES:
                raise ValidationError(
                    f"Invalid supercategory value '{value}'. "
                    f"Allowed: {sorted(self._SUPERCATEGORY_VALUES)}"
                )

        elif tag_type_name == "category":
            # Determine fight's active supercategory value
            sc_tag = next(
                (t for t in fight.tags if not t.is_deactivated and t.tag_type and t.tag_type.name == "supercategory"),
                None
            )
            if sc_tag is None:
                raise ValidationError("Fight has no active supercategory tag. Cannot add category.")
            allowed = self._CATEGORY_VALUES.get(sc_tag.value, set())
            if value not in allowed:
                raise ValidationError(
                    f"Category value '{value}' is not valid for supercategory '{sc_tag.value}'. "
                    f"Allowed: {sorted(allowed)}"
                )

        elif tag_type_name == "gender":
            if value not in self._GENDER_VALUES:
                raise ValidationError(
                    f"Invalid gender value '{value}'. "
                    f"Allowed: {sorted(self._GENDER_VALUES)}"
                )

        elif tag_type_name == "weapon":
            # Get active category tag for weapon validation
            category_tag = next(
                (t for t in fight.tags if not t.is_deactivated and t.tag_type and t.tag_type.name == "category"),
                None
            )
            self._validate_weapon_tag(category_tag, value)

        elif tag_type_name == "league":
            # Get active category tag for league validation
            category_tag = next(
                (t for t in fight.tags if not t.is_deactivated and t.tag_type and t.tag_type.name == "category"),
                None
            )
            self._validate_league_tag(category_tag, value)

        elif tag_type_name == "ruleset":
            # Get active category tag for ruleset validation
            category_tag = next(
                (t for t in fight.tags if not t.is_deactivated and t.tag_type and t.tag_type.name == "category"),
                None
            )
            self._validate_ruleset_tag(category_tag, value)

        elif tag_type_name == "custom":
            if not value or not value.strip():
                raise ValidationError("Custom tag value cannot be empty")
            if len(value) > 200:
                raise ValidationError("Custom tag value cannot exceed 200 characters")

    async def get_by_id(self, fight_id: UUID, include_deactivated: bool = False) -> Fight:
        """
        Get a fight by ID.

        Args:
            fight_id: UUID of the fight
            include_deactivated: If True, include deactivated fights

        Returns:
            Fight instance

        Raises:
            FightNotFoundError: If fight not found
        """
        fight = await self.fight_repository.get_by_id(fight_id, include_deactivated=include_deactivated)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")
        return fight

    async def list_all(self, include_deactivated: bool = False) -> list[Fight]:
        """
        List all fights.

        Args:
            include_deactivated: If True, include deactivated fights

        Returns:
            List of Fight instances
        """
        return await self.fight_repository.list_all(include_deactivated=include_deactivated)

    async def list_by_date_range(
        self,
        start_date: date,
        end_date: date,
        include_deactivated: bool = False
    ) -> list[Fight]:
        """
        List fights within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            include_deactivated: If True, include deactivated fights

        Returns:
            List of Fight instances
        """
        return await self.fight_repository.list_by_date_range(
            start_date, end_date, include_deactivated=include_deactivated
        )

    async def update(self, fight_id: UUID, update_data: Dict[str, Any]) -> Fight:
        """
        Update a fight.

        Args:
            fight_id: UUID of the fight to update
            update_data: Dictionary with fields to update

        Returns:
            Updated Fight instance

        Raises:
            FightNotFoundError: If fight not found
            ValidationError: If validation fails
        """
        # Check fight exists
        fight = await self.fight_repository.get_by_id(fight_id)
        if fight is None:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

        self._validate_fight_data(update_data, is_update=True)
        return await self.fight_repository.update(fight_id, update_data)

    async def deactivate(self, fight_id: UUID) -> None:
        """
        Deactivate a fight.

        Args:
            fight_id: UUID of the fight to deactivate

        Raises:
            FightNotFoundError: If fight not found
        """
        try:
            await self.fight_repository.deactivate(fight_id)
        except ValueError:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

    async def delete(self, fight_id: UUID) -> None:
        """
        Permanently delete a fight from the database.

        Args:
            fight_id: UUID of the fight to delete

        Raises:
            FightNotFoundError: If fight not found
        """
        try:
            await self.fight_repository.delete(fight_id)
        except ValueError:
            raise FightNotFoundError(f"Fight with ID {fight_id} not found")

    # =========================================================================
    # Phase 3B: Tag Validation Methods
    # =========================================================================

    def _validate_weapon_tag(self, category_tag: Optional[Tag], value: str) -> None:
        """
        Validate weapon tag can be added. Only valid for category='duel'.

        Args:
            category_tag: The current category tag (or None)
            value: The weapon value to validate

        Raises:
            MissingParentTagError: If no category tag exists
            InvalidTagError: If category is not 'duel'
            InvalidTagValueError: If value is not in allowed weapons list
        """
        if not category_tag:
            raise MissingParentTagError("Weapon requires a category tag")
        if category_tag.value != "duel":
            raise InvalidTagError("Weapon tags only valid for 'duel' category")
        if value not in VALID_WEAPONS:
            valid = ", ".join(VALID_WEAPONS)
            raise InvalidTagValueError(f"Invalid weapon '{value}'. Valid options: {valid}")

    def _validate_league_tag(self, category_tag: Optional[Tag], value: str) -> None:
        """
        Validate league tag value for the current category.

        Args:
            category_tag: The current category tag (or None)
            value: The league value to validate

        Raises:
            MissingParentTagError: If no category tag exists
            InvalidTagError: If category doesn't support leagues
            InvalidTagValueError: If value is not valid for this category
        """
        if not category_tag:
            raise MissingParentTagError("League requires a category tag")

        category = category_tag.value
        if category not in VALID_LEAGUES:
            raise InvalidTagError(f"League tags not valid for category '{category}'")

        if value not in VALID_LEAGUES[category]:
            valid = ", ".join(VALID_LEAGUES[category])
            raise InvalidTagValueError(
                f"Invalid league '{value}' for category '{category}'. Valid options: {valid}"
            )

    def _validate_ruleset_tag(self, category_tag: Optional[Tag], value: str) -> None:
        """
        Validate ruleset tag value for the current category.

        Args:
            category_tag: The current category tag (or None)
            value: The ruleset value to validate

        Raises:
            MissingParentTagError: If no category tag exists
            InvalidTagError: If category doesn't support rulesets
            InvalidTagValueError: If value is not valid for this category
        """
        if not category_tag:
            raise MissingParentTagError("Ruleset requires a category tag")

        category = category_tag.value
        if category not in VALID_RULESETS:
            raise InvalidTagError(f"Ruleset tags not valid for category '{category}'")

        if value not in VALID_RULESETS[category]:
            valid = ", ".join(VALID_RULESETS[category])
            raise InvalidTagValueError(
                f"Invalid ruleset '{value}' for category '{category}'. Valid options: {valid}"
            )

    def _validate_team_size_for_category_at_creation(
        self, participations: List[Dict[str, Any]], category: str
    ) -> None:
        """
        Validate participations at fight creation time against category team size rules.

        Args:
            participations: List of participation dictionaries
            category: Category value (e.g., "5s", "10s")

        Raises:
            InvalidParticipantCountError: If team size doesn't meet category requirements
        """
        if category not in TEAM_SIZE_RULES:
            return  # No team size rule for this category (e.g., singles categories)

        min_size, max_size = TEAM_SIZE_RULES[category]

        for side in [1, 2]:
            count = len([p for p in participations if p["side"] == side])
            if count < min_size:
                raise InvalidParticipantCountError(
                    f"Category '{category}' requires {min_size}-{max_size if max_size else 'unlimited'} "
                    f"fighters per side, but side {side} has {count}"
                )
            if max_size and count > max_size:
                raise InvalidParticipantCountError(
                    f"Category '{category}' requires {min_size}-{max_size} "
                    f"fighters per side, but side {side} has {count}"
                )

    def _validate_team_size_for_category(self, fight: Fight, category: str) -> None:
        """
        Validate fight's current participations satisfy category team size rules.

        Args:
            fight: The fight with participations
            category: Category value to validate against

        Raises:
            InvalidParticipantCountError: If team size doesn't meet category requirements
        """
        if category not in TEAM_SIZE_RULES:
            return  # No team size rule for this category

        min_size, max_size = TEAM_SIZE_RULES[category]

        for side in [1, 2]:
            count = len([p for p in fight.participations
                         if p.side == side and not p.is_deleted])
            if count < min_size:
                raise InvalidParticipantCountError(
                    f"Cannot use category '{category}': requires {min_size}-{max_size if max_size else 'unlimited'} "
                    f"fighters per side, but side {side} has {count}"
                )
            if max_size and count > max_size:
                raise InvalidParticipantCountError(
                    f"Cannot use category '{category}': requires {min_size}-{max_size} "
                    f"fighters per side, but side {side} has {count}"
                )
