from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.routing import APIRoute
from sentry_sdk import capture_exception, init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from structlog import get_logger

from app.apdapter.orm import DEFAULT_SESSION_FACTORY, get_session
from app.application.admin.account.router import admin_account_router
from app.application.admin.router import admin_router
from app.application.file.router import file_router
from app.application.user.discipline.router import user_discipline_router
from app.application.user.router import user_router
from app.application.notice.router import notice_router
from app.application.service.model import Service
from app.application.service.router import service_router
from app.application.terms.history.router import terms_history_router
from app.application.terms.router import terms_router
from app.application.user.schema import AccessTokenClaims
from app.application.version.router import version_router
from app.application.withdraw_reason.router import withdraw_router
from app.common.code import Code
from app.common.exception import (
    AuthenticationException401,
    AuthorityException403,
    RequestException400,
    SystemException500,
)
from app.config.config import get_settings
from app.utils.jwt import create_access_token
from app.utils.string import camelize

log = get_logger()

settings = get_settings()
if settings.deployment_environment not in ("local", "test"):
    init(
        settings.sentry_dsn,
        environment=settings.deployment_environment,
        integrations=[
            SqlalchemyIntegration(),
            StarletteIntegration(),
            FastApiIntegration(),
        ],
    )

app = None
if settings.deployment_environment in ("local", "sandbox", "qa"):
    session: Session = DEFAULT_SESSION_FACTORY()
    services = session.execute(
        select(Service.id, Service.name, Service.platforms, Service.use_flag)
    ).all()
    markdown_service_grid = [
        f"| **{x.id}** | {x.name} | {x.platforms} | {x.use_flag} |" for x in services
    ]
    app = FastAPI(
        default_response_class=ORJSONResponse,
        title="NO-IT SERVICE ADMIN API",
        docs_url="/docs",
        description="### 로그인 후 사용자 인증을 위해 헤더에 `Authorization`, `AuthorizationR` 값이 필요함\n\n"
        "토큰값을 헤더에서 전달할때는 scheme 정보인 `Bearer ` 를 반드시 붙여줘야 한다. "
        "(예: 토큰이 eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 라면 "
        "`Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9` 로 전달주어야 한다)\n\n"
        "### 테스트을 위한 JWT 토큰은 아래 값을 사용하세요."
        f"""
        {(
            create_access_token( 
                AccessTokenClaims(
                    id=1,
                    login_id="no-reply@no-it.io",
                    name="시스템",
                    image_url=None,
                    manager_flag=True,
                    service_authorities=[],
                )
            )
        )} """
        "\n\n### NO-IT 에서 관리하는 서비스 목록입니다.\n\n"
        "| **서비스 ID** | 서비스명 | 지원 플랫폼 | 사용 중 |\n"
        "|-------|-------|-------|-------|\n" + "\n".join(markdown_service_grid),
    )
else:
    app = FastAPI(
        title="NO-IT SERVICE ADMIN API",
    )

origins = [
    "http://localhost:3000",
    "https://d19m17vt7yiaa.cloudfront.net",
    "https://d28o3cjh16dtx4.cloudfront.net",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(notice_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(admin_account_router, prefix="/api")
app.include_router(version_router, prefix="/api")
app.include_router(service_router, prefix="/api")
app.include_router(terms_router, prefix="/api")
app.include_router(terms_history_router, prefix="/api")
app.include_router(withdraw_router, prefix="/api")
app.include_router(file_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(user_discipline_router, prefix="/api")

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
                "detail": "\n".join(
                    [
                        f"{x['loc'][1] if len(x['loc']) > 1 else x['loc'][0]}: {x['msg']}"
                        for x in details
                    ]
                )
            }
        ),
    )


@app.exception_handler(RequestException400)
def handle_exception_400(_request: Request, exc: RequestException400):
    return ORJSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(exc),
    )


@app.exception_handler(AuthenticationException401)
def handle_expired_token_exception(_request: Request, exc: AuthenticationException401):
    return ORJSONResponse(
        status_code=HTTP_401_UNAUTHORIZED,
        content=jsonable_encoder(exc),
        headers=({"token": "must-renew"} if exc.code == Code.EXPIRED_TOKEN else {}),
    )


@app.exception_handler(AuthorityException403)
def handle_invalid_authority_exception(_request: Request, exc: AuthorityException403):
    return ORJSONResponse(
        status_code=HTTP_403_FORBIDDEN,
        content=jsonable_encoder(exc),
    )


@app.exception_handler(SystemException500)
def handle_invalid_authentication_exception(_request: Request, exc: SystemException500):
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
