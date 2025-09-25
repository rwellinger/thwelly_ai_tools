"""
Instrumental Generation Routes mit MUREKA + Pydantic validation
"""
from flask import Blueprint, request, jsonify
from flask_pydantic import validate
from api.controllers.song_controller import SongController
from schemas.song_schemas import (
    InstrumentalGenerateRequest, InstrumentalGenerateResponse,
    SongHealthResponse
)
from schemas.common_schemas import ErrorResponse

api_instrumental_v1 = Blueprint("api_instrumental_v1", __name__, url_prefix="/api/v1/instrumental")

# Controller instance (reuse existing song controller)
song_controller = SongController()

@api_instrumental_v1.route("/generate", methods=["POST"])
@validate()
def instrumental_generate(body: InstrumentalGenerateRequest):
    """Startet Instrumental-Generierung"""
    try:
        # Convert Pydantic model to dict for controller
        payload = body.dict()

        # Add empty lyrics and mark as instrumental
        payload['lyrics'] = ""
        payload['is_instrumental'] = True

        response_data, status_code = song_controller.generate_instrumental(
            payload=payload,
            host_url=request.host_url
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ErrorResponse(error=str(e))
        return jsonify(error_response.dict()), 500


@api_instrumental_v1.route("/celery-health", methods=["GET"])
def celery_health():
    """Überprüft Celery Worker Status"""
    response_data, status_code = song_controller.get_celery_health()
    return jsonify(response_data), status_code


@api_instrumental_v1.route("/mureka-account", methods=["GET"])
def mureka_account():
    """Abfrage der MUREKA Account-Informationen"""
    response_data, status_code = song_controller.get_mureka_account()
    return jsonify(response_data), status_code


# Task routes (reuse existing ones with task_id)
api_instrumental_task_v1 = Blueprint("api_instrumental_task_v1", __name__, url_prefix="/api/v1/instrumental/task")

@api_instrumental_task_v1.route("/status/<task_id>", methods=["GET"])
def instrumental_status(task_id):
    """Überprüft Status einer Instrumental-Generierung"""
    response_data, status_code = song_controller.get_song_status(task_id)

    return jsonify(response_data), status_code


@api_instrumental_task_v1.route("/cancel/<task_id>", methods=["POST"])
def cancel_task(task_id):
    """Cancelt einen Task"""
    response_data, status_code = song_controller.cancel_task(task_id)

    return jsonify(response_data), status_code


@api_instrumental_task_v1.route("/delete/<task_id>", methods=["DELETE"])
def delete_task_result(task_id):
    """Löscht Task-Ergebnis"""
    response_data, status_code = song_controller.delete_task_result(task_id)

    return jsonify(response_data), status_code


@api_instrumental_task_v1.route("/queue-status", methods=["GET"])
def queue_status():
    """Gibt Queue-Status zurück"""
    response_data, status_code = song_controller.get_queue_status()

    return jsonify(response_data), status_code