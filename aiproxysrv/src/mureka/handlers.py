"""
Error Handler für MUREKA API
"""
from requests import HTTPError


def handle_http_error(task, error: HTTPError) -> dict:
    """Behandelt HTTP-Fehler von der MUREKA API"""
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
    """Behandelt allgemeine Fehler"""
    return {
        "status": "ERROR",
        "http_code": None,
        "message": str(error),
        "task_id": task.request.id,
    }
