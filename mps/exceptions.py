class MacPhotoStudioError(Exception):
    """Base exception for Mac Photo Studio."""


class ConfigurationError(MacPhotoStudioError):
    """Raised when configuration loading or validation fails."""
