import { HttpErrorResponse } from '@angular/common/http';

/**
 * Backend Error Response Structures
 */
interface BackendErrorResponse {
  error?: string;
  success?: boolean;
  message?: string;
}

interface ValidationErrorDetail {
  msg: string;
  loc: string[];
  type: string;
  ctx?: {
    error?: string;
  };
}

interface ValidationErrorResponse {
  validation_error?: {
    body_params?: ValidationErrorDetail[];
    query_params?: ValidationErrorDetail[];
    path_params?: ValidationErrorDetail[];
  };
}

/**
 * Extract user-friendly error message from HttpErrorResponse
 *
 * Handles multiple backend error formats:
 * 1. { "error": "message", "success": false } - Business/Auth errors
 * 2. { "validation_error": { "body_params": [...] } } - Pydantic validation errors
 * 3. { "message": "error" } - Generic backend errors
 * 4. Plain text error responses
 * 5. HTTP status text as fallback
 */
export function extractErrorMessage(error: HttpErrorResponse | Error | any): string {
  // Handle non-HTTP errors (e.g., network errors, timeout errors)
  if (!(error instanceof HttpErrorResponse)) {
    return error?.message || 'An unexpected error occurred';
  }

  const httpError = error as HttpErrorResponse;

  // Try to extract error from response body
  if (httpError.error) {
    // Check for backend error structure: { "error": "message", "success": false }
    if (typeof httpError.error === 'object') {
      const backendError = httpError.error as BackendErrorResponse;

      if (backendError.error) {
        return backendError.error;
      }

      if (backendError.message) {
        return backendError.message;
      }

      // Check for validation error structure
      const validationError = httpError.error as ValidationErrorResponse;
      if (validationError.validation_error) {
        const validationMessage = extractValidationError(validationError);
        if (validationMessage) {
          return validationMessage;
        }
      }
    }

    // Handle plain text error responses
    if (typeof httpError.error === 'string') {
      return httpError.error;
    }
  }

  // Fallback to HTTP status text
  return getStatusMessage(httpError.status, httpError.statusText);
}

/**
 * Extract validation error message from Pydantic validation error structure
 */
function extractValidationError(validationError: ValidationErrorResponse): string | null {
  const validation = validationError.validation_error;

  if (!validation) {
    return null;
  }

  // Check body_params first (most common)
  if (validation.body_params && validation.body_params.length > 0) {
    const firstError = validation.body_params[0];
    return formatValidationError(firstError);
  }

  // Check query_params
  if (validation.query_params && validation.query_params.length > 0) {
    const firstError = validation.query_params[0];
    return formatValidationError(firstError);
  }

  // Check path_params
  if (validation.path_params && validation.path_params.length > 0) {
    const firstError = validation.path_params[0];
    return formatValidationError(firstError);
  }

  return null;
}

/**
 * Format validation error detail into user-friendly message
 */
function formatValidationError(detail: ValidationErrorDetail): string {
  const field = detail.loc.length > 0 ? detail.loc.join('.') : 'field';

  // Use ctx.error if available (contains custom validation message)
  if (detail.ctx?.error) {
    return `${field}: ${detail.ctx.error}`;
  }

  // Use msg
  if (detail.msg) {
    // Remove "Value error, " prefix if present (Pydantic adds this)
    const cleanMsg = detail.msg.replace(/^Value error,\s*/i, '');
    return `${field}: ${cleanMsg}`;
  }

  return `Validation error for ${field}`;
}

/**
 * Get user-friendly message based on HTTP status code
 */
function getStatusMessage(status: number, statusText: string): string {
  switch (status) {
    case 0:
      return 'Unable to connect to server. Please check your internet connection.';
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      return 'Authentication required. Please log in again.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 408:
      return 'Request timeout. Please try again.';
    case 409:
      return 'Conflict. The resource already exists or has been modified.';
    case 422:
      return 'Validation error. Please check your input.';
    case 429:
      return 'Too many requests. Please wait a moment and try again.';
    case 500:
      return 'Server error. Please try again later.';
    case 502:
      return 'Bad gateway. The server is temporarily unavailable.';
    case 503:
      return 'Service unavailable. Please try again later.';
    case 504:
      return 'Gateway timeout. The server took too long to respond.';
    default:
      return statusText || `Error ${status}: An error occurred`;
  }
}