"""Song Task Controller - Handles task management logic"""
import requests
import time
import json
from typing import Tuple, Dict, Any
from config.settings import MUREKA_API_KEY, MUREKA_STATUS_ENDPOINT
from celery_app import celery_app, get_slot_status
from db.song_service import song_service
from utils.logger import logger


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
        """Check Status of Song Generation - First check DB, then fallback to Redis/Celery"""
        
        # First try to get status from database
        song = song_service.get_song_by_task_id(task_id)

        if song:
            logger.debug("Song found in database", task_id=task_id, status=song.status)
            
            response = {
                "task_id": task_id,
                "status": song.status,
                "created_at": song.created_at.isoformat() if song.created_at else None,
                "updated_at": song.updated_at.isoformat() if song.updated_at else None
            }
            
            # Add job_id if available
            if song.job_id:
                response["job_id"] = song.job_id
            
            # Add progress info if available
            if song.progress_info:
                try:
                    progress_data = json.loads(song.progress_info)
                    response["progress"] = progress_data
                except json.JSONDecodeError:
                    response["progress"] = {"raw": song.progress_info}
            
            # Always add mureka_status to progress for UI compatibility
            if song.mureka_status:
                if "progress" not in response:
                    response["progress"] = {}
                response["progress"]["mureka_status"] = song.mureka_status
            
            # Add result data for successful songs
            if song.status == "SUCCESS":
                result = {}
                if song.mureka_response:
                    try:
                        result = json.loads(song.mureka_response)
                    except json.JSONDecodeError:
                        result = {"raw_response": song.mureka_response}
                
                # Add structured choices data from database
                choices_data = []
                for choice in song.choices:
                    choice_data = {
                        "id": choice.mureka_choice_id,
                        "index": choice.choice_index,
                        "url": choice.mp3_url,
                        "flac_url": choice.flac_url,
                        "duration": choice.duration,
                    }
                    # Add optional fields if available
                    if choice.video_url:
                        choice_data["video_url"] = choice.video_url
                    if choice.image_url:
                        choice_data["image_url"] = choice.image_url
                    if choice.title:
                        choice_data["title"] = choice.title
                    if choice.tags:
                        choice_data["tags"] = choice.tags.split(',') if choice.tags else []
                    
                    choices_data.append(choice_data)
                
                # Override choices in result with DB data (more reliable)
                if choices_data:
                    result["choices"] = choices_data
                
                response["result"] = result
                if song.completed_at:
                    response["completed_at"] = song.completed_at.timestamp()
            
            # Add error message for failed songs
            elif song.status == "FAILURE" and song.error_message:
                response["error"] = song.error_message
            
            return response, 200

        # Fallback to Celery/Redis if not found in database
        logger.debug("Song not found in database, checking Celery", task_id=task_id)
        result = celery_app.AsyncResult(task_id)

        if result.state == 'PENDING':
            logger.debug("Task is pending", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "PENDING",
                "message": "Task is waiting for execution"
            }, 200

        elif result.state == 'PROGRESS':
            logger.debug("Task in progress", task_id=task_id)
            progress_info = result.info if isinstance(result.info, dict) else {}
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "progress": progress_info
            }, 200

        elif result.state == 'SUCCESS':
            logger.debug("Task completed successfully", task_id=task_id)
            task_result = result.result
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "result": task_result
            }, 200

        elif result.state == 'FAILURE':
            logger.debug("Task failed", task_id=task_id)
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "error": str(result.result) if result.result else "Unknown error occurred"
            }, 200

        else:
            logger.debug("Unknown task state", task_id=task_id, state=result.state)
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
            logger.error("Error cancelling task", task_id=task_id, error=str(e))
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
            logger.error("Error deleting task result", task_id=task_id, error=str(e))
            return {
                "error": f"Failed to delete task result: {str(e)}"
            }, 500
    
    def force_complete_task(self, job_id: str) -> Tuple[Dict[str, Any], int]:
        """Force Completion of a Task"""
        try:
            headers = {"Authorization": f"Bearer {MUREKA_API_KEY}"}
            status_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"

            logger.debug("Force completing task", job_id=job_id, url=MUREKA_STATUS_ENDPOINT)
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
            logger.error("Error force completing task", job_id=job_id, error=str(e))
            return {"error": str(e)}, 500
    
    def get_queue_status(self) -> Tuple[Dict[str, Any], int]:
        """Get Queue Status"""
        try:
            slot_status = get_slot_status()
            return slot_status, 200
        except Exception as e:
            logger.error("Error getting queue status", error=str(e))
            return {"error": str(e)}, 500