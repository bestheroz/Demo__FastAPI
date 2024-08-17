from re import search

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import count
from structlog import get_logger

from app.application.admin.account.model import AdminAccount
from app.application.user.schema import AccessTokenClaims
from app.application.user.type import AuthorityEnum
from app.common.code import Code
from app.common.exception import (
    AuthenticationException401,
    AuthorityException403,
    RequestException400,
    SystemException500,
)
from app.config.config import get_settings
from app.utils.jwt import get_access_token_claims, is_validated_jwt

settings = get_settings()

log = get_logger()


def get_service_id_from_request_url_path(request: Request) -> int | None:
    pattern = r"/api/v1/services/(\d+)"
    match = search(pattern, request.url.path)
    if match:
        return int(match.group(1))
    return None


async def get_admin_account_id(request: Request) -> int | None:
    authorization = request.headers.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    if not credentials:
        raise AuthenticationException401()
    operator_id = get_access_token_claims(credentials).id

    if operator_id is not None:
        return operator_id
    return None


async def get_operator_id(request: Request) -> int | None:
    authorization = request.headers.get("Authorization")
    scheme, credentials = get_authorization_scheme_param(authorization)
    claims = get_access_token_claims(credentials)
    service_authorities = claims.service_authorities
    if not service_authorities:
        if claims.manager_flag:
            return 1  # 시스템
        raise AuthenticationException401()

    service_id = get_service_id_from_request_url_path(request)
    if service_id is None:
        log.warning("service_id is None!! Can't get operator_id.")
        raise SystemException500()

    admin_id = next(
        (sa.id for sa in service_authorities if sa.service_id == service_id),
        None,
    )
    if admin_id is None:
        raise SystemException500()
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
        required_authority: AuthorityEnum | None = None,
    ):
        self.required_authority = required_authority

    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ) -> HTTPAuthorizationCredentials | None:
        if self.required_authority is None or self.is_authorized(credentials, request):
            return credentials

        raise AuthorityException403()

    def is_authorized(
        self,
        credentials: HTTPAuthorizationCredentials,
        request: Request,
    ) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise AuthenticationException401(Code.EXPIRED_TOKEN)

        claims = get_access_token_claims(access_token)
        if claims.manager_flag:
            return True

        service_id = get_service_id_from_request_url_path(request)
        if service_id is not None:
            service_authorities = claims.service_authorities
            if not service_authorities:
                raise AuthorityException403()
            check_service_id_flag = next(
                (True for sa in service_authorities if sa.service_id == service_id),
                False,
            )
            if not check_service_id_flag:
                raise RequestException400(Code.UNKNOWN_SERVICE)
            return self.check_service_authority(claims, service_id)

        return False

    @staticmethod
    def check_service_user(operator_id: int, service_id: int, session: Session):
        if (
            session.scalar(
                select(count(AdminAccount.id))
                .filter_by(id=operator_id)
                .join(AdminAccount.profiles)
                .filter_by(service_id=service_id)
            )
            == 0
        ):
            raise RequestException400(Code.UNKNOWN_SERVICE)

    def check_service_authority(
        self, claims: AccessTokenClaims, service_id: int
    ) -> bool:
        service_authorities = claims.service_authorities
        if not service_authorities:
            return False

        for sa in service_authorities:
            if sa.service_id == service_id and (
                sa.manager_flag or self.required_authority in (sa.authorities or [])
            ):
                return True
        return False


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


class ServiceManagerOnly(HTTPBearer):
    async def __call__(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(verify_jwt),
    ) -> HTTPAuthorizationCredentials | None:
        if self.is_authorized(credentials, request):
            return credentials

        raise AuthorityException403()

    async def authenticate(self, request: Request) -> HTTPAuthorizationCredentials:
        credentials = await super().__call__(request)
        if not credentials:
            raise AuthenticationException401()
        return credentials

    @staticmethod
    def is_authorized(
        credentials: HTTPAuthorizationCredentials,
        request: Request,
    ) -> bool:
        access_token = credentials.credentials
        if not is_validated_jwt(access_token):
            raise AuthenticationException401(Code.EXPIRED_TOKEN)

        claims = get_access_token_claims(access_token)
        if claims.manager_flag:
            return True

        service_id = get_service_id_from_request_url_path(request)
        if service_id is not None:
            service_authorities = claims.service_authorities
            if not service_authorities:
                raise AuthorityException403()
            check_service_id_flag = next(
                (True for sa in service_authorities if sa.service_id == service_id),
                False,
            )
            if check_service_id_flag:
                return True

        raise RequestException400(Code.UNKNOWN_SERVICE)
