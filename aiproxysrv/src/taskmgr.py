import os
import requests
import time
from celery import Celery
from requests import HTTPError
from typing import Dict, Any
from celery.exceptions import SoftTimeLimitExceeded
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# Celery‑Setup
# --------------------------------------------------
celery_app = Celery(
    "taskmgr",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND"),
)

celery_app.conf.broker_connection_retry_on_startup = True
celery_app.conf.task_time_limit = 1800
celery_app.conf.task_soft_time_limit = 1500
celery_app.conf.worker_concurrency = 1
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.task_acks_late = True

# --------------------------------------------------
# MUREKA Config
# --------------------------------------------------
MUREKA_GENERATE_ENDPOINT = os.getenv("MUREKA_GENERATE_ENDPOINT")
MUREKA_STATUS_ENDPOINT = os.getenv("MUREKA_STATUS_ENDPOINT")
MUREKA_API_KEY = os.getenv("MUREKA_API_KEY")
MUREKA_TIMEOUT = int(os.getenv("MUREKA_TIMEOUT", "30"))
MUREKA_POLL_INTERVAL = int(os.getenv("MUREKA_POLL_INTERVAL", "15"))
MUREKA_MAX_POLL_ATTEMPTS = int(os.getenv("MUREKA_MAX_POLL_ATTEMPTS", "240"))  # 60 Minuten

current_requests = 0
active_tasks = {}


# --------------------------------------------------
# Helper: Simple Slot Management
# --------------------------------------------------
def acquire_mureka_slot(task_id: str) -> bool:
    global current_requests
    try:
        if current_requests >= 1:
            return False
        current_requests += 1
        active_tasks[task_id] = time.time()
        return True
    except Exception as e:
        print(f"Error in acquire_mureka_slot: {e}")
        return False


def release_mureka_slot(task_id: str):
    global current_requests
    try:
        if current_requests > 0:
            current_requests -= 1
        if task_id in active_tasks:
            del active_tasks[task_id]
    except Exception as e:
        print(f"Error in release_mureka_slot: {e}")


def wait_for_mureka_slot(task_id: str, max_wait: int = 3600) -> bool:
    start_time = time.time()

    while time.time() - start_time < max_wait:
        if acquire_mureka_slot(task_id):
            return True
        time.sleep(10)
    return False


# --------------------------------------------------
# Helper: MUREKA‑Requests
# --------------------------------------------------
def start_mureka_generation(payload: dict) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"Starting MUREKA generation")

    resp = requests.post(
        MUREKA_GENERATE_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=MUREKA_TIMEOUT,
    )
    resp.raise_for_status()

    response_data = resp.json()
    job_id = response_data.get("id")
    print(f"MUREKA generation started. Job ID: {job_id}")
    return response_data


def check_mureka_status(job_id: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
    }

    status_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"
    print(f"Checking MUREKA status: {status_url}")

    resp = requests.get(
        status_url,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()

    status_data = resp.json()
    print(f"MUREKA status for job {job_id}: {status_data.get('status')}")
    return status_data


def wait_for_mureka_completion(task, job_id: str) -> Dict[str, Any]:
    max_attempts = MUREKA_MAX_POLL_ATTEMPTS
    poll_interval = MUREKA_POLL_INTERVAL

    for attempt in range(max_attempts):
        try:
            status_response = check_mureka_status(job_id)
            current_status = status_response.get("status", "unknown")

            task.update_state(
                state='PROGRESS',
                meta={
                    'status': 'POLLING',
                    'job_id': job_id,
                    'attempt': attempt + 1,
                    'mureka_status': current_status,
                    'progress': status_response.get("progress", 0),
                }
            )

            if current_status == "succeeded":
                print(f"MUREKA job completed: {job_id}")
                return status_response

            elif current_status in ["failed", "cancelled"]:
                error_reason = status_response.get("failed_reason", "Song processing failed")
                print(f"MUREKA job failed: {job_id} - {error_reason}")
                raise Exception(f"Job failed: {error_reason}")

            elif current_status in ["preparing", "queued", "running", "timeouted"]:
                print(f"MUREKA job {job_id}: {current_status}")
                time.sleep(poll_interval)

            else:
                print(f"Unknown MUREKA status: {current_status} for job {job_id}")
                time.sleep(poll_interval)

        except HTTPError as e:
            if e.response.status_code in [429, 502, 503, 504]:
                # Temporäre Fehler - weiter versuchen
                wait_time = poll_interval * 2
                print(f"Temporary error ({e.response.status_code}), retrying in {wait_time}s")
                time.sleep(wait_time)
                continue
            else:
                print(f"HTTP error checking status: {e}")
                raise

    raise Exception(f"Timeout after {max_attempts} polling attempts ({(max_attempts * poll_interval) // 60} minutes)")


# --------------------------------------------------
# Celery‑Tasks
# --------------------------------------------------
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_song_task(self, payload: dict) -> dict:
    task_id = self.request.id
    print(f"Starting song generation task: {task_id}")

    try:
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


# --------------------------------------------------
# Error Handling
# --------------------------------------------------
def handle_http_error(task, error: HTTPError) -> dict:
    resp = error.response
    status_code = resp.status_code

    try:
        error_body = resp.json()
        message = error_body.get("message") or error_body.get("error") or resp.text
    except ValueError:
        message = resp.text or resp.reason

    error_payload = {
        "status": "ERROR",
        "http_code": status_code,
        "message": message,
        "task_id": task.request.id,
    }

    if status_code == 429:
        rate_headers = {
            "Retry-After": resp.headers.get("Retry-After"),
            "X-RateLimit-Limit": resp.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Remaining": resp.headers.get("X-RateLimit-Remaining"),
            "X-RateLimit-Reset": resp.headers.get("X-RateLimit-Reset"),
        }
        error_payload["rate_limit_info"] = {k: v for k, v in rate_headers.items() if v}

    return error_payload


def handle_general_error(task, error: Exception) -> dict:
    return {
        "status": "ERROR",
        "http_code": None,
        "message": str(error),
        "task_id": task.request.id,
    }
