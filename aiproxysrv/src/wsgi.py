"""
WSGI Entry Point für Gunicorn
"""
from api.app import create_app

# Flask-App erstellen
app = create_app()

if __name__ == "__main__":
    # Fallback für direkten Python-Start (Development)
    import sys
    from config.settings import OPENAI_PORT, OPENAI_HOST, DEBUG, MUREKA_BILLING_URL

    print(f"Flask-Server läuft auf http://{OPENAI_HOST}:{OPENAI_PORT}", file=sys.stderr)
    print(f"MUREKA Billing: {MUREKA_BILLING_URL}", file=sys.stderr)

    app.run(host=OPENAI_HOST, port=OPENAI_PORT, debug=DEBUG)
