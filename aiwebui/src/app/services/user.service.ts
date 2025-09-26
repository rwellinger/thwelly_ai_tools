import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  User,
  UserUpdateRequest,
  UserUpdateResponse,
  PasswordChangeRequest,
  PasswordChangeResponse
} from '../models/user.model';
import { AuthService } from './auth.service';

@Injectable({
  providedIn: 'root'
})
export class UserService {
  private readonly baseUrl = environment.apiUrl;

  private http = inject(HttpClient);
  private authService = inject(AuthService);

  /**
   * Get user profile by ID
   */
  public getUserProfile(userId: string): Observable<User> {
    const headers = this.getAuthHeaders();

    return this.http.get<User>(`${this.baseUrl}/api/v1/user/profile/${userId}`, { headers })
      .pipe(
        map(response => response),
        catchError(this.handleError)
      );
  }

  /**
   * Update user profile (first name, last name)
   */
  public updateUserProfile(userId: string, userData: UserUpdateRequest): Observable<User> {
    const headers = this.getAuthHeaders();

    return this.http.put<UserUpdateResponse>(`${this.baseUrl}/api/v1/user/edit/${userId}`, userData, { headers })
      .pipe(
        map(response => {
          if (response.success && response.user) {
            // Update the user in auth service
            const currentUser = this.authService.getCurrentUser();
            if (currentUser && currentUser.id === userId) {
              const updatedUser = { ...currentUser, ...userData };
              this.authService.updateUser(updatedUser);
            }
            return response.user;
          }
          throw new Error(response.message || 'Failed to update user profile');
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Change user password
   */
  public changePassword(userId: string, passwordData: PasswordChangeRequest): Observable<PasswordChangeResponse> {
    const headers = this.getAuthHeaders();

    return this.http.put<PasswordChangeResponse>(`${this.baseUrl}/api/v1/user/password/${userId}`, passwordData, { headers })
      .pipe(
        map(response => {
          if (response.success) {
            return response;
          }
          throw new Error(response.message || 'Failed to change password');
        }),
        catchError(this.handleError)
      );
  }

  /**
   * Get current user profile
   */
  public getCurrentUserProfile(): Observable<User> {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.getUserProfile(currentUser.id);
  }

  /**
   * Update current user profile
   */
  public updateCurrentUserProfile(userData: UserUpdateRequest): Observable<User> {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.updateUserProfile(currentUser.id, userData);
  }

  /**
   * Change current user password
   */
  public changeCurrentUserPassword(passwordData: PasswordChangeRequest): Observable<PasswordChangeResponse> {
    const currentUser = this.authService.getCurrentUser();
    if (!currentUser) {
      return throwError(() => new Error('No authenticated user'));
    }

    return this.changePassword(currentUser.id, passwordData);
  }

  /**
   * Get authorization headers
   */
  private getAuthHeaders(): HttpHeaders {
    const token = this.authService.getToken();
    if (!token) {
      throw new Error('No authentication token available');
    }

    return new HttpHeaders({
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    });
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any): Observable<never> {
    console.error('UserService error:', error);

    let errorMessage = 'An error occurred';

    if (error.error) {
      if (typeof error.error === 'string') {
        errorMessage = error.error;
      } else if (error.error.error) {
        errorMessage = error.error.error;
      } else if (error.error.message) {
        errorMessage = error.error.message;
      }
    } else if (error.message) {
      errorMessage = error.message;
    }

    return throwError(() => new Error(errorMessage));
  }
}