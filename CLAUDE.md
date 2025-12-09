# CLAUDE.md

이 파일은 Claude Code (claude.ai/code)가 이 저장소의 코드 작업 시 참고하는 가이드입니다.

## 개발 명령어

### 코드 품질 및 테스트
- **린트 검사**: `ruff check`
- **코드 포맷팅**: `ruff format`
- **타입 검사**: `mypy app/`
- **대체 타입 검사**: `pyright app/`
- **테스트 실행**: `pytest`
- **커버리지 포함 테스트**: `pytest --cov=app --cov-report=term-missing`
- **단일 테스트 파일 실행**: `pytest tests/test_specific_file.py`
- **단일 테스트 함수 실행**: `pytest tests/test_file.py::test_function_name`

### 애플리케이션 실행
- **개발 서버 시작**: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- **운영 서버**: `DEPLOYMENT_ENVIRONMENT` 설정에 따라 `uvicorn` 운영 설정 사용

### 패키지 관리
- 이 프로젝트는 **Poetry**를 사용하여 의존성 관리
- **의존성 설치**: `poetry install`
- **새 패키지 추가**: `poetry add <package-name>`
- **개발 의존성 추가**: `poetry add --group dev <package-name>`

## 아키텍처 개요

### 프로젝트 구조
클린 아키텍처 원칙을 따르는 **FastAPI** 애플리케이션:

- **`app/api/`**: API 라우터 및 엔드포인트 (v1 버전 관리)
- **`app/services/`**: 비즈니스 로직 레이어
- **`app/models/`**: SQLAlchemy ORM 모델
- **`app/schemas/`**: 요청/응답 검증용 Pydantic 스키마
- **`app/dependencies/`**: FastAPI 의존성 (인증, 데이터베이스, 로깅)
- **`app/core/`**: 핵심 기능 (설정, 예외, 코드)
- **`app/utils/`**: 유틸리티 함수 (JWT, 날짜시간, 페이지네이션)
- **`app/types/`**: 타입 정의 및 열거형
- **`migrations/`**: SQL 마이그레이션 파일 (V1__, V2__ 등)

### 주요 아키텍처 패턴

#### 도메인 구조
애플리케이션은 세 가지 주요 도메인으로 구성:
- **Admin**: JWT 인증을 사용한 관리자 사용자 관리
- **User**: JWT 인증을 사용한 일반 사용자 관리
- **Notice**: 공지사항 시스템

#### 데이터베이스 아키텍처
- **데이터베이스 세션 관리**: 읽기/쓰기 분리가 가능한 커스텀 `DatabaseSessionManager`
- **커넥션 풀링**: 읽기 전용 최적화를 포함한 풀 크기 설정
- **듀얼 세션 지원**: 쿼리 최적화를 위한 별도의 읽기 전용 세션
- **기본 모델**: 감사 추적을 위한 `IdCreated` 및 `IdCreatedUpdated`

#### 인증 및 인가
- 사용자 유형별 별도 토큰을 사용한 **JWT 기반 인증**
- `AuthorityChecker` 의존성을 사용한 **권한 기반 인가**
- **듀얼 사용자 시스템**: 서로 다른 권한을 가진 Admin과 User 타입
- 만료된 토큰 처리가 가능한 **토큰 갱신** 메커니즘

#### 설정 관리
- 커스텀 `CustomBaseSettings`를 사용한 **환경 기반 설정**
- **다중 dotenv 지원**: `dotenvs/.env.{environment}` 및 `dotenvs/.env`에서 읽기
- Pydantic v1 호환성을 갖춘 **설정 검증**

#### API 설계
- 명확한 라우트 구성을 갖춘 **버전 관리 API** (v1)
- 페이지네이션 응답을 위한 `ListResult` 사용으로 **일관된 응답 형식**
- 성능 최적화를 위한 **ORJSON 응답**
- 커스텀 예외 타입을 사용한 **포괄적인 에러 처리**

### 개발 환경 설정
1. **환경 변수**: 적절한 `.env` 파일을 `dotenvs/` 디렉토리에 복사
2. **데이터베이스**: 환경 변수에서 MySQL 연결 설정 (aiomysql 사용)
3. **배포 환경**: `DEPLOYMENT_ENVIRONMENT` 설정 (local/sandbox/qa/production)
4. **의존성**: `poetry install`로 설치 (Poetry 패키지 관리 사용)

### 데이터베이스 마이그레이션
- **SQL 마이그레이션 파일**: `migrations/` 디렉토리에 `V{번호}__{설명}.sql` 패턴으로 위치
- **현재 마이그레이션**: V1 (admins), V2 (users), V3 (notices)

### 코드 스타일 및 품질
- **줄 길이**: 120자 (`ruff.toml`에서 설정)
- **Python 버전**: 3.14
- **임포트 정렬**: ruff의 isort 통합 사용
- **따옴표 스타일**: 큰따옴표 선호
- **Async/await**: 애플리케이션 전반에서 광범위하게 사용

### 테스트 설정
- **테스트 프레임워크**: 비동기 지원이 포함된 pytest
- **커버리지 리포팅**: `pytest.ini`에서 term-missing 리포트로 설정
- **환경 파일**: `dotenvs/.env` 및 `dotenvs/.env.test` 사용
- **테스트 경로**: 테스트는 `tests/` 디렉토리에 위치
- **비동기 테스트**: 자동 비동기 테스트 처리를 위해 `asyncio_mode=auto` 설정

### 주요 도구 및 의존성
- **FastAPI 0.116.1**: 자동 OpenAPI 문서화가 포함된 웹 프레임워크
- **SQLAlchemy 2.0.42**: 비동기 지원이 포함된 ORM
- **Pydantic 2.11.7**: 데이터 검증 및 설정 관리
- **aiomysql 0.2.0**: 비동기 MySQL 커넥터
- **uvicorn 0.35.0**: 성능을 위한 uvloop이 포함된 ASGI 서버
- **Sentry SDK**: 에러 모니터링 및 로깅
- **structlog**: 구조화된 로깅
- **PyJWT**: JWT 토큰 처리

## 배포

### Serverless Framework (AWS Lambda)
이 프로젝트는 Serverless Framework를 사용하여 AWS Lambda에 배포됩니다.

#### Lambda Function URL
- **API Gateway 대신 Lambda Function URL 사용**: 비용 절감을 위해 API Gateway 없이 직접 호출
- **CORS 설정**: `serverless.yml`의 `url.cors` 섹션에서 설정
- **엔드포인트 형식**: `https://<lambda-url-id>.lambda-url.<region>.on.aws/`

#### 배포 명령어
- **배포**: `serverless deploy --stage <stage>`
- **특정 함수만 배포**: `serverless deploy function -f main --stage <stage>`
- **로그 확인**: `serverless logs -f main --stage <stage>`

#### 환경별 설정
- **설정 파일 위치**: `serverless-env/{stage}.json`
- **지원 환경**: local, sandbox, qa, production

#### 비용 최적화
| 항목 | API Gateway | Lambda Function URL |
|------|-------------|---------------------|
| 요청 비용 | $3.50/백만 건 | 무료 |
| 데이터 전송 | 별도 과금 | Lambda 비용에 포함 |
| WebSocket | 지원 | 미지원 |
| 사용자 지정 도메인 | 기본 지원 | CloudFront 필요 |

> **참고**: Lambda Function URL은 WebSocket을 지원하지 않으며, 사용자 지정 도메인 사용 시 CloudFront 설정이 필요합니다.
