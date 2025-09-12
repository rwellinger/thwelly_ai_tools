"""
Error Handler für MUREKA API
"""
import sys
from requests import HTTPError


def handle_http_error(task, error: HTTPError) -> dict:
    """Behandelt HTTP-Fehler von der MUREKA API"""
    resp = error.response
    status_code = resp.status_code
    
    print(f"Task {task.request.id}: HTTP Error {status_code} from MUREKA API", file=sys.stderr)

    try:
        error_body = resp.json()
        message = error_body.get("message") or error_body.get("error") or resp.text
        print(f"Task {task.request.id}: Error body: {error_body}", file=sys.stderr)
    except ValueError:
        message = resp.text or resp.reason
        print(f"Task {task.request.id}: Raw error response: {resp.text}", file=sys.stderr)

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
        rate_limit_info = {k: v for k, v in rate_headers.items() if v}
        print(f"Task {task.request.id}: Rate limit headers: {rate_limit_info}", file=sys.stderr)
        error_payload["rate_limit_info"] = rate_limit_info

    return error_payload


def handle_general_error(task, error: Exception) -> dict:
    """Behandelt allgemeine Fehler"""
    print(f"Task {task.request.id}: General error: {type(error).__name__}: {error}", file=sys.stderr)
    return {
        "status": "ERROR",
        "http_code": None,
        "message": str(error),
        "task_id": task.request.id,
    }
