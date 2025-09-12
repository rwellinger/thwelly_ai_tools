from flask import Blueprint, jsonify
import sys
import traceback
from api.redis_controller import RedisController

api_redis_v1 = Blueprint("api_redis_v1",__name__, url_prefix="/api/v1/redis")

# Controller instance
redis_controller = RedisController()

@api_redis_v1.route("/list", methods=["GET"])
def list_celery_tasks_route():
    """
    Gibt alle Celery‑Task‑Metadaten zurück.
    """
    response_data, status_code = redis_controller.list_celery_tasks()
    return jsonify(response_data), status_code


@api_redis_v1.route("/list/keys", methods=["GET"])
def list_redis_keys():
    """
    Gibt alle Celery‑Meta‑Keys zurück, sortiert nach `created_at`.
    """
    response_data, status_code = redis_controller.list_redis_keys()
    return jsonify(response_data), status_code


@api_redis_v1.route("/<task_id>", methods=["DELETE"])
def delete_redis_key(task_id):
    """
    Lösche einen Key aus Redis.
    """
    response_data, status_code = redis_controller.delete_redis_key(task_id)
    return jsonify(response_data), status_code
