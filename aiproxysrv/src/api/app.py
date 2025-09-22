"""
Flask App mit allen Blueprints
"""
import sys
import traceback
from flask import Flask, jsonify, Blueprint
from flask_cors import CORS
from .image_routes import api_image_v1
from .song_routes import api_song_v1, api_song_task_v1
from .redis_routes import api_redis_v1
from .chat_routes import api_chat_v1
from .prompt_routes import api_prompt_v1


def create_app():
    """Flask App Factory"""
    app = Flask(__name__)
    
    # Configure CORS to allow requests from Angular frontend
    CORS(app,
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Global API Blueprint
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @api_v1.route("/health")
    def health():
        return jsonify(status="ok"), 200

    # Error Handler
    @app.errorhandler(404)
    def not_found(error):
        print(f"404 Error - Resource not found: {error}", file=sys.stderr)
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(429)
    def subscription_error(error):
        print(f"429 Error - Rate limit exceeded: {error}", file=sys.stderr)
        return jsonify({"error": str(error)}), 429

    @app.errorhandler(500)
    def internal_error(error):
        print(f"500 Error - Internal server error: {error}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        print(f"Unhandled Exception: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({"error": "An unexpected error occurred"}), 500

    # Register Blueprints
    app.register_blueprint(api_v1)
    app.register_blueprint(api_image_v1)
    app.register_blueprint(api_song_v1)
    app.register_blueprint(api_song_task_v1)
    app.register_blueprint(api_redis_v1)
    app.register_blueprint(api_chat_v1)
    app.register_blueprint(api_prompt_v1)

    return app
