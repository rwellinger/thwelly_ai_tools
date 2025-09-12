"""Song Service - Database operations for song management"""
import json
import sys
import redis
import traceback
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from db.models import Song, SongChoice, SongStatus
from db.database import get_db
from config.settings import CELERY_BROKER_URL


class SongService:
    """Service for song database operations"""
    
    def __init__(self):
        self.redis_url = CELERY_BROKER_URL
    
    def _get_redis_connection(self) -> redis.Redis:
        """Get Redis connection"""
        return redis.from_url(self.redis_url)
    
    def create_song(self, task_id: str, lyrics: str, prompt: str, model: str = "chirp-v3-5") -> Optional[Song]:
        """Create a new song record in the database"""
        try:
            db = next(get_db())
            try:
                song = Song(
                    task_id=task_id,
                    lyrics=lyrics,
                    prompt=prompt,
                    model=model,
                    status=SongStatus.PENDING.value
                )
                
                db.add(song)
                db.commit()
                db.refresh(song)
                
                print(f"Created song record: task_id={task_id}, id={song.id}", file=sys.stderr)
                return song
                
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Database error creating song: {e}", file=sys.stderr)
                raise
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error creating song: {e}", file=sys.stderr)
            return None
    
    def get_song_by_task_id(self, task_id: str) -> Optional[Song]:
        """Get song by task_id with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.task_id == task_id).first()
                print(f"Retrieved song by task_id {task_id}: {'Found' if song else 'Not found'}", file=sys.stderr)
                if song:
                    print(f"Song has {len(song.choices)} choices", file=sys.stderr)
                return song
            finally:
                db.close()
        except Exception as e:
            print(f"Error getting song by task_id {task_id}: {e}", file=sys.stderr)
            return None
    
    def get_song_by_job_id(self, job_id: str) -> Optional[Song]:
        """Get song by job_id (MUREKA job ID) with choices loaded"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).options(joinedload(Song.choices)).filter(Song.job_id == job_id).first()
                print(f"Retrieved song by job_id {job_id}: {'Found' if song else 'Not found'}", file=sys.stderr)
                if song:
                    print(f"Song has {len(song.choices)} choices", file=sys.stderr)
                return song
            finally:
                db.close()
        except Exception as e:
            print(f"Error getting song by job_id {job_id}: {e}", file=sys.stderr)
            return None
    
    def update_song_status(self, task_id: str, status: str, progress_info: Optional[Dict[str, Any]] = None, job_id: Optional[str] = None) -> bool:
        """Update song status and progress information"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    print(f"Song not found for task_id: {task_id}", file=sys.stderr)
                    return False
                
                song.status = status
                if progress_info:
                    song.progress_info = json.dumps(progress_info)
                if job_id:
                    song.job_id = job_id
                
                db.commit()
                print(f"Updated song status: task_id={task_id}, status={status}, job_id={job_id}", file=sys.stderr)
                return True
                
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Database error updating song status: {e}", file=sys.stderr)
                raise
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error updating song status: {e}", file=sys.stderr)
            return False
    
    def update_song_result(self, task_id: str, result_data: Dict[str, Any]) -> bool:
        """Update song with completion results and create choices"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    print(f"Song not found for task_id: {task_id}", file=sys.stderr)
                    return False
                
                # Update status to SUCCESS
                song.status = SongStatus.SUCCESS.value
                
                # Store complete MUREKA response
                if 'result' in result_data and result_data['result']:
                    mureka_result = result_data['result']
                    song.mureka_response = json.dumps(mureka_result)
                    song.mureka_status = mureka_result.get('status')
                    
                    # Process choices array
                    choices_data = mureka_result.get('choices', [])
                    print(f"Processing {len(choices_data)} choices for task_id={task_id}", file=sys.stderr)
                    
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
                        print(f"Created choice {choice_data.get('index', 'N/A')}: {choice_data.get('url', 'No URL')}", file=sys.stderr)
                
                # Set completion timestamp
                if 'completed_at' in result_data:
                    from datetime import datetime
                    song.completed_at = datetime.fromtimestamp(result_data['completed_at'])
                
                db.commit()
                print(f"Updated song result with {len(choices_data)} choices: task_id={task_id}", file=sys.stderr)
                return True
                
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Database error updating song result: {e}", file=sys.stderr)
                print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
                raise
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error updating song result: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return False
    
    def update_song_error(self, task_id: str, error_message: str) -> bool:
        """Update song with error information"""
        try:
            db = next(get_db())
            try:
                song = db.query(Song).filter(Song.task_id == task_id).first()
                if not song:
                    print(f"Song not found for task_id: {task_id}", file=sys.stderr)
                    return False
                
                song.status = SongStatus.FAILURE.value
                song.error_message = error_message
                
                db.commit()
                print(f"Updated song error: task_id={task_id}, error={error_message}", file=sys.stderr)
                return True
                
            except SQLAlchemyError as e:
                db.rollback()
                print(f"Database error updating song error: {e}", file=sys.stderr)
                raise
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error updating song error: {e}", file=sys.stderr)
            return False
    
    def cleanup_redis_data(self, task_id: str) -> bool:
        """Clean up Redis data after successful DB storage"""
        try:
            r = self._get_redis_connection()
            
            # Delete Celery task metadata 
            celery_key = f"celery-task-meta-{task_id}"
            deleted = r.delete(celery_key)
            
            if deleted:
                print(f"Successfully cleaned up Redis data for task_id: {task_id}", file=sys.stderr)
            else:
                print(f"No Redis data found to cleanup for task_id: {task_id}", file=sys.stderr)
            
            return True
            
        except redis.RedisError as e:
            print(f"Redis error cleaning up data for {task_id}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error cleaning up Redis data for {task_id}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
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
                
                print(f"Bulk cleanup results: {cleanup_results}", file=sys.stderr)
                return cleanup_results
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error in bulk cleanup: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {"error": str(e)}
    
    def get_song_choices(self, song_id: int) -> List[SongChoice]:
        """Get all choices for a specific song"""
        try:
            db = next(get_db())
            try:
                choices = db.query(SongChoice).filter(SongChoice.song_id == song_id).order_by(SongChoice.choice_index).all()
                print(f"Retrieved {len(choices)} choices for song_id={song_id}", file=sys.stderr)
                return choices
            finally:
                db.close()
        except Exception as e:
            print(f"Error getting song choices for song_id {song_id}: {e}", file=sys.stderr)
            return []
    
    def get_choice_by_mureka_id(self, mureka_choice_id: str) -> Optional[SongChoice]:
        """Get a specific choice by MUREKA choice ID"""
        try:
            db = next(get_db())
            try:
                choice = db.query(SongChoice).filter(SongChoice.mureka_choice_id == mureka_choice_id).first()
                print(f"Retrieved choice by mureka_choice_id {mureka_choice_id}: {'Found' if choice else 'Not found'}", file=sys.stderr)
                return choice
            finally:
                db.close()
        except Exception as e:
            print(f"Error getting choice by mureka_choice_id {mureka_choice_id}: {e}", file=sys.stderr)
            return None


# Global service instance
song_service = SongService()