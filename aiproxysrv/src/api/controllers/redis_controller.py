"""Redis Controller - Handles business logic for Redis operations"""
import traceback
import redis
import json
from typing import Tuple, Dict, Any, List
from config.settings import CELERY_BROKER_URL
from utils.logger import logger


class RedisController:
    """Controller for Redis task operations"""
    
    def __init__(self):
        self.redis_url = CELERY_BROKER_URL
    
    def _get_redis_connection(self) -> redis.Redis:
        """Get Redis connection"""
        return redis.from_url(self.redis_url)
    
    def list_celery_tasks(self) -> Tuple[Dict[str, Any], int]:
        """
        List all Celery task metadata
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            logger.debug("Connecting to Redis", redis_url=self.redis_url)
            r = self._get_redis_connection()
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

            logger.info("Retrieved tasks from Redis", task_count=len(tasks))
            return {"tasks": tasks}, 200

        except Exception as e:
            logger.error("Error listing Redis tasks", error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return {"error": str(e)}, 500
    
    def list_redis_keys(self) -> Tuple[Dict[str, Any], int]:
        """
        List all Celery meta keys, sorted by created_at
        
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            r = self._get_redis_connection()
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
            return {"tasks": tasks}, 200

        except Exception as exc:
            logger.error("Error listing Redis keys", error=str(exc), error_type=type(exc).__name__, stacktrace=traceback.format_exc())
            return {"error": str(exc)}, 500
    
    def delete_redis_key(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete a Redis key by task ID
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            r = self._get_redis_connection()
            pattern = "celery-task-meta-"
            celery_task_id = f"{pattern}{task_id}"
            
            deleted = r.delete(celery_task_id)
            
            if deleted:
                return {
                    "task_id": celery_task_id,
                    "status": "SUCCESS"
                }, 200
            else:
                return {
                    "task_id": celery_task_id,
                    "status": "NOT FOUND"
                }, 404

        except Exception as exc:
            logger.error("Error deleting Redis key", task_id=task_id, error=str(exc), error_type=type(exc).__name__, stacktrace=traceback.format_exc())
            return {
                "task_id": task_id,
                "status": "ERROR"
            }, 422