import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { HeaderComponent } from '../../shared/header/header.component';
import { FooterComponent } from '../../shared/footer/footer.component';
import { SongProfileComponent } from '../../song-profile/song-profile.component';
import { PasswordChangeModalComponent } from '../password-change-modal/password-change-modal.component';

import { UserService } from '../../services/user.service';
import { AuthService } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';
import { User } from '../../models/user.model';

@Component({
  selector: 'app-user-profile',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatCardModule,
    MatIconModule,
    MatSnackBarModule,
    HeaderComponent,
    FooterComponent,
    SongProfileComponent
  ],
  templateUrl: './user-profile.component.html',
  styleUrl: './user-profile.component.scss'
})
export class UserProfileComponent implements OnInit, OnDestroy {
  userForm: FormGroup;
  currentUser: User | null = null;
  isLoading = false;
  isEditing = false;

  private destroy$ = new Subject<void>();
  private fb = inject(FormBuilder);
  private dialog = inject(MatDialog);
  private userService = inject(UserService);
  private authService = inject(AuthService);
  private notificationService = inject(NotificationService);

  constructor() {
    this.userForm = this.fb.group({
      first_name: ['', [Validators.required, Validators.minLength(2)]],
      last_name: ['', [Validators.required, Validators.minLength(2)]]
    });
  }

  ngOnInit(): void {
    this.loadUserProfile();
    this.subscribeToAuthState();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Subscribe to auth state changes
   */
  private subscribeToAuthState(): void {
    this.authService.authState$
      .pipe(takeUntil(this.destroy$))
      .subscribe(authState => {
        this.currentUser = authState.user;
        if (this.currentUser) {
          this.updateFormValues();
        }
      });
  }

  /**
   * Load user profile data
   */
  private loadUserProfile(): void {
    this.isLoading = true;

    this.userService.getCurrentUserProfile()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (user) => {
          this.currentUser = user;
          this.updateFormValues();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading user profile:', error);
          this.notificationService.error('Error loading profile');
          this.isLoading = false;
        }
      });
  }

  /**
   * Update form values from current user data
   */
  private updateFormValues(): void {
    if (this.currentUser) {
      this.userForm.patchValue({
        first_name: this.currentUser.first_name || '',
        last_name: this.currentUser.last_name || ''
      });
    }
  }

  /**
   * Get error message for form fields
   */
  public getErrorMessage(fieldName: string): string {
    const field = this.userForm.get(fieldName);

    if (field?.hasError('required')) {
      return `${this.getFieldDisplayName(fieldName)} is required`;
    }

    if (field?.hasError('minlength')) {
      const requiredLength = field.errors?.['minlength']?.requiredLength;
      return `${this.getFieldDisplayName(fieldName)} must be at least ${requiredLength} characters long`;
    }

    return '';
  }

  /**
   * Get display name for form fields
   */
  private getFieldDisplayName(fieldName: string): string {
    switch (fieldName) {
      case 'first_name':
        return 'First name';
      case 'last_name':
        return 'Last name';
      default:
        return fieldName;
    }
  }

  /**
   * Check if field has error
   */
  public hasFieldError(fieldName: string): boolean {
    const field = this.userForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Start editing mode
   */
  public startEditing(): void {
    this.isEditing = true;
  }

  /**
   * Cancel editing and reset form
   */
  public cancelEditing(): void {
    this.isEditing = false;
    this.updateFormValues();
  }

  /**
   * Save user profile changes
   */
  public saveProfile(): void {
    if (this.userForm.valid && !this.isLoading) {
      this.isLoading = true;

      const formData = this.userForm.value;

      this.userService.updateCurrentUserProfile(formData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updatedUser) => {
            this.currentUser = updatedUser;
            this.isEditing = false;
            this.isLoading = false;
            this.notificationService.success('Profile updated successfully');
          },
          error: (error) => {
            console.error('Error updating profile:', error);
            this.notificationService.error(error.message || 'Error updating profile');
            this.isLoading = false;
          }
        });
    }
  }

  /**
   * Open password change modal
   */
  public openPasswordChangeModal(): void {
    const dialogRef = this.dialog.open(PasswordChangeModalComponent, {
      width: '450px',
      maxWidth: '90vw',
      disableClose: true,
      panelClass: 'password-modal-panel'
    });

    dialogRef.afterClosed()
      .pipe(takeUntil(this.destroy$))
      .subscribe(result => {
        if (result) {
          console.log('Password changed successfully');
        }
      });
  }

  /**
   * Get user display name
   */
  public getUserDisplayName(): string {
    if (!this.currentUser) return 'Unknown User';

    if (this.currentUser.first_name && this.currentUser.last_name) {
      return `${this.currentUser.first_name} ${this.currentUser.last_name}`;
    }

    if (this.currentUser.first_name) {
      return this.currentUser.first_name;
    }

    return this.currentUser.email.split('@')[0];
  }

  /**
   * Format date for display
   */
  public formatDate(dateString: string): string {
    if (!dateString) return 'Unknown';

    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}