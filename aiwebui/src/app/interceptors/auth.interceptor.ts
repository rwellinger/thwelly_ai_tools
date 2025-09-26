import { inject } from '@angular/core';
import { HttpInterceptorFn, HttpErrorResponse, HttpRequest, HttpHandlerFn } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, switchMap, filter, take } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

let isRefreshing = false;
let refreshTokenSubject: BehaviorSubject<any> = new BehaviorSubject<any>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  console.log('🔍 Auth Interceptor - Request URL:', req.url);
  console.log('🔍 Auth Interceptor - Request method:', req.method);

  // Skip authentication for auth-related endpoints
  const isAuthEndpointResult = isAuthEndpoint(req.url);
  console.log('🔍 Auth Interceptor - Is auth endpoint:', isAuthEndpointResult);

  if (isAuthEndpointResult) {
    console.log('⏭️  Skipping auth for endpoint:', req.url);
    return next(req);
  }

  // Add authentication token to request
  const authToken = authService.getToken();
  console.log('🔍 Auth Interceptor - Token available:', !!authToken);
  console.log('🔍 Auth Interceptor - Token preview:', authToken ? authToken.substring(0, 20) + '...' : 'None');

  if (authToken) {
    console.log('🔐 Adding Authorization header to request');
    req = addTokenToRequest(req, authToken);
    console.log('🔍 Auth Interceptor - Request headers after token:', req.headers.keys());
  } else {
    console.log('❌ No token available, proceeding without Authorization header');
  }

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Handle 401 Unauthorized errors
      if (error.status === 401 && authToken) {
        return handle401Error(req, next, authService, router);
      }

      // Handle other errors
      if (error.status === 403) {
        // Forbidden - user doesn't have permission
        authService.forceLogout();
        router.navigate(['/login']);
      }

      return throwError(() => error);
    })
  );
};

function isAuthEndpoint(url: string): boolean {
  const authEndpoints = [
    '/api/v1/user/login',
    '/api/v1/user/create',
    '/api/v1/user/validate-token'
  ];
  return authEndpoints.some(endpoint => url.includes(endpoint));
}

function addTokenToRequest(request: HttpRequest<any>, token: string): HttpRequest<any> {
  return request.clone({
    setHeaders: {
      'Authorization': `Bearer ${token}`
    }
  });
}

function handle401Error(request: HttpRequest<any>, next: HttpHandlerFn, authService: AuthService, router: Router): Observable<any> {
  if (!isRefreshing) {
    isRefreshing = true;
    refreshTokenSubject.next(null);

    // Validate current token
    return authService.validateToken().pipe(
      switchMap((isValid: boolean) => {
        isRefreshing = false;

        if (isValid) {
          // Token is still valid, retry original request
          const token = authService.getToken();
          if (token) {
            refreshTokenSubject.next(token);
            return next(addTokenToRequest(request, token));
          }
        }

        // Token is invalid, logout user
        authService.forceLogout();
        router.navigate(['/login']);
        return throwError(() => new Error('Authentication failed'));
      }),
      catchError((error) => {
        isRefreshing = false;
        authService.forceLogout();
        router.navigate(['/login']);
        return throwError(() => error);
      })
    );
  } else {
    // Wait for token refresh to complete
    return refreshTokenSubject.pipe(
      filter(token => token != null),
      take(1),
      switchMap(token => {
        return next(addTokenToRequest(request, token));
      })
    );
  }
}