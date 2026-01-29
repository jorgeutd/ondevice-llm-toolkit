"""Custom error types for ODLT."""


class ODLTError(Exception):
    """Base error for the toolkit."""


class ConfigError(ODLTError):
    """Configuration is invalid or unreadable."""


class CommandError(ODLTError):
    """External command failed or produced invalid output."""


class DownloadError(ODLTError):
    """Model download failed."""


class ValidationError(ODLTError):
    """Validation failure for user inputs or outputs."""
