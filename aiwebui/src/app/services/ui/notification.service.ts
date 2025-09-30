import {Injectable, inject} from '@angular/core';
import {MatSnackBar, MatSnackBarRef, TextOnlySnackBar} from '@angular/material/snack-bar';
import {HttpErrorResponse} from '@angular/common/http';
import {extractErrorMessage} from '../../utils/error-extractor';

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
    private loadingRef: MatSnackBarRef<TextOnlySnackBar> | null = null;

    private snackBar = inject(MatSnackBar);

    success(message: string, duration: number = 8000): void {
        this.dismissLoading();
        this.snackBar.open(message, 'Close', {
            duration: duration,
            panelClass: ['success-snackbar'],
            verticalPosition: 'top',
            horizontalPosition: 'right'
        });
    }

    error(message: string, duration: number = 6000): void {
        this.dismissLoading();
        this.snackBar.open(message, 'Close', {
            duration: duration,
            panelClass: ['error-snackbar'],
            verticalPosition: 'top',
            horizontalPosition: 'right'
        });
    }

    /**
     * Display error message extracted from HttpErrorResponse
     * Uses error-extractor utility to parse backend error structures
     */
    errorFromResponse(error: HttpErrorResponse | Error | any, duration: number = 6000): void {
        const errorMessage = extractErrorMessage(error);
        this.error(errorMessage, duration);
    }

    info(message: string, duration: number = 4000): void {
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
