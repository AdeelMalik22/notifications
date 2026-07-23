# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12.13
ARG UV_VERSION=0.11.18

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

RUN groupadd --system notificationos \
    && useradd --system --gid notificationos --home-dir /app notificationos

COPY --from=uv /uv /uvx /usr/local/bin/
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY --chown=notificationos:notificationos apps ./apps
COPY --chown=notificationos:notificationos notifications ./notifications
COPY --chown=notificationos:notificationos manage.py ./

RUN DJANGO_SETTINGS_MODULE=notifications.settings.base \
    DJANGO_SECRET_KEY=container-build-only-key \
    python manage.py collectstatic --noinput

USER notificationos

EXPOSE 8000

CMD ["gunicorn", "notifications.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "30", "--access-logfile", "-"]
