from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from structlog import get_logger

from app.core.code import Code
from app.core.config import get_settings
from app.core.exception import (
    ForbiddenException403,
    UnauthorizedException401,
)
from app.schemas.base import AccessTokenClaims, Operator
from app.types.base import AuthorityEnum, UserTypeEnum
from app.utils.jwt import get_access_token_claims, is_validated_jwt

settings = get_settings()

log = get_logger()


def get_operator(request: Request) -> Operator:
    authorization = request.headers.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    claims = get_access_token_claims(credentials)
    return Operator.model_validate(claims.model_dump())


def get_admin_id(request: Request) -> int:
    operator = get_operator(request)
    if operator.type != UserTypeEnum.ADMIN:
        log.warning(f"You are not admin: {operator}")
        raise ForbiddenException403()
    return operator.id


def get_user_id(request: Request) -> int:
    operator = get_operator(request)
    if operator.type != UserTypeEnum.USER:
        log.warning(f"You are not user: {operator}")
        raise ForbiddenException403()
    return operator.id


class JWTToken(HTTPBearer):
    async def __call__(
        self,
        request: Request,
    ) -> HTTPAuthorizationCredentials | None:
        credentials = await self.authenticate(request)
        if self.is_authorized(credentials):
            return credentials

        raise ForbiddenException403()

    async def authenticate(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials:
            raise UnauthorizedException401()
        return credentials

    @staticmethod
    def is_authorized(credentials: HTTPAuthorizationCredentials) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise UnauthorizedException401(Code.EXPIRED_TOKEN)
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
        if not self.require_authorities or self.is_authorized(credentials):
            return credentials
        log.warning(
            f"Need: {self.require_authorities}, Yours: {get_access_token_claims(credentials.credentials).authorities}"
        )
        raise ForbiddenException403()

    def is_authorized(
        self,
        credentials: HTTPAuthorizationCredentials,
    ) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise UnauthorizedException401(Code.EXPIRED_TOKEN)

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


class SuperManagerOnly:
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ) -> HTTPAuthorizationCredentials | None:
        if self.is_authorized(credentials):
            return credentials
        raise ForbiddenException403()

    @staticmethod
    def is_authorized(credentials: HTTPAuthorizationCredentials) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise UnauthorizedException401(Code.EXPIRED_TOKEN)

        claims = get_access_token_claims(access_token)
        result = bool(claims.manager_flag)
        if not result:
            log.warning(f"You are not super admin: {claims}")
        return result
