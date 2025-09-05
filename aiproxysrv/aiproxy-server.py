import os
import sys
import requests
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, Blueprint
from dotenv import load_dotenv
from taskmgr import celery_app, generate_song_task
import time
import hashlib

load_dotenv()

app = Flask(__name__)

# MUREKA Konfiguration
MUREKA_API_KEY = os.getenv("MUREKA_API_KEY")
MUREKA_BILLING_URL = os.getenv("MUREKA_BILLING_URL")

def ensure_images_dir() -> Path:
    """Erstellt den images-Ordner, wenn er nicht existiert."""
    images_path = Path(__file__).parent / "images"
    try:
        images_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Folder '{images_path}' created or exists already.", file=sys.stderr)
    except Exception as e:
        print(f"❌ Error on create folder: {e}", file=sys.stderr)
        raise
    return images_path


# ---------------------------------------------------------------
# Global API
# ---------------------------------------------------------------
api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")

@api_v1.route("/health")
def health():
    return jsonify(status="ok"), 200


# ---------------------------------------------------------------
# DALL.E API - Image Generator
# ---------------------------------------------------------------
api_image_v1 = Blueprint("api_image_v1", __name__, url_prefix="/api/v1/image")

@api_image_v1.route('/<path:filename>')
def serve_image(filename):
    images_dir = ensure_images_dir()
    return send_from_directory(images_dir, filename)


@api_image_v1.route('/generate', methods=['POST'])
def generate():
    raw_json = request.get_json(silent=True)

    if not raw_json or 'prompt' not in raw_json or 'size' not in raw_json:
        return jsonify({"error": "No 'prompt' or 'size' in JSON."}), 400

    prompt = raw_json['prompt']
    size = raw_json['size']

    print(f"📝 Prompt: {prompt}", file=sys.stderr)
    print(f"📝 Size:   {size}", file=sys.stderr)

    headers = {
        'Authorization': f'Bearer {os.getenv("OPENAI_API_KEY")}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': os.getenv("OPENAI_MODEL"),
        'prompt': prompt,
        'size': size,
        'n': 1
    }

    try:
        resp = requests.post(os.path.join(os.getenv("OPENAI_URL"), "generations"), headers=headers, json=payload,
                             timeout=30)
        resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Network-Error: {e}"}), 500

    if resp.status_code != 200:
        print("DALL·E Response:", resp.text, file=sys.stderr)
        return jsonify({"error": resp.json()}), resp.status_code

    resp_json = resp.json()
    image_url = resp_json['data'][0]['url']

    try:
        img_resp = requests.get(image_url, stream=True, timeout=30)
        img_resp.raise_for_status()
    except Exception as e:
        return jsonify({"error": f"Download-Error: {e}"}), 500

    images_dir = ensure_images_dir()
    prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:10]
    filename = f"{prompt_hash}_{int(time.time())}.png"
    image_path = images_dir / filename

    try:
        with open(image_path, 'wb') as f:
            for chunk in img_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"📁 Image stored here: {image_path}", file=sys.stderr)
    except Exception as e:
        return jsonify({"error": f"Error on persist image: {e}"}), 500

    local_url = f"{request.host_url}images/{filename}"

    return jsonify({
        "url": local_url,
        "saved_path": str(image_path)
    })


# ---------------------------------------------------------------
# Mureka Song Generator
# ---------------------------------------------------------------
api_song_v1 = Blueprint("api_song_v1", __name__, url_prefix="/api/v1/song")


@api_song_v1.route("/celery-health", methods=["GET"])
def celery_health():
    """Überprüft Celery Connectivity"""
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

        response = requests.get(
            MUREKA_BILLING_URL,
            headers=headers,
            timeout=10
        )
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
    """
    Erwartet JSON:
    {
        "lyrics": "...",
        "model": "...",
        "prompt": "..."
    }
    """
    payload = request.get_json(force=True)

    if not payload.get("lyrics") or not payload.get("prompt"):
        return jsonify({
            "error": "Missing required fields: 'lyrics' and 'prompt' are required"
        }), 400

    # Prüfe Account-Status vor Generierung
    try:
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
        account_response = requests.get(MUREKA_BILLING_URL, headers=headers, timeout=10)

        if account_response.status_code == 200:
            account_data = account_response.json()
            balance = account_data.get("balance", 0)

            if balance <= 0:
                return jsonify({
                    "error": "Insufficient MUREKA balance",
                    "account_info": account_data
                }), 402  # Payment Required
    except Exception as e:
        print(f"⚠️ Could not check MUREKA account balance: {e}", file=sys.stderr)

    print(f"🎵 Starting song generation", file=sys.stderr)
    print(f"📋 Lyrics length: {len(payload.get('lyrics', ''))} characters", file=sys.stderr)
    print(f"🎹 Prompt: {payload.get('prompt', '')}", file=sys.stderr)

    task = generate_song_task.delay(payload)

    return jsonify({
        "task_id": task.id,
        "status_url": f"{request.host_url}song/status/{task.id}"
    }), 202


