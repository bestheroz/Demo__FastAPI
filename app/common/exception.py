from app.common.code import Code


class RequestException400(Exception):
    def __init__(self, code: Code, data: dict | list | None = None):
        self.code = code.name
        self.message = code.value
        self.data = data


class AuthenticationException401(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHENTICATION,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data


class AuthorityException403(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_AUTHORITY,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data


class SystemException500(Exception):
    def __init__(
        self,
        code: Code = Code.UNKNOWN_SYSTEM_ERROR,
        data: dict | list | None = None,
    ):
        self.code = code.name
        self.message = code.value
        self.data = data
