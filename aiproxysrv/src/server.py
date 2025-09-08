"""
Flask Server Starter
"""
import sys
from api.app import create_app
from config.settings import OPENAI_PORT, OPENAI_HOST, DEBUG, MUREKA_BILLING_URL

if __name__ == '__main__':
    app = create_app()

    print(f"Flask-Server läuft auf http://{OPENAI_HOST}:{OPENAI_PORT}", file=sys.stderr)
    print(f"MUREKA Billing: {MUREKA_BILLING_URL}", file=sys.stderr)

    app.run(host=OPENAI_HOST, port=OPENAI_PORT, debug=DEBUG)
