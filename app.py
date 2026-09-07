"""Core application factory.

Registers blueprints, initialises extensions, exposes template globals
(theme CSS variables, site metadata, nav content) and registers CLI commands.
"""
import os

from flask import Flask, render_template, request, current_app
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import get_config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "admin.login"
login_manager.login_message = "Please sign in to access the admin area."


def create_app(config_class= None) -> Flask:
    if config_class is None:
        config_class = get_config()
    app = Flask(__name__, instance_relative_config= False)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok= True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "products"), exist_ok= True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "media"), exist_ok= True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "models"), exist_ok= True)
    os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "documents"), exist_ok= True)
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok= True)

    db.init_app(app)
    login_manager.init_app(app)

    # Template context to power the dynamic theme + navigation.
    @app.context_processor
    def inject_globals():
        from models import ThemeSettings, Page
        theme = ThemeSettings.get_active()
        nav_pages = Page.query.filter_by(in_navigation= True, is_published= True).order_by(Page.nav_order.asc()).all()
        return {
            "theme": theme,
            "nav_pages": nav_pages,
            "site_name": theme.site_name if theme and theme.site_name else "Nirmal Rugs",
            "google_fonts_url": _google_fonts_url(theme),
            "current_year": __import__("datetime").datetime.now().year,
        }

    @app.context_processor
    def inject_seo():
        from models import SEOSettings
        return {"seo": SEOSettings.get_active()}

    from blueprints.main import main_bp
    from blueprints.admin import admin_bp
    from blueprints.orders import orders_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    register_commands(app)
    register_error_handlers(app)

    return app


def _google_fonts_url(theme) -> str:
    """Build a Google Fonts URL from the theme's font choices(guarded)."""
    heading = getattr(theme, "heading_font", "Fraunces" if theme else "Fraunces") or "Fraunces"
    body = getattr(theme, "body_font", "Outfit" if theme else "Outfit") or "Outfit"
    fonts = {}
    for key, name in (("family", heading), ("family", body)):
        fonts.setdefault(name, []).append("400;500;600;700" if key == "family" else "300;400;500;600")
    parts = [f"family={name}:wght@{','.join(weights)}" for name, weights in fonts.items()]
    return "https://fonts.googleapis.com/css2?" + "&".join(parts) + "&display=swap"


def register_commands(app: Flask) -> None:
    from sqlalchemy import inspect

    @app.cli.command("init-db")
    def init_db():
        """Create all tables and seed default content."""
        import seed
        db.create_all()
        seed.run(app)
        print("Database initialised and seeded.")


def register_error_handlers(app: Flask) -> None:
    from models import Page

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback() if hasattr(db, "session") else None
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def too_large(e):
        return render_template("errors/413.html"), 413


@login_manager.user_loader
def load_user(user_id):
    from models import AdminUser
    return db.session.get(AdminUser, int(user_id))
