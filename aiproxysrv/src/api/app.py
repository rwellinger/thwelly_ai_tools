"""
Flask App mit allen Blueprints + OpenAPI/Swagger Integration
"""
import sys
import traceback
import yaml
from flask import Flask, jsonify, Blueprint, render_template_string, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from apispec import APISpec
from .routes.image_routes import api_image_v1
from .routes.song_routes import api_song_v1, api_song_task_v1
from .routes.instrumental_routes import api_instrumental_v1, api_instrumental_task_v1
from .routes.redis_routes import api_redis_v1
from .routes.chat_routes import api_chat_v1
from .routes.prompt_routes import api_prompt_v1
from .routes.user_routes import api_user_v1


def create_app():
    """Flask App Factory with OpenAPI/Swagger Integration"""
    app = Flask(__name__)

    # Add ProxyFix middleware to handle reverse proxy headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    # Monkey patch json.dumps to handle ValueError serialization globally
    import json
    original_dumps = json.dumps

    def patched_dumps(obj, **kwargs):
        try:
            return original_dumps(obj, **kwargs)
        except TypeError as e:
            if "ValueError" in str(e) and "not JSON serializable" in str(e):
                # Convert ValueError objects to strings recursively
                def convert_valueerrors(o):
                    if isinstance(o, ValueError):
                        return str(o)
                    elif isinstance(o, dict):
                        return {k: convert_valueerrors(v) for k, v in o.items()}
                    elif isinstance(o, list):
                        return [convert_valueerrors(item) for item in o]
                    return o

                converted_obj = convert_valueerrors(obj)
                return original_dumps(converted_obj, **kwargs)
            raise e

    # Replace json.dumps globally
    json.dumps = patched_dumps

    # Configure CORS to allow requests from Angular frontend
    CORS(app,
         origins="*",
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # OpenAPI/Swagger Configuration
    spec = APISpec(
        title='thWellys AI-Proxy API',
        version='1.5.2',
        openapi_version='3.0.2',
        info=dict(
            description='API für AI-Services: Bildgenerierung, Musikgenerierung und Chat-Integration',
            contact=dict(name='Rob'),
            email=dict(name='rob.wellinger@gmail.com'),
        ),
        servers=[
            dict(url='http://localhost:5050/api/v1', description='Development Server')
        ]
    )

    # Global API Blueprint
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

    @api_v1.route("/health")
    def health():
        """Health check endpoint"""
        from schemas.common_schemas import HealthResponse
        response = HealthResponse()
        return jsonify(response.model_dump()), 200

    @app.route("/api/openapi.json")
    def openapi_spec():
        """OpenAPI JSON specification endpoint"""
        try:
            # Import and register schemas
            from schemas.image_schemas import (
                ImageGenerateRequest, ImageResponse, ImageGenerateResponse,
                ImageListRequest, ImageListResponse, ImageUpdateRequest,
                ImageUpdateResponse, ImageDeleteResponse
            )
            from schemas.song_schemas import (
                SongGenerateRequest, SongResponse, SongGenerateResponse,
                SongListRequest, SongListResponse, SongUpdateRequest, SongUpdateResponse,
                StemGenerateRequest, StemGenerateResponse, SongHealthResponse,
                SongTaskStatusResponse, SongDeleteResponse, ChoiceRatingUpdateRequest,
                ChoiceRatingUpdateResponse, MurekaAccountResponse, CeleryHealthResponse,
                SongJobInfoResponse, ForceCompleteResponse, QueueStatusResponse, TaskCancelResponse,
                InstrumentalGenerateRequest, InstrumentalGenerateResponse
            )
            from schemas.chat_schemas import ChatRequest, ChatResponse
            from schemas.prompt_schemas import (
                PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateResponse,
                PromptTemplateListResponse, PromptCategoryResponse, PromptTemplatesGroupedResponse
            )
            from schemas.common_schemas import (
                ErrorResponse, HealthResponse, BulkDeleteRequest, BulkDeleteResponse,
                RedisTaskResponse, RedisTaskListResponse, RedisKeyListResponse
            )
            from schemas.user_schemas import (
                UserCreateRequest, UserCreateResponse, LoginRequest, LoginResponse,
                UserUpdateRequest, UserUpdateResponse, PasswordChangeRequest, PasswordChangeResponse,
                PasswordResetRequest, PasswordResetResponse, UserResponse, UserListResponse,
                LogoutResponse, TokenValidationResponse
            )

            # Register schemas with APISpec (only if not already registered)
            schemas_to_register = [
                # Image schemas
                ("ImageGenerateRequest", ImageGenerateRequest),
                ("ImageResponse", ImageResponse),
                ("ImageGenerateResponse", ImageGenerateResponse),
                ("ImageListRequest", ImageListRequest),
                ("ImageListResponse", ImageListResponse),
                ("ImageUpdateRequest", ImageUpdateRequest),
                ("ImageUpdateResponse", ImageUpdateResponse),
                ("ImageDeleteResponse", ImageDeleteResponse),
                # Song schemas
                ("SongGenerateRequest", SongGenerateRequest),
                ("SongResponse", SongResponse),
                ("SongGenerateResponse", SongGenerateResponse),
                ("SongListRequest", SongListRequest),
                ("SongListResponse", SongListResponse),
                ("SongUpdateRequest", SongUpdateRequest),
                ("SongUpdateResponse", SongUpdateResponse),
                ("StemGenerateRequest", StemGenerateRequest),
                ("StemGenerateResponse", StemGenerateResponse),
                ("SongHealthResponse", SongHealthResponse),
                ("SongTaskStatusResponse", SongTaskStatusResponse),
                ("SongDeleteResponse", SongDeleteResponse),
                ("ChoiceRatingUpdateRequest", ChoiceRatingUpdateRequest),
                ("ChoiceRatingUpdateResponse", ChoiceRatingUpdateResponse),
                ("MurekaAccountResponse", MurekaAccountResponse),
                ("CeleryHealthResponse", CeleryHealthResponse),
                ("SongJobInfoResponse", SongJobInfoResponse),
                ("ForceCompleteResponse", ForceCompleteResponse),
                ("QueueStatusResponse", QueueStatusResponse),
                ("TaskCancelResponse", TaskCancelResponse),
                # Instrumental schemas
                ("InstrumentalGenerateRequest", InstrumentalGenerateRequest),
                ("InstrumentalGenerateResponse", InstrumentalGenerateResponse),
                # Chat schemas
                ("ChatRequest", ChatRequest),
                ("ChatResponse", ChatResponse),
                # Prompt schemas
                ("PromptTemplateCreate", PromptTemplateCreate),
                ("PromptTemplateUpdate", PromptTemplateUpdate),
                ("PromptTemplateResponse", PromptTemplateResponse),
                ("PromptTemplateListResponse", PromptTemplateListResponse),
                ("PromptCategoryResponse", PromptCategoryResponse),
                ("PromptTemplatesGroupedResponse", PromptTemplatesGroupedResponse),
                # Common schemas
                ("ErrorResponse", ErrorResponse),
                ("HealthResponse", HealthResponse),
                ("BulkDeleteRequest", BulkDeleteRequest),
                ("BulkDeleteResponse", BulkDeleteResponse),
                ("RedisTaskResponse", RedisTaskResponse),
                ("RedisTaskListResponse", RedisTaskListResponse),
                ("RedisKeyListResponse", RedisKeyListResponse),
                # User schemas
                ("UserCreateRequest", UserCreateRequest),
                ("UserCreateResponse", UserCreateResponse),
                ("LoginRequest", LoginRequest),
                ("LoginResponse", LoginResponse),
                ("UserUpdateRequest", UserUpdateRequest),
                ("UserUpdateResponse", UserUpdateResponse),
                ("PasswordChangeRequest", PasswordChangeRequest),
                ("PasswordChangeResponse", PasswordChangeResponse),
                ("PasswordResetRequest", PasswordResetRequest),
                ("PasswordResetResponse", PasswordResetResponse),
                ("UserResponse", UserResponse),
                ("UserListResponse", UserListResponse),
                ("LogoutResponse", LogoutResponse),
                ("TokenValidationResponse", TokenValidationResponse),
            ]

            # Only register schemas that aren't already registered
            for schema_name, schema_class in schemas_to_register:
                try:
                    spec.components.schema(schema_name, schema=schema_class)
                except Exception:
                    # Schema already registered, skip
                    pass

            # Automatic route discovery and OpenAPI generation
            def generate_paths_from_routes():
                """Automatically generate OpenAPI paths from Flask routes"""
                import inspect

                # Tag mapping for cleaner organization
                tag_mapping = {
                    'api_image_v1': 'Images',
                    'api_song_v1': 'Songs',
                    'api_song_task_v1': 'Song Tasks',
                    'api_instrumental_v1': 'Instrumentals',
                    'api_instrumental_task_v1': 'Instrumental Tasks',
                    'api_prompt_v1': 'Prompt Templates',
                    'api_redis_v1': 'Redis/Celery',
                    'api_chat_v1': 'Chat',
                    'api_user_v1': 'User Management',
                    'api_v1': 'System'
                }

                current_paths = set(spec.to_dict().get('paths', {}).keys())

                for rule in app.url_map.iter_rules():
                    # Only process API routes
                    if not rule.endpoint.startswith(('api_image_v1', 'api_song_v1', 'api_instrumental_v1', 'api_instrumental_task_v1', 'api_prompt_v1', 'api_redis_v1', 'api_chat_v1', 'api_user_v1', 'api_v1')):
                        continue

                    # Skip if already added
                    route_path = rule.rule.replace('/api/v1', '')
                    if route_path in current_paths:
                        continue

                    try:
                        # Get the view function
                        view_func = app.view_functions.get(rule.endpoint)
                        if not view_func:
                            continue

                        # Extract blueprint name for tagging
                        blueprint_name = rule.endpoint.split('.')[0] if '.' in rule.endpoint else rule.endpoint.split('_')[0] + '_' + rule.endpoint.split('_')[1] + '_v1'
                        tag = tag_mapping.get(blueprint_name, 'API')

                        # Get function signature for parameter detection
                        sig = inspect.signature(view_func)

                        # Build operations for each HTTP method
                        operations = {}
                        for method in rule.methods:
                            if method in ['OPTIONS', 'HEAD']:
                                continue

                            operation = {
                                "tags": [tag],
                                "summary": (view_func.__doc__ or f"{method} {route_path}").strip(),
                                "description": view_func.__doc__ or f"API endpoint for {route_path}",
                                "responses": {
                                    "200": {
                                        "description": "Success",
                                        "content": {
                                            "application/json": {
                                                "schema": {"type": "object"}
                                            }
                                        }
                                    },
                                    "400": {
                                        "description": "Bad Request",
                                        "content": {
                                            "application/json": {
                                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                            }
                                        }
                                    }
                                }
                            }

                            # Add request body for POST/PUT methods with Pydantic models
                            if method.lower() in ['post', 'put']:
                                # Try to detect Pydantic model from function signature
                                for param_name, param in sig.parameters.items():
                                    if param_name == 'body' and hasattr(param.annotation, '__name__'):
                                        schema_name = param.annotation.__name__
                                        operation["requestBody"] = {
                                            "required": True,
                                            "content": {
                                                "application/json": {
                                                    "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                                                }
                                            }
                                        }
                                        break

                            # Add path parameters
                            if '<' in rule.rule:
                                operation["parameters"] = []
                                for arg in rule.arguments:
                                    # noinspection PyTypeChecker
                                    operation["parameters"].append({
                                        "name": arg,
                                        "in": "path",
                                        "required": True,
                                        "schema": {"type": "string"},
                                        "description": f"Path parameter: {arg}"
                                    })

                            operations[method.lower()] = operation

                        # Add path to spec
                        if operations:
                            spec.path(path=route_path, operations=operations)

                    except Exception as e:
                        # Skip problematic routes
                        print(f"Warning: Could not process route {rule.rule}: {e}", file=sys.stderr)
                        continue

            # Generate all paths automatically
            generate_paths_from_routes()

            return jsonify(spec.to_dict())
        except Exception as e:
            print(f"OpenAPI spec error: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return jsonify({"error": f"OpenAPI generation failed: {str(e)}"}), 500

    @app.route("/api/openapi.yaml")
    def openapi_spec_yaml():
        """OpenAPI YAML specification endpoint"""
        try:
            # Get the JSON spec
            from flask import url_for, request
            with app.test_request_context():
                json_response = openapi_spec()
                if json_response.status_code != 200:
                    return json_response

                openapi_dict = json_response.get_json()
                yaml_content = yaml.dump(openapi_dict, default_flow_style=False, allow_unicode=True)

                return Response(
                    yaml_content,
                    mimetype='application/x-yaml',
                    headers={'Content-Disposition': 'inline; filename="openapi.yaml"'}
                )
        except Exception as e:
            print(f"OpenAPI YAML spec error: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return jsonify({"error": f"OpenAPI YAML generation failed: {str(e)}"}), 500

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
                    ]
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

    # Add specific Pydantic ValidationError handler
    from pydantic import ValidationError

    @app.errorhandler(ValidationError)
    def handle_pydantic_validation_error(error):
        """Handle Pydantic validation errors with HTTP 400"""
        print(f"Pydantic ValidationError: {error}", file=sys.stderr)

        # Extract field-specific error messages
        error_details = []
        for err in error.errors():
            field = '.'.join(str(x) for x in err['loc'])
            message = err['msg']
            error_details.append(f"{field}: {message}")

        error_message = "; ".join(error_details) if error_details else str(error)
        return jsonify({
            "error": error_message,
            "validation_errors": error.errors()
        }), 400

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError from Pydantic validators with HTTP 400"""
        error_str = str(error)

        # Check if this is likely a validation error from our Pydantic validators
        validation_keywords = ['must be one of', 'must be a valid', 'must be either', 'Field required']
        if any(keyword in error_str for keyword in validation_keywords):
            print(f"Pydantic Validator ValueError: {error}", file=sys.stderr)
            return jsonify({"error": error_str}), 400

        # For other ValueErrors, fall back to 500
        print(f"General ValueError: {error}", file=sys.stderr)
        return jsonify({"error": "An unexpected error occurred"}), 500

    @app.errorhandler(Exception)
    def handle_general_exception(error):
        """Handle all other exceptions with HTTP 500"""
        print(f"Unhandled Exception: {type(error).__name__}: {error}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({"error": "An unexpected error occurred"}), 500

    # Register Blueprints
    app.register_blueprint(api_v1)
    app.register_blueprint(api_image_v1)
    app.register_blueprint(api_song_v1)
    app.register_blueprint(api_song_task_v1)
    app.register_blueprint(api_instrumental_v1)
    app.register_blueprint(api_instrumental_task_v1)
    app.register_blueprint(api_redis_v1)
    app.register_blueprint(api_chat_v1)
    app.register_blueprint(api_prompt_v1)
    app.register_blueprint(api_user_v1)

    return app
