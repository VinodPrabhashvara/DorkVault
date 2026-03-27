"""Domain exceptions for DorkVault."""


class DorkVaultError(Exception):
    """Base exception for application-specific errors."""


class DataValidationError(DorkVaultError):
    """Raised when a technique definition is missing required data."""


class TechniqueLoadError(DorkVaultError):
    """Raised when technique data cannot be loaded from disk."""


class PersistenceError(DorkVaultError):
    """Base exception for local file persistence failures."""


class SettingsError(PersistenceError):
    """Raised when application settings cannot be loaded or saved safely."""


class FavoritesError(PersistenceError):
    """Raised when favorites cannot be persisted safely."""


class RecentHistoryError(PersistenceError):
    """Raised when recent history cannot be persisted safely."""


class CustomTechniqueError(PersistenceError):
    """Raised when custom techniques cannot be loaded or saved safely."""


class ExportError(PersistenceError):
    """Raised when exported output cannot be written safely."""


class QueryRenderError(DorkVaultError):
    """Base exception for query rendering failures."""


class MissingVariableError(QueryRenderError):
    """Raised when a required template variable is missing."""


class MalformedTemplateError(QueryRenderError):
    """Raised when a technique query template cannot be parsed or rendered."""


class BrowserIntegrationError(DorkVaultError):
    """Base exception for browser URL building and launch failures."""


class UnsupportedBrowserEngineError(BrowserIntegrationError):
    """Raised when no browser URL strategy exists for a technique engine."""
