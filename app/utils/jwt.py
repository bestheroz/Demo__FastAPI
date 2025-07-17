from datetime import UTC, datetime, timedelta

from jwt import DecodeError, InvalidTokenError, decode, encode

from app.core.config import get_settings
from app.schemas.base import AccessTokenClaims, RefreshTokenClaims

settings = get_settings()

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_TIME = timedelta(
    minutes=(
        1440 if settings.deployment_environment in ("sandbox", "local") else 5
    )  # 개발 환경에서는 swagger-ui 를 통한 테스트를 할 수 있기 때문에 access token 의 시간을 길게 잡는다.(1일)
)
REFRESH_TOKEN_EXPIRE_TIME = timedelta(minutes=30)


def create_access_token(data) -> str:
    _dict = AccessTokenClaims.model_validate(data).model_dump(by_alias=True)
    _dict.update({"exp": int((datetime.now(UTC) + ACCESS_TOKEN_EXPIRE_TIME).timestamp())})
    return encode(_dict, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data) -> str:
    _dict = RefreshTokenClaims.model_validate(data).model_dump(by_alias=True)
    _dict.update({"exp": int((datetime.now(UTC) + REFRESH_TOKEN_EXPIRE_TIME).timestamp())})
    return encode(_dict, SECRET_KEY, algorithm=ALGORITHM)


def is_validated_jwt(token: str) -> bool:
    try:
        decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return True
    except (DecodeError, InvalidTokenError):
        return False


def issued_refresh_token_in_10_seconds(token: str) -> bool:
    if settings.deployment_environment == "test":
        return False
    try:
        payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        expiration_time_from_current = datetime.now(UTC) + REFRESH_TOKEN_EXPIRE_TIME
        expiration_time = datetime.fromtimestamp(payload["exp"], tz=UTC).replace(tzinfo=UTC)
        return expiration_time_from_current - expiration_time < timedelta(seconds=10)
    except (DecodeError, InvalidTokenError):
        return False


def get_claims(token: str) -> dict:
    return decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_access_token_claims(access_token: str) -> AccessTokenClaims:
    return AccessTokenClaims.model_validate(get_claims(access_token))


def get_refresh_token_claims(refresh_token: str) -> RefreshTokenClaims:
    return RefreshTokenClaims.model_validate(get_claims(refresh_token))
