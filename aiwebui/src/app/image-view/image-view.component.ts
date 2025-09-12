import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import {CommonModule} from '@angular/common';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { DisplayNamePipe } from '../pipes/display-name.pipe';

interface ImageData {
  id: string;
  filename: string;
  model_used: string;
  prompt: string;
  prompt_hash: string;
  size: string;
  url: string;
  created_at: string;
}

interface PaginationInfo {
  has_more: boolean;
  limit: number;
  offset: number;
  total: number;
}

@Component({
  selector: 'app-image-view',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent, MatSnackBarModule, DisplayNamePipe],
  templateUrl: './image-view.component.html',
  styleUrl: './image-view.component.css',
  encapsulation: ViewEncapsulation.None
})
export class ImageViewComponent implements OnInit {
  images: ImageData[] = [];
  selectedImage: ImageData | null = null;
  isLoading = false;
  loadingMessage = '';
  currentPage = 0;
  pageSize = 20;
  pagination: PaginationInfo = {
    has_more: false,
    limit: 20,
    offset: 0,
    total: 0
  };

  constructor(
    private apiConfig: ApiConfigService,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    this.loadImages();
  }

  async loadImages(page: number = 0) {
    this.isLoading = true;
    this.loadingMessage = 'Loading images...';
    this.notificationService.loading('Loading images...');

    try {
      const offset = page * this.pageSize;
      const url = this.apiConfig.endpoints.image.list(this.pageSize, offset);

      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.images && Array.isArray(data.images)) {
        this.images = data.images;
        this.pagination = data.pagination;
        this.currentPage = page;
        this.notificationService.success(`${this.images.length} images loaded successfully!`);
      } else {
        this.images = [];
        this.notificationService.error('No images found');
      }
    } catch (error: any) {
      this.notificationService.error(`Error loading images: ${error.message}`);
      this.images = [];
    } finally {
      this.isLoading = false;
    }
  }


  async loadImageDetail(image: ImageData) {
    this.isLoading = true;
    this.loadingMessage = 'Loading image detail...';
    this.notificationService.loading('Loading image detail...');

    try {
      const url = this.apiConfig.endpoints.image.detail(image.id);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      this.selectedImage = data;
      this.notificationService.success('Image detail loaded successfully!');
    } catch (error: any) {
      this.selectedImage = image;
      this.notificationService.error(`Using cached data: ${error.message}`);
    } finally {
      this.isLoading = false;
    }
  }

  selectImage(image: ImageData) {
    this.loadImageDetail(image);
  }

  clearSelection() {
    this.selectedImage = null;
  }

  nextPage() {
    if (this.pagination.has_more) {
      this.loadImages(this.currentPage + 1);
    }
  }

  previousPage() {
    if (this.currentPage > 0) {
      this.loadImages(this.currentPage - 1);
    }
  }

  formatDate(dateString: string): string {
    try {
      return new Date(dateString).toLocaleDateString('de-DE', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  }

  onImageError(event: Event): void {
    const target = event.target as HTMLImageElement;
    if (target) {
      target.style.display = 'none';
    }
  }

  protected readonly Math = Math;
}
