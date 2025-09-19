"""
MUREKA API Client
"""
import sys
import traceback
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
    MUREKA_MAX_POLL_ATTEMPTS,
    MUREKA_POLL_INTERVAL_SHORT,
    MUREKA_POLL_INTERVAL_MEDIUM,
    MUREKA_POLL_INTERVAL_LONG
)
from api.json_helpers import prune

def start_mureka_generation(payload: dict) -> Dict[str, Any]:
    """Startet eine MUREKA Generierung"""
    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"Starting MUREKA generation - Endpoint: {MUREKA_GENERATE_ENDPOINT}", file=sys.stderr)
    
    try:
        resp = requests.post(
            MUREKA_GENERATE_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=MUREKA_TIMEOUT,
        )
        print(f"MUREKA API Response Status: {resp.status_code}", file=sys.stderr)
        resp.raise_for_status()

        response_data = resp.json()
        job_id = response_data.get("id")
        print(f"MUREKA generation started successfully. Job ID: {job_id}", file=sys.stderr)
        return response_data
    except HTTPError as e:
        print(f"MUREKA API HTTP Error: {e}", file=sys.stderr)
        print(f"Response content: {e.response.text if e.response else 'No response'}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"MUREKA generation error: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        raise


def check_mureka_status(job_id: str) -> Dict[str, Any]:
    """Überprüft den Status einer MUREKA Generierung"""
    headers = {
        "Authorization": f"Bearer {MUREKA_API_KEY}",
    }

    status_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"
    print(f"Checking MUREKA status: {status_url}", file=sys.stderr)

    try:
        resp = requests.get(
            status_url,
            headers=headers,
            timeout=30,
        )
        print(f"MUREKA Status API Response: {resp.status_code}", file=sys.stderr)
        resp.raise_for_status()

        status_data = resp.json()
        print(f"MUREKA status for job {job_id}: {status_data.get('status')}", file=sys.stderr)
        return status_data
    except HTTPError as e:
        print(f"MUREKA Status API HTTP Error: {e}", file=sys.stderr)
        print(f"Response content: {e.response.text if e.response else 'No response'}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"MUREKA status check error: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
        raise


def get_adaptive_poll_interval(elapsed_seconds: float) -> int:
    """
    Berechnet adaptives Polling-Intervall basierend auf elapsed time:
    - 0-2 Min: MUREKA_POLL_INTERVAL_SHORT (default 5s)
    - 2-5 Min: MUREKA_POLL_INTERVAL_MEDIUM (default 15s)
    - 5+ Min: MUREKA_POLL_INTERVAL_LONG (default 30s)
    """
    if elapsed_seconds < 120:  # 0-2 Minuten
        return MUREKA_POLL_INTERVAL_SHORT
    elif elapsed_seconds < 300:  # 2-5 Minuten
        return MUREKA_POLL_INTERVAL_MEDIUM
    else:  # 5+ Minuten
        return MUREKA_POLL_INTERVAL_LONG


def wait_for_mureka_completion(task, job_id: str) -> Dict[str, Any]:
    """Wartet auf die Vollendung einer MUREKA Generierung"""
    max_attempts = MUREKA_MAX_POLL_ATTEMPTS
    start_time = time.time()

    for attempt in range(max_attempts):
        try:
            elapsed_time = time.time() - start_time
            poll_interval = get_adaptive_poll_interval(elapsed_time)

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
                    'elapsed_time': int(elapsed_time),
                    'poll_interval': poll_interval,
                }
            )

            if current_status == "succeeded":
                print(f"MUREKA job completed: {job_id}")
                keys_to_remove = {"lyrics_sections"}
                cleaned_json = prune(status_response, keys_to_remove)
                return cleaned_json

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
                elapsed_time = time.time() - start_time
                current_poll_interval = get_adaptive_poll_interval(elapsed_time)
                wait_time = current_poll_interval * 2
                print(f"Temporary MUREKA error ({e.response.status_code}), retrying in {wait_time}s", file=sys.stderr)
                print(f"Response content: {e.response.text if e.response else 'No response'}", file=sys.stderr)
                time.sleep(wait_time)
                continue
            else:
                print(f"HTTP error checking MUREKA status: {e}", file=sys.stderr)
                print(f"Response content: {e.response.text if e.response else 'No response'}", file=sys.stderr)
                print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
                raise
        except Exception as e:
            print(f"Unexpected error in MUREKA polling: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            raise

    total_elapsed = time.time() - start_time
    raise Exception(f"Timeout after {max_attempts} polling attempts ({int(total_elapsed)} seconds elapsed)")
