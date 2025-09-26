import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, map, catchError, shareReplay } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ImageBlobService {
  private http = inject(HttpClient);
  private blobCache = new Map<string, Observable<string>>();

  /**
   * Get blob URL for image with authentication headers
   */
  getImageBlobUrl(imageUrl: string): Observable<string> {
    if (!imageUrl) {
      return of('');
    }

    // Check cache first
    if (this.blobCache.has(imageUrl)) {
      return this.blobCache.get(imageUrl)!;
    }

    // Create observable for authenticated image fetch
    const blobUrl$ = this.http.get(imageUrl, {
      responseType: 'blob',
      // HttpClient will automatically add auth headers via interceptor
    }).pipe(
      map((blob: Blob) => {
        // Create blob URL for display
        return URL.createObjectURL(blob);
      }),
      catchError(error => {
        console.error('Failed to load image:', imageUrl, error);
        // Return empty string on error - image will show broken
        return of('');
      }),
      shareReplay(1) // Cache the result
    );

    // Cache the observable
    this.blobCache.set(imageUrl, blobUrl$);
    return blobUrl$;
  }

  /**
   * Download image with authentication
   */
  downloadImage(imageUrl: string, filename?: string): void {
    if (!imageUrl) return;

    this.http.get(imageUrl, {
      responseType: 'blob'
    }).subscribe({
      next: (blob: Blob) => {
        // Create download link
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename || this.extractFilename(imageUrl);

        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Cleanup
        URL.revokeObjectURL(url);
      },
      error: (error) => {
        console.error('Failed to download image:', error);
      }
    });
  }

  /**
   * Clear blob cache for memory management
   */
  clearCache(): void {
    // Revoke all blob URLs to free memory
    this.blobCache.forEach(obs => {
      obs.subscribe(url => {
        if (url) {
          URL.revokeObjectURL(url);
        }
      });
    });
    this.blobCache.clear();
  }

  /**
   * Remove specific image from cache
   */
  clearImageFromCache(imageUrl: string): void {
    const obs = this.blobCache.get(imageUrl);
    if (obs) {
      obs.subscribe(url => {
        if (url) {
          URL.revokeObjectURL(url);
        }
      });
      this.blobCache.delete(imageUrl);
    }
  }

  private extractFilename(url: string): string {
    try {
      const pathname = new URL(url).pathname;
      return pathname.split('/').pop() || 'image.png';
    } catch {
      return 'image.png';
    }
  }
}