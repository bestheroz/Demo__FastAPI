FROM public.ecr.aws/lambda/python:3.13
LABEL maintainer="joony.kim <bestheroz@gmail.com>"

ENV POETRY_VERSION=2.1.3
RUN pip install --disable-pip-version-check --no-cache-dir poetry==$POETRY_VERSION

COPY poetry.lock pyproject.toml ${LAMBDA_TASK_ROOT}/
WORKDIR ${LAMBDA_TASK_ROOT}

RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-root

COPY ./dotenvs ${LAMBDA_TASK_ROOT}/dotenvs/
COPY ./app ${LAMBDA_TASK_ROOT}/app/

CMD ["app.main.handler"]
