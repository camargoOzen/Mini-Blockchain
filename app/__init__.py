from flask import Flask
import os

def create_app():
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')

    from .routes.main import main_bp
    from .routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app