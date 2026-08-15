"""
KisanAI OS
Application Exceptions
"""


class AppError(Exception):
    """Base application error."""

    status_code = 500
    message = "Application error"
    code = "SERVER_ERROR"

    def __init__(self, message: str | None = None, code: str | None = None):
        self.message = message or self.message
        if code:
            self.code = code
        super().__init__(self.message)


class NotFoundError(AppError):
    """Resource not found."""

    status_code = 404
    message = "Resource not found"
    code = "NOT_FOUND"


class ConflictError(AppError):
    """Resource already exists / conflict."""

    status_code = 409
    message = "Resource already exists"
    code = "CONFLICT"


class ValidationAppError(AppError):
    """Business rule validation failure."""

    status_code = 422
    message = "Validation failed"
    code = "VALIDATION_ERROR"
