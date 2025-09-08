"""
MUREKA API Client
"""
import requests
import time
from typing import Dict, Any
from requests import HTTPError
from config.settings import (
    MUREKA_GENERATE_ENDPOINT,
    MUREKA_STATUS_ENDPOINT,
    MUREKA_API_KEY,
    MUREKA_TIMEOUT,
    MUREKA_POLL_INTERVAL,
    MUREKA_MAX_POLL_ATTEMPTS
)


def start_mureka_generation(payload: dict) -> Dict[str, Any]:
    """Startet eine MUREKA Generierung"""
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
    """Überprüft den Status einer MUREKA Generierung"""
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
    """Wartet auf die Vollendung einer MUREKA Generierung"""
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
