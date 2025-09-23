"""
Flask App mit allen Blueprints + OpenAPI/Swagger Integration
"""
import sys
import traceback
from flask import Flask, jsonify, Blueprint, render_template_string
from flask_cors import CORS
from apispec import APISpec
from .image_routes import api_image_v1
from .song_routes import api_song_v1, api_song_task_v1
from .redis_routes import api_redis_v1
from .chat_routes import api_chat_v1
from .prompt_routes import api_prompt_v1


def create_app():
    """Flask App Factory with OpenAPI/Swagger Integration"""
    app = Flask(__name__)

    # Configure CORS to allow requests from Angular frontend
    CORS(app,
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # OpenAPI/Swagger Configuration
    spec = APISpec(
        title='AI Proxy Service API',
        version='1.3.0',
        openapi_version='3.0.2',
        info=dict(
            description='API für AI-Services: Bildgenerierung, Musikgenerierung und Chat-Integration',
            contact=dict(name='Rob'),
            license=dict(name='MIT')
        ),
        servers=[
            dict(url='http://localhost:8000/api/v1', description='Development Server'),
            dict(url='/api/v1', description='Production Server (relative)')
        ]
    )

    # Global API Blueprint
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @api_v1.route("/health")
    def health():
        """Health check endpoint"""
        from schemas.common_schemas import HealthResponse
        response = HealthResponse()
        return jsonify(response.dict()), 200

    @app.route("/api/openapi.json")
    def openapi_spec():
        """OpenAPI JSON specification endpoint"""
        return jsonify(spec.to_dict())

    @app.route("/api/docs/")
    def swagger_ui():
        """Swagger UI endpoint"""
        swagger_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Proxy Service API Documentation</title>
            <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        </head>
        <body>
            <div id="swagger-ui"></div>
            <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
            <script>
                SwaggerUIBundle({
                    url: '/api/openapi.json',
                    dom_id: '#swagger-ui',
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIBundle.presets.standalone
                    ],
                    layout: "StandaloneLayout"
                });
            </script>
        </body>
        </html>
        """
        return swagger_html

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
