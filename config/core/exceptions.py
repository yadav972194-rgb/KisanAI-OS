"""
KisanAI OS
Application Exceptions
"""


class AppError(Exception):
    """Base application error."""

    status_code = 500
    message = "Application error"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found."""

    status_code = 404
    message = "Resource not found"


class ConflictError(AppError):
    """Resource already exists / conflict."""

    status_code = 409
    message = "Resource already exists"


class ValidationAppError(AppError):
    """Business rule validation failure."""

    status_code = 422
    message = "Validation failed"
