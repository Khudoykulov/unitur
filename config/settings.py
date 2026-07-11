"""Django settings for Unitur.

Single settings module for every environment (local dev, tests, production).
Behavior is switched by environment variables (.env) rather than by
importing a chain of settings files:

- DEBUG        toggles dev-only apps/middleware, cookie security, storage,
                logging verbosity and the email backend.
- TESTING      auto-detected (pytest is running) — swaps in an in-memory
                SQLite DB, locmem cache, fast password hashing, and disables
                rate limiting / auto-translate / network calls for tests.
"""

import sys
from pathlib import Path

import dj_database_url
from decouple import Csv, config
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG: bool = config("DEBUG", cast=bool, default=True)
TESTING: bool = "pytest" in sys.modules

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY: str = config("SECRET_KEY", default="django-insecure-dev-only-change-in-production-abc123xyz")
ALLOWED_HOSTS: list[str] = config("ALLOWED_HOSTS", cast=Csv(), default="localhost,127.0.0.1")

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    # modeltranslation MUST precede django.contrib.admin
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "rosetta",
    "django_filters",
    "crispy_forms",
    "crispy_tailwind",
    "ckeditor",
    "ckeditor_uploader",
    "cloudinary_storage",
    "cloudinary",
    "whitenoise.runserver_nostatic",
    "django_celery_results",
    "django_celery_beat",
    "import_export",
]

LOCAL_APPS = [
    "apps.core",
    "apps.tours",
    "apps.destinations",
    "apps.ichki_turlar",
    "apps.hotels",
    "apps.bookings",
    "apps.guides",
    "apps.reviews",
    "apps.accounts",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "csp.middleware.CSPMiddleware",
    "apps.dashboard.middleware.DashboardAccessMiddleware",
]

# Dev-only tooling — never active during tests, even if DEBUG=True.
if DEBUG and not TESTING:
    INSTALLED_APPS += ["debug_toolbar", "django_extensions"]
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
        "SHOW_COLLAPSED": True,
    }
    # Exclude TemplatesPanel — it monkey-patches Template.render() adding ~10
    # frames per include, which exhausts the stack on complex pages with many
    # nested templates.
    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.history.HistoryPanel",
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ]

# ── Dashboard / Admin security ──────────────────────────────────────────
ADMIN_URL = config("ADMIN_URL", default="admin/")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600 * 8  # 8 hours

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.core.context_processors.site_settings",
                "apps.core.context_processors.navigation",
                "apps.core.context_processors.languages",
                "apps.dashboard.context_processors.dashboard_counts",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — always Postgres via DATABASE_URL, except tests (fast in-memory
# SQLite, isolated per test run).
# ---------------------------------------------------------------------------
if TESTING:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
else:
    DATABASES = {
        "default": dj_database_url.config(
            default=config("DATABASE_URL", default="sqlite:///db.sqlite3"),
            conn_max_age=600,
        )
    }

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
if TESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_USER_MODEL = "auth.User"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
ACCOUNT_ADAPTER = "apps.accounts.adapters.AccountAdapter"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = config("LANGUAGE_CODE", default="en")

LANGUAGES = [
    ("en", _("English")),
    ("uz", _("O'zbekcha")),
    ("ru", _("Русский")),
    ("it", _("Italiano")),
    ("es", _("Español")),
    ("ja", _("日本語")),
]

LANGUAGE_FLAGS = {
    "en": "🇬🇧",
    "uz": "🇺🇿",
    "ru": "🇷🇺",
    "it": "🇮🇹",
    "es": "🇪🇸",
    "ja": "🇯🇵",
}

TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

# ---------------------------------------------------------------------------
# Static & Media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Django 5.1+ ignores the legacy STATICFILES_STORAGE / DEFAULT_FILE_STORAGE
# settings — only STORAGES is honoured. Plain storage in dev/tests
# (runserver-friendly, no manifest file needed); production gets a
# content-hashing backend for cache-busting.
if DEBUG or TESTING:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "config.storages.ForgivingManifestStaticFilesStorage"},
    }

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Cloudinary — only used to actually store media when not running locally.
import cloudinary  # noqa: E402

CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY": config("CLOUDINARY_API_KEY", default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}
if DEBUG or TESTING:
    DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
else:
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Sites framework
# ---------------------------------------------------------------------------
SITE_ID = 1

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
if TESTING:
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
elif DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="Unitur <noreply@unitur.uz>")

# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = config("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# ---------------------------------------------------------------------------
# Cache & sessions
# ---------------------------------------------------------------------------
if TESTING:
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    SESSION_ENGINE = "django.contrib.sessions.backends.db"
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": config("REDIS_URL", default="redis://localhost:6379/1"),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "unitur",
        }
    }
    SESSION_ENGINE = "django.contrib.sessions.backends.cache"
    SESSION_CACHE_ALIAS = "default"

# ---------------------------------------------------------------------------
# django-allauth
# ---------------------------------------------------------------------------
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# ---------------------------------------------------------------------------
# CKEditor
# ---------------------------------------------------------------------------
CKEDITOR_UPLOAD_PATH = "ckeditor_uploads/"
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "toolbar_Custom": [
            ["Bold", "Italic", "Underline"],
            ["NumberedList", "BulletedList", "-", "Outdent", "Indent"],
            ["JustifyLeft", "JustifyCenter", "JustifyRight"],
            ["Link", "Unlink"],
            ["RemoveFormat", "Source"],
            ["Image", "Table", "HorizontalRule"],
            ["Styles", "Format"],
        ],
        "height": 400,
        "width": "100%",
        "removePlugins": "elementspath",
        "resize_enabled": True,
        "extraPlugins": "image2",
    }
}

