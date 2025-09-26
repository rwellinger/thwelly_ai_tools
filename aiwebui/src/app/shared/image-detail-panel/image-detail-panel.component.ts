import { Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnChanges, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ImageBlobService } from '../../services/image-blob.service';

@Component({
  selector: 'app-image-detail-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './image-detail-panel.component.html',
  styleUrl: './image-detail-panel.component.scss'
})
export class ImageDetailPanelComponent implements OnChanges {
  private imageBlobService = inject(ImageBlobService);
  imageBlobUrl: string = '';
  @Input() image: any = null;
  @Input() showEditTitle: boolean = true;
  @Input() title: string = 'Image Details';
  @Input() showMetaInfo: string[] = ['model', 'size', 'created'];
  @Input() placeholderText: string = 'Select an image from the list to view details';
  @Input() placeholderIcon: string = 'fas fa-image';

  @Output() titleChanged = new EventEmitter<string>();
  @Output() downloadClicked = new EventEmitter<string>();
  @Output() previewClicked = new EventEmitter<void>();

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

  saveTitle() {
    if (!this.image) return;
    this.titleChanged.emit(this.editTitleValue);
    this.editingTitle = false;
  }

  cancelEditTitle() {
    this.editingTitle = false;
    this.editTitleValue = '';
  }

  onDownload() {
    if (this.image?.url) {
      // Use authenticated download instead of window.open
      this.imageBlobService.downloadImage(this.image.url, this.getImageFilename());
    }
  }

  private getImageFilename(): string {
    const title = this.image?.title || this.image?.prompt || 'image';
    const sanitized = title.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50);
    return `${sanitized}.png`;
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['image'] && this.image?.url) {
      // Load blob URL when image changes
      this.imageBlobService.getImageBlobUrl(this.image.url).subscribe({
        next: (blobUrl) => {
          this.imageBlobUrl = blobUrl;
        },
        error: (error) => {
          console.error('Failed to load image blob:', error);
          this.imageBlobUrl = '';
        }
      });
    } else if (!this.image) {
      this.imageBlobUrl = '';
    }
  }

  onPreview() {
    this.previewClicked.emit();
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
