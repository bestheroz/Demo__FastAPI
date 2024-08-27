from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from structlog import get_logger

from app.common.code import Code
from app.common.exception import (
    AuthenticationException401,
    AuthorityException403,
)
from app.common.schema import AccessTokenClaims
from app.common.type import AuthorityEnum
from app.config.config import get_settings
from app.utils.jwt import get_access_token_claims, is_validated_jwt

settings = get_settings()

log = get_logger()


async def get_admin_id(request: Request) -> int | None:
    authorization = request.headers.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    if not credentials:
        raise AuthenticationException401()
    operator_id = get_access_token_claims(credentials).id
    return operator_id


async def get_operator_id(request: Request) -> int | None:
    authorization = request.headers.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    claims = get_access_token_claims(credentials)
    admin_id = claims.id
    if admin_id is None:
        raise AuthenticationException401()
    return int(admin_id)


class JWTToken(HTTPBearer):
    async def __call__(
        self,
        request: Request,
    ) -> HTTPAuthorizationCredentials | None:
        credentials = await self.authenticate(request)
        if self.is_authorized(credentials):
            return credentials

        raise AuthorityException403()

    async def authenticate(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials:
            raise AuthenticationException401()
        return credentials

    @staticmethod
    def is_authorized(credentials: HTTPAuthorizationCredentials) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise AuthenticationException401(Code.EXPIRED_TOKEN)
        return True


verify_jwt = JWTToken()


class AuthorityChecker:
    def __init__(
        self,
        require_authorities: list[AuthorityEnum] | None = None,
    ):
        self.require_authorities = require_authorities

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ) -> HTTPAuthorizationCredentials | None:
        if self.require_authorities is None or self.is_authorized(credentials):
            return credentials

        raise AuthorityException403()

    def is_authorized(
        self,
        credentials: HTTPAuthorizationCredentials,
    ) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise AuthenticationException401(Code.EXPIRED_TOKEN)

        claims = get_access_token_claims(access_token)
        if claims.manager_flag:
            return True

        return self.check_authorities(claims)

    def check_authorities(self, claims: AccessTokenClaims) -> bool:
        if not self.require_authorities:
            return True

        if not claims.authorities:
            return False

        return any(require_authority in claims.authorities for require_authority in self.require_authorities)


class SuperManagerOnly(HTTPBearer):
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ) -> HTTPAuthorizationCredentials | None:
        if self.is_authorized(credentials):
            return credentials

        raise AuthorityException403()

    async def authenticate(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials:
            raise AuthenticationException401()
        return credentials

    @staticmethod
    def is_authorized(credentials: HTTPAuthorizationCredentials) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise AuthenticationException401(Code.EXPIRED_TOKEN)

        claims = get_access_token_claims(access_token)
        return bool(claims.manager_flag)
