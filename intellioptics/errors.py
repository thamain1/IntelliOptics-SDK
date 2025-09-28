class ApiTokenError(Exception):
    """Raised when the SDK cannot resolve a usable API token."""


class IntelliOpticsClientError(Exception):
    """Base error type for HTTP and SDK level failures."""


class ExperimentalFeatureUnavailable(IntelliOpticsClientError):
    """Raised when an experimental helper is accessed but not implemented by the backend."""

    def __init__(self, feature: str, message: str | None = None) -> None:
        details = message or f"Experimental feature '{feature}' is not available on this server version."
        super().__init__(details)
        self.feature = feature
