"""Flask application factory."""
from flask import Flask

from app.config import Config
from app.error_handlers import register_error_handlers
from app.extensions import cors, db, jwt, migrate
from app.health import health_bp
from app.logging_config import configure_logging


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    configure_logging()
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}})

    register_blueprints(app)
    app.register_blueprint(health_bp)
    register_error_handlers(app)
    return app


def register_blueprints(app: Flask) -> None:
    """Feature Blueprint registration point; filled in by task 14.1."""
