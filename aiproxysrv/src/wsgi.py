"""
WSGI Entry Point für Gunicorn
"""
import sys
import tomli
from pathlib import Path
from api.app import create_app

# Read version from pyproject.toml
try:
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomli.load(f)
    version = pyproject_data.get("project", {}).get("version", "unknown")
except Exception:
    version = "unknown"

# Flask-App erstellen
app = create_app()

# Worker startup message (wird in jedem Gunicorn Worker ausgeführt)
print("=" * 80, file=sys.stdout, flush=True)
print("*** AIPROXYSRV WORKER STARTED ***", file=sys.stdout, flush=True)
print(f"*** Version: {version} ***", file=sys.stdout, flush=True)
print("=" * 80, file=sys.stdout, flush=True)

if __name__ == "__main__":
    # Fallback für direkten Python-Start (Development)
    from config.settings import FLASK_SERVER_PORT, FLASK_SERVER_HOST, DEBUG
    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT, debug=DEBUG)
