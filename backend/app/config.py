"""Application configuration, read from environment variables (TC-09)."""
import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _parse_origins(value: str) -> list[str]:
    """Split a comma-separated CORS_ORIGINS value; a wildcard is never allowed."""
    origins = [item.strip() for item in value.split(',') if item.strip()]
    return [origin for origin in origins if origin != '*']


class Config:
    FLASK_APP = os.environ.get('FLASK_APP', 'app:create_app()')
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', '')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=60)
    CORS_ORIGINS = _parse_origins(os.environ.get('CORS_ORIGINS', 'http://localhost:3000'))
