"""
WSGI Entry Point für Gunicorn
"""
from api.app import create_app

# Flask-App erstellen
app = create_app()

if __name__ == "__main__":
    # Fallback für direkten Python-Start (Development)
    from config.settings import FLASK_SERVER_PORT, FLASK_SERVER_HOST, DEBUG
    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT, debug=DEBUG)
