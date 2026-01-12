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


class FightNotFoundError(Exception):
    """Raised when a fight is not found in the database."""

    def __init__(self, message: str = "Fight not found"):
        self.message = message
        super().__init__(self.message)


class InvalidFighterError(Exception):
    """Raised when a participation references an invalid fighter."""

    def __init__(self, message: str = "Invalid fighter"):
        self.message = message
        super().__init__(self.message)


class InvalidFightError(Exception):
    """Raised when referencing an invalid or inactive fight."""

    def __init__(self, message: str = "Invalid fight"):
        self.message = message
        super().__init__(self.message)


class TagTypeNotFoundError(Exception):
    """Raised when a tag type is not found."""

    def __init__(self, message: str = "Tag type not found"):
        self.message = message
        super().__init__(self.message)


class TagNotFoundError(Exception):
    """Raised when a tag is not found."""

    def __init__(self, message: str = "Tag not found"):
        self.message = message
        super().__init__(self.message)


class DuplicateTagError(Exception):
    """Raised when attempting to create a duplicate tag."""

    def __init__(self, message: str = "Tag already exists"):
        self.message = message
        super().__init__(self.message)


class TagChangeRequestNotFoundError(Exception):
    """Raised when a tag change request is not found."""

    def __init__(self, message: str = "Tag change request not found"):
        self.message = message
        super().__init__(self.message)


class DuplicateVoteError(Exception):
    """Raised when a session tries to vote twice on the same request."""

    def __init__(self, message: str = "Already voted on this request"):
        self.message = message
        super().__init__(self.message)
