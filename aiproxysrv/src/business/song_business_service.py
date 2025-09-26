"""Song Business Service - Handles song management business logic"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from db.song_service import song_service

logger = logging.getLogger(__name__)


class SongBusinessError(Exception):
    """Base exception for song business logic errors"""
    pass


class SongBusinessService:
    """Business logic service for song operations"""

    def get_songs_with_pagination(self, limit: int = 20, offset: int = 0, status: str = None,
                                search: str = '', sort_by: str = 'created_at',
                                sort_direction: str = 'desc', workflow: str = None) -> Dict[str, Any]:
        """
        Get paginated list of songs with search and filtering

        Args:
            limit: Number of songs to return
            offset: Number of songs to skip
            status: Optional status filter
            search: Search term for filtering
            sort_by: Field to sort by
            sort_direction: Sort direction
            workflow: Optional workflow filter

        Returns:
            Dict containing songs and pagination info
        """
        try:
            songs = song_service.get_songs_paginated(
                limit=limit,
                offset=offset,
                status=status,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction,
                workflow=workflow
            )
            total_count = song_service.get_total_songs_count(
                status=status,
                search=search,
                workflow=workflow
            )

            # Transform to API response format
            songs_list = [self._transform_song_to_list_format(song) for song in songs]

            return {
                "songs": songs_list,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }

        except Exception as e:
            logger.error(f"Error retrieving songs: {e}")
            raise SongBusinessError(f"Failed to retrieve songs: {e}") from e

    def get_song_details(self, song_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a single song with all choices

        Args:
            song_id: ID of the song

        Returns:
            Dict containing song details with choices or None if not found
        """
        try:
            song = song_service.get_song_by_id(song_id)
            if not song:
                return None

            return self._transform_song_to_detail_format(song)

        except Exception as e:
            logger.error(f"Error retrieving song {song_id}: {e}")
            raise SongBusinessError(f"Failed to retrieve song: {e}") from e

    def update_song_metadata(self, song_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update song metadata with validation

        Args:
            song_id: ID of the song to update
            update_data: Data to update

        Returns:
            Updated song data or None if not found
        """
        try:
            # Check if song exists
            song = song_service.get_song_by_id(song_id)
            if not song:
                return None

            # Validate and filter allowed fields
            allowed_fields = ['title', 'tags', 'workflow']
            filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

            if not filtered_data:
                raise SongBusinessError("No valid fields provided for update")

            # Update the song
            updated_song = song_service.update_song(song_id, filtered_data)
            if not updated_song:
                raise SongBusinessError("Failed to update song")

            logger.info(f"Song {song_id} updated successfully")
            return {
                "id": str(updated_song.id),
                "title": updated_song.title,
                "tags": updated_song.tags,
                "workflow": updated_song.workflow,
                "updated_at": updated_song.updated_at.isoformat() if updated_song.updated_at else None
            }

        except Exception as e:
            logger.error(f"Error updating song {song_id}: {e}")
            raise SongBusinessError(f"Failed to update song: {e}") from e

    def delete_single_song(self, song_id: str) -> bool:
        """
        Delete a single song including all choices

        Args:
            song_id: ID of the song to delete

        Returns:
            True if successful, False if song not found
        """
        try:
            song = song_service.get_song_by_id(song_id)
            if not song:
                return False

            success = song_service.delete_song_by_id(song_id)
            if success:
                logger.info(f"Song {song_id} and its choices deleted successfully")
                return True
            else:
                raise SongBusinessError("Failed to delete song")

        except Exception as e:
            logger.error(f"Error deleting song {song_id}: {type(e).__name__}: {e}")
            raise SongBusinessError(f"Failed to delete song: {e}") from e

    def bulk_delete_songs(self, song_ids: List[str]) -> Dict[str, Any]:
        """
        Delete multiple songs with detailed results

        Args:
            song_ids: List of song IDs to delete

        Returns:
            Dict containing deletion results and summary
        """
        if not song_ids:
            raise SongBusinessError("No song IDs provided")

        if len(song_ids) > 100:
            raise SongBusinessError("Too many songs (max 100 per request)")

        results = {
            "deleted": [],
            "not_found": [],
            "errors": []
        }

        for song_id in song_ids:
            try:
                song = song_service.get_song_by_id(song_id)
                if not song:
                    results["not_found"].append(song_id)
                    continue

                success = song_service.delete_song_by_id(song_id)
                if success:
                    results["deleted"].append(song_id)
                    logger.info(f"Song {song_id} and its choices deleted successfully")
                else:
                    results["errors"].append({"id": song_id, "error": "Failed to delete song"})

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                results["errors"].append({"id": song_id, "error": error_msg})
                logger.error(f"Error deleting song {song_id}: {error_msg}")

        summary = {
            "total_requested": len(song_ids),
            "deleted": len(results["deleted"]),
            "not_found": len(results["not_found"]),
            "errors": len(results["errors"])
        }

        logger.info(f"Bulk delete completed: {summary}")
        return {
            "summary": summary,
            "results": results
        }

    def update_choice_rating(self, choice_id: str, rating: Optional[int]) -> Optional[Dict[str, Any]]:
        """
        Update rating for a song choice

        Args:
            choice_id: ID of the choice
            rating: Rating value (0, 1, or None)

        Returns:
            Updated choice data or None if not found
        """
        try:
            # Validate rating value
            if rating is not None and rating not in [0, 1]:
                raise SongBusinessError("Rating must be null, 0 (thumbs down), or 1 (thumbs up)")

            # Check if choice exists
            choice = song_service.get_choice_by_id(choice_id)
            if not choice:
                return None

            # Update rating
            success = song_service.update_choice_rating(choice_id, rating)
            if not success:
                raise SongBusinessError("Failed to update choice rating")

            logger.info(f"Choice {choice_id} rating updated to {rating}")
            return {
                "id": choice_id,
                "rating": rating,
                "message": "Rating updated successfully"
            }

        except Exception as e:
            logger.error(f"Error updating choice rating {choice_id}: {e}")
            raise SongBusinessError(f"Failed to update choice rating: {e}") from e

    def _transform_song_to_list_format(self, song) -> Dict[str, Any]:
        """Transform song object to list display format"""
        return {
            "id": str(song.id),
            "lyrics": song.lyrics,
            "title": song.title,
            "model": song.model,
            "workflow": song.workflow,
            "is_instrumental": song.is_instrumental,
            "created_at": song.created_at.isoformat() if song.created_at else None,
        }

    def _transform_song_to_detail_format(self, song) -> Dict[str, Any]:
        """Transform song object to detailed format with choices"""
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
        return {
            "id": str(song.id),
            "task_id": song.task_id,
            "job_id": song.job_id,
            "lyrics": song.lyrics,
            "prompt": song.prompt,
            "model": song.model,
            "title": song.title,
            "tags": song.tags,
            "workflow": song.workflow,
            "is_instrumental": song.is_instrumental,
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

    def _format_duration_from_ms(self, duration_ms: float) -> str:
        """Format duration from milliseconds to MM:SS format"""
        if not duration_ms:
            return "00:00"

        total_seconds = int(duration_ms / 1000)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"