import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import {CommonModule} from '@angular/common';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {DisplayNamePipe} from '../pipes/display-name.pipe';

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
  filteredImages: ImageData[] = [];
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

  // Search and sort
  searchTerm: string = '';
  sortDirection: 'asc' | 'desc' = 'desc';

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
        
        this.applyFilterAndSort();

        // Auto-select first image if available and none selected
        if (this.filteredImages.length > 0 && !this.selectedImage) {
          this.selectImage(this.filteredImages[0]);
        }
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

    try {
      const url = this.apiConfig.endpoints.image.detail(image.id);
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      this.selectedImage = await response.json();
    } catch (error: any) {
      this.selectedImage = image;
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

  downloadImage(imageUrl: string) {
    // Create a temporary anchor element to trigger the download
    const link = document.createElement('a');
    link.href = imageUrl;
    link.download = ''; // This will use the filename from the URL
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  onImageError(event: Event): void {
    const target = event.target as HTMLImageElement;
    if (target) {
      target.style.display = 'none';
    }
  }

  formatDateShort(dateString: string): string {
    try {
      return new Date(dateString).toLocaleDateString('de-CH', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  }

  // Modern pagination methods
  getVisiblePages(): (number | string)[] {
    const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
    const current = this.currentPage + 1;
    const pages: (number | string)[] = [];

    if (totalPages <= 7) {
      // Show all pages if 7 or less
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Smart pagination with ellipsis
      if (current <= 4) {
        // Show: 1 2 3 4 5 ... last
        for (let i = 1; i <= 5; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (current >= totalPages - 3) {
        // Show: 1 ... n-4 n-3 n-2 n-1 n
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
      } else {
        // Show: 1 ... current-1 current current+1 ... last
        pages.push(1);
        pages.push('...');
        for (let i = current - 1; i <= current + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }

    return pages;
  }

  goToPage(pageIndex: number) {
    if (pageIndex >= 0 && pageIndex < Math.ceil(this.pagination.total / this.pagination.limit) && !this.isLoading) {
      this.loadImages(pageIndex * this.pagination.limit);
    }
  }

  trackByPage(index: number, page: number | string): number | string {
    return page;
  }

  // Client-side filter and sort
  applyFilterAndSort() {
    let filtered = [...this.images];

    // Apply search filter
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      filtered = filtered.filter(image => 
        image.prompt?.toLowerCase().includes(term)
      );
    }

    // Apply sort by created date
    filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return this.sortDirection === 'desc' ? dateB - dateA : dateA - dateB;
    });

    this.filteredImages = filtered;
  }

  onSearchChange(searchTerm: string) {
    this.searchTerm = searchTerm;
    this.applyFilterAndSort();
  }

  toggleSort() {
    this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
    this.applyFilterAndSort();
  }

  protected readonly Math = Math;
}