@api_song_v1.route("/status/<task_id>", methods=["GET"])
def song_status(task_id):
    result = celery_app.AsyncResult(task_id)

    if result.state == 'PENDING':
        return jsonify({
            "task_id": task_id,
            "status": "PENDING",
            "message": "Task is waiting for execution"
        }), 200

    elif result.state == 'PROGRESS':
        progress_info = result.info if isinstance(result.info, dict) else {}
        return jsonify({
            "task_id": task_id,
            "status": "PROGRESS",
            "progress": progress_info
        }), 200

    elif result.state == 'SUCCESS':
        task_result = result.result
        return jsonify({
            "task_id": task_id,
            "status": "SUCCESS",
            "result": task_result
        }), 200

    elif result.state == 'FAILURE':
        return jsonify({
            "task_id": task_id,
            "status": "FAILURE",
            "error": str(result.result) if result.result else "Unknown error occurred"
        }), 200

    else:
        return jsonify({
            "task_id": task_id,
            "status": result.state,
            "message": "Unknown task state"
        }), 200


@api_song_v1.route("/force-complete/<job_id>", methods=["POST"])
def force_complete_task(job_id):
    """Erzwingt den Abschluss eines Tasks mit direktem MUREKA Check"""
    try:
        # Hole Ergebnis direkt von MUREKA
        headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
        status_url = f"https://api.mureka.ai/v1/song/query/{job_id}"

        response = requests.get(status_url, headers=headers, timeout=10)
        response.raise_for_status()
        mureka_result = response.json()

        # Setze das Ergebnis im Celery Backend
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
        return jsonify({"error": str(e)}), 500


@api_song_v1.route("/cancel/<task_id>", methods=["POST"])
def cancel_task(task_id):
    """Bricht einen laufenden Task ab"""
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
        return jsonify({
            "error": f"Failed to cancel task: {str(e)}"
        }), 500


@api_song_v1.route("/delete/<task_id>", methods=["DELETE"])
def delete_task_result(task_id):
    """Löscht das Ergebnis eines abgeschlossenen Tasks"""
    try:
        celery_app.AsyncResult(task_id).forget()
        return jsonify({
            "task_id": task_id,
            "message": "Task result deleted successfully"
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to delete task result: {str(e)}"
        }), 500


@api_song_v1.route("/queue-status", methods=["GET"])
def queue_status():
    """Zeigt den aktuellen Warteschlangen-Status"""
    try:
        import redis
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

        current_requests = int(redis_client.get("mureka:current_requests") or 0)
        waiting_tasks = len(redis_client.keys("mureka:task:*"))

        return jsonify({
            "current_requests": current_requests,
            "max_concurrent": 1,
            "waiting_tasks": waiting_tasks,
            "available": current_requests < 1
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------
# Error Handler
# ---------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500


# ---------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------
app.register_blueprint(api_v1)
app.register_blueprint(api_image_v1)
app.register_blueprint(api_song_v1)

# ---------------------------------------------------------------
# Server-Start
# ---------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.getenv("OPENAI_PORT", 5050))
    host = os.getenv("OPENAI_HOST", "0.0.0.0")
    print(f"🚀 Flask-Server läuft auf http://0.0.0.0:{port}", file=sys.stderr)
    print(f"🎵 MUREKA Endpoint: {os.getenv('MUREKA_ENDPOINT', 'Not configured')}", file=sys.stderr)
    print(f"💰 MUREKA Billing: {MUREKA_BILLING_URL}", file=sys.stderr)

    app.run(host=host, port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
