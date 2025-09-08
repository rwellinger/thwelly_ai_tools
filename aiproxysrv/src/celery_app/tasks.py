"""
Celery Tasks für Song-Generierung
"""
import time
from celery.exceptions import SoftTimeLimitExceeded
from requests import HTTPError

from .celery_config import celery_app
from .slot_manager import wait_for_mureka_slot, release_mureka_slot
from mureka.client import start_mureka_generation, wait_for_mureka_completion
from mureka.handlers import handle_http_error


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_song_task(self, payload: dict) -> dict:
    """Celery Task für Song-Generierung"""
    task_id = self.request.id
    print(f"Starting song generation task: {task_id}")

    try:
        # Warte auf verfügbaren MUREKA Slot
        if not wait_for_mureka_slot(task_id):
            print(f"Task {task_id} waiting for MUREKA slot")
            raise self.retry(exc=Exception("No available MUREKA slot"), countdown=60)

        # Slot acquired - update status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'SLOT_ACQUIRED', 'message': 'Acquired MUREKA slot'}
        )

        print(f"Slot acquired for task {task_id}, starting MUREKA generation")

        # Starte die Generierung bei MUREKA
        initial_response = start_mureka_generation(payload)
        job_id = initial_response.get("id")

        if not job_id:
            raise Exception("No job ID received from MUREKA")

        # Warte auf Completion
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'GENERATION_STARTED',
                'job_id': job_id,
            }
        )

        print(f"Waiting for completion of job: {job_id}")
        final_result = wait_for_mureka_completion(self, job_id)

        # Erfolgreich abgeschlossen
        return {
            "status": "SUCCESS",
            "task_id": task_id,
            "job_id": job_id,
            "result": final_result,
            "completed_at": time.time()
        }

    except SoftTimeLimitExceeded:
        print(f"Task {task_id} timeout exceeded")
        release_mureka_slot(task_id)
        return {
            "status": "ERROR",
            "message": "Task timeout exceeded",
            "task_id": task_id
        }

    except HTTPError as e:
        print(f"HTTP error in task {task_id}: {e}")
        release_mureka_slot(task_id)

        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 60))
            print(f"Rate limited, retrying in {retry_after}s")
            raise self.retry(exc=e, countdown=retry_after)
        else:
            return handle_http_error(self, e)

    except Exception as exc:
        print(f"Error in task {task_id}: {exc}")
        release_mureka_slot(task_id)
        raise self.retry(exc=exc, countdown=60)

    finally:
        try:
            release_mureka_slot(task_id)
        except:
            pass