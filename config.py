"""Application configuration.

cPanel / Phusion Passenger compatible:
- All secrets come from environment variables (set in Setup Python App or .env*..)
- DATABASE_URL points at MySQL in production; falls back to SQLite locally..
- No long-running processes are started by this module; Passenger owns the process lifecycle..
"""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:
    """Base configuration shared by all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _bool(os.environ.get("SESSION_COOKIE_SECURE", "1"))
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB - 3D models can be large
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        os.path.join(BASE_DIR, "static", "uploads"),
    )
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "avif", "svg"}
    ALLOWED_MEDIA_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "avif", "svg", "glb", "gltf", "bin", "mp4", "webm", "pdf", "zip"}

    # Email (SMTP) — configurable via env, no credentials hard-coded..
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@nirmalrugs.com")
    SMTP_USE_TLS = _bool(os.environ.get("SMTP_USE_TLS", "1"))
    SMTP_USE_SSL = _bool(os.environ.get("SMTP_USE_SSL", "0"))
    MAIL_SUBJECT_PREFIX = os.environ.get("MAIL_SUBJECT_PREFIX", "[Nirmal Rugs] ")

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "change-me")

    # cPanel-friendly toggles
    PREFERRED_URL_SCHEME = os.environ.get("PREFERRED_URL_SCHEME", "https")
    SERVER_NAME = os.environ.get("SERVER_NAME", None)
    SESSION_COOKIE_DOMAIN = os.environ.get("SESSION_COOKIE_DOMAIN", None)


class ProductionConfig(Config):
    """Explicit production config - fails safe when secrets are missing."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY must be set in production. Set it in Setup Python App or .env.")


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


def get_config():
    env = os.environ.get("FLASK_ENV", "development").lower()
    if env == "production":
        return ProductionConfig
    return DevelopmentConfig
