class IntelliOpticsClientError(Exception):
    """Generic client-side error from the IntelliOptics SDK."""

class ApiTokenError(IntelliOpticsClientError):
    """Raised when the API token is missing or invalid."""
