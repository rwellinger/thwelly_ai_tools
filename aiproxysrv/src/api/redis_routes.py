from flask import Blueprint, jsonify
import redis

from config.settings import CELERY_BROKER_URL

api_redis_v1 = Blueprint("api_redis_v1",__name__, url_prefix="/api/v1/redis")

@api_redis_v1.route("/list", methods=["GET"])
def list_celery_tasks_route():
    """
    Gibt alle Celery‑Task‑Metadaten zurück.
    """
    try:
        # 1. Verbindung zu Redis
        r = redis.from_url(CELERY_BROKER_URL)
        pattern = "celery-task-meta-*"

        tasks = []
        for key in r.scan_iter(match=pattern):
            key_str = key.decode()
            task_id = key_str[len("celery-task-meta-"):]

            meta_json = r.get(key)
            meta_str = meta_json.decode() if meta_json else None

            tasks.append({
                "key": key_str,
                "task_id": task_id,
                "meta": meta_str
            })

        return jsonify({"tasks": tasks}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_redis_v1.route("/list/keys", methods=["GET"])
def list_redis_keys():
    """
    Gibt nur die Keys zurück
    """
    try:
        # 1. Verbindung zu Redis
        r = redis.from_url(CELERY_BROKER_URL)
        pattern = "celery-task-meta-*"

        tasks = []
        for key in r.scan_iter(match=pattern):
            key_str = key.decode()
            task_id = key_str[len("celery-task-meta-"):]

            tasks.append({
                "key": key_str,
                "task_id": task_id,
            })

        return jsonify({"tasks": tasks}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
