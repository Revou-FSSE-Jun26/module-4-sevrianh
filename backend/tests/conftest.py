"""Shared pytest setup. Environment defaults are set before `app.config` is imported."""
import os

os.environ.setdefault(
    'DATABASE_URL', 'postgresql+psycopg2://user:password@localhost:5432/sevy_test')
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-with-at-least-32-characters')
os.environ.setdefault('CORS_ORIGINS', 'http://localhost:3000')
