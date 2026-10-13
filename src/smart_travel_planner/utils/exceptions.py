"""Application-specific exceptions."""


class SmartTravelPlannerError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(SmartTravelPlannerError):
    """Raised when required runtime configuration is missing or invalid."""


class ProviderError(SmartTravelPlannerError):
    """Raised when an external data provider fails safely."""
