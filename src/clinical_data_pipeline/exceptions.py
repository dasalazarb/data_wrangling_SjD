class PipelineError(Exception):
    """Base exception for pipeline errors."""


class ValidationError(PipelineError):
    """Raised when validation checks fail."""
