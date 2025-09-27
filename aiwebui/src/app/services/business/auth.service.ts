import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { BehaviorSubject, Observable, throwError } from 'rxjs';
import { map, catchError, tap } from 'rxjs/operators';
import { CookieService } from 'ngx-cookie-service';
import { environment } from '../../../environments/environment';
import {
  User,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  UserCreateRequest,
  UserCreateResponse,
  AuthState
} from '../../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly baseUrl = environment.apiUrl;
  private readonly tokenKey = 'auth_token';
  private readonly userKey = 'auth_user';

  private authStateSubject = new BehaviorSubject<AuthState>({
    isAuthenticated: false,
    user: null,
    token: null,
    loading: false,
    error: null
  });

  public authState$ = this.authStateSubject.asObservable();

  private http = inject(HttpClient);
  private cookieService = inject(CookieService);

  constructor() {
    this.initializeAuthState();
  }

  /**
   * Initialize auth state from stored cookies
   */
  private initializeAuthState(): void {
    const token = this.cookieService.get(this.tokenKey);
    const userJson = this.cookieService.get(this.userKey);

    if (token && userJson) {
      try {
        const user = JSON.parse(userJson);
        this.updateAuthState({
          isAuthenticated: true,
          user,
          token,
          loading: false,
          error: null
        });
      } catch (error) {
        this.clearAuthData();
      }
    }
  }

  /**
   * Update the auth state
   */
  private updateAuthState(newState: Partial<AuthState>): void {
    const currentState = this.authStateSubject.value;
    this.authStateSubject.next({ ...currentState, ...newState });
  }

  /**
   * Get current user
   */
  public getCurrentUser(): User | null {
    return this.authStateSubject.value.user;
  }

  /**
   * Get current token
   */
  public getToken(): string | null {
    return this.authStateSubject.value.token;
  }

  /**
   * Check if user is authenticated
   */
  public isAuthenticated(): boolean {
    return this.authStateSubject.value.isAuthenticated;
  }

  /**
   * Login user
   */
  public login(credentials: LoginRequest): Observable<LoginResponse> {
    this.updateAuthState({ loading: true, error: null });

    return this.http.post<LoginResponse>(`${this.baseUrl}/api/v1/user/login`, credentials)
      .pipe(
        tap(response => {
          if (response.success && response.token && response.user) {
            this.storeAuthData(response.token, response.user);
            this.updateAuthState({
              isAuthenticated: true,
              user: response.user,
              token: response.token,
              loading: false,
              error: null
            });
          }
        }),
        catchError(error => {
          this.updateAuthState({
            loading: false,
            error: error.error?.error || 'Login failed'
          });
          return throwError(() => error);
        })
      );
  }

  /**
   * Logout user
   */
  public logout(): Observable<LogoutResponse> {
    this.updateAuthState({ loading: true });

    return this.http.post<LogoutResponse>(`${this.baseUrl}/api/v1/user/logout`, {})
      .pipe(
        tap(() => {
          this.clearAuthData();
          this.updateAuthState({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: null
          });
        }),
        catchError(error => {
          // Clear auth data even if logout fails
          this.clearAuthData();
          this.updateAuthState({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: null
          });
          return throwError(() => error);
        })
      );
  }

  /**
   * Register new user
   */
  public register(userData: UserCreateRequest): Observable<UserCreateResponse> {
    this.updateAuthState({ loading: true, error: null });

    return this.http.post<UserCreateResponse>(`${this.baseUrl}/api/v1/user/create`, userData)
      .pipe(
        tap(() => {
          this.updateAuthState({
            loading: false,
            error: null
          });
        }),
        catchError(error => {
          this.updateAuthState({
            loading: false,
            error: error.error?.error || 'Registration failed'
          });
          return throwError(() => error);
        })
      );
  }

  /**
   * Validate current token
   */
  public validateToken(): Observable<boolean> {
    const token = this.getToken();
    if (!token) {
      return new Observable(observer => {
        observer.next(false);
        observer.complete();
      });
    }

    const headers = new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });

    return this.http.post<any>(`${this.baseUrl}/api/v1/user/validate-token`, {}, { headers })
      .pipe(
        map(response => {
          if (response.valid) {
            return true;
          } else {
            this.clearAuthData();
            this.updateAuthState({
              isAuthenticated: false,
              user: null,
              token: null
            });
            return false;
          }
        }),
        catchError(() => {
          this.clearAuthData();
          this.updateAuthState({
            isAuthenticated: false,
            user: null,
            token: null
          });
          return new Observable<boolean>(observer => {
            observer.next(false);
            observer.complete();
          });
        })
      );
  }

  /**
   * Store authentication data in cookies
   */
  private storeAuthData(token: string, user: User): void {
    // Store token for 24 hours (same as JWT expiration)
    this.cookieService.set(
      this.tokenKey,
      token,
      1, // 1 day
      '/', // path
      undefined, // domain
      true, // secure
      'Lax' // sameSite
    );

    // Store user data
    this.cookieService.set(
      this.userKey,
      JSON.stringify(user),
      1, // 1 day
      '/', // path
      undefined, // domain
      true, // secure
      'Lax' // sameSite
    );
  }

  /**
   * Clear authentication data
   */
  private clearAuthData(): void {
    this.cookieService.delete(this.tokenKey, '/');
    this.cookieService.delete(this.userKey, '/');
  }

  /**
   * Force logout (clear local data)
   */
  public forceLogout(): void {
    this.clearAuthData();
    this.updateAuthState({
      isAuthenticated: false,
      user: null,
      token: null,
      loading: false,
      error: null
    });
  }

  /**
   * Update user data in auth state
   */
  public updateUser(user: User): void {
    const currentState = this.authStateSubject.value;
    if (currentState.isAuthenticated && currentState.token) {
      this.storeAuthData(currentState.token, user);
      this.updateAuthState({ user });
    }
  }
}