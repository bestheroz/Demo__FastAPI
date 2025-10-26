import time
from urllib.parse import urlparse
from uuid import uuid4

import structlog
from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.routing import APIRoute
from fastapi_events.handlers.local import local_handler
from fastapi_events.middleware import EventHandlerASGIMiddleware
from mangum import Mangum
from sentry_sdk import capture_exception, init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sqlalchemy import text
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.api.v1.admin import admin_router
from app.api.v1.notice import notice_router
from app.api.v1.user import user_router
from app.core.code import Code
from app.core.config import get_settings
from app.core.exception import (
    BadRequestException400,
    ForbiddenException403,
    UnauthorizedException401,
    UnknownSystemException500,
)
from app.dependencies.database import get_session
from app.dependencies.logger import setup_logger
from app.schemas.base import AccessTokenClaims
from app.types.base import UserTypeEnum
from app.utils.jwt import create_access_token
from app.utils.string import camelize

setup_logger()
log = structlog.get_logger()

settings = get_settings()
if settings.sentry_dsn and settings.deployment_environment not in ("local", "test"):
    init(
        dsn=settings.sentry_dsn,
        environment=settings.deployment_environment,
        integrations=[
            SqlalchemyIntegration(),
            StarletteIntegration(),
            FastApiIntegration(),
        ],
        send_default_pii=True,
    )


app = None
if settings.deployment_environment in ("local", "sandbox", "qa"):
    app = FastAPI(
        default_response_class=ORJSONResponse,
        title="Demo API",
        docs_url="/api-docs",
        description="### 로그인 후 사용자 인증을 위해 헤더에 `Authorization` 값이 필요함\n\n"
        "토큰값을 헤더에서 전달할때는 scheme 정보인 `Bearer ` 를 반드시 붙여줘야 한다. "
        "(예: 토큰이 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 라면 "
        "`Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9` 로 전달주어야 한다)\n\n"
        "토큰 갱신 시에도 동일한 `Authorization` 헤더에 refresh token을 Bearer 형식으로 전달한다.\n\n"
        "### 테스트을 위한 JWT 토큰은 아래 값을 사용하세요."
        f"""
        {
            (
                create_access_token(
                    AccessTokenClaims(
                        id=1,
                        login_id="developer",
                        name="개발자",
                        type=UserTypeEnum.ADMIN,
                        manager_flag=True,
                        authorities=[],
                    )
                )
            )
        } """,
    )
else:
    app = FastAPI(
        default_response_class=ORJSONResponse,
        title="DEMO API",
    )

cors_origins = settings.cors_origins.split(",")
origins = [origin.strip() for origin in cors_origins]

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.add_middleware(
    EventHandlerASGIMiddleware,  # type: ignore
    handlers=[local_handler],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # URL에서 경로와 쿼리 파라미터만 추출
    parsed_url = urlparse(str(request.url))
    path_and_query = parsed_url.path
    if parsed_url.query:
        path_and_query += f"?{parsed_url.query}"

    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=trace_id)

    # 요청 파라미터 로깅 (민감한 정보 필터링)
    safe_params = {k: "***" if k.lower() in ("password", "token") else v for k, v in request.query_params.items()}
    log.info(f"Request[{request.method} {path_and_query}] params: {safe_params}")

    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    log.info(f"Response[{request.method} {path_and_query}] status={response.status_code}, time: {process_time:.2f}ms")
    response.headers["X-Process-Time"] = str(process_time)
    return response


app.include_router(notice_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(user_router, prefix="/api")

for route in app.routes:
    if isinstance(route, APIRoute):
        for param in route.dependant.query_params:
            param.field_info.alias = camelize(param.name)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Get the original 'detail' list of errors
    details = exc.errors()
    log.error(f"Full error details: {details}")
    log.exception(exc)
    return ORJSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "code": Code.INVALID_PARAMETER,
                "message": "\n".join(
                    [f"{x['loc'][1] if len(x['loc']) > 1 else x['loc'][0]}: {x['msg']}" for x in details]
                ),
            }
        ),
    )


@app.exception_handler(BadRequestException400)
def handle_exception_400(_request: Request, exc: BadRequestException400):
    return ORJSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(exc),
    )


@app.exception_handler(UnauthorizedException401)
def handle_expired_token_exception(_request: Request, exc: UnauthorizedException401):
    return ORJSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content=jsonable_encoder(exc),
        headers=({"token": "must-renew"} if exc.code == Code.EXPIRED_TOKEN else {}),
    )


@app.exception_handler(ForbiddenException403)
def handle_invalid_authority_exception(_request: Request, exc: ForbiddenException403):
    return ORJSONResponse(
        status_code=HTTP_403_FORBIDDEN,
        content=jsonable_encoder(exc),
    )


@app.exception_handler(UnknownSystemException500)
def handle_invalid_authentication_exception(_request: Request, exc: UnknownSystemException500):
    capture_exception(exc)
    return ORJSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(exc),
    )


@app.get("/health/liveness", include_in_schema=False)
def liveness():
    return {"status": f"{settings.deployment_environment} OK"}


@app.get("/health/readiness", include_in_schema=False)
def readiness(session=Depends(get_session)):
    session.execute(text("SELECT now()"))
    return {"status": f"{settings.deployment_environment} UP"}


public_paths = [
    "/openapi.json",
    "/docs",
    "/health/liveness",
    "/health/readiness",
]


handler = Mangum(app, lifespan="off")
