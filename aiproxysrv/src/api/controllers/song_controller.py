"""Song Controller - Orchestrates specialized song controllers"""
import logging
from typing import Tuple, Dict, Any, List
from .song_creation_controller import SongCreationController
from .song_task_controller import SongTaskController
from .song_account_controller import SongAccountController
from business.song_business_service import SongBusinessService, SongBusinessError

logger = logging.getLogger(__name__)


class SongController:
    """Main controller that orchestrates specialized song controllers"""
    
    def __init__(self):
        self.creation_controller = SongCreationController()
        self.task_controller = SongTaskController()
        self.account_controller = SongAccountController()
        self.business_service = SongBusinessService()
    
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

    def generate_instrumental(self, payload: Dict[str, Any], host_url: str) -> Tuple[Dict[str, Any], int]:
        """Start Instrumental Generation"""
        return self.creation_controller.generate_instrumental(
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
    
    def get_songs(self, limit: int = 20, offset: int = 0, status: str = None, search: str = '',
                  sort_by: str = 'created_at', sort_direction: str = 'desc', workflow: str = None) -> Tuple[Dict[str, Any], int]:
        """
        Get list of songs with pagination, search and sorting

        Args:
            limit: Number of songs to return (default 20)
            offset: Number of songs to skip (default 0)
            status: Optional status filter (SUCCESS, PENDING, FAILURE, etc.)
            search: Search term to filter by title, lyrics, or tags
            sort_by: Field to sort by (created_at, title, lyrics)
            sort_direction: Sort direction (asc, desc)
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.get_songs_with_pagination(
                limit=limit,
                offset=offset,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
                workflow=workflow
            )
            return result, 200

        except SongBusinessError as e:
            logger.error(f"Failed to retrieve songs: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving songs: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500
    
    def get_song_by_id(self, song_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get single song by ID with all choices

        Args:
            song_id: UUID of the song

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.get_song_details(song_id)

            if result is None:
                return {"error": "Song not found"}, 404

            return result, 200

        except SongBusinessError as e:
            logger.error(f"Failed to retrieve song {song_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def update_song(self, song_id: str, update_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Update song by ID

        Args:
            song_id: UUID of the song to update
            update_data: Dictionary containing fields to update

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.update_song_metadata(song_id, update_data)

            if result is None:
                return {"error": "Song not found"}, 404

            return result, 200

        except SongBusinessError as e:
            logger.error(f"Failed to update song {song_id}: {e}")
            return {"error": str(e)}, 400 if "No valid fields" in str(e) else 500
        except Exception as e:
            logger.error(f"Unexpected error updating song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def delete_song(self, song_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete song by ID including all choices

        Args:
            song_id: UUID of the song to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            success = self.business_service.delete_single_song(song_id)

            if not success:
                return {"error": "Song not found"}, 404

            return {"message": "Song deleted successfully"}, 200

        except SongBusinessError as e:
            logger.error(f"Failed to delete song {song_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error deleting song {song_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def bulk_delete_songs(self, song_ids: List[str]) -> Tuple[Dict[str, Any], int]:
        """
        Delete multiple songs by IDs including all choices

        Args:
            song_ids: List of song IDs to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        if not song_ids:
            return {"error": "No song IDs provided"}, 400

        if len(song_ids) > 100:
            return {"error": "Too many songs (max 100 per request)"}, 400

        try:
            result = self.business_service.bulk_delete_songs(song_ids)

            # Determine response status based on results
            summary = result["summary"]
            if summary["deleted"] > 0:
                status_code = 200
                if summary["not_found"] > 0 or summary["errors"] > 0:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if summary["errors"] > 0 else 404

            return result, status_code

        except SongBusinessError as e:
            logger.error(f"Bulk delete failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in bulk delete: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500


    def update_choice_rating(self, choice_id: str, rating_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Update rating for a specific song choice

        Args:
            choice_id: UUID of the choice
            rating_data: Dictionary containing rating field

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            rating = rating_data.get('rating')
            result = self.business_service.update_choice_rating(choice_id, rating)

            if result is None:
                return {"error": "Song choice not found"}, 404

            return result, 200

        except SongBusinessError as e:
            logger.error(f"Failed to update choice rating {choice_id}: {e}")
            if "Rating must be" in str(e):
                return {"error": str(e)}, 400
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error updating choice rating {choice_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

