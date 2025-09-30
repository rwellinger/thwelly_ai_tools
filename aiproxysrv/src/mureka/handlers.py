"""
Error Handler für MUREKA API
"""
from requests import HTTPError
from utils.logger import logger


def analyze_429_error_type(error_message: str) -> str:
    """
    Analyze 429 error message to distinguish between rate limit and quota exceeded

    Args:
        error_message: The error message from the API response

    Returns:
        'quota' if quota is exceeded (no retry), 'rate_limit' if rate limited (retry possible)
    """
    message_lower = error_message.lower()

    # Check for quota-related keywords
    quota_keywords = ['quota', 'exceeded', 'credits', 'billing']
    if any(keyword in message_lower for keyword in quota_keywords):
        return 'quota'

    # Check for rate limit keywords
    rate_limit_keywords = ['rate limit', 'too quickly', 'pace your requests']
    if any(keyword in message_lower for keyword in rate_limit_keywords):
        return 'rate_limit'

    # Default to rate_limit for unknown 429 cases (safer for retry)
    return 'rate_limit'


def handle_http_error(task, error: HTTPError) -> dict:
    """Behandelt HTTP-Fehler von der MUREKA API"""
    resp = error.response
    status_code = resp.status_code

    logger.error("HTTP Error from MUREKA API", task_id=task.request.id, status_code=status_code)

    try:
        error_body = resp.json()
        message = error_body.get("message") or error_body.get("error") or resp.text
        logger.debug("MUREKA error body", task_id=task.request.id, error_body=error_body)
    except ValueError:
        message = resp.text or resp.reason
        logger.debug("MUREKA raw error response", task_id=task.request.id, response_text=resp.text)

    error_payload = {
        "status": "ERROR",
        "http_code": status_code,
        "message": message,
        "task_id": task.request.id,
    }

    if status_code == 429:
        # Analyze 429 error type
        error_type = analyze_429_error_type(message)
        error_payload["error_type"] = error_type

        logger.error("MUREKA 429 Error", task_id=task.request.id, error_type=error_type)

        rate_headers = {
            "Retry-After": resp.headers.get("Retry-After"),
            "X-RateLimit-Limit": resp.headers.get("X-RateLimit-Limit"),
            "X-RateLimit-Remaining": resp.headers.get("X-RateLimit-Remaining"),
            "X-RateLimit-Reset": resp.headers.get("X-RateLimit-Reset"),
        }
        rate_limit_info = {k: v for k, v in rate_headers.items() if v}
        logger.debug("Rate limit headers", task_id=task.request.id, rate_limit_info=rate_limit_info)
        error_payload["rate_limit_info"] = rate_limit_info

    return error_payload


def handle_general_error(task, error: Exception) -> dict:
    """Behandelt allgemeine Fehler"""
    logger.error("General error", task_id=task.request.id, error_type=type(error).__name__, error=str(error))
    return {
        "status": "ERROR",
        "http_code": None,
        "message": str(error),
        "task_id": task.request.id,
    }
