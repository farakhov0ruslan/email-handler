ARG BASE_IMAGE="python:3.12.4-slim"
FROM ${BASE_IMAGE}

ARG ARTIFACTORY_USER
ARG ARTIFACTORY_PWD

ENV PYTHONSAVEPATH='1' \
    PYTHONPATH='/run/app' \
    UV_INDEX_CORE_USERNAME="${ARTIFACTORY_USER}" \
    UV_INDEX_CORE_PASSWORD="${ARTIFACTORY_PWD}" \
    UV_PROJECT_ENVIRONMENT=/usr/local

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential tini curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /run
COPY pyproject.toml ./

RUN uv sync --active

COPY . ./app
RUN chmod -R 0777 ./app

ENTRYPOINT ["tini", "--"]
