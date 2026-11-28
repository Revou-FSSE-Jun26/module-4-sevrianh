"""Flask application factory."""
import time

from flask import Flask, g

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

    @app.before_request
    def start_server_timer() -> None:
        g.server_request_started_at = time.perf_counter()

    @app.after_request
    def add_server_duration(response):
        started_at = getattr(g, 'server_request_started_at', None)
        if started_at is not None:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            response.headers['X-Server-Duration-Ms'] = f'{elapsed_ms:.3f}'
        return response

    register_blueprints(app)
    app.register_blueprint(health_bp)
    register_error_handlers(app)
    return app


def register_blueprints(app: Flask) -> None:
    """Register the eight feature Blueprints exactly once."""
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.auth import auth_bp
    from app.blueprints.boards import boards_bp
    from app.blueprints.cards import cards_bp
    from app.blueprints.columns import columns_bp
    from app.blueprints.comments import comments_bp
    from app.blueprints.notifications import notifications_bp
    from app.blueprints.users import users_bp

    app.register_blueprint(analytics_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(cards_bp)
    app.register_blueprint(columns_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(users_bp)
