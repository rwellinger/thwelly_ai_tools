import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  INFO = 'info',
  LOADING = 'loading'
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private loadingRef: any = null;

  constructor(private snackBar: MatSnackBar) {}

  success(message: string, duration: number = 15000): void {
    this.dismissLoading();
    this.snackBar.open(message, 'Close', {
      duration: duration,
      panelClass: ['success-snackbar'],
      verticalPosition: 'top',
      horizontalPosition: 'right'
    });
  }

  error(message: string, duration: number = 10000): void {
    this.dismissLoading();
    this.snackBar.open(message, 'Close', {
      duration: duration,
      panelClass: ['error-snackbar'],
      verticalPosition: 'top',
      horizontalPosition: 'right'
    });
  }

  info(message: string, duration: number = 8000): void {
    this.snackBar.open(message, 'Close', {
      duration: duration,
      panelClass: ['info-snackbar'],
      verticalPosition: 'top',
      horizontalPosition: 'right'
    });
  }

  loading(message: string): void {
    this.dismissLoading();
    this.loadingRef = this.snackBar.open(message, undefined, {
      panelClass: ['loading-snackbar'],
      verticalPosition: 'top',
      horizontalPosition: 'right'
    });
  }

  dismissLoading(): void {
    if (this.loadingRef) {
      this.loadingRef.dismiss();
      this.loadingRef = null;
    }
  }

  dismiss(): void {
    this.snackBar.dismiss();
  }
}