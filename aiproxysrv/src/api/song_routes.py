"""
Song Generation Routes mit MUREKA
"""
from flask import Blueprint, request, jsonify
from api.song_controller import SongController

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
