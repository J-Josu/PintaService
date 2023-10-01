from flask import Flask, render_template, request
from werkzeug import exceptions

from src.core import config, csrf, db, seed
from src.services.site import SiteService


def create_app(env: str = "development", static_folder: str = "../../static"):
    app = Flask(
        __name__, static_folder=static_folder, template_folder="./templates"
    )

    config.init_app(app, env)
    db.init_app(app)
    csrf.init_app(app)

    from src.web.controllers import blueprints

    for bp in blueprints:
        app.register_blueprint(bp)

    @app.before_request
    def hook():
        if (
            not SiteService.maintenance_active()
            or request.path.startswith("/api")
            or request.args.get("maintenance") != "true"
        ):
            return None

        if request.method == "GET" and (
            request.path.startswith("/login")
            or request.path.startswith("/static")
        ):
            return None

        return (
            render_template(
                "maintenance.html",
                maintenance_message=SiteService.maintenance_message(),
            ),
            503,
        )

    @app.errorhandler(404)
    def page_not_found(error: exceptions.NotFound):
        return (
            render_template(
                "error.html",
                error_code="404",
                error_message="Página no encontrada",
            ),
            404,
        )

    @app.cli.command("reset_db")
    def reset_db():
        """
        Reset the database.
        Clear all tables and create them again.
        """
        db.reset_db()

    @app.cli.command("seed_db")
    def seed_db():
        """
        Seed the database.
        """
        seed.seed_db()

    return app
