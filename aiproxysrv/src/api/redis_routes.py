from flask import Blueprint, jsonify
import redis
import json

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
    Gibt alle Celery‑Meta‑Keys zurück, sortiert nach `created_at`.
    """
    try:
        r = redis.from_url(CELERY_BROKER_URL)

        pattern = "celery-task-meta-*"
        tasks = []

        for key_bytes in r.scan_iter(match=pattern):
            key_str = key_bytes.decode()
            task_id = key_str.removeprefix("celery-task-meta-")

            meta_json = r.get(key_bytes)
            if not meta_json:
                continue

            meta = json.loads(meta_json)

            if meta.get("status") != "SUCCESS":
                continue

            result = meta.get("result", {}).get("result")
            created_at = result.get("created_at") if result else ""

            tasks.append({
                "key": key_str,
                "task_id": task_id,
                "created_at": created_at
            })

        tasks.sort(key=lambda t: t["created_at"], reverse=True)
        return jsonify({"tasks": tasks}), 200

    except Exception as exc:
        print("failed to list redis keys: {}".format(exc))
        return jsonify({"error": str(exc)}), 500


@api_redis_v1.route("/<task_id>", methods=["DELETE"])
def delete_redis_key(task_id):
    """
    Lösche einen Key aus Redis.
    """
    try:
        r = redis.from_url(CELERY_BROKER_URL)
        pattern = "celery-task-meta-"
        celery_task_id = f"{pattern}{task_id}"
        deleted = r.delete(celery_task_id)
        if deleted:
            return jsonify(
                {"task_id": celery_task_id,
                 "status": "SUCCESS"
                 }), 200
        else:
            return jsonify(
                {"task_id": celery_task_id,
                 "status": "NOT FOUND"
                 }), 404


    except Exception as exc:
        print("failed to delete redis key: {}".format(exc))
        return jsonify(
            {"task_id": task_id,
             "status": "ERROR"
             }), 422
