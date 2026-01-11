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


class TeamNotFoundError(Exception):
    """Raised when a team is not found in the database."""

    def __init__(self, message: str = "Team not found"):
        self.message = message
        super().__init__(self.message)


class InvalidCountryError(Exception):
    """Raised when a team references an invalid or inactive country."""

    def __init__(self, message: str = "Invalid country"):
        self.message = message
        super().__init__(self.message)


class FighterNotFoundError(Exception):
    """Raised when a fighter is not found in the database."""

    def __init__(self, message: str = "Fighter not found"):
        self.message = message
        super().__init__(self.message)


class InvalidTeamError(Exception):
    """Raised when a fighter references an invalid or inactive team."""

    def __init__(self, message: str = "Invalid team"):
        self.message = message
        super().__init__(self.message)
