"""
MUREKA Generation Client - Standard song generation
"""
import sys
import logging
import time
from typing import Dict, Any
from requests import HTTPError
from config.settings import (
    MUREKA_GENERATE_ENDPOINT,
    MUREKA_STATUS_ENDPOINT
)
from .base_client import MurekaBaseClient

logger = logging.getLogger(__name__)


class MurekaGenerationClient(MurekaBaseClient):
    """Client for standard MUREKA song generation"""

    def start_generation(self, payload: dict) -> Dict[str, Any]:
        """Start a MUREKA song generation"""
        headers = self._get_headers()

        # Clean payload - only send allowed parameters to MUREKA
        allowed_params = ["lyrics", "prompt", "model"]
        mureka_payload = self._clean_payload(payload, allowed_params)

        print(f"Starting MUREKA generation - Endpoint: {MUREKA_GENERATE_ENDPOINT}", file=sys.stderr)
        print(f"Sending payload: {mureka_payload}", file=sys.stderr)

        response = self._make_request(
            "POST",
            MUREKA_GENERATE_ENDPOINT,
            headers=headers,
            json=mureka_payload
        )

        response_data = response.json()
        job_id = response_data.get("id")
        print(f"MUREKA generation started successfully. Job ID: {job_id}", file=sys.stderr)
        return response_data

    def check_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a MUREKA generation"""
        headers = self._get_headers()
        status_url = f"{MUREKA_STATUS_ENDPOINT}/{job_id}"

        print(f"Checking MUREKA status: {status_url}", file=sys.stderr)

        response = self._make_request("GET", status_url, headers=headers)

        status_data = response.json()
        print(f"MUREKA status for job {job_id}: {status_data.get('status')}", file=sys.stderr)
        return status_data

    def wait_for_completion(self, task, job_id: str) -> Dict[str, Any]:
        """Wait for the completion of a MUREKA generation"""
        start_time = time.time()

        for attempt in range(self.max_poll_attempts):
            try:
                elapsed_time = time.time() - start_time
                poll_interval = self.get_adaptive_poll_interval(elapsed_time)

                status_response = self.check_status(job_id)
                current_status = status_response.get("status", "unknown")

                self._update_task_state(
                    task, job_id, attempt + 1, status_response,
                    elapsed_time, poll_interval, "standard"
                )

                if current_status == "succeeded":
                    print(f"MUREKA job completed: {job_id}")
                    return self._clean_response_data(status_response)

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
                elapsed_time = time.time() - start_time
                wait_time = self._handle_polling_error(e, elapsed_time)
                if wait_time is not None:
                    time.sleep(wait_time)
                    continue
                else:
                    raise

            except Exception as e:
                print(f"Unexpected error in MUREKA polling: {type(e).__name__}: {e}", file=sys.stderr)
                print(f"Stacktrace: {sys.exc_info()}", file=sys.stderr)
                raise

        total_elapsed = time.time() - start_time
        raise Exception(f"Timeout after {self.max_poll_attempts} polling attempts ({int(total_elapsed)} seconds elapsed)")


# Convenience functions for backward compatibility
_client = MurekaGenerationClient()

def start_mureka_generation(payload: dict) -> Dict[str, Any]:
    """Backward compatibility function"""
    return _client.start_generation(payload)

def check_mureka_status(job_id: str) -> Dict[str, Any]:
    """Backward compatibility function"""
    return _client.check_status(job_id)

def wait_for_mureka_completion(task, job_id: str) -> Dict[str, Any]:
    """Backward compatibility function"""
    return _client.wait_for_completion(task, job_id)