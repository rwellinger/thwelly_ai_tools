"""
DALL-E Image Generation Routes with Pydantic validation
"""
import sys
import traceback
from flask import Blueprint, request, jsonify, send_from_directory
from flask_pydantic import validate
from config.settings import IMAGES_DIR
from api.controllers.image_controller import ImageController
from api.auth_middleware import jwt_required
from schemas.image_schemas import (
    ImageGenerateRequest, ImageGenerateResponse,
    ImageListRequest, ImageListResponse,
    ImageUpdateRequest, ImageUpdateResponse,
    ImageDeleteResponse
)
from schemas.common_schemas import ErrorResponse

api_image_v1 = Blueprint("api_image_v1", __name__, url_prefix="/api/v1/image")

# Controller instance
image_controller = ImageController()

@api_image_v1.route('/generate', methods=['POST'])
@jwt_required
@validate()
def generate(body: ImageGenerateRequest):
    """Generate image with DALL-E"""
    try:
        response_data, status_code = image_controller.generate_image(
            prompt=body.prompt,
            size=body.size
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_image_v1.route('/list', methods=['GET'])
@jwt_required
@validate()
def list_images(query: ImageListRequest):
    """Get list of generated images with pagination, search and sorting"""
    try:
        response_data, status_code = image_controller.get_images(
            limit=query.limit,
            offset=query.offset,
            search=query.search,
            sort_by=query.sort,
            sort_direction=query.order
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500



@api_image_v1.route('/<path:filename>')
@jwt_required
def serve_image(filename):
    """Serve stored images"""
    try:
        print(f"Serving image: {filename}", file=sys.stderr)
        return send_from_directory(IMAGES_DIR, filename)
    except Exception as e:
        print(f"Error serving image {filename}: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        return jsonify({"error": "Image not found"}), 404


@api_image_v1.route('/id/<string:image_id>', methods=['GET'])
@jwt_required
def get_image(image_id):
    """Get single image by ID"""
    response_data, status_code = image_controller.get_image_by_id(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route('/id/<string:image_id>', methods=['DELETE'])
@jwt_required
def delete_image(image_id):
    """Delete image by ID"""
    response_data, status_code = image_controller.delete_image(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route('/bulk-delete', methods=['DELETE'])
@jwt_required
def bulk_delete_images():
    """Delete multiple images by IDs"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    image_ids = raw_json.get('ids', [])

    if not isinstance(image_ids, list):
        return jsonify({"error": "ids must be an array"}), 400

    response_data, status_code = image_controller.bulk_delete_images(image_ids)

    return jsonify(response_data), status_code


@api_image_v1.route('/id/<string:image_id>', methods=['PUT'])
@jwt_required
@validate()
def update_image_metadata(image_id: str, body: ImageUpdateRequest):
    """Update image metadata (title and/or tags)"""
    try:
        response_data, status_code = image_controller.update_image_metadata(
            image_id, body.title, body.tags
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500

