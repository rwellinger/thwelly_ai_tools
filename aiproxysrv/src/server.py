"""
Flask Server Starter
"""
import sys
from api.app import create_app
from config.settings import FLASK_SERVER_PORT, FLASK_SERVER_HOST, DEBUG, MUREKA_BILLING_URL

if __name__ == '__main__':
    app = create_app()

    print(f"Flask-Server läuft auf http://{FLASK_SERVER_HOST}:{FLASK_SERVER_PORT}", file=sys.stderr)
    print(f"MUREKA Billing: {MUREKA_BILLING_URL}", file=sys.stderr)

    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT, debug=DEBUG)
