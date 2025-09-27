import {Component, OnInit, Input, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {ApiConfigService} from '../../services/api-config.service';
import {NotificationService} from '../../services/notification.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';

@Component({
    selector: 'app-song-profile',
    standalone: true,
    imports: [CommonModule, MatSnackBarModule],
    templateUrl: './song-profile.component.html',
    styleUrl: './song-profile.component.scss'
})
export class SongProfileComponent implements OnInit {
    @Input() isEmbedded: boolean = false;

    isLoading = true;
    billingInfo: any = null;

    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private http = inject(HttpClient);

    ngOnInit() {
        this.loadBillingInfo();
    }

    async loadBillingInfo() {
        this.isLoading = true;
        try {
            this.billingInfo = await firstValueFrom(
                this.http.get<any>(this.apiConfig.endpoints.billing.info)
            );
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
