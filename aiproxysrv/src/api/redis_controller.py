"""Redis Controller - Handles business logic for Redis operations"""
import sys
import traceback
import redis
import json
from typing import Tuple, Dict, Any, List
from config.settings import CELERY_BROKER_URL


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
            print(f"Connecting to Redis: {self.redis_url}", file=sys.stderr)
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
            
            print(f"Retrieved {len(tasks)} tasks from Redis", file=sys.stderr)
            return {"tasks": tasks}, 200
            
        except Exception as e:
            print(f"Error listing Redis tasks: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
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
            print(f"Error listing Redis keys: {type(exc).__name__}: {exc}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
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
            print(f"Error deleting Redis key {task_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {
                "task_id": task_id,
                "status": "ERROR"
            }, 422