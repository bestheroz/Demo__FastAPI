# FastAPI 서버 배포 구성 가이드

## 목차
- [개요](#개요)
- [배포 환경별 서버 구성](#배포-환경별-서버-구성)
- [ASGI 서버 선택 가이드](#asgi-서버-선택-가이드)
- [환경별 상세 구성](#환경별-상세-구성)
- [성능 튜닝](#성능-튜닝)
- [모니터링 및 헬스체크](#모니터링-및-헬스체크)

---

## 개요

FastAPI는 ASGI(Asynchronous Server Gateway Interface) 프레임워크이므로, 프로덕션 환경에서는 적절한 ASGI 서버가 필요합니다. 배포 환경에 따라 최적의 서버 구성이 다르므로, 이 가이드는 각 환경별 권장 구성을 제시합니다.

### 프로젝트 현황
- **프레임워크**: FastAPI 0.120.0
- **Python 버전**: 3.13
- **주요 의존성**:
  - uvicorn 0.38.0
  - SQLAlchemy 2.0.44 (비동기 지원)
  - aiomysql 0.3.2
  - Sentry SDK (모니터링)

---

## 배포 환경별 서버 구성

| 환경 | 추천 구성 | ASGI 서버 | 프로세스 관리 | 주요 고려사항 |
|------|----------|-----------|--------------|--------------|
| **로컬 개발** | Uvicorn (단독) | Uvicorn | 단일 프로세스 | 빠른 재시작, 디버깅 용이성 |
| **AWS Lambda** | Mangum | - | Lambda 관리 | Cold start 최소화, 메모리 효율 |
| **EKS/K8s** | Gunicorn + Uvicorn Workers | Uvicorn | Gunicorn | 멀티코어 활용, 안정성 |

---

## ASGI 서버 선택 가이드

### 1. Uvicorn (단독)

#### 특징
- 순수 ASGI 서버, async/await 네이티브 지원
- 단일 프로세스 실행 (--workers 옵션으로 멀티 프로세스 가능)
- 경량, 빠른 시작 시간
- uvloop 및 httptools로 성능 최적화

#### 장점
✅ 메모리 효율적
✅ 간단한 설정
✅ Cold start 빠름 (Lambda에 유리)
✅ 개발 환경에 최적화 (--reload)

#### 단점
❌ 단일 프로세스 시 CPU 멀티코어 활용 제한
❌ 프로세스 관리 기능 부족 (크래시 복구 등)
❌ Graceful shutdown/reload 기능 제한

#### 사용 시나리오
- **로컬 개발 환경**
- **AWS Lambda** (Mangum 어댑터와 함께)
- **단순 프로덕션** (트래픽이 적고 단일 프로세스로 충분한 경우)

---

### 2. Gunicorn + Uvicorn Workers

#### 특징
- Gunicorn이 프로세스 매니저 역할
- 여러 Uvicorn worker 프로세스를 관리
- WSGI와 ASGI 모두 지원 (worker class로 지정)
- 프로덕션 표준 구성

#### 장점
✅ 멀티 프로세스로 CPU 멀티코어 완전 활용
✅ Worker 자동 재시작 (크래시 복구)
✅ Graceful shutdown/reload
✅ 프로덕션 안정성 우수
✅ Kubernetes/EKS와 궁합 좋음

#### 단점
❌ 메모리 사용량 증가 (worker 수만큼)
❌ 시작 시간 느림 (Lambda에 불리)
❌ 설정 복잡도 증가

#### 사용 시나리오
- **EKS/Kubernetes Pod**
- **EC2/VM 프로덕션**
- **높은 트래픽 서비스**
- **멀티코어 CPU 환경**

---

### 3. Hypercorn (고급 대안)

#### 특징
- HTTP/2, HTTP/3 (QUIC) 지원
- Trio, asyncio 둘 다 지원
- ASGI 표준 완벽 준수
- Uvicorn보다 기능 풍부

#### 장점
✅ HTTP/2 프로토콜 지원 (성능 향상)
✅ 멀티 워커 내장 (Gunicorn 불필요)
✅ 최신 프로토콜 지원
✅ 프로덕션 ready

#### 단점
❌ Uvicorn보다 덜 검증됨
❌ 커뮤니티 규모 작음
❌ Lambda에서는 사용 불가

#### 사용 시나리오
- **HTTP/2 필요 시**
- **고성능 요구사항**
- **최신 프로토콜 활용**

---

## 환경별 상세 구성

### 🖥️ 로컬 개발 환경

#### 기본 실행
```bash
# 단순 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 자동 재시작 (개발 중 권장)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 로그 레벨 조정
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

#### Poetry 스크립트 추가
```toml
# pyproject.toml
[tool.poetry.scripts]
dev = "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
```

```bash
# 실행
poetry run dev
```

#### 환경 설정
```bash
# dotenvs/.env.local
DEPLOYMENT_ENVIRONMENT=local
DB_HOST=localhost
DB_PORT=3306
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

### ☁️ AWS Lambda 환경

#### 아키텍처 구조
```
API Gateway/ALB
    → Lambda (컨테이너)
        → AWS Lambda Adapter (HTTP → Lambda Event 변환)
            → Uvicorn (HTTP 서버)
                → FastAPI 앱
```

#### 현재 프로젝트 구성 (Dockerfile 기반)

이 프로젝트는 **AWS Lambda Adapter** 방식을 사용합니다:

```dockerfile
# Dockerfile (현재 구성)
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm

# Lambda Adapter 설치 (HTTP → Lambda Event 변환)
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 \
     /lambda-adapter /opt/extensions/lambda-adapter

# 애플리케이션 코드
WORKDIR /opt/code
COPY ./app app/

# Uvicorn으로 HTTP 서버 실행
ENV PORT=8080
CMD exec uvicorn --port=$PORT --host 0.0.0.0 app.main:app --workers 5
```

#### Lambda Adapter vs Mangum 비교

| 구분 | Lambda Adapter (현재) | Mangum |
|------|---------------------|--------|
| **방식** | Uvicorn HTTP 서버 유지 | Lambda Event 직접 처리 |
| **코드 변경** | 불필요 (기존 코드 그대로) | handler 함수 추가 필요 |
| **성능** | 약간 느림 (HTTP 변환 오버헤드) | 더 빠름 (직접 처리) |
| **호환성** | 모든 ASGI 프레임워크 | FastAPI 특화 |
| **메모리** | 더 높음 (Uvicorn 실행) | 더 낮음 (Mangum만) |
| **Cold Start** | 약간 느림 | 빠름 |

#### Mangum 방식 (대안)

코드를 최소한으로 변경하여 성능을 개선하고 싶다면 Mangum 사용:

```python
# app/main.py (마지막에 추가)
from mangum import Mangum

# 기존 FastAPI 앱
app = FastAPI(...)

# Lambda handler 추가
handler = Mangum(app)
```

```dockerfile
# Dockerfile.lambda (Mangum 방식)
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app /var/task/app

# Lambda가 handler 함수 직접 호출
CMD ["app.main.handler"]
```

```txt
# requirements.txt
fastapi==0.120.0
mangum==0.17.0
pydantic[email]==2.12.3
sqlalchemy==2.0.44
aiomysql==0.3.2
```

#### Lambda 최적화 권장사항

1. **메모리 설정**: 512MB - 1GB
2. **타임아웃**: 30초 이하 (API Gateway 제한)
3. **Worker 수**: 1 (Lambda는 단일 요청만 처리)
4. **환경변수**:
   ```bash
   DEPLOYMENT_ENVIRONMENT=production
   ```

5. **VPC 구성** (DB 접근 시):
   - Private Subnet에 Lambda 배치
   - Security Group으로 RDS 접근 허용
   - NAT Gateway (외부 API 호출 필요 시)

---

### 🚢 EKS/Kubernetes 환경

#### 현재 Dockerfile 구성

```dockerfile
# Dockerfile (EKS 배포용)
FROM public.ecr.aws/docker/library/python:3.13-bookworm as builder
ENV POETRY_VERSION=2.1.3
RUN pip install --disable-pip-version-check --no-cache-dir poetry==$POETRY_VERSION

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm as runner
RUN useradd --create-home appuser
USER appuser

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/code
COPY ./dotenvs dotenvs/
COPY ./app app/

ENV PORT=8080
CMD exec uvicorn --port=$PORT --host 0.0.0.0 app.main:app --workers 5
```

#### Worker 수 계산 공식

```python
# 현재 설정: --workers 5
# 권장 공식: (CPU 코어 수 * 2) + 1

# 예시:
# allocated_cpu = 2  # k8s에서 할당된 CPU
# workers = allocated_cpu * 2 + 1  # 일반적인 공식
# 결과 = 5 workers
```

#### Gunicorn 방식 (권장)

더 나은 프로세스 관리를 위해 Gunicorn 사용:

```python
# gunicorn.conf.py
import multiprocessing
import os

# Kubernetes에서 할당된 CPU 기반 계산
cpu_count = int(os.getenv("K8S_CPU_LIMIT", multiprocessing.cpu_count()))
workers = cpu_count * 2 + 1

# Worker 클래스
worker_class = "uvicorn.workers.UvicornWorker"

# 바인딩
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# 연결 유지
keepalive = 120

# 타임아웃
timeout = 120
graceful_timeout = 30

# Worker 재활용 (메모리 누수 방지)
max_requests = 1000
max_requests_jitter = 50

# 로깅
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Preload (메모리 효율성)
preload_app = True
```

```dockerfile
# Dockerfile (Gunicorn 버전)
CMD exec gunicorn app.main:app -c gunicorn.conf.py
```

```bash
# requirements.txt에 추가
gunicorn==22.0.0
```

#### Kubernetes Deployment 구성

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi
        image: your-ecr-repo/fastapi-app:latest
        ports:
        - containerPort: 8080
          protocol: TCP

        env:
        - name: DEPLOYMENT_ENVIRONMENT
          value: "production"
        - name: K8S_CPU_LIMIT
          valueFrom:
            resourceFieldRef:
              resource: limits.cpu
        - name: PORT
          value: "8080"

        envFrom:
        - secretRef:
            name: fastapi-secrets

        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "2000m"

        livenessProbe:
          httpGet:
            path: /health/liveness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health/readiness
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]

---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: fastapi-app
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-app
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### ConfigMap 및 Secret 구성

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fastapi-config
  namespace: production
data:
  CORS_ORIGINS: "https://your-domain.com,https://admin.your-domain.com"

---
# secret.yaml (예시 - 실제로는 AWS Secrets Manager 사용 권장)
apiVersion: v1
kind: Secret
metadata:
  name: fastapi-secrets
  namespace: production
type: Opaque
data:
  JWT_SECRET_KEY: <base64-encoded-secret>
  DB_HOST: <base64-encoded-host>
  DB_USERNAME: <base64-encoded-username>
  DB_PASSWORD: <base64-encoded-password>
  SENTRY_DSN: <base64-encoded-dsn>
```

---

### 🖥️ EC2/VM 환경

#### systemd 서비스 구성

```ini
# /etc/systemd/system/fastapi.service
[Unit]
Description=FastAPI Application
After=network.target

[Service]
Type=notify
User=appuser
Group=appuser
WorkingDirectory=/opt/fastapi
Environment="PATH=/opt/fastapi/venv/bin"
Environment="DEPLOYMENT_ENVIRONMENT=production"

ExecStart=/opt/fastapi/venv/bin/gunicorn app.main:app \
    -c /opt/fastapi/gunicorn.conf.py

ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 관리
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi

# 무중단 재시작
sudo systemctl reload fastapi

# 로그 확인
sudo journalctl -u fastapi -f
```

#### Nginx 리버스 프록시

```nginx
# /etc/nginx/sites-available/fastapi
upstream fastapi_backend {
    # Gunicorn Unix socket (더 빠름)
    server unix:/opt/fastapi/gunicorn.sock fail_timeout=0;

    # 또는 TCP 소켓
    # server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name api.your-domain.com;

    # HTTPS로 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    # SSL 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # 보안 헤더
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # 클라이언트 요청 크기 제한
    client_max_body_size 10M;

    location / {
        proxy_pass http://fastapi_backend;

        # 프록시 헤더
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 타임아웃
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # WebSocket 지원 (필요 시)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 정적 파일 (있는 경우)
    location /static/ {
        alias /opt/fastapi/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 헬스체크 캐싱 비활성화
    location ~ ^/health/ {
        proxy_pass http://fastapi_backend;
        proxy_set_header Host $host;
        proxy_cache off;
    }
}
```

---

## 성능 튜닝

### Worker 수 최적화

#### CPU 바운드 애플리케이션
```python
# CPU 집약적 작업이 많은 경우
workers = (cpu_count * 2) + 1
```

#### I/O 바운드 애플리케이션
```python
# 데이터베이스 쿼리, 외부 API 호출이 많은 경우
workers = cpu_count * 4
```

### 데이터베이스 연결 풀 조정

```python
# app/dependencies/database.py
from sqlalchemy.ext.asyncio import create_async_engine

# Worker당 연결 수 계산
workers = 5
pool_size_per_worker = 10
max_overflow_per_worker = 20

# 총 연결 수
total_pool_size = pool_size_per_worker * workers
total_max_overflow = max_overflow_per_worker * workers

# DB 설정에 맞게 조정 (MySQL max_connections 확인 필요)
engine = create_async_engine(
    database_url,
    pool_size=pool_size_per_worker,  # Worker당 기본 연결
    max_overflow=max_overflow_per_worker,  # Worker당 최대 추가 연결
    pool_recycle=3600,  # 1시간마다 연결 재생성 (MySQL wait_timeout 대응)
    pool_pre_ping=True,  # 연결 유효성 체크
)
```

### Uvicorn 성능 옵션

```bash
# 프로덕션 최적화
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 5 \
    --loop uvloop \           # 빠른 이벤트 루프
    --http httptools \        # 빠른 HTTP 파서
    --log-level warning \     # 로그 레벨 조정
    --access-log \            # 액세스 로그 활성화
    --proxy-headers \         # 프록시 헤더 신뢰
    --forwarded-allow-ips='*'
```

### Gunicorn 성능 옵션

```python
# gunicorn.conf.py
import multiprocessing
import os

# Worker 설정
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# 성능 최적화
max_requests = 1000  # Worker 재시작 (메모리 누수 방지)
max_requests_jitter = 50

# Preload (메모리 공유)
preload_app = True

# 타임아웃
timeout = 120
graceful_timeout = 30
keepalive = 5

# 로깅
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
```

---

## 모니터링 및 헬스체크

### 헬스체크 엔드포인트 (현재 구현)

프로젝트에는 이미 헬스체크 엔드포인트가 구현되어 있습니다:

```python
# app/main.py

@app.get("/health/liveness", include_in_schema=False)
def liveness():
    """컨테이너 생존 여부 확인 (Kubernetes liveness probe)"""
    return {"status": f"{settings.deployment_environment} OK"}

@app.get("/health/readiness", include_in_schema=False)
def readiness(session=Depends(get_session)):
    """서비스 준비 상태 확인 (Kubernetes readiness probe)"""
    session.execute(text("SELECT now()"))
    return {"status": f"{settings.deployment_environment} UP"}
```

#### Liveness vs Readiness

| 구분 | Liveness | Readiness |
|------|----------|-----------|
| **목적** | 컨테이너 생존 여부 | 트래픽 수신 가능 여부 |
| **체크 내용** | 기본 응답 확인 | DB 연결 등 의존성 확인 |
| **실패 시 조치** | 컨테이너 재시작 | 트래픽 라우팅 중지 |
| **체크 주기** | 느림 (10-30초) | 빠름 (5-10초) |

### Sentry 모니터링 (현재 구현)

```python
# app/main.py
from sentry_sdk import capture_exception, init
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

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
        send_default_pii=True,  # 개인정보 포함 (주의 필요)
    )
```

### 구조화된 로깅 (현재 구현)

```python
# app/dependencies/logger.py
import structlog

# 현재 미들웨어에서 trace_id 바인딩
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    trace_id = str(uuid4())
    request.state.trace_id = trace_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(trace_id=trace_id)

    # 요청/응답 로깅
    log.info(f"Request[{request.method} {path_and_query}] params: {safe_params}")
    # ... 처리 ...
    log.info(f"Response[{request.method} {path_and_query}] status={response.status_code}, time: {process_time:.2f}ms")
```

### Prometheus 메트릭 (선택사항)

추가 모니터링을 위한 Prometheus 통합:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
# app/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

# Prometheus 메트릭 노출
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
```

---

## 환경별 체크리스트

### 🖥️ 로컬 개발
- [ ] `.env.local` 파일 설정
- [ ] `uvicorn --reload` 실행
- [ ] 로그 레벨 debug 설정
- [ ] API 문서 확인 (`http://localhost:8000/api-docs`)

### ☁️ Lambda
- [ ] Mangum 또는 Lambda Adapter 선택
- [ ] 메모리 512MB-1GB 할당
- [ ] 타임아웃 30초 이하 설정
- [ ] VPC 구성 (DB 접근 시)
- [ ] 환경변수 `DEPLOYMENT_ENVIRONMENT=production` 설정
- [ ] Cold start 최적화 (Provisioned Concurrency 고려)

### 🚢 EKS/K8s
- [ ] Gunicorn 설정 파일 작성
- [ ] Deployment YAML 작성
- [ ] Resource limits/requests 설정
- [ ] Liveness/Readiness probe 설정
- [ ] HPA 구성
- [ ] Secret/ConfigMap 구성
- [ ] Ingress/Service 설정

### 🖥️ EC2/VM
- [ ] systemd 서비스 파일 작성
- [ ] Gunicorn 설정 최적화
- [ ] Nginx 리버스 프록시 구성
- [ ] SSL 인증서 설정
- [ ] 로그 로테이션 설정
- [ ] 모니터링 에이전트 설치

---

## 문제 해결

### Worker 수가 너무 많을 때
**증상**: 메모리 부족, DB 연결 풀 고갈
**해결**: Worker 수 줄이기, DB 연결 풀 크기 조정

### Cold Start가 느릴 때 (Lambda)
**증상**: 첫 요청이 매우 느림
**해결**:
- Mangum 사용
- Provisioned Concurrency 활성화
- 의존성 최소화
- Docker 이미지 크기 줄이기

### Graceful Shutdown 실패
**증상**: 요청 처리 중 강제 종료
**해결**:
- Kubernetes: `preStop` hook 추가
- Gunicorn: `graceful_timeout` 증가

### DB 연결 고갈
**증상**: `OperationalError: (2003, "Can't connect to MySQL server")`
**해결**:
- Worker당 pool_size 줄이기
- MySQL `max_connections` 증가
- `pool_pre_ping=True` 설정

---

## 참고 자료

- [FastAPI 공식 문서 - Deployment](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn 공식 문서](https://www.uvicorn.org/)
- [Gunicorn 공식 문서](https://docs.gunicorn.org/)
- [AWS Lambda Adapter](https://github.com/awslabs/aws-lambda-web-adapter)
- [Mangum 공식 문서](https://mangum.io/)

---

## 문서 버전
- **작성일**: 2025-01-26
- **프로젝트 버전**: FastAPI 0.120.0, Python 3.13
- **마지막 업데이트**: 2025-01-26
