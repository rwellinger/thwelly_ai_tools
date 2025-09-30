"""
Flask Server Starter (DEVELOPMENT)
"""
from api.app import create_app
from config.settings import FLASK_SERVER_PORT, FLASK_SERVER_HOST, DEBUG, LOG_LEVEL
from utils.logger import logger, LoguruHandler
from pathlib import Path
import tomli
import logging

try:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    version = pyproject_data.get("project", {}).get("version", "unknown")
except Exception:
    version = "unknown"

if __name__ == '__main__':
    app = create_app()

    flask_logger = logging.getLogger("werkzeug")
    flask_logger.handlers = [LoguruHandler()]
    flask_logger.setLevel(LOG_LEVEL)

    logger.info("*** AIPROXYSRV SERVER STARTED ***")
    logger.info(f"*** Version: {version} ***")

    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT, debug=DEBUG)