# ---------------------------------------------------------------------------
# Crispy Forms
# ---------------------------------------------------------------------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# ---------------------------------------------------------------------------
# django-modeltranslation
# ---------------------------------------------------------------------------
MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("en", "uz", "ru", "it", "es", "ja")
MODELTRANSLATION_FALLBACK_LANGUAGES = ("en",)

# Auto-translation: when content is saved from the dashboard, machine-translate
# the entered text into the other languages (deep-translator / Google).
# Always off during tests — never hit the network from the test suite.
AUTO_TRANSLATE = False if TESTING else config("AUTO_TRANSLATE", cast=bool, default=True)

# ---------------------------------------------------------------------------
# Rate limiting (django-ratelimit) — module is django_ratelimit
# ---------------------------------------------------------------------------
RATELIMIT_USE_CACHE = "default"
RATELIMIT_ENABLE = not (DEBUG or TESTING)
# Behind nginx (Unix socket) REMOTE_ADDR is empty; nginx sets the real client
# IP in X-Real-IP (from $remote_addr, not client-spoofable). Use it for keying.
RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"

# ---------------------------------------------------------------------------
# CSP headers (django-csp)
# ---------------------------------------------------------------------------
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "fonts.googleapis.com",
    "cdn.jsdelivr.net",
    "unpkg.com",
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
)
CSP_FONT_SRC = ("'self'", "fonts.gstatic.com", "fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "res.cloudinary.com", "*.tile.openstreetmap.org")
CSP_CONNECT_SRC = ("'self'",)
CSP_REPORT_ONLY = DEBUG  # enforce in production, report-only while developing

# ---------------------------------------------------------------------------
# django-import-export
# ---------------------------------------------------------------------------
IMPORT_EXPORT_USE_TRANSACTIONS = True

# ---------------------------------------------------------------------------
# Site meta (used by context processor)
# ---------------------------------------------------------------------------
SITE_NAME = config("SITE_NAME", default="UNITUR travel agency")
SITE_URL = config("SITE_URL", default="http://localhost:8000")
SITE_TAGLINE = "Dunyoning eng go'zal joylarini kashf eting"
SITE_PHONE = "+998919917101"
SITE_EMAIL = "burkhanov1c@gmail.com"
SITE_ADDRESS = "Navoiy viloyati, Navoiy shahri, Jasorat 29-36"
SITE_LATITUDE = 40.0844
SITE_LONGITUDE = 65.3792
SITE_WORKING_HOURS = "Dushanba–Shanba, 9:00–18:00"
SOCIAL_LINKS = {
    "facebook": "https://facebook.com/unituruz",
    "instagram": "https://instagram.com/unitouruz",
    "telegram": "https://t.me/unituruz",
    "youtube": "https://youtube.com/@Unituruz",
}

# ---------------------------------------------------------------------------
# Security hardening — degrades safely to dev-friendly defaults when
# HTTPS_ENABLED is unset (local dev/tests), matches production when set.
# ---------------------------------------------------------------------------
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

_https = config("HTTPS_ENABLED", cast=bool, default=False)
SECURE_HSTS_SECONDS = 31_536_000 if _https else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = _https
SECURE_HSTS_PRELOAD = _https
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", cast=bool, default=False)
SESSION_COOKIE_SECURE = _https
CSRF_COOKIE_SECURE = _https
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if _https else None

# ---------------------------------------------------------------------------
# Sentry — only initialised when a DSN is actually configured.
# ---------------------------------------------------------------------------
_sentry_dsn = config("SENTRY_DSN", default="")
if _sentry_dsn and not TESTING:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production" if not DEBUG else "development",
    )

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
if DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {"console": {"class": "logging.StreamHandler"}},
        "root": {"handlers": ["console"], "level": "DEBUG"},
        "loggers": {
            "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "django.db.backends": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        },
    }
else:
    import os as _os

    _LOG_DIR = "/var/log/unitur"
    _file_handlers_available = _os.path.isdir(_LOG_DIR) and _os.access(_LOG_DIR, _os.W_OK)

    _handlers = {"console": {"class": "logging.StreamHandler", "formatter": "verbose"}}
    _django_handlers = ["console"]
    _dashboard_handlers = ["console"]

    if _file_handlers_available:
        _handlers["file_error"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{_LOG_DIR}/error.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "level": "ERROR",
        }
        _handlers["file_dashboard"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": f"{_LOG_DIR}/dashboard.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "simple",
        }
        _django_handlers.append("file_error")
        _dashboard_handlers.append("file_dashboard")

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {"format": "{levelname} {asctime} {module} {process:d} {message}", "style": "{"},
            "simple": {"format": "{levelname} {asctime} {message}", "style": "{"},
        },
        "handlers": _handlers,
        "root": {"handlers": ["console"], "level": "WARNING"},
        "loggers": {
            "django": {"handlers": _django_handlers, "level": "WARNING", "propagate": False},
            "dashboard": {"handlers": _dashboard_handlers, "level": "INFO", "propagate": False},
        },
    }
