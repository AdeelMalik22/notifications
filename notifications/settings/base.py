"""Shared settings for every NotificationOS environment."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
INSECURE_SECRET_KEY = "insecure-local-development-key"


def load_local_dotenv() -> None:
    """Load simple local key/value settings for host-based development only."""
    if not os.getenv("DJANGO_SETTINGS_MODULE", "").endswith(".local"):
        return
    dotenv_path = BASE_DIR / ".env"
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


load_local_dotenv()


def env_list(name: str, default: str = "") -> list[str]:
    """Return a comma-separated environment value as a clean list."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", INSECURE_SECRET_KEY)
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.common",
    "apps.audit",
    "apps.notifications",
    "apps.delivery",
    "apps.health",
    "apps.tenancy",
    "apps.catalog",
    "apps.recipients",
]

MIDDLEWARE = [
    "apps.common.middleware.RequestIDMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "notifications.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "notifications.wsgi.application"
ASGI_APPLICATION = "notifications.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "notifications"),
        "USER": os.getenv("POSTGRES_USER", "notifications"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "local-postgres-password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "connect_timeout": int(os.getenv("POSTGRES_CONNECT_TIMEOUT", "3")),
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://localhost:6379/1"),
        "TIMEOUT": 300,
        "OPTIONS": {
            "socket_connect_timeout": 1,
            "socket_timeout": 1,
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "NotificationOS API",
    "DESCRIPTION": "Multi-tenant notification delivery API.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1025"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").lower() == "true"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "notifications@example.test")
SMS_PROVIDER_BACKEND = os.getenv(
    "SMS_PROVIDER_BACKEND",
    "apps.delivery.providers.fake_sms.FakeSMSProvider",
)
PROVIDER_ENCRYPTION_KEY = os.getenv("PROVIDER_ENCRYPTION_KEY", "")
CONTACT_ENCRYPTION_KEY = os.getenv("CONTACT_ENCRYPTION_KEY", "")
CONTACT_LOOKUP_KEY = os.getenv("CONTACT_LOOKUP_KEY", "")
NOTIFICATION_TENANT_RATE_LIMIT = int(os.getenv("NOTIFICATION_TENANT_RATE_LIMIT", "100"))
NOTIFICATION_RECIPIENT_RATE_LIMIT = int(os.getenv("NOTIFICATION_RECIPIENT_RATE_LIMIT", "10"))
NOTIFICATION_MAX_OUTBOX_PER_TENANT = int(os.getenv("NOTIFICATION_MAX_OUTBOX_PER_TENANT", "1000"))
NOTIFICATION_MAX_PAYLOAD_BYTES = int(os.getenv("NOTIFICATION_MAX_PAYLOAD_BYTES", "32768"))
NOTIFICATION_MAX_VARIABLES = int(os.getenv("NOTIFICATION_MAX_VARIABLES", "100"))
NOTIFICATION_MAX_IDEMPOTENCY_KEY_LENGTH = int(
    os.getenv("NOTIFICATION_MAX_IDEMPOTENCY_KEY_LENGTH", "255")
)
NOTIFICATION_CONTENT_RETENTION_DAYS = int(os.getenv("NOTIFICATION_CONTENT_RETENTION_DAYS", "30"))
NOTIFICATION_METADATA_RETENTION_DAYS = int(os.getenv("NOTIFICATION_METADATA_RETENTION_DAYS", "90"))

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
CELERY_RESULT_BACKEND = None
CELERY_TASK_IGNORE_RESULT = True
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_TIMEOUT = 5
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_CANCEL_LONG_RUNNING_TASKS_ON_CONNECTION_LOSS = True
CELERY_CONTROL_QUEUE_EXCLUSIVE = True
CELERY_EVENT_QUEUE_EXCLUSIVE = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "apps.common.logging.RequestContextFilter",
        },
    },
    "formatters": {
        "json": {
            "()": "apps.common.logging.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_context"],
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.server": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_SERVER_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
