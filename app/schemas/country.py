"""
Pydantic schemas for Country entity.

Defines request and response schemas for Country API operations.
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
import re


class CountryCreate(BaseModel):
    """
    Schema for creating a new country.

    Attributes:
        name: Country name (1-100 characters)
        code: ISO 3166-1 alpha-3 country code (3 uppercase letters)
    """
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=3, max_length=3)

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate that code is 3 uppercase letters."""
        if not re.match(r'^[A-Z]{3}$', v):
            raise ValueError('Code must be 3 uppercase letters')
        return v


class CountryUpdate(BaseModel):
    """
    Schema for updating an existing country.

    Attributes:
        name: Optional country name (1-100 characters)
        code: Optional ISO 3166-1 alpha-3 country code (3 uppercase letters)
    """
    name: str | None = Field(None, min_length=1, max_length=100)
    code: str | None = Field(None, min_length=3, max_length=3)

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str | None) -> str | None:
        """Validate that code is 3 uppercase letters if provided."""
        if v is not None and not re.match(r'^[A-Z]{3}$', v):
            raise ValueError('Code must be 3 uppercase letters')
        return v


class CountryResponse(BaseModel):
    """
    Schema for country response.

    Attributes:
        id: Country UUID
        name: Country name
        code: ISO 3166-1 alpha-3 country code
        created_at: Timestamp of creation
    """
    id: UUID
    name: str
    code: str
    created_at: datetime

    model_config = {
        "from_attributes": True  # Enable ORM mode for SQLAlchemy compatibility
    }
