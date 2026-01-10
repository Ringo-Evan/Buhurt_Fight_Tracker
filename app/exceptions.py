"""
Custom exceptions for the application.

Defines business logic and domain-specific exceptions.
"""


class CountryNotFoundError(Exception):
    """Raised when a country is not found in the database."""

    def __init__(self, message: str = "Country not found"):
        self.message = message
        super().__init__(self.message)


class DuplicateCountryCodeError(Exception):
    """Raised when attempting to create a country with a duplicate code."""

    def __init__(self, code: str):
        self.code = code
        self.message = f"Country with code {code} already exists"
        super().__init__(self.message)


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
