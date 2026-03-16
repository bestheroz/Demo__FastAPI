from app.core.code import Code


class AppException(Exception):
    """Base exception class to reduce code duplication."""

    def __init__(self, code: Code, data: dict | list | None = None):
        self.code = code.name
        self.message = code.value
        self.data = data
        super().__init__(self.message)


class BadRequestException400(AppException):
    """400 Bad Request exception."""


class UnauthorizedException401(AppException):
    """401 Unauthorized exception."""

    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHENTICATION,
        data: dict | list | None = None,
    ):
        super().__init__(code, data)


class ForbiddenException403(AppException):
    """403 Forbidden exception."""

    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHORITY,
        data: dict | list | None = None,
    ):
        super().__init__(code, data)


class UnknownSystemException500(AppException):
    """500 Internal Server Error exception."""

    def __init__(
        self,
        code: Code = Code.UNKNOWN_SYSTEM_ERROR,
        data: dict | list | None = None,
    ):
        super().__init__(code, data)
