import {
    Component,
    OnInit,
    ViewEncapsulation,
    ViewChild,
    ElementRef,
    AfterViewInit,
    OnDestroy,
    inject
} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {DisplayNamePipe} from '../pipes/display-name.pipe';
import {ImageDetailPanelComponent} from '../shared/image-detail-panel/image-detail-panel.component';
import {Subject, debounceTime, distinctUntilChanged, takeUntil} from 'rxjs';

interface ImageData {
    id: string;
    filename: string;
    model_used: string;
    prompt: string;
    prompt_hash: string;
    size: string;
    url: string;
    title?: string;
    tags?: string;
    created_at: string;
    updated_at?: string;
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
    imports: [CommonModule, FormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, DisplayNamePipe, ImageDetailPanelComponent],
    templateUrl: './image-view.component.html',
    styleUrl: './image-view.component.scss',
    encapsulation: ViewEncapsulation.None
})
export class ImageViewComponent implements OnInit, AfterViewInit, OnDestroy {
    images: ImageData[] = [];
    selectedImage: ImageData | null = null;
    isLoading = false;
    loadingMessage = '';
    currentPage = 0;
    pageSize = 15;
    pagination: PaginationInfo = {
        has_more: false,
        limit: this.pageSize,
        offset: 0,
        total: 0
    };

    // Search and sort (server-based)
    searchTerm: string = '';
    sortBy: string = 'created_at';
    sortDirection: 'asc' | 'desc' = 'desc';

    // RxJS subjects for debouncing
    private searchSubject = new Subject<string>();
    private destroy$ = new Subject<void>();

    // Modal state
    showImageModal = false;

    // Selection mode state
    isSelectionMode = false;
    selectedImageIds = new Set<string>();

    // Inline editing state
    editingTitle = false;
    editTitleValue = '';

    // Image placeholder and dimensions analysis
    @ViewChild('imagePlaceholder') imagePlaceholder!: ElementRef;
    placeholderDimensions = {
        width: 0,
        height: 0,
        aspectRatio: '0:0',
        viewportWidth: 0,
        viewportHeight: 0
    };

