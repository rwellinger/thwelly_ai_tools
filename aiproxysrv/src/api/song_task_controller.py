"""Song Task Controller - Handles task management logic"""
import sys
import requests
import time
from typing import Tuple, Dict, Any
from config.settings import MUREKA_API_KEY, MUREKA_STATUS_ENDPOINT
from celery_app import celery_app, get_slot_status


class SongTaskController:
    """Controller for song task management operations"""
    
    def get_celery_health(self) -> Tuple[Dict[str, Any], int]:
        """Check Celery Worker Status"""
        try:
            inspector = celery_app.control.inspect()
            stats = inspector.stats()
            if stats:
                return {"status": "healthy", "celery_workers": len(stats)}, 200
            else:
                return {"status": "warning", "message": "No Celery workers available"}, 200
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500
    
    def get_song_status(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Check Status of Song Generation"""
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            print(f"{task_id} PENDING", file=sys.stderr)
            return {
                "task_id": task_id,
                "status": "PENDING",
                "message": "Task is waiting for execution"
            }, 200

        elif result.state == 'PROGRESS':
            print(f"{task_id} PROGRESS", file=sys.stderr)
            progress_info = result.info if isinstance(result.info, dict) else {}
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "progress": progress_info
            }, 200

        elif result.state == 'SUCCESS':
            print(f"{task_id} SUCCESS", file=sys.stderr)
            task_result = result.result
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task_result
            }, 200

        elif result.state == 'FAILURE':
            print(f"{task_id} FAILURE", file=sys.stderr)
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(result.result) if result.result else "Unknown error occurred"
            }, 200

        else:
            print(f"{task_id} UNKNOWN", file=sys.stderr)
            return {
                "task_id": task_id,
                "status": result.state,
                "message": "Unknown task state"
            }, 200
    
    def cancel_task(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Cancel a Task"""
        try:
            result = celery_app.AsyncResult(task_id)

            if result.state in ['PENDING', 'PROGRESS']:
                result.revoke(terminate=True)
                return {
                    "task_id": task_id,
                    "status": "CANCELLED",
                    "message": "Task cancellation requested"
                }, 200
            else:
                return {
                    "task_id": task_id,
                    "status": result.state,
                    "message": "Task cannot be cancelled in current state"
                }, 400

        except Exception as e:
            print(f"Error on cancel task: {e}", file=sys.stderr)
            return {
                "error": f"Failed to cancel task: {str(e)}"
            }, 500
    
    def delete_task_result(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Delete Task Result"""
        try:
            celery_app.AsyncResult(task_id).forget()
            return {
                "task_id": task_id,
                "message": "Task result deleted successfully"
            }, 200
        except Exception as e:
            print(f"Error on delete task: {e}", file=sys.stderr)
            return {
                "error": f"Failed to delete task result: {str(e)}"
            }, 500
    
    def force_complete_task(self, job_id: str) -> Tuple[Dict[str, Any], int]:
        """Force Completion of a Task"""
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

            return {
                "task_id": job_id,
                "status": "FORCED_COMPLETION",
                "mureka_status": mureka_result.get("status"),
                "message": "Task manually completed with MUREKA result"
            }, 200

        except Exception as e:
            print(f"Error on force complete task: {e}", file=sys.stderr)
            return {"error": str(e)}, 500
    
    def get_queue_status(self) -> Tuple[Dict[str, Any], int]:
        """Get Queue Status"""
        try:
            slot_status = get_slot_status()
            return slot_status, 200
        except Exception as e:
            print(f"Error on get queue status: {e}", file=sys.stderr)
            return {"error": str(e)}, 500