"""
Flask Server Starter
"""
from api.app import create_app
from config.settings import FLASK_SERVER_PORT, FLASK_SERVER_HOST, DEBUG

if __name__ == '__main__':
    app = create_app()
    app.run(host=FLASK_SERVER_HOST, port=FLASK_SERVER_PORT, debug=DEBUG)
