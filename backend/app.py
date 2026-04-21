from flask import Flask, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from database.db import db
from extensions import limiter
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.delivery_routes import delivery_bp
from routes.order_routes import order_bp
from routes.product_routes import product_bp
from utils.logging_helper import configure_logging, register_request_logging
from utils.response_helper import register_error_handlers, success_response


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(delivery_bp)


def register_frontend_routes(app):
    @app.get("/")
    def serve_index():
        return send_from_directory(str(app.config["FRONTEND_PAGES_DIR"]), "index.html")

    @app.get("/student")
    def serve_student():
        return send_from_directory(str(app.config["FRONTEND_PAGES_DIR"]), "student.html")

    @app.get("/admin")
    def serve_admin():
        return send_from_directory(str(app.config["FRONTEND_PAGES_DIR"]), "admin.html")

    @app.get("/delivery")
    def serve_delivery():
        return send_from_directory(str(app.config["FRONTEND_PAGES_DIR"]), "delivery.html")

    @app.get("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(str(app.config["FRONTEND_CSS_DIR"]), filename)

    @app.get("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(str(app.config["FRONTEND_JS_DIR"]), filename)

    @app.get("/assets/<path:filename>")
    def serve_assets(filename):
        return send_from_directory(str(app.config["FRONTEND_ASSETS_DIR"]), filename)

    @app.get("/uploads/products/<path:filename>")
    def serve_product_uploads(filename):
        return send_from_directory(str(app.config["UPLOAD_DIR"]), filename)

    @app.get("/health")
    def healthcheck():
        return success_response("ZestMart API is healthy.", {"status": "ok"})


def create_app():
    Config.ensure_directories()
    Config.validate_runtime_settings()
    configure_logging(Config.LOG_LEVEL)

    app = Flask(__name__)
    app.config.from_object(Config)
    app.json.sort_keys = False
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=app.config["TRUST_PROXY_COUNT"],
        x_proto=app.config["TRUST_PROXY_COUNT"],
        x_host=app.config["TRUST_PROXY_COUNT"],
        x_port=app.config["TRUST_PROXY_COUNT"],
    )

    CORS(
        app,
        resources={r"/*": {"origins": list(app.config["CORS_ORIGINS"])}},
        supports_credentials=True,
    )
    db.init_app(app)
    limiter.init_app(app)
    register_error_handlers(app)
    register_request_logging(app)
    register_blueprints(app)
    register_frontend_routes(app)

    return app


app = create_app()
