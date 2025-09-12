"""
Celery Tasks für Song-Generierung
"""
import sys
import traceback
import time
from celery.exceptions import SoftTimeLimitExceeded
from requests import HTTPError

from .celery_config import celery_app
from .slot_manager import wait_for_mureka_slot, release_mureka_slot
from mureka.client import start_mureka_generation, wait_for_mureka_completion
from mureka.handlers import handle_http_error
from db.song_service import song_service


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_song_task(self, payload: dict) -> dict:
    """Celery Task für Song-Generierung"""
    task_id = self.request.id
    print(f"Starting song generation task: {task_id}", file=sys.stderr)

    try:
        # Warte auf verfügbaren MUREKA Slot
        print(f"Task {task_id}: Waiting for MUREKA slot", file=sys.stderr)
        if not wait_for_mureka_slot(task_id):
            print(f"Task {task_id}: No MUREKA slot available, retrying", file=sys.stderr)
            raise self.retry(exc=Exception("No available MUREKA slot"), countdown=60)

        # Slot acquired - update status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'SLOT_ACQUIRED', 'message': 'Acquired MUREKA slot'}
        )
        
        # Update song status in database
        song_service.update_song_status(
            task_id=task_id,
            status='PROGRESS',
            progress_info={'status': 'SLOT_ACQUIRED', 'message': 'Acquired MUREKA slot'}
        )

        print(f"Task {task_id}: Slot acquired, starting MUREKA generation", file=sys.stderr)

        # Starte die Generierung bei MUREKA
        initial_response = start_mureka_generation(payload)
        job_id = initial_response.get("id")

        if not job_id:
            print(f"Task {task_id}: No job ID received from MUREKA", file=sys.stderr)
            raise Exception("No job ID received from MUREKA")

        # Warte auf Completion
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'GENERATION_STARTED',
                'job_id': job_id,
            }
        )
        
        # Update song status in database with job_id
        song_service.update_song_status(
            task_id=task_id,
            status='PROGRESS',
            progress_info={
                'status': 'GENERATION_STARTED',
                'job_id': job_id,
            },
            job_id=job_id
        )

        print(f"Task {task_id}: Waiting for completion of job: {job_id}", file=sys.stderr)
        final_result = wait_for_mureka_completion(self, job_id)

        # Erfolgreich abgeschlossen
        print(f"Task {task_id}: Completed successfully", file=sys.stderr)
        
        # Prepare success result
        success_result = {
            "status": "SUCCESS",
            "task_id": task_id,
            "job_id": job_id,
            "result": final_result,
            "completed_at": time.time()
        }
        
        # Update song result in database
        if song_service.update_song_result(task_id, success_result):
            print(f"Task {task_id}: Successfully updated song result in database", file=sys.stderr)
            # Clean up Redis data after successful DB storage
            song_service.cleanup_redis_data(task_id)
        else:
            print(f"Task {task_id}: Failed to update song result in database", file=sys.stderr)
        
        return success_result

    except SoftTimeLimitExceeded:
        print(f"Task {task_id}: Timeout exceeded", file=sys.stderr)
        release_mureka_slot(task_id)
        
        # Update song error in database
        error_msg = "Task timeout exceeded"
        song_service.update_song_error(task_id, error_msg)
        
        return {
            "status": "ERROR",
            "message": error_msg,
            "task_id": task_id
        }

    except HTTPError as e:
        print(f"Task {task_id}: HTTP error: {e}", file=sys.stderr)
        print(f"Response content: {e.response.text if e.response else 'No response'}", file=sys.stderr)
        release_mureka_slot(task_id)

        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            print(f"Task {task_id}: Rate limited, retrying in {retry_after}s", file=sys.stderr)
            raise self.retry(exc=e, countdown=retry_after)
        else:
            # Update song error in database for non-retry HTTP errors
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text if e.response else 'No response'}"
            song_service.update_song_error(task_id, error_msg)
            return handle_http_error(self, e)

    except Exception as exc:
        print(f"Task {task_id}: Unexpected error: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        release_mureka_slot(task_id)
        
        # Update song error in database for unexpected errors
        error_msg = f"Unexpected error: {type(exc).__name__}: {str(exc)}"
        song_service.update_song_error(task_id, error_msg)
        
        raise self.retry(exc=exc, countdown=60)

    finally:
        try:
            release_mureka_slot(task_id)
        except Exception as e:
            print(f"Task {task_id}: Error releasing slot: {e}", file=sys.stderr)