# syntax=docker/dockerfile:1.7
FROM python:3.12.10-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd --gid "${GROUP_ID}" appuser \
    && useradd --uid "${USER_ID}" --gid appuser --create-home --shell /bin/bash appuser \
    && mkdir -p /app/tmp /app/logs /app/uploads \
    && chown -R appuser:appuser /app

FROM base AS runtime-deps
COPY requirements.txt ./
RUN pip install --prefix=/install --requirement requirements.txt

FROM base AS development
COPY requirements.txt requirements-dev.txt ./
RUN pip install --requirement requirements-dev.txt
COPY --chown=appuser:appuser . .
RUN chmod +x /app/docker/entrypoint.sh
USER appuser
EXPOSE 8000 5678
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["api"]

FROM base AS production
COPY --from=runtime-deps /install /usr/local
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic ./alembic
COPY --chown=appuser:appuser docker ./docker
RUN chmod +x /app/docker/entrypoint.sh
USER appuser
EXPOSE 8000
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["api-prod"]

