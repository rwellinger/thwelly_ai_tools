"""
DALL-E Image Generation Routes - Clean version
"""
import sys
import traceback
from flask import Blueprint, request, jsonify, send_from_directory
from config.settings import IMAGES_DIR
from api.controllers.image_controller import ImageController

api_image_v1 = Blueprint("api_image_v1", __name__, url_prefix="/api/v1/image")

# Controller instance
image_controller = ImageController()

@api_image_v1.route('/generate', methods=['POST'])
def generate():
    """Generate image with DALL-E"""
    raw_json = request.get_json(silent=True)
    
    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400
    
    prompt = raw_json.get('prompt')
    size = raw_json.get('size')
    
    response_data, status_code = image_controller.generate_image(
        prompt=prompt,
        size=size,
        host_url=request.host_url
    )
    
    return jsonify(response_data), status_code


@api_image_v1.route('/list', methods=['GET'])
def list_images():
    """Get list of generated images with pagination, search and sorting"""
    # Parse query parameters
    try:
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        # Validate parameters
        if limit <= 0 or limit > 100:
            return jsonify({"error": "Limit must be between 1 and 100"}), 400
        if offset < 0:
            return jsonify({"error": "Offset must be >= 0"}), 400

    except ValueError:
        return jsonify({"error": "Invalid limit or offset parameter"}), 400

    # Parse search and sort parameters
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_direction = request.args.get('sort_direction', 'desc')

    # Validate sort parameters
    valid_sort_fields = ['created_at', 'title', 'prompt']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    response_data, status_code = image_controller.get_images(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction
    )

    return jsonify(response_data), status_code



@api_image_v1.route('/<path:filename>')
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
def get_image(image_id):
    """Get single image by ID"""
    response_data, status_code = image_controller.get_image_by_id(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route('/id/<string:image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete image by ID"""
    response_data, status_code = image_controller.delete_image(image_id)

    return jsonify(response_data), status_code


@api_image_v1.route('/bulk-delete', methods=['DELETE'])
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
def update_image_metadata(image_id):
    """Update image metadata (title and/or tags)"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    title = raw_json.get('title')
    tags = raw_json.get('tags')

    if title is None and tags is None:
        return jsonify({"error": "At least one field (title or tags) must be provided"}), 400

    response_data, status_code = image_controller.update_image_metadata(image_id, title, tags)

    return jsonify(response_data), status_code

