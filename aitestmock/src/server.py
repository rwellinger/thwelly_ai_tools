from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from pathlib import Path

from api.openai import openai_routes
from api.mureka import mureka_routes
from api.chat import api_chat_mock
import logging
import tomli

from config.settings import LOG_LEVEL
from utils.logger import logger, LoguruHandler


try:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    version = pyproject_data.get("project", {}).get("version", "unknown")
except Exception:
    version = "unknown"


def create_app():
    load_dotenv()

    # Set static folder to absolute path
    static_folder = Path(__file__).parent.parent / 'static'
    app = Flask(__name__, static_folder=str(static_folder), static_url_path='/static')
    CORS(app)

    app.config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'

    app.register_blueprint(openai_routes, url_prefix='/v1')
    app.register_blueprint(mureka_routes, url_prefix='/v1')
    app.register_blueprint(api_chat_mock)

    @app.route('/health')
    def health():
        return {'status': 'ok'}


    return app


def main():
    app = create_app()

    # Set rewrite internal logger
    flask_logger = logging.getLogger("werkzeug")
    flask_logger.handlers = [LoguruHandler()]
    flask_logger.setLevel(LOG_LEVEL)

    logger.info("*** AITESTMOCK STARTED ***")
    logger.info(f"*** Version: {version} ***")

    app.run(host='0.0.0.0', port=3080, debug=app.config['DEBUG'])


if __name__ == '__main__':
    main()