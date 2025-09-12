"""Song Controller - Orchestrates specialized song controllers"""
from typing import Tuple, Dict, Any
from .song_creation_controller import SongCreationController
from .song_task_controller import SongTaskController
from .song_account_controller import SongAccountController


class SongController:
    """Main controller that orchestrates specialized song controllers"""
    
    def __init__(self):
        self.creation_controller = SongCreationController()
        self.task_controller = SongTaskController()
        self.account_controller = SongAccountController()
    
    def get_celery_health(self) -> Tuple[Dict[str, Any], int]:
        """Check Celery Worker Status"""
        return self.task_controller.get_celery_health()
    
    def get_mureka_account(self) -> Tuple[Dict[str, Any], int]:
        """Get MUREKA Account Information"""
        return self.account_controller.get_mureka_account()
    
    def generate_song(self, payload: Dict[str, Any], host_url: str) -> Tuple[Dict[str, Any], int]:
        """Start Song Generation"""
        return self.creation_controller.generate_song(
            payload, host_url, self.account_controller.check_balance
        )
    
    def generate_stems(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """Generate stems from MP3"""
        return self.creation_controller.generate_stems(
            payload, self.account_controller.check_balance
        )
    
    def get_song_info(self, job_id: str) -> Tuple[Dict[str, Any], int]:
        """Get Song structure direct from MUREKA again who was generated successfully"""
        return self.creation_controller.get_song_info(job_id)
    
    def force_complete_task(self, job_id: str) -> Tuple[Dict[str, Any], int]:
        """Force Completion of a Task"""
        return self.task_controller.force_complete_task(job_id)
    
    def get_song_status(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Check Status of Song Generation"""
        return self.task_controller.get_song_status(task_id)
    
    def cancel_task(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Cancel a Task"""
        return self.task_controller.cancel_task(task_id)
    
    def delete_task_result(self, task_id: str) -> Tuple[Dict[str, Any], int]:
        """Delete Task Result"""
        return self.task_controller.delete_task_result(task_id)
    
    def get_queue_status(self) -> Tuple[Dict[str, Any], int]:
        """Get Queue Status"""
        return self.task_controller.get_queue_status()
    
