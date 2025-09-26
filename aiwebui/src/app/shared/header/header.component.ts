import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { AuthService } from '../../services/auth.service';
import { User, AuthState } from '../../models/user.model';
import * as packageInfo from '../../../../package.json';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterModule, CommonModule],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent implements OnInit, OnDestroy {
  version = (packageInfo as any).version;
  authState: AuthState | null = null;
  currentUser: User | null = null;

  private destroy$ = new Subject<void>();
  private authService = inject(AuthService);
  private router = inject(Router);

  ngOnInit(): void {
    this.authService.authState$
      .pipe(takeUntil(this.destroy$))
      .subscribe(authState => {
        this.authState = authState;
        this.currentUser = authState.user;
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  public onLogout(): void {
    this.authService.logout()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.router.navigate(['/login']);
        },
        error: (error) => {
          console.error('Logout error:', error);
          // Force logout even on error
          this.authService.forceLogout();
          this.router.navigate(['/login']);
        }
      });
  }

  public getUserDisplayName(): string {
    if (!this.currentUser) return 'Guest';

    if (this.currentUser.first_name && this.currentUser.last_name) {
      return `${this.currentUser.first_name} ${this.currentUser.last_name}`;
    }

    if (this.currentUser.first_name) {
      return this.currentUser.first_name;
    }

    return this.currentUser.email.split('@')[0];
  }

  public getFirstName(): string {
    if (!this.currentUser) return 'Guest';

    if (this.currentUser.first_name) {
      return this.currentUser.first_name;
    }

    return this.currentUser.email.split('@')[0];
  }
}
