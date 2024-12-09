from app.common.code import Code


class BadRequestException400(Exception):
    def __init__(self, code: Code, data: dict | list | None = None):
        self.code = code.name
        self.message = code.value
        self.data = data


class UnauthorizedException401(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHENTICATION,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data


class ForbiddenException403(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHORITY,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data


class UnknownSystemException500(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_SYSTEM_ERROR,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data
