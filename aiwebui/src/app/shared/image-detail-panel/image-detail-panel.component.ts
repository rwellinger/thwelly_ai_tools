import { Component, Input, Output, EventEmitter, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-image-detail-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './image-detail-panel.component.html',
  styleUrl: './image-detail-panel.component.scss'
})
export class ImageDetailPanelComponent {
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
      this.downloadClicked.emit(this.image.url);
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
