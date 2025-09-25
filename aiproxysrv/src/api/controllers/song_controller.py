"""Song Controller - Orchestrates specialized song controllers"""
import sys
from typing import Tuple, Dict, Any, List
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
            # Get songs from database via service
            songs = song_service.get_songs_paginated(
                limit=limit,
                offset=offset,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
                workflow=workflow
            )
            total_count = song_service.get_total_songs_count(status=status, search=search, workflow=workflow)
            
            # Convert to API response format (minimal data for list view)
            songs_list = []
            for song in songs:
                # Format song data (only fields needed for list display)
                song_data = {
                    "id": str(song.id),
                    "lyrics": song.lyrics,
                    "title": song.title,
                    "model": song.model,
                    "workflow": song.workflow,
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
                    "stem_url": choice.stem_url,
                    "stem_generated_at": choice.stem_generated_at.isoformat() if choice.stem_generated_at else None,
                    "duration": choice.duration,
                    "title": choice.title,
                    "tags": choice.tags,
                    "rating": choice.rating,
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
                "title": song.title,
                "tags": song.tags,
                "workflow": song.workflow,
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
            # Check if song exists first
            song = song_service.get_song_by_id(song_id)
            if not song:
                return {"error": "Song not found"}, 404

            # Only allow certain fields to be updated
            allowed_fields = ['title', 'tags', 'workflow']
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if not filtered_data:
                return {"error": "No valid fields provided for update"}, 400

            # Update the song
            updated_song = song_service.update_song(song_id, filtered_data)

            if not updated_song:
                return {"error": "Failed to update song"}, 500

            # Return updated song data
            return {
                "id": str(updated_song.id),
                "title": updated_song.title,
                "tags": updated_song.tags,
                "workflow": updated_song.workflow,
                "updated_at": updated_song.updated_at.isoformat() if updated_song.updated_at else None
            }, 200

        except Exception as e:
            print(f"Error updating song {song_id}: {e}", file=sys.stderr)
            return {"error": f"Failed to update song: {e}"}, 500

    def delete_song(self, song_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete song by ID including all choices

        Args:
            song_id: UUID of the song to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Check if song exists first
            song = song_service.get_song_by_id(song_id)
            if not song:
                return {"error": "Song not found"}, 404

            # Delete song and all its choices (handled by cascade)
            success = song_service.delete_song_by_id(song_id)
            if success:
                print(f"Song {song_id} and its choices deleted successfully", file=sys.stderr)
                return {"message": "Song deleted successfully"}, 200
            else:
                return {"error": "Failed to delete song"}, 500

        except Exception as e:
            print(f"Error deleting song {song_id}: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": f"Failed to delete song: {e}"}, 500

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

        results = {
            "deleted": [],
            "not_found": [],
            "errors": []
        }

        try:
            for song_id in song_ids:
                try:
                    # Check if song exists
                    song = song_service.get_song_by_id(song_id)
                    if not song:
                        results["not_found"].append(song_id)
                        continue

                    # Delete song and all its choices (handled by cascade)
                    success = song_service.delete_song_by_id(song_id)
                    if success:
                        results["deleted"].append(song_id)
                        print(f"Song {song_id} and its choices deleted successfully", file=sys.stderr)
                    else:
                        results["errors"].append({"id": song_id, "error": "Failed to delete song"})

                except Exception as e:
                    error_msg = f"{type(e).__name__}: {e}"
                    results["errors"].append({"id": song_id, "error": error_msg})
                    print(f"Error deleting song {song_id}: {error_msg}", file=sys.stderr)

            # Determine response status
            if results["deleted"]:
                status_code = 200
                if results["not_found"] or results["errors"]:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if not results["not_found"] else 404

            summary = {
                "total_requested": len(song_ids),
                "deleted": len(results["deleted"]),
                "not_found": len(results["not_found"]),
                "errors": len(results["errors"])
            }

            response_data = {
                "summary": summary,
                "results": results
            }

            print(f"Bulk delete completed: {summary}", file=sys.stderr)
            return response_data, status_code

        except Exception as e:
            print(f"Error in bulk delete operation: {type(e).__name__}: {e}", file=sys.stderr)
            return {"error": f"Bulk delete failed: {e}"}, 500

    def _format_duration_from_ms(self, duration_ms: float) -> str:
        """Format duration from milliseconds to MM:SS format"""
        if not duration_ms:
            return "00:00"

        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

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
            # Validate rating value
            rating = rating_data.get('rating')
            if rating is not None and rating not in [0, 1]:
                return {"error": "Rating must be null, 0 (thumbs down), or 1 (thumbs up)"}, 400

            # Check if choice exists
            choice = song_service.get_choice_by_id(choice_id)
            if not choice:
                return {"error": "Song choice not found"}, 404

            # Update rating
            success = song_service.update_choice_rating(choice_id, rating)
            if not success:
                return {"error": "Failed to update choice rating"}, 500

            # Return updated choice data
            return {
                "id": choice_id,
                "rating": rating,
                "message": "Rating updated successfully"
            }, 200

        except Exception as e:
            print(f"Error updating choice rating {choice_id}: {e}", file=sys.stderr)
            return {"error": f"Failed to update choice rating: {e}"}, 500

