import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnInit, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ImageBlobService } from '../../services/ui/image-blob.service';
import { NotificationService } from '../../services/ui/notification.service';
import { ApiConfigService } from '../../services/config/api-config.service';

@Component({
  selector: 'app-image-detail-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './image-detail-panel.component.html',
  styleUrl: './image-detail-panel.component.scss'
})
export class ImageDetailPanelComponent implements OnInit, OnChanges {
  private imageBlobService = inject(ImageBlobService);
  private notificationService = inject(NotificationService);
  private apiConfigService = inject(ApiConfigService);
  private http = inject(HttpClient);

  imageBlobUrl: string = '';
  @Input() image: any = null;
  @Input() imageId: string | null = null;
  @Input() showEditTitle: boolean = true;
  @Input() title: string = 'Image Details';
  @Input() showMetaInfo: string[] = ['model', 'size', 'created'];
  @Input() placeholderText: string = 'Select an image from the list to view details';
  @Input() placeholderIcon: string = 'fas fa-image';
  @Input() isGenerating: boolean = false;
  @Input() showActionButtons: boolean = true;

  // Component state
  isLoading = false;
  loadingError: string | null = null;

  @Output() titleChanged = new EventEmitter<string>();
  @Output() downloadOriginal = new EventEmitter<void>();
  @Output() previewImage = new EventEmitter<void>();

  @ViewChild('titleInput') titleInput!: ElementRef;

  editingTitle = false;
  editTitleValue = '';

  startEditTitle() {
    if (!this.showEditTitle || !this.image) return;
    this.editingTitle = true;
    this.editTitleValue = this.getDisplayTitle(this.image);
    setTimeout(() => {
      this.titleInput?.nativeElement?.focus();
    });
  }

  async saveTitle() {
    if (!this.image || !this.imageId) return;

    try {
      await firstValueFrom(
        this.http.put<any>(this.apiConfigService.endpoints.image.update(this.imageId), {
          title: this.editTitleValue.trim()
        })
      );

      this.editingTitle = false;
      this.titleChanged.emit(this.editTitleValue);

      // Auto-refresh to show updated data
      await this.reloadImage();

    } catch (error: any) {
      this.notificationService.error(`Error updating title: ${error.message}`);
    }
  }

  cancelEditTitle() {
    this.editingTitle = false;
    this.editTitleValue = '';
  }

  onDownloadOriginal() {
    this.downloadOriginal.emit();
  }

  onPreview() {
    this.previewImage.emit();
  }

  ngOnInit() {
    if (this.imageId) {
      this.loadImageFromDB(this.imageId);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['imageId'] && this.imageId && this.imageId !== changes['imageId'].previousValue) {
      this.loadImageFromDB(this.imageId);
    } else if (changes['image'] && this.image?.url) {
      // Load blob URL when image changes
      this.loadImageBlob();
    } else if (!this.image) {
      this.imageBlobUrl = '';
    }
  }

  private loadImageBlob() {
    console.log('🖼️ Loading blob for URL:', this.image?.url);
    console.log('🖼️ Image object:', this.image);
    if (this.image?.url) {
      this.imageBlobService.getImageBlobUrl(this.image.url).subscribe({
        next: (blobUrl) => {
          this.imageBlobUrl = blobUrl;
        },
        error: (error) => {
          console.error('Failed to load image blob:', error);
          this.imageBlobUrl = '';
        }
      });
    }
  }

  public async reloadImage() {
    if (this.imageId) {
      await this.loadImageFromDB(this.imageId);
    }
  }

  private async loadImageFromDB(imageId: string) {
    console.log('🔍 Loading image with ID:', imageId);
    this.isLoading = true;
    this.loadingError = null;

    try {
      const response = await firstValueFrom(
        this.http.get<any>(this.apiConfigService.endpoints.image.detail(imageId))
      );

      if (response && response.data) {
        this.image = response.data;
      } else {
        this.image = response;
      }

      // Load the blob URL for the image
      this.loadImageBlob();

    } catch (error: any) {
      this.loadingError = `Failed to load image: ${error.message}`;
      this.notificationService.error(`Error loading image details: ${error.message}`);
      this.image = null;
    } finally {
      this.isLoading = false;
    }
  }

  getDisplayTitle(image: any): string {
    if (!image) return '';
    return image.title || image.prompt?.slice(0, 50) + (image.prompt?.length > 50 ? '...' : '') || 'Untitled Image';
  }

  formatDate(dateString: string): string {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  onImageError(event: any) {
    console.error('Image failed to load:', event);
  }

  shouldShowMetaInfo(type: string): boolean {
    return this.showMetaInfo.includes(type);
  }

  getImageSizeClass(): string {
    if (!this.image?.size) return '';

    const size = this.image.size;

    if (size === '1024x1024') {
      return 'square';
    } else if (size === '1792x1024') {
      return 'landscape';
    } else if (size === '1024x1792') {
      return 'portrait';
    }

    return '';
  }
}