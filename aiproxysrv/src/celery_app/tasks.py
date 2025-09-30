"""
Celery Tasks für Song-Generierung
"""
import traceback
import time
from celery.exceptions import SoftTimeLimitExceeded
from requests import HTTPError

from .celery_config import celery_app
from .slot_manager import wait_for_mureka_slot, release_mureka_slot
from mureka import start_mureka_generation, wait_for_mureka_completion, start_mureka_instrumental_generation, wait_for_mureka_instrumental_completion
from mureka.handlers import handle_http_error
from db.song_service import song_service
from utils.logger import logger


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_song_task(self, payload: dict) -> dict:
    """Celery Task für Song-Generierung"""
    task_id = self.request.id
    logger.info("Starting song generation task", extra={"task_id": task_id})

    try:
        # Warte auf verfügbaren MUREKA Slot
        logger.info("Waiting for MUREKA slot", extra={"task_id": task_id})
        if not wait_for_mureka_slot(task_id):
            logger.warning("No MUREKA slot available, retrying", extra={"task_id": task_id})
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

        logger.info("Slot acquired, starting MUREKA generation", extra={"task_id": task_id})

        # Starte die Generierung bei MUREKA
        initial_response = start_mureka_generation(payload)
        job_id = initial_response.get("id")

        if not job_id:
            logger.error("No job ID received from MUREKA", extra={"task_id": task_id})
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

        logger.info("Waiting for completion", extra={"task_id": task_id, "job_id": job_id})
        final_result = wait_for_mureka_completion(self, job_id)

        # Erfolgreich abgeschlossen
        logger.info("Completed successfully", extra={"task_id": task_id, "job_id": job_id})
        
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
            logger.info("Successfully updated song result in database", extra={"task_id": task_id, "job_id": job_id})
            # Clean up Redis data after successful DB storage
            song_service.cleanup_redis_data(task_id)
        else:
            logger.error("Failed to update song result in database", extra={"task_id": task_id, "job_id": job_id})
        
        return success_result

    except SoftTimeLimitExceeded:
        logger.error("Task timeout exceeded", extra={"task_id": task_id})
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
        logger.error("HTTP error occurred", extra={
            "task_id": task_id,
            "error": str(e),
            "response": e.response.text if e.response else 'No response'
        })
        release_mureka_slot(task_id)

        if e.response.status_code == 429:
            # Analyze 429 error type for retry decision
            try:
                error_body = e.response.json()
                error_message = error_body.get("message") or error_body.get("error") or e.response.text
            except ValueError:
                error_message = e.response.text or e.response.reason

            from mureka.handlers import analyze_429_error_type
            error_type = analyze_429_error_type(error_message)

            if error_type == 'quota':
                # Quota exceeded - don't retry, update song with error
                error_msg = f"Quota exceeded: {error_message}"
                song_service.update_song_error(task_id, error_msg)
                logger.error("Quota exceeded, not retrying", extra={"task_id": task_id, "error_message": error_message})
                return handle_http_error(self, e)
            else:
                # Rate limit - retry with backoff
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning("Rate limited, retrying", extra={"task_id": task_id, "retry_after": retry_after})
                raise self.retry(exc=e, countdown=retry_after)
        else:
            # Update song error in database for non-retry HTTP errors
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text if e.response else 'No response'}"
            song_service.update_song_error(task_id, error_msg)
            return handle_http_error(self, e)

    except Exception as exc:
        logger.error("Unexpected error occurred", extra={
            "task_id": task_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "stacktrace": traceback.format_exc()
        })
        release_mureka_slot(task_id)

        # Update song error in database for unexpected errors
        error_msg = f"Unexpected error: {type(exc).__name__}: {str(exc)}"
        song_service.update_song_error(task_id, error_msg)

        raise self.retry(exc=exc, countdown=60)

    finally:
        try:
            release_mureka_slot(task_id)
        except Exception as e:
            logger.error("Error releasing slot", extra={"task_id": task_id, "error": str(e)})


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_instrumental_task(self, payload: dict) -> dict:
    """Celery Task für Instrumental-Generierung"""
    task_id = self.request.id
    logger.info("Starting instrumental generation task", extra={"task_id": task_id})

    try:
        # Warte auf verfügbaren MUREKA Slot
        logger.info("Waiting for MUREKA slot", extra={"task_id": task_id, "type": "instrumental"})
        if not wait_for_mureka_slot(task_id):
            logger.warning("No MUREKA slot available, retrying", extra={"task_id": task_id, "type": "instrumental"})
            raise self.retry(exc=Exception("No available MUREKA slot"), countdown=60)

        # Slot acquired - update status
        self.update_state(
            state='PROGRESS',
            meta={'status': 'SLOT_ACQUIRED', 'message': 'Acquired MUREKA slot for instrumental generation'}
        )

        # Update song status in database - mark as instrumental
        song_service.update_song_status(
            task_id=task_id,
            status='PROGRESS',
            progress_info={'status': 'SLOT_ACQUIRED', 'message': 'Acquired MUREKA slot for instrumental generation'}
        )

        logger.info("Slot acquired, starting MUREKA instrumental generation", extra={"task_id": task_id})

        # Starte die Instrumental-Generierung bei MUREKA
        initial_response = start_mureka_instrumental_generation(payload)
        job_id = initial_response.get("id")

        if not job_id:
            logger.error("No job ID received from MUREKA instrumental", extra={"task_id": task_id})
            raise Exception("No job ID received from MUREKA instrumental")

        # Warte auf Completion
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'GENERATION_STARTED',
                'job_id': job_id,
                'type': 'instrumental'
            }
        )

        # Update song status in database with job_id and instrumental flag
        song_service.update_song_status(
            task_id=task_id,
            status='PROGRESS',
            progress_info={
                'status': 'GENERATION_STARTED',
                'job_id': job_id,
                'type': 'instrumental'
            },
            job_id=job_id
        )

        logger.info("Waiting for instrumental completion", extra={"task_id": task_id, "job_id": job_id, "type": "instrumental"})
        final_result = wait_for_mureka_instrumental_completion(self, job_id)

        # Erfolgreich abgeschlossen
        logger.info("Instrumental completed successfully", extra={"task_id": task_id, "job_id": job_id})

        # Prepare success result
        success_result = {
            "status": "SUCCESS",
            "task_id": task_id,
            "job_id": job_id,
            "result": final_result,
            "completed_at": time.time(),
            "is_instrumental": True
        }

        # Update song result in database with instrumental flag
        if song_service.update_song_result(task_id, success_result):
            logger.info("Successfully updated instrumental song result in database", extra={"task_id": task_id, "job_id": job_id})
            # Clean up Redis data after successful DB storage
            song_service.cleanup_redis_data(task_id)
        else:
            logger.error("Failed to update instrumental song result in database", extra={"task_id": task_id, "job_id": job_id})

        return success_result

    except SoftTimeLimitExceeded:
        logger.error("Instrumental timeout exceeded", extra={"task_id": task_id})
        release_mureka_slot(task_id)

        # Update song error in database
        error_msg = "Instrumental task timeout exceeded"
        song_service.update_song_error(task_id, error_msg)

        return {
            "status": "ERROR",
            "message": error_msg,
            "task_id": task_id,
            "is_instrumental": True
        }

    except HTTPError as e:
        logger.error("Instrumental HTTP error occurred", extra={
            "task_id": task_id,
            "error": str(e),
            "response": e.response.text if e.response else 'No response'
        })
        release_mureka_slot(task_id)

        if e.response.status_code == 429:
            # Analyze 429 error type for retry decision
            try:
                error_body = e.response.json()
                error_message = error_body.get("message") or error_body.get("error") or e.response.text
            except ValueError:
                error_message = e.response.text or e.response.reason

            from mureka.handlers import analyze_429_error_type
            error_type = analyze_429_error_type(error_message)

            if error_type == 'quota':
                # Quota exceeded - don't retry, update song with error
                error_msg = f"Instrumental quota exceeded: {error_message}"
                song_service.update_song_error(task_id, error_msg)
                logger.error("Instrumental quota exceeded, not retrying", extra={"task_id": task_id, "error_message": error_message})
                return handle_http_error(self, e)
            else:
                # Rate limit - retry with backoff
                retry_after = int(e.response.headers.get('Retry-After', 60))
                logger.warning("Instrumental rate limited, retrying", extra={"task_id": task_id, "retry_after": retry_after})
                raise self.retry(exc=e, countdown=retry_after)
        else:
            # Update song error in database for non-retry HTTP errors
            error_msg = f"Instrumental HTTP error: {e.response.status_code} - {e.response.text if e.response else 'No response'}"
            song_service.update_song_error(task_id, error_msg)
            return handle_http_error(self, e)

    except Exception as exc:
        logger.error("Unexpected instrumental error occurred", extra={
            "task_id": task_id,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "stacktrace": traceback.format_exc()
        })
        release_mureka_slot(task_id)

        # Update song error in database for unexpected errors
        error_msg = f"Unexpected instrumental error: {type(exc).__name__}: {str(exc)}"
        song_service.update_song_error(task_id, error_msg)

        raise self.retry(exc=exc, countdown=60)

    finally:
        try:
            release_mureka_slot(task_id)
        except Exception as e:
            logger.error("Error releasing slot", extra={"task_id": task_id, "error": str(e)})