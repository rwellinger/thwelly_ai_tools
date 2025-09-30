"""Song Service - Database operations for song management"""
import json
import redis
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from db.models import Song, SongChoice, SongStatus
from db.database import get_db
from config.settings import CELERY_BROKER_URL
from utils.logger import logger


class SongService:
    """Service for song database operations"""
    
    def __init__(self):
        self.redis_url = CELERY_BROKER_URL
    
    def _get_redis_connection(self) -> redis.Redis:
        """Get Redis connection"""
        return redis.from_url(self.redis_url)
    
    def create_song(self, task_id: str, lyrics: str, prompt: str, model: str = "auto", is_instrumental: bool = False, title: str = None) -> Optional[Song]:
        """Create a new song record in the database"""
        try:
            db = next(get_db())
            try:
                song = Song(
                    task_id=task_id,
                    lyrics=lyrics,
                    prompt=prompt,
                    model=model,
                    status=SongStatus.PENDING.value,
                    is_instrumental=is_instrumental,
                    title=title
                )
                
                db.add(song)
                db.commit()
                db.refresh(song)

                logger.info("song_created", task_id=task_id, song_id=str(song.id), model=model, is_instrumental=is_instrumental)
                return song

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_creation_db_error", task_id=task_id, error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("song_creation_failed", task_id=task_id, error=str(e), error_type=type(e).__name__)
            return None
    
    def get_song_by_task_id(self, task_id: str) -> Optional[Song]:
        """Get song by task_id with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.task_id == task_id).first()
                if song:
                    logger.debug("song_retrieved_by_task_id", task_id=task_id, song_id=str(song.id), choices_count=len(song.choices))
                else:
                    logger.debug("song_not_found_by_task_id", task_id=task_id)
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_task_id", task_id=task_id, error=str(e), error_type=type(e).__name__)
            return None
    
    def get_song_by_job_id(self, job_id: str) -> Optional[Song]:
        """Get song by job_id (MUREKA job ID) with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.job_id == job_id).first()
                if song:
                    logger.debug("song_retrieved_by_job_id", job_id=job_id, song_id=str(song.id), choices_count=len(song.choices))
                else:
                    logger.debug("song_not_found_by_job_id", job_id=job_id)
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_job_id", job_id=job_id, error=str(e), error_type=type(e).__name__)
            return None
    
    def update_song_status(self, task_id: str, status: str, progress_info: Optional[Dict[str, Any]] = None, job_id: Optional[str] = None) -> bool:
        """Update song status and progress information"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    logger.warning("song_not_found_for_status_update", task_id=task_id)
                    return False

                song.status = status
                if progress_info:
                    song.progress_info = json.dumps(progress_info)
                if job_id:
                    song.job_id = job_id

                db.commit()
                logger.info("song_status_updated", task_id=task_id, status=status, job_id=job_id, has_progress_info=bool(progress_info))
                return True

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_status_update_db_error", task_id=task_id, error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("song_status_update_failed", task_id=task_id, error=str(e), error_type=type(e).__name__)
            return False
    
    def update_song_result(self, task_id: str, result_data: Dict[str, Any]) -> bool:
        """Update song with completion results and create choices"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    logger.warning("song_not_found_for_result_update", task_id=task_id)
                    return False

                # Update status to SUCCESS
                song.status = SongStatus.SUCCESS.value

                # Store complete MUREKA response
                if 'result' in result_data and result_data['result']:
                    mureka_result = result_data['result']
                    song.mureka_response = json.dumps(mureka_result)
                    song.mureka_status = mureka_result.get('status')

                    # Update model with the actual model used by Mureka (not the request model)
                    if mureka_result.get('model'):
                        song.model = mureka_result.get('model')
                        logger.info("song_model_updated", task_id=task_id, model=song.model)

                    # Process choices array
                    choices_data = mureka_result.get('choices', [])
                    logger.info("processing_song_choices", task_id=task_id, choices_count=len(choices_data))

                    for choice_data in choices_data:
                        song_choice = SongChoice(
                            song_id=song.id,
                            mureka_choice_id=choice_data.get('id'),
                            choice_index=choice_data.get('index'),
                            mp3_url=choice_data.get('url'),
                            flac_url=choice_data.get('flac_url'),
                            video_url=choice_data.get('video_url'),
                            image_url=choice_data.get('image_url'),
                            duration=float(choice_data['duration']) if choice_data.get('duration') else None,
                            title=choice_data.get('title'),
                            tags=','.join(choice_data['tags']) if choice_data.get('tags') and isinstance(choice_data['tags'], list) else None
                        )
                        db.add(song_choice)
                        logger.debug("song_choice_created", task_id=task_id, choice_index=choice_data.get('index'), has_url=bool(choice_data.get('url')))

                # Set completion timestamp
                if 'completed_at' in result_data:
                    from datetime import datetime
                    song.completed_at = datetime.fromtimestamp(result_data['completed_at'])

                db.commit()
                logger.info("song_result_updated", task_id=task_id, choices_count=len(choices_data))
                return True

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_result_update_db_error", task_id=task_id, error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("song_result_update_failed", task_id=task_id, error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return False
    
    def update_song_error(self, task_id: str, error_message: str) -> bool:
        """Update song with error information"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    logger.warning("song_not_found_for_error_update", task_id=task_id)
                    return False

                song.status = SongStatus.FAILURE.value
                song.error_message = error_message

                db.commit()
                logger.info("song_error_updated", task_id=task_id, error_message=error_message)
                return True

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_error_update_db_error", task_id=task_id, error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("song_error_update_failed", task_id=task_id, error=str(e), error_type=type(e).__name__)
            return False
    
    def cleanup_redis_data(self, task_id: str) -> bool:
        """Clean up Redis data after successful DB storage"""
        try:
            r = self._get_redis_connection()
            
            # Delete Celery task metadata
            celery_key = f"celery-task-meta-{task_id}"
            deleted = r.delete(celery_key)

            if deleted:
                logger.info("redis_cleanup_successful", task_id=task_id, deleted_keys=deleted)
            else:
                logger.debug("redis_cleanup_no_data", task_id=task_id)

            return True

        except redis.RedisError as e:
            logger.error("redis_cleanup_error", task_id=task_id, error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return False
        except Exception as e:
            logger.error("redis_cleanup_failed", task_id=task_id, error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return False
    
    def bulk_cleanup_completed_songs(self, limit: int = 100) -> Dict[str, Any]:
        """Bulk cleanup Redis data for completed songs in database"""
        try:
            db = next(get_db())
            try:
                # Get completed songs that might still have Redis data
                completed_songs = db.query(Song).filter(
                    Song.status == SongStatus.SUCCESS.value
                ).limit(limit).all()
                
                cleanup_results = {
                    "cleaned": 0,
                    "errors": 0,
                    "not_found": 0,
                    "task_ids": []
                }
                
                for song in completed_songs:
                    success = self.cleanup_redis_data(song.task_id)
                    if success:
                        cleanup_results["cleaned"] += 1
                        cleanup_results["task_ids"].append(song.task_id)
                    else:
                        cleanup_results["errors"] += 1

                logger.info("bulk_cleanup_completed", cleaned=cleanup_results["cleaned"], errors=cleanup_results["errors"], not_found=cleanup_results["not_found"])
                return cleanup_results

            finally:
                db.close()

        except Exception as e:
            logger.error("bulk_cleanup_failed", error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return {"error": str(e)}
    
    def get_song_choices(self, song_id) -> List[SongChoice]:
        """Get all choices for a specific song"""
        try:
            db = next(get_db())
            try:
                choices = db.query(SongChoice).filter(SongChoice.song_id == song_id).order_by(SongChoice.choice_index).all()
                logger.debug("song_choices_retrieved", song_id=str(song_id), choices_count=len(choices))
                return choices
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_choices", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
            return []
    
    def get_choice_by_mureka_id(self, mureka_choice_id: str) -> Optional[SongChoice]:
        """Get a specific choice by MUREKA choice ID"""
        try:
            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.mureka_choice_id == mureka_choice_id).first()
                if choice:
                    logger.debug("choice_retrieved_by_mureka_id", mureka_choice_id=mureka_choice_id, choice_id=str(choice.id))
                else:
                    logger.debug("choice_not_found_by_mureka_id", mureka_choice_id=mureka_choice_id)
                return choice
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_choice_by_mureka_id", mureka_choice_id=mureka_choice_id, error=str(e), error_type=type(e).__name__)
            return None
    
    def get_songs_paginated(self, limit: int = 20, offset: int = 0, status: str = None, search: str = '',
                           sort_by: str = 'created_at', sort_direction: str = 'desc', workflow: str = None) -> List[Song]:
        """
        Get songs with pagination, search and sorting

        Args:
            limit: Number of songs to return (default 20)
            offset: Number of songs to skip (default 0)
            status: Optional status filter (SUCCESS, PENDING, FAILURE, etc.)
            search: Search term to filter by title, lyrics, or tags
            sort_by: Field to sort by (created_at, title, lyrics)
            sort_direction: Sort direction (asc, desc)
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            List of Song instances with loaded choices
        """
        try:
            db = next(get_db())
            try:
                query = (db.query(Song)
                        .options(joinedload(Song.choices)))

                # Apply status filter if provided
                if status:
                    query = query.filter(Song.status == status)

                # Apply workflow filter if provided
                if workflow:
                    query = query.filter(Song.workflow == workflow)

                # Apply search filter if provided
                if search:
                    search_term = f"%{search}%"
                    from sqlalchemy import or_
                    query = query.filter(
                        or_(
                            Song.title.ilike(search_term),
                            Song.lyrics.ilike(search_term),
                            Song.tags.ilike(search_term)
                        )
                    )

                # Apply sorting
                if sort_by == 'title':
                    # Handle null titles by treating them as empty strings for sorting
                    if sort_direction == 'desc':
                        query = query.order_by(Song.title.desc().nullslast())
                    else:
                        query = query.order_by(Song.title.asc().nullsfirst())
                elif sort_by == 'lyrics':
                    if sort_direction == 'desc':
                        query = query.order_by(Song.lyrics.desc())
                    else:
                        query = query.order_by(Song.lyrics.asc())
                else:  # default to created_at
                    if sort_direction == 'desc':
                        query = query.order_by(Song.created_at.desc())
                    else:
                        query = query.order_by(Song.created_at.asc())

                songs = query.limit(limit).offset(offset).all()
                logger.debug("songs_retrieved_paginated", count=len(songs), limit=limit, offset=offset, status=status, search=search, workflow=workflow, sort_by=sort_by, sort_direction=sort_direction)
                return songs
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_paginated_songs", error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return []
    
    def get_total_songs_count(self, status: str = None, search: str = '', workflow: str = None) -> int:
        """
        Get total count of songs with optional search and workflow filter

        Args:
            status: Optional status filter
            search: Search term to filter by title, lyrics, or tags
            workflow: Optional workflow filter (onWork, inUse, notUsed)

        Returns:
            Total number of songs matching the criteria
        """
        try:
            db = next(get_db())
            try:
                query = db.query(Song)

                if status:
                    query = query.filter(Song.status == status)

                # Apply workflow filter if provided
                if workflow:
                    query = query.filter(Song.workflow == workflow)

                # Apply search filter if provided
                if search:
                    search_term = f"%{search}%"
                    from sqlalchemy import or_
                    query = query.filter(
                        or_(
                            Song.title.ilike(search_term),
                            Song.lyrics.ilike(search_term),
                            Song.tags.ilike(search_term)
                        )
                    )

                count = query.count()
                logger.debug("total_songs_count_retrieved", count=count, status=status, search=search, workflow=workflow)
                return count
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_total_songs_count", error=str(e), error_type=type(e).__name__)
            return 0
    
    def get_song_by_id(self, song_id) -> Optional[Song]:
        """
        Get song by ID with loaded choices
        
        Args:
            song_id: UUID of the song
            
        Returns:
            Song instance with loaded choices, or None if not found
        """
        try:
            db = next(get_db())
            try:
                song = (db.query(Song)
                       .options(joinedload(Song.choices))
                       .filter(Song.id == song_id)
                       .first())
                if song:
                    logger.debug("song_retrieved_by_id", song_id=str(song_id), choices_count=len(song.choices))
                else:
                    logger.debug("song_not_found_by_id", song_id=str(song_id))
                return song
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_song_by_id", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
            return None
    
    def get_recent_songs(self, limit: int = 10) -> List[Song]:
        """
        Get most recently created songs
        
        Args:
            limit: Number of songs to return
            
        Returns:
            List of Song instances with loaded choices
        """
        try:
            db = next(get_db())
            try:
                songs = (db.query(Song)
                        .options(joinedload(Song.choices))
                        .order_by(Song.created_at.desc())
                        .limit(limit)
                        .all())
                logger.debug("recent_songs_retrieved", count=len(songs), limit=limit)
                return songs
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_recent_songs", error=str(e), error_type=type(e).__name__)
            return []
    
    def delete_song_by_id(self, song_id) -> bool:
        """
        Delete song and all its choices by ID
        
        Args:
            song_id: UUID of the song
            
        Returns:
            True if successful, False otherwise
        """
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.id == song_id).first()
                if song:
                    db.delete(song)  # Cascade will delete choices
                    db.commit()
                    logger.info("song_deleted", song_id=str(song_id))
                    return True
                logger.warning("song_not_found_for_deletion", song_id=str(song_id))
                return False
            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_deletion_db_error", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()
        except Exception as e:
            logger.error("song_deletion_failed", song_id=str(song_id), error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return False

    def update_song(self, song_id: str, update_data: Dict[str, Any]) -> Optional[Song]:
        """
        Update song fields by ID

        Args:
            song_id: UUID of the song
            update_data: Dictionary with fields to update (title, tags, etc.)

        Returns:
            Updated Song object if successful, None otherwise
        """
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.id == song_id).first()
                if not song:
                    logger.warning("song_not_found_for_update", song_id=str(song_id))
                    return None

                # Update allowed fields
                if 'title' in update_data:
                    song.title = update_data['title']
                if 'tags' in update_data:
                    song.tags = update_data['tags']
                if 'workflow' in update_data:
                    song.workflow = update_data['workflow']

                # Update timestamp
                song.updated_at = datetime.utcnow()

                db.commit()

                # Create a detached copy of the song object with updated fields
                updated_song_data = {
                    'id': song.id,
                    'title': song.title,
                    'tags': song.tags,
                    'workflow': song.workflow,
                    'updated_at': song.updated_at
                }

                logger.info("song_updated", song_id=str(song_id), fields_updated=list(update_data.keys()))

                # Return a simple object with the data we need
                class UpdatedSong:
                    def __init__(self, data):
                        self.id = data['id']
                        self.title = data['title']
                        self.tags = data['tags']
                        self.workflow = data['workflow']
                        self.updated_at = data['updated_at']

                return UpdatedSong(updated_song_data)

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("song_update_db_error", song_id=str(song_id), error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("song_update_failed", song_id=str(song_id), error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return None

    def update_choice_rating(self, choice_id: str, rating: Optional[int]) -> bool:
        """
        Update rating for a specific song choice

        Args:
            choice_id: UUID of the choice
            rating: Rating value (None=unset, 0=thumbs down, 1=thumbs up)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate rating value
            if rating is not None and rating not in [0, 1]:
                logger.warning("invalid_rating_value", choice_id=str(choice_id), rating=rating)
                return False

            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.id == choice_id).first()
                if not choice:
                    logger.warning("choice_not_found_for_rating_update", choice_id=str(choice_id))
                    return False

                choice.rating = rating
                choice.updated_at = datetime.utcnow()

                db.commit()
                logger.info("choice_rating_updated", choice_id=str(choice_id), rating=rating)
                return True

            except SQLAlchemyError as e:
                db.rollback()
                logger.error("choice_rating_update_db_error", choice_id=str(choice_id), error=str(e), error_type=type(e).__name__)
                raise
            finally:
                db.close()

        except Exception as e:
            logger.error("choice_rating_update_failed", choice_id=str(choice_id), error=str(e), error_type=type(e).__name__, stacktrace=traceback.format_exc())
            return False

    def get_choice_by_id(self, choice_id: str) -> Optional[SongChoice]:
        """
        Get a specific choice by ID

        Args:
            choice_id: UUID of the choice

        Returns:
            SongChoice instance or None if not found
        """
        try:
            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.id == choice_id).first()
                if choice:
                    logger.debug("choice_retrieved_by_id", choice_id=str(choice_id))
                else:
                    logger.debug("choice_not_found_by_id", choice_id=str(choice_id))
                return choice
            finally:
                db.close()
        except Exception as e:
            logger.error("error_getting_choice_by_id", choice_id=str(choice_id), error=str(e), error_type=type(e).__name__)
            return None


# Global service instance
song_service = SongService()