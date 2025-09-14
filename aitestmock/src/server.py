from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from pathlib import Path

from api.openai import openai_routes
from api.mureka import mureka_routes


def create_app():
    load_dotenv()

    # Set static folder to absolute path
    static_folder = Path(__file__).parent.parent / 'static'
    app = Flask(__name__, static_folder=str(static_folder), static_url_path='/static')
    CORS(app)

    app.config['DEBUG'] = os.getenv('DEBUG', 'false').lower() == 'true'

    app.register_blueprint(openai_routes, url_prefix='/v1')
    app.register_blueprint(mureka_routes, url_prefix='/v1')

    @app.route('/health')
    def health():
        return {'status': 'ok'}


    return app


def main():
    app = create_app()
    app.run(host='0.0.0.0', port=3080, debug=app.config['DEBUG'])


if __name__ == '__main__':
    main()