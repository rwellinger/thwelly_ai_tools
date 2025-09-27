import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatIconModule } from '@angular/material/icon';
import { UserService } from '../../services/business/user.service';
import { NotificationService } from '../../services/ui/notification.service';

@Component({
  selector: 'app-password-change-modal',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule
  ],
  templateUrl: './password-change-modal.component.html',
  styleUrl: './password-change-modal.component.scss'
})
export class PasswordChangeModalComponent {
  passwordForm: FormGroup;
  isLoading = false;
  showOldPassword = false;
  showNewPassword = false;
  showConfirmPassword = false;

  private fb = inject(FormBuilder);
  private dialogRef = inject(MatDialogRef<PasswordChangeModalComponent>);
  private userService = inject(UserService);
  private notificationService = inject(NotificationService);

  constructor() {
    this.passwordForm = this.fb.group({
      oldPassword: ['', [Validators.required, Validators.minLength(6)]],
      newPassword: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  /**
   * Custom validator to check if new password and confirm password match
   */
  private passwordMatchValidator(form: FormGroup): null | { passwordMismatch: boolean } {
    const newPassword = form.get('newPassword')?.value;
    const confirmPassword = form.get('confirmPassword')?.value;

    if (newPassword && confirmPassword && newPassword !== confirmPassword) {
      return { passwordMismatch: true };
    }

    return null;
  }

  /**
   * Toggle visibility of password fields
   */
  public togglePasswordVisibility(field: 'old' | 'new' | 'confirm'): void {
    switch (field) {
      case 'old':
        this.showOldPassword = !this.showOldPassword;
        break;
      case 'new':
        this.showNewPassword = !this.showNewPassword;
        break;
      case 'confirm':
        this.showConfirmPassword = !this.showConfirmPassword;
        break;
    }
  }

  /**
   * Get error message for form fields
   */
  public getErrorMessage(fieldName: string): string {
    const field = this.passwordForm.get(fieldName);

    if (field?.hasError('required')) {
      return `${this.getFieldDisplayName(fieldName)} is required`;
    }

    if (field?.hasError('minlength')) {
      return `${this.getFieldDisplayName(fieldName)} must be at least 6 characters long`;
    }

    if (fieldName === 'confirmPassword' && this.passwordForm.hasError('passwordMismatch')) {
      return 'Passwords do not match';
    }

    return '';
  }

  /**
   * Get display name for form fields
   */
  private getFieldDisplayName(fieldName: string): string {
    switch (fieldName) {
      case 'oldPassword':
        return 'Current password';
      case 'newPassword':
        return 'New password';
      case 'confirmPassword':
        return 'Confirm password';
      default:
        return fieldName;
    }
  }

  /**
   * Check if field has error
   */
  public hasFieldError(fieldName: string): boolean {
    const field = this.passwordForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Submit the password change form
   */
  public onSubmit(): void {
    if (this.passwordForm.valid && !this.isLoading) {
      this.isLoading = true;

      const formData = this.passwordForm.value;
      const passwordChangeData = {
        old_password: formData.oldPassword,
        new_password: formData.newPassword
      };

      this.userService.changeCurrentUserPassword(passwordChangeData)
        .subscribe({
          next: () => {
            this.notificationService.success('Password changed successfully');
            this.dialogRef.close(true);
          },
          error: (error) => {
            this.notificationService.error(error.message || 'Error changing password');
            this.isLoading = false;
          }
        });
    }
  }

  /**
   * Cancel and close the dialog
   */
  public onCancel(): void {
    this.dialogRef.close(false);
  }
}