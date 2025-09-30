import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';
import { NotificationService } from '../services/ui/notification.service';
import { extractErrorMessage } from '../utils/error-extractor';

/**
 * HTTP Error Interceptor
 *
 * Catches all HTTP errors and displays user-friendly error messages via NotificationService.
 * This interceptor runs AFTER auth.interceptor, so 401/403 errors that were not handled
 * by auth logic will also be caught here.
 *
 * Error message extraction is handled by error-extractor utility which supports:
 * - Backend business/auth errors: { "error": "message" }
 * - Pydantic validation errors: { "validation_error": { ... } }
 * - HTTP status code fallbacks
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const notificationService = inject(NotificationService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Extract user-friendly error message
      const errorMessage = extractErrorMessage(error);

      // Display error notification
      // Only show notification for non-401/403 errors (those are handled by auth.interceptor)
      if (error.status !== 401 && error.status !== 403) {
        notificationService.error(errorMessage);
      }

      // Re-throw error so components can still handle it if needed
      return throwError(() => error);
    })
  );
};