import { Injectable } from '@angular/core';
import {
  CanActivate,
  CanActivateChild,
  ActivatedRouteSnapshot,
  RouterStateSnapshot,
  Router
} from '@angular/router';
import { Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate, CanActivateChild {

  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> {
    return this.checkAuthentication(state.url);
  }

  canActivateChild(
    childRoute: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean> {
    return this.checkAuthentication(state.url);
  }

  private checkAuthentication(url: string): Observable<boolean> {
    // If user is already authenticated locally, allow access
    if (this.authService.isAuthenticated()) {
      // Optionally validate token with server
      return this.authService.validateToken().pipe(
        map(isValid => {
          if (!isValid) {
            this.redirectToLogin(url);
            return false;
          }
          return true;
        }),
        catchError(() => {
          this.redirectToLogin(url);
          return of(false);
        })
      );
    }

    // Not authenticated, redirect to login
    this.redirectToLogin(url);
    return of(false);
  }

  private redirectToLogin(returnUrl?: string): void {
    const navigationExtras = returnUrl ? { queryParams: { returnUrl } } : {};
    this.router.navigate(['/login'], navigationExtras);
  }
}