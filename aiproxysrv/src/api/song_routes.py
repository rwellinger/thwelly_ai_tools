"""
Song Generation Routes mit MUREKA
"""
import sys
import requests
import time
from flask import Blueprint, request, jsonify
from config.settings import MUREKA_API_KEY, MUREKA_BILLING_URL, MUREKA_STATUS_ENDPOINT, REDIS_URL, \
    MUREKA_STEM_GENERATE_ENDPOINT
from celery_app import celery_app, generate_song_task, get_slot_status
from .json_helpers import prune

api_song_v1 = Blueprint("api_song_v1", __name__, url_prefix="/api/v1/song")

@api_song_v1.route("/celery-health", methods=["GET"])
def celery_health():
    """Überprüft Celery Worker Status"""
    try:
        inspector = celery_app.control.inspect()
        stats = inspector.stats()
        if stats:
            return jsonify({"status": "healthy", "celery_workers": len(stats)}), 200
        else:
            return jsonify({"status": "warning", "message": "No Celery workers available"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@api_song_v1.route("/mureka-account", methods=["GET"])
def mureka_account():
    """Abfrage der MUREKA Account-Informationen"""
    if not MUREKA_API_KEY:
        return jsonify({"error": "MUREKA_API_KEY not configured"}), 500

    try:
        headers = {
            "Authorization": f"Bearer {MUREKA_API_KEY}"
        }

        print("Request URL", MUREKA_BILLING_URL)
        response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)
        response.raise_for_status()

        account_data = response.json()
        return jsonify({
            "status": "success",
            "account_info": account_data
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch MUREKA account info: {str(e)}"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500


@api_song_v1.route("/generate", methods=["POST"])
def song_generate():
    """Startet Song-Generierung"""
    payload = request.get_json(force=True)

    if not payload.get("lyrics") or not payload.get("prompt"):
        return jsonify({
            "error": "Missing required fields: 'lyrics' and 'prompt' are required"
        }), 400

    if not check_balance():
        return jsonify({
            "error": "Insufficient MUREKA balance"
        }), 402  # Payment Required

    print(f"Starting song generation", file=sys.stderr)
    print(f"Lyrics length: {len(payload.get('lyrics', ''))} characters", file=sys.stderr)
    print(f"Prompt: {payload.get('prompt', '')}", file=sys.stderr)

    task = generate_song_task.delay(payload)

    return jsonify({
        "task_id": task.id,
        "status_url": f"{request.host_url}api/v1/song/status/{task.id}"
    }), 202



@api_song_v1.route("/stem/generate", methods=["POST"])
def stems_generator():
    """Erstelle stems anhand einer MP3"""
    payload = request.get_json(force=True)

    url = payload.get("url", None)
    if not url:
        return jsonify({
            "error": "Missing required field: 'url' is required"
        }), 400

    if not check_balance():
        return jsonify({
            "error": "Insufficient MUREKA balance"
        }), 402  # Payment Required

    print(f"Starting stem generation", file=sys.stderr)
    print(f"Request URL: {MUREKA_STEM_GENERATE_ENDPOINT}", file=sys.stderr)
    print(f"Url: {url}", file=sys.stderr)

    try:
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}

        """ Das erstellen der Stems kann eine Weile dauern. 5 Minuten (300) Timeout daher """
        response = requests.post(MUREKA_STEM_GENERATE_ENDPOINT, headers=headers, timeout=(10, 300), json=payload)
        response.raise_for_status()
        result = response.json()

        return jsonify({
            "status": "SUCCESS",
            "result": result,
            "completed_at": time.time()
        }), 200

    except Exception as e:
        print(f"Error on create stem: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


@api_song_v1.route("/query/<job_id>", methods=["GET"])
def song_info(job_id):
    """Get Song structure direct from MUREKA again who was generated successfully"""
    try:
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}

        print("Request URL", MUREKA_STATUS_ENDPOINT)
        song_info_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"

        response = requests.get(song_info_url, headers=headers, timeout=10)
        response.raise_for_status()
        mureka_result = response.json()
        keys_to_remove = {"lyrics_sections"}
        cleaned_json = prune(mureka_result, keys_to_remove)

        return jsonify({
            "status": "SUCCESS",
            "task_id": job_id,
            "job_id": job_id,
            "result": cleaned_json,
            "completed_at": time.time()
        }), 200

    except Exception as e:
        print(f"Error on get song: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


@api_song_v1.route("/force-complete/<job_id>", methods=["POST"])
def force_complete_task(job_id):
    """Erzwingt Completion eines Tasks"""
    try:
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
        status_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"

        print("Request URL", MUREKA_STATUS_ENDPOINT)
        response = requests.get(status_url, headers=headers, timeout=10)
        response.raise_for_status()
        mureka_result = response.json()

        from celery.result import AsyncResult
        result = AsyncResult(job_id)

        success_payload = {
            "status": "SUCCESS",
            "task_id": job_id,
            "job_id": job_id,
            "result": mureka_result,
            "completed_at": time.time()
        }

        result.backend.store_result(result.id, success_payload, "SUCCESS")

        return jsonify({
            "task_id": job_id,
            "status": "FORCED_COMPLETION",
            "mureka_status": mureka_result.get("status"),
            "message": "Task manually completed with MUREKA result"
        }), 200

    except Exception as e:
        print(f"Error on force complete task: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


api_song_task_v1 = Blueprint("api_song_task_v1", __name__, url_prefix="/api/v1/song/task")

@api_song_task_v1.route("/status/<task_id>", methods=["GET"])
def song_status(task_id):
    """Überprüft Status einer Song-Generierung"""
    result = celery_app.AsyncResult(task_id)

    if result.state == 'PENDING':
        print(f"{task_id} PENDING", file=sys.stderr)
        return jsonify({
            "task_id": task_id,
            "status": "PENDING",
            "message": "Task is waiting for execution"
        }), 200

    elif result.state == 'PROGRESS':
        print(f"{task_id} PROGRESS", file=sys.stderr)
        progress_info = result.info if isinstance(result.info, dict) else {}
        return jsonify({
            "task_id": task_id,
            "status": "PROGRESS",
            "progress": progress_info
        }), 200

    elif result.state == 'SUCCESS':
        print(f"{task_id} SUCCESS", file=sys.stderr)
        task_result = result.result
        return jsonify({
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task_result
        }), 200

    elif result.state == 'FAILURE':
        print(f"{task_id} FAILURE", file=sys.stderr)
        return jsonify({
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(result.result) if result.result else "Unknown error occurred"
        }), 200

    else:
        print(f"{task_id} UKNOWN", file=sys.stderr)
        return jsonify({
            "task_id": task_id,
            "status": result.state,
            "message": "Unknown task state"
        }), 200


@api_song_task_v1.route("/cancel/<task_id>", methods=["POST"])
def cancel_task(task_id):
    """Cancelt einen Task"""
    try:
        result = celery_app.AsyncResult(task_id)

        if result.state in ['PENDING', 'PROGRESS']:
            result.revoke(terminate=True)
            return jsonify({
                "task_id": task_id,
                "status": "CANCELLED",
                "message": "Task cancellation requested"
            }), 200
        else:
            return jsonify({
                "task_id": task_id,
                "status": result.state,
                "message": "Task cannot be cancelled in current state"
            }), 400

    except Exception as e:
        print(f"Error on cancel task: {e}", file=sys.stderr)
        return jsonify({
            "error": f"Failed to cancel task: {str(e)}"
        }), 500


@api_song_task_v1.route("/delete/<task_id>", methods=["DELETE"])
def delete_task_result(task_id):
    """Löscht Task-Ergebnis"""
    try:
        celery_app.AsyncResult(task_id).forget()
        return jsonify({
            "task_id": task_id,
            "message": "Task result deleted successfully"
        }), 200
    except Exception as e:
        print(f"Error on delete task: {e}", file=sys.stderr)
        return jsonify({
            "error": f"Failed to delete task result: {str(e)}"
        }), 500


@api_song_task_v1.route("/queue-status", methods=["GET"])
def queue_status():
    """Gibt Queue-Status zurück"""
    try:
        slot_status = get_slot_status()
        return jsonify(slot_status), 200
    except Exception as e:
        print(f"Error on get queue status: {e}", file=sys.stderr)
        return jsonify({"error": str(e)}), 500


def check_balance():
    """Check Balance"""
    try:
        print(f"Request URL: {MUREKA_BILLING_URL}", file=sys.stderr)
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
        account_response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)

        if account_response.status_code == 200:
            account_data = account_response.json()
            balance = account_data.get("balance", 0)

            if balance <= 0:
                print(f"Insufficient MUREKA balance: {balance}", file=sys.stderr)
                return False
            else:
                print(f"Account OK : {balance}", file=sys.stderr)
                return True

    except Exception as e:
        print(f"Could not check MUREKA balance: {e}", file=sys.stderr)
        return False
