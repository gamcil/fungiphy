import os

from dotenv import load_dotenv
from flask import Flask

from fungphy.database import session


__version__ = "0.0.1"


def create_app():
    app = Flask(__name__)
    app.secret_key = "secret key"

    from fungphy.views import view
    app.register_blueprint(view)

    from fungphy.admin import admin
    admin.init_app(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()

    return app
