FROM public.ecr.aws/docker/library/python:3.13-bookworm as builder
LABEL maintainer="joony.kim <bestheroz@gmail.com>"

ENV POETRY_VERSION=2.1.2
#RUN apt-get update && apt-get upgrade -y && apt-get install gcc -y
RUN pip install --disable-pip-version-check --no-cache-dir poetry==$POETRY_VERSION

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python -m venv $VIRTUAL_ENV

COPY poetry.lock pyproject.toml ./
RUN poetry export -f requirements.txt -o requirements.txt --without-hashes \
    && pip install --disable-pip-version-check -r requirements.txt

FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm as runner
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 /lambda-adapter /opt/extensions/lambda-adapter
LABEL maintainer="joony.kim <bestheroz@gmail.com>"

RUN useradd --create-home appuser
USER appuser

ENV VIRTUAL_ENV=/opt/venv
COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /opt/code
COPY ./dotenvs dotenvs/
COPY ./app app/

ENV PORT=8080
CMD exec uvicorn --port=$PORT --host 0.0.0.0 app.main:app --workers 5

# 권장되는 worker 수 계산
# allocated_cpu = 2  # k8s에서 할당된 CPU
# workers = allocated_cpu * 2 + 1  # 일반적인 공식
# 이 경우 workers = 5가 됨
