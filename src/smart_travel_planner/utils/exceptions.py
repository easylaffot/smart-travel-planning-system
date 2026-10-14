"""Application-specific exceptions."""


class SmartTravelPlannerError(Exception):
    """Base exception for expected application failures."""


class ConfigurationError(SmartTravelPlannerError):
    """Raised when required runtime configuration is missing or invalid."""


class ProviderError(SmartTravelPlannerError):
    """Raised when an external data provider fails safely."""


class LLMConfigurationError(ConfigurationError):
    """Raised when the configured LLM cannot be constructed safely."""


class CrewConfigurationError(ConfigurationError):
    """Raised when agents, tasks, or the Crew are configured incorrectly."""


class AgentExecutionError(SmartTravelPlannerError):
    """Raised when controlled agent execution cannot be completed."""


class WorkflowExecutionError(SmartTravelPlannerError):
    """Raised when the integrated planning workflow cannot complete."""


class ResultParsingError(WorkflowExecutionError):
    """Raised when a CrewAI result cannot be validated safely."""


class PlanValidationError(WorkflowExecutionError):
    """Raised when the final travel plan violates required constraints."""
