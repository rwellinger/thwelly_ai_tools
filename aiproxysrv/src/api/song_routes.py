"""
Song Generation Routes mit MUREKA
"""
from flask import Blueprint, request, jsonify
from api.controllers.song_controller import SongController

api_song_v1 = Blueprint("api_song_v1", __name__, url_prefix="/api/v1/song")

# Controller instance
song_controller = SongController()

@api_song_v1.route("/celery-health", methods=["GET"])
def celery_health():
    """Überprüft Celery Worker Status"""
    response_data, status_code = song_controller.get_celery_health()
    return jsonify(response_data), status_code


@api_song_v1.route("/mureka-account", methods=["GET"])
def mureka_account():
    """Abfrage der MUREKA Account-Informationen"""
    response_data, status_code = song_controller.get_mureka_account()
    return jsonify(response_data), status_code


@api_song_v1.route("/generate", methods=["POST"])
def song_generate():
    """Startet Song-Generierung"""
    payload = request.get_json(force=True)
    
    response_data, status_code = song_controller.generate_song(
        payload=payload,
        host_url=request.host_url
    )
    
    return jsonify(response_data), status_code



@api_song_v1.route("/stem/generate", methods=["POST"])
def stems_generator():
    """Erstelle stems anhand einer MP3"""
    payload = request.get_json(force=True)
    
    response_data, status_code = song_controller.generate_stems(payload)
    
    return jsonify(response_data), status_code


@api_song_v1.route("/query/<job_id>", methods=["GET"])
def song_info(job_id):
    """Get Song structure direct from MUREKA again who was generated successfully"""
    response_data, status_code = song_controller.get_song_info(job_id)
    
    return jsonify(response_data), status_code


@api_song_v1.route("/force-complete/<job_id>", methods=["POST"])
def force_complete_task(job_id):
    """Erzwingt Completion eines Tasks"""
    response_data, status_code = song_controller.force_complete_task(job_id)
    
    return jsonify(response_data), status_code


@api_song_v1.route("/list", methods=["GET"])
def list_songs():
    """Get list of songs with pagination, search and sorting"""
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
    status = request.args.get('status', None)  # Optional status filter
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_direction = request.args.get('sort_direction', 'desc')
    workflow = request.args.get('workflow', None)  # Optional workflow filter

    # Validate sort parameters
    valid_sort_fields = ['created_at', 'title', 'lyrics']
    if sort_by not in valid_sort_fields:
        return jsonify({"error": f"Invalid sort_by field. Must be one of: {valid_sort_fields}"}), 400

    if sort_direction not in ['asc', 'desc']:
        return jsonify({"error": "Invalid sort_direction. Must be 'asc' or 'desc'"}), 400

    response_data, status_code = song_controller.get_songs(
        limit=limit,
        offset=offset,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_direction=sort_direction,
        workflow=workflow
    )

    return jsonify(response_data), status_code


@api_song_v1.route("/id/<song_id>", methods=["GET"])
def get_song(song_id):
    """Get single song by ID with all choices"""
    response_data, status_code = song_controller.get_song_by_id(song_id)

    return jsonify(response_data), status_code


@api_song_v1.route("/id/<song_id>", methods=["PUT"])
def update_song(song_id):
    """Update song by ID"""
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "No data provided"}), 400

    response_data, status_code = song_controller.update_song(song_id, payload)

    return jsonify(response_data), status_code


@api_song_v1.route("/id/<song_id>", methods=["DELETE"])
def delete_song(song_id):
    """Delete song by ID including all choices"""
    response_data, status_code = song_controller.delete_song(song_id)

    return jsonify(response_data), status_code


@api_song_v1.route("/bulk-delete", methods=["DELETE"])
def bulk_delete_songs():
    """Delete multiple songs by IDs"""
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "No JSON provided"}), 400

    song_ids = payload.get('ids', [])

    if not isinstance(song_ids, list):
        return jsonify({"error": "ids must be an array"}), 400

    response_data, status_code = song_controller.bulk_delete_songs(song_ids)

    return jsonify(response_data), status_code


@api_song_v1.route("/choice/<choice_id>/rating", methods=["PUT"])
def update_choice_rating(choice_id):
    """Update rating for a specific song choice"""
    payload = request.get_json(force=True)

    if not payload:
        return jsonify({"error": "No data provided"}), 400

    response_data, status_code = song_controller.update_choice_rating(choice_id, payload)

    return jsonify(response_data), status_code


api_song_task_v1 = Blueprint("api_song_task_v1", __name__, url_prefix="/api/v1/song/task")

@api_song_task_v1.route("/status/<task_id>", methods=["GET"])
def song_status(task_id):
    """Überprüft Status einer Song-Generierung"""
    response_data, status_code = song_controller.get_song_status(task_id)
    
    return jsonify(response_data), status_code


@api_song_task_v1.route("/cancel/<task_id>", methods=["POST"])
def cancel_task(task_id):
    """Cancelt einen Task"""
    response_data, status_code = song_controller.cancel_task(task_id)
    
    return jsonify(response_data), status_code


@api_song_task_v1.route("/delete/<task_id>", methods=["DELETE"])
def delete_task_result(task_id):
    """Löscht Task-Ergebnis"""
    response_data, status_code = song_controller.delete_task_result(task_id)
    
    return jsonify(response_data), status_code


@api_song_task_v1.route("/queue-status", methods=["GET"])
def queue_status():
    """Gibt Queue-Status zurück"""
    response_data, status_code = song_controller.get_queue_status()
    
    return jsonify(response_data), status_code
