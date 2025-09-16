"""Song Controller - Orchestrates specialized song controllers"""
import sys
from typing import Tuple, Dict, Any
from .song_creation_controller import SongCreationController
from .song_task_controller import SongTaskController
from .song_account_controller import SongAccountController
from db.song_service import song_service


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
    
    def get_songs(self, limit: int = 20, offset: int = 0, status: str = None) -> Tuple[Dict[str, Any], int]:
        """
        Get list of songs with pagination and optional status filter
        
        Args:
            limit: Number of songs to return (default 20)
            offset: Number of songs to skip (default 0)
            status: Optional status filter (SUCCESS, PENDING, FAILURE, etc.)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get songs from database via service
            songs = song_service.get_songs_paginated(limit=limit, offset=offset, status=status)
            total_count = song_service.get_total_songs_count(status=status)
            
            # Convert to API response format (minimal data for list view)
            songs_list = []
            for song in songs:
                # Format song data (only fields needed for list display)
                song_data = {
                    "id": str(song.id),
                    "lyrics": song.lyrics,
                    "model": song.model,
                    "created_at": song.created_at.isoformat() if song.created_at else None,
                }
                songs_list.append(song_data)
            
            response_data = {
                "songs": songs_list,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
            return response_data, 200
            
        except Exception as e:
            print(f"Error retrieving songs: {e}", file=sys.stderr)
            return {"error": f"Failed to retrieve songs: {e}"}, 500
    
    def get_song_by_id(self, song_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get single song by ID with all choices
        
        Args:
            song_id: UUID of the song
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            song = song_service.get_song_by_id(song_id)
            
            if not song:
                return {"error": "Song not found"}, 404
            
            # Format choices
            choices_list = []
            for choice in song.choices:
                choice_data = {
                    "id": str(choice.id),
                    "mureka_choice_id": choice.mureka_choice_id,
                    "choice_index": choice.choice_index,
                    "mp3_url": choice.mp3_url,
                    "flac_url": choice.flac_url,
                    "video_url": choice.video_url,
                    "image_url": choice.image_url,
                    "duration": choice.duration,
                    "title": choice.title,
                    "tags": choice.tags,
                    "formattedDuration": self._format_duration_from_ms(choice.duration) if choice.duration else None,
                    "created_at": choice.created_at.isoformat() if choice.created_at else None
                }
                choices_list.append(choice_data)
            
            # Format song data
            song_data = {
                "id": str(song.id),
                "task_id": song.task_id,
                "job_id": song.job_id,
                "lyrics": song.lyrics,
                "prompt": song.prompt,
                "model": song.model,
                "status": song.status,
                "progress_info": song.progress_info,
                "error_message": song.error_message,
                "mureka_response": song.mureka_response,
                "mureka_status": song.mureka_status,
                "choices_count": len(choices_list),
                "choices": choices_list,
                "created_at": song.created_at.isoformat() if song.created_at else None,
                "updated_at": song.updated_at.isoformat() if song.updated_at else None,
                "completed_at": song.completed_at.isoformat() if song.completed_at else None
            }
            
            return song_data, 200
            
        except Exception as e:
            print(f"Error retrieving song {song_id}: {e}", file=sys.stderr)
            return {"error": f"Failed to retrieve song: {e}"}, 500

    def _format_duration_from_ms(self, duration_ms: float) -> str:
        """Format duration from milliseconds to MM:SS format"""
        if not duration_ms:
            return "00:00"
        
        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
