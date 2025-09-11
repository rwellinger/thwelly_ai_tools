import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { ApiConfigService } from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-song-profile',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent, MatSnackBarModule],
  templateUrl: './song-profile.component.html',
  styleUrl: './song-profile.component.css'
})
export class SongProfileComponent implements OnInit {
  isLoading = true;
  billingInfo: any = null;

  constructor(
    private apiConfig: ApiConfigService,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    this.notificationService.loading('Loading billing info...');
    this.loadBillingInfo();
  }

  async loadBillingInfo() {
    try {
      const response = await fetch(this.apiConfig.endpoints.billing.info);
      const data = await response.json();
      this.billingInfo = data;
      this.notificationService.success('Billing info loaded successfully!');
    } catch (error) {
      this.notificationService.error('Error loading billing info');
      this.billingInfo = {
        balance: 'N/A',
        totalSpending: 'N/A',
        requestLimit: 'N/A',
        status: 'Error loading data'
      };
    } finally {
      this.isLoading = false;
    }
  }
}
