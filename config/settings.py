import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.getenv("DJANGO_ENV", "development")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if ENVIRONMENT == "production" and not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required in production.")
if not SECRET_KEY:
    SECRET_KEY = "replace-this-in-development"

DEBUG = os.getenv("DJANGO_DEBUG", "1" if ENVIRONMENT != "production" else "0") == "1"
ALLOWED_HOSTS = [host for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "").split(",") if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if origin]
if ENVIRONMENT == "production" and DEBUG:
    raise ImproperlyConfigured("DJANGO_DEBUG must be disabled in production.")
if ENVIRONMENT == "production" and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required in production.")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "rest_framework", "accounts", "products", "inspections", "defects", "dashboard",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"

# SQLite enables a zero-configuration first run. Set DB_ENGINE=mysql and DB_* values for MariaDB/MySQL.
if os.getenv("DB_ENGINE", "sqlite") == "mysql":
    DATABASES = {"default": {"ENGINE": "django.db.backends.mysql", "NAME": os.environ["DB_NAME"], "USER": os.environ["DB_USER"], "PASSWORD": os.environ["DB_PASSWORD"], "HOST": os.getenv("DB_HOST", "127.0.0.1"), "PORT": os.getenv("DB_PORT", "3306"), "OPTIONS": {"charset": "utf8mb4"}}}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "zh-hant"
TIME_ZONE = "Asia/Taipei"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/admin/login/"
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"], "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication", "rest_framework.authentication.BasicAuthentication"]}
REST_FRAMEWORK["EXCEPTION_HANDLER"] = "config.api.qms_exception_handler"

if ENVIRONMENT == "production":
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = os.getenv("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