    @ViewChild('titleInput') titleInput!: ElementRef;
    @ViewChild('searchInput') searchInput!: ElementRef;

    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);

    constructor() {
        // Setup search debouncing
        this.searchSubject.pipe(
            debounceTime(300),
            distinctUntilChanged(),
            takeUntil(this.destroy$)
        ).subscribe(searchTerm => {
            const hadFocus = document.activeElement === this.searchInput?.nativeElement;
            this.searchTerm = searchTerm;
            this.loadImages(0).then(() => {
                // Restore focus if it was in search field
                if (hadFocus && this.searchInput) {
                    setTimeout(() => this.searchInput.nativeElement.focus(), 0);
                }
            });
        });
    }

    ngOnInit() {
        this.loadImages();
    }

    ngOnDestroy() {
        this.destroy$.next();
        this.destroy$.complete();
    }

    ngAfterViewInit() {
        // Initial dimension measurement
        this.measureDimensions();

        // Update dimensions on window resize
        window.addEventListener('resize', () => {
            setTimeout(() => this.measureDimensions(), 100);
        });
    }

    private measureDimensions() {
        if (this.imagePlaceholder) {
            const element = this.imagePlaceholder.nativeElement;
            const rect = element.getBoundingClientRect();

            this.placeholderDimensions = {
                width: Math.round(rect.width),
                height: Math.round(rect.height),
                aspectRatio: this.calculateAspectRatio(rect.width, rect.height),
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight
            };
        }
    }

    private calculateAspectRatio(width: number, height: number): string {
        if (height === 0) return '0:0';
        const gcd = this.gcd(Math.round(width), Math.round(height));
        return `${Math.round(width / gcd)}:${Math.round(height / gcd)}`;
    }

    private gcd(a: number, b: number): number {
        return b === 0 ? a : this.gcd(b, a % b);
    }

    async loadImages(page: number = 0) {
        this.isLoading = true;
        this.loadingMessage = 'Loading images...';

        try {
            const offset = page * this.pageSize;

            // Build URL with search and sort parameters
            const params = new URLSearchParams({
                limit: this.pageSize.toString(),
                offset: offset.toString(),
                sort_by: this.sortBy,
                sort_direction: this.sortDirection
            });

            if (this.searchTerm.trim()) {
                params.append('search', this.searchTerm.trim());
            }

            const url = `${this.apiConfig.endpoints.image.list(this.pageSize, offset).split('?')[0]}?${params.toString()}`;

            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.images && Array.isArray(data.images)) {
                this.images = data.images;
                this.pagination = data.pagination;
                this.currentPage = page;

                // Auto-select first image if available and none selected
                if (this.images.length > 0 && !this.selectedImage) {
                    this.selectImage(this.images[0]);
                }
            } else {
                this.images = [];
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
        // Measure dimensions when image changes
        setTimeout(() => this.measureDimensions(), 100);
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
            this.loadImages(pageIndex);
        }
    }

    trackByPage(index: number, page: number | string): number | string {
        return page;
    }

    trackByImage(index: number, image: ImageData): string {
        return image.id;
    }

    onSearchChange(searchTerm: string) {
        this.searchSubject.next(searchTerm);
    }

    clearSearch() {
        this.searchTerm = '';
        this.searchSubject.next('');
    }

    toggleSort() {
        this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
        this.loadImages(0); // Reset to first page and reload with new sort
    }

    openImageModal() {
        this.showImageModal = true;
    }

    closeImageModal() {
        this.showImageModal = false;
    }

    // Selection mode methods
    toggleSelectionMode() {
        this.isSelectionMode = !this.isSelectionMode;
        if (!this.isSelectionMode) {
            this.selectedImageIds.clear();
        }
    }

    toggleImageSelection(imageId: string) {
        if (this.selectedImageIds.has(imageId)) {
            this.selectedImageIds.delete(imageId);
        } else {
            this.selectedImageIds.add(imageId);
        }
    }

    selectAllImages() {
        this.images.forEach(image => {
            this.selectedImageIds.add(image.id);
        });
    }

    deselectAllImages() {
        this.selectedImageIds.clear();
    }

    onSelectAllChange(event: Event) {
        const checkbox = event.target as HTMLInputElement;
        if (checkbox.checked) {
            this.selectAllImages();
        } else {
            this.deselectAllImages();
        }
    }

    async bulkDeleteImages() {
        if (this.selectedImageIds.size === 0) {
            this.notificationService.error('No images selected for deletion');
            return;
        }

        const confirmation = confirm(`Are you sure you want to delete ${this.selectedImageIds.size} selected image(s)?`);
        if (!confirmation) {
            return;
        }

        this.isLoading = true;
        try {
            const response = await fetch(this.apiConfig.endpoints.image.bulkDelete, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ids: Array.from(this.selectedImageIds)
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            // Show detailed result notification
            if (result.summary) {
                const {deleted, not_found, errors} = result.summary;
                let message = `Bulk delete completed: ${deleted} deleted`;
                if (not_found > 0) message += `, ${not_found} not found`;
                if (errors > 0) message += `, ${errors} errors`;

                if (deleted > 0) {
                    this.notificationService.success(message);
                } else {
                    this.notificationService.error(message);
                }
            }

            // Clear selections and reload
            this.selectedImageIds.clear();
            this.isSelectionMode = false;

            // Clear selected image if it was deleted
            if (this.selectedImage && this.selectedImageIds.has(this.selectedImage.id)) {
                this.selectedImage = null;
            }

            // Reload current page
            await this.loadImages(this.currentPage);

        } catch (error: any) {
            this.notificationService.error(`Error deleting images: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    // Title editing methods
    getDisplayTitle(image: ImageData): string {
        if (image.title && image.title.trim()) {
            return image.title.trim();
        }
        // Generate title from prompt (first 30 chars)
        return image.prompt.length > 30 ? image.prompt.substring(0, 27) + '...' : image.prompt;
    }

    startEditTitle() {
        if (!this.selectedImage) return;

        this.editingTitle = true;
        // Use current title if exists, otherwise use generated title as template
        this.editTitleValue = this.selectedImage.title || this.getDisplayTitle(this.selectedImage);

        // Focus input after view updates
        setTimeout(() => {
            if (this.titleInput) {
                this.titleInput.nativeElement.focus();
                this.titleInput.nativeElement.select();
            }
        }, 100);
    }

    cancelEditTitle() {
        this.editingTitle = false;
        this.editTitleValue = '';
    }

    async saveTitle() {
        if (!this.selectedImage) return;

        this.isLoading = true;
        try {
            const response = await fetch(this.apiConfig.endpoints.image.update(this.selectedImage.id), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: this.editTitleValue.trim()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedImage = await response.json();

            // Update selected image with new data (ensure all fields are preserved)
            this.selectedImage = {
                ...this.selectedImage,
                title: updatedImage.title,
                tags: updatedImage.tags,
                updated_at: updatedImage.updated_at
            };

            // Update in images list too
            const imageIndex = this.images.findIndex(img => img.id === this.selectedImage!.id);
            if (imageIndex !== -1) {
                this.images[imageIndex] = {
                    ...this.images[imageIndex],
                    title: updatedImage.title,
                    tags: updatedImage.tags
                };
                this.loadImages(0); // Refresh filtered list
            }

            this.editingTitle = false;
            this.editTitleValue = '';

        } catch (error: any) {
            this.notificationService.error(`Error updating title: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    // Handlers for shared image detail panel
    async onTitleChanged(newTitle: string) {
        if (!this.selectedImage) return;

        this.isLoading = true;
        try {
            const response = await fetch(this.apiConfig.endpoints.image.update(this.selectedImage.id), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: newTitle.trim()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const updatedImage = await response.json();

            // Update selected image with new data
            this.selectedImage = {
                ...this.selectedImage,
                title: updatedImage.title,
                tags: updatedImage.tags,
                updated_at: updatedImage.updated_at
            };

            // Update in images list
            const imageIndex = this.images.findIndex(img => img.id === this.selectedImage!.id);
            if (imageIndex !== -1) {
                this.images[imageIndex] = {...this.selectedImage};
            }

            // No need to update filtered images as we use server-side filtering

        } catch (error: any) {
            this.notificationService.error(`Error updating title: ${error.message}`);
        } finally {
            this.isLoading = false;
        }
    }

    onDownloadImage(imageUrl: string) {
        this.downloadImage(imageUrl);
    }

    onPreviewImage() {
        this.openImageModal();
    }

    protected readonly Math = Math;
}
