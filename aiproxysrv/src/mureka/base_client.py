"""
MUREKA Base Client - Shared HTTP and utilities logic
"""
import sys
import traceback
import logging
import requests
import time
from typing import Dict, Any, Optional
from requests import HTTPError
from config.settings import (
    MUREKA_API_KEY,
    MUREKA_TIMEOUT,
    MUREKA_POLL_INTERVAL_SHORT,
    MUREKA_POLL_INTERVAL_MEDIUM,
    MUREKA_POLL_INTERVAL_LONG,
    MUREKA_MAX_POLL_ATTEMPTS
)
from api.json_helpers import prune

logger = logging.getLogger(__name__)


class MurekaBaseClient:
    """Base client with shared HTTP logic and utilities for MUREKA API"""

    def __init__(self):
        self.api_key = MUREKA_API_KEY
        self.timeout = MUREKA_TIMEOUT
        self.max_poll_attempts = MUREKA_MAX_POLL_ATTEMPTS

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get standard headers for MUREKA API requests"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": content_type,
        }

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make HTTP request with standard error handling"""
        try:
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            logger.debug(f"MUREKA API {method} {url} - Status: {response.status_code}")
            response.raise_for_status()
            return response
        except HTTPError as e:
            logger.error(f"MUREKA API HTTP Error: {e}")
            logger.error(f"Response content: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"MUREKA API request error: {type(e).__name__}: {e}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise

    def _clean_payload(self, payload: dict, allowed_params: list) -> dict:
        """Clean payload to only include allowed parameters"""
        return {key: value for key, value in payload.items() if key in allowed_params}

    def get_adaptive_poll_interval(self, elapsed_seconds: float) -> int:
        """
        Calculate adaptive polling interval based on elapsed time:
        - 0-2 Min: SHORT (default 5s)
        - 2-5 Min: MEDIUM (default 15s)
        - 5+ Min: LONG (default 30s)
        """
        if elapsed_seconds < 120:  # 0-2 minutes
            return MUREKA_POLL_INTERVAL_SHORT
        elif elapsed_seconds < 300:  # 2-5 minutes
            return MUREKA_POLL_INTERVAL_MEDIUM
        else:  # 5+ minutes
            return MUREKA_POLL_INTERVAL_LONG

    def _handle_polling_error(self, error: HTTPError, elapsed_time: float) -> Optional[int]:
        """
        Handle polling errors and return wait time or None to stop polling

        Returns:
            int: Wait time in seconds for retry
            None: Stop polling (e.g., quota exceeded)
        """
        if error.response.status_code == 429:
            # Handle 429 errors with message analysis
            try:
                error_body = error.response.json()
                error_message = error_body.get("message") or error_body.get("error") or error.response.text
            except ValueError:
                error_message = error.response.text or error.response.reason

            from mureka.handlers import analyze_429_error_type
            error_type = analyze_429_error_type(error_message)

            if error_type == 'quota':
                # Quota exceeded - stop polling immediately
                logger.error(f"MUREKA quota exceeded: {error_message}")
                raise Exception(f"Quota exceeded: {error_message}")
            else:
                # Rate limit - retry with backoff
                current_poll_interval = self.get_adaptive_poll_interval(elapsed_time)
                wait_time = current_poll_interval * 2
                logger.warning(f"MUREKA rate limit hit, retrying in {wait_time}s: {error_message}")
                return wait_time

        elif error.response.status_code in [502, 503, 504]:
            # Other temporary errors - retry
            current_poll_interval = self.get_adaptive_poll_interval(elapsed_time)
            wait_time = current_poll_interval * 2
            logger.warning(f"Temporary MUREKA error ({error.response.status_code}), retrying in {wait_time}s")
            logger.warning(f"Response content: {error.response.text if error.response else 'No response'}")
            return wait_time
        else:
            # Other HTTP errors - stop polling
            logger.error(f"HTTP error in MUREKA polling: {error}")
            logger.error(f"Response content: {error.response.text if error.response else 'No response'}")
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise

    def _clean_response_data(self, response_data: dict) -> dict:
        """Clean response data by removing unwanted keys"""
        keys_to_remove = {"lyrics_sections"}
        return prune(response_data, keys_to_remove)

    def _update_task_state(self, task, job_id: str, attempt: int, status_response: dict,
                          elapsed_time: float, poll_interval: int, job_type: str = "standard"):
        """Update Celery task state with progress information"""
        task.update_state(
            state='PROGRESS',
            meta={
                'status': 'POLLING',
                'job_id': job_id,
                'attempt': attempt,
                'mureka_status': status_response.get("status", "unknown"),
                'progress': status_response.get("progress", 0),
                'elapsed_time': int(elapsed_time),
                'poll_interval': poll_interval,
                'type': job_type
            }
        )