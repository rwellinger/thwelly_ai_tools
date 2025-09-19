import {Component, OnInit, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';

@Component({
    selector: 'app-song-profile',
    standalone: true,
    imports: [CommonModule, HeaderComponent, FooterComponent, MatSnackBarModule],
    templateUrl: './song-profile.component.html',
    styleUrl: './song-profile.component.scss'
})
export class SongProfileComponent implements OnInit {
    isLoading = true;
    billingInfo: any = null;

    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);

    ngOnInit() {
        this.loadBillingInfo();
    }

    async loadBillingInfo() {
        this.isLoading = true;
        try {
            const response = await fetch(this.apiConfig.endpoints.billing.info);
            if (response.ok) {
                this.billingInfo = await response.json();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
        } catch (error) {
            console.error('Error loading billing info:', error);
            this.notificationService.error('Error loading billing info');
            this.billingInfo = null;
        } finally {
            this.isLoading = false;
        }
    }

    formatCurrency(amount: number): string {
        return (amount / 100).toFixed(2);
    }

    getStatusClass(status: string): string {
        if (!status) return 'status-unknown';

        switch (status.toLowerCase()) {
            case 'active':
            case 'good':
                return 'status-active';
            case 'inactive':
            case 'suspended':
                return 'status-inactive';
            case 'pending':
                return 'status-pending';
            default:
                return 'status-unknown';
        }
    }

    getStatusIcon(status: string): string {
        if (!status) return 'fa-question-circle';

        switch (status.toLowerCase()) {
            case 'active':
            case 'good':
                return 'fa-check-circle';
            case 'inactive':
            case 'suspended':
                return 'fa-times-circle';
            case 'pending':
                return 'fa-clock';
            default:
                return 'fa-question-circle';
        }
    }
}
