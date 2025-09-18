import { Component, Input, Output, EventEmitter, OnDestroy, OnChanges, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeUrl } from '@angular/platform-browser';

@Component({
  selector: 'app-popup-audio-player',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './popup-audio-player.component.html',
  styleUrl: './popup-audio-player.component.scss',
  encapsulation: ViewEncapsulation.None
})
export class PopupAudioPlayerComponent implements OnDestroy, OnChanges {
  @Input() audioUrl: string | null = null;
  @Input() songTitle: string = 'Audio Player';
  @Input() visible: boolean = false;
  @Output() closePlayer = new EventEmitter<void>();
  @Output() audioEnded = new EventEmitter<void>();
  @Output() audioLoadError = new EventEmitter<{code: number, message: string}>();

  sanitizedAudioUrl: SafeUrl | null = null;

  constructor(private sanitizer: DomSanitizer) {}

  ngOnChanges() {
    if (this.audioUrl) {
      try {
        this.sanitizedAudioUrl = this.sanitizer.bypassSecurityTrustUrl(this.audioUrl);
      } catch (error) {
        console.error('URL sanitization failed:', error);
        this.sanitizedAudioUrl = null;
      }
    } else {
      this.sanitizedAudioUrl = null;
    }
  }

  isDragging = false;
  dragStartX = 0;
  dragStartY = 0;
  initialLeft = 0;
  initialTop = 0;
  popupLeft = 50;
  popupTop = 50;

  ngOnDestroy() {
    this.cleanup();
  }

  close() {
    this.closePlayer.emit();
  }

  onLoadStart() {
    // Audio loading started
  }

  onLoadedMetadata() {
    // Audio metadata loaded successfully
  }

  onAudioError(event: any) {
    console.error('Audio loading error:', event);
    console.error('Audio URL that failed:', this.audioUrl);
    console.error('Sanitized URL:', this.sanitizedAudioUrl);

    // Get more detailed error information
    if (event.target) {
      console.error('Audio element error details:', {
        error: event.target.error,
        networkState: event.target.networkState,
        readyState: event.target.readyState,
        src: event.target.src
      });

      if (event.target.error) {
        const errorCode = event.target.error.code;
        const errorMessages: Record<number, string> = {
          1: 'MEDIA_ERR_ABORTED - Playback was aborted',
          2: 'MEDIA_ERR_NETWORK - Network error while fetching the media',
          3: 'MEDIA_ERR_DECODE - Error occurred when decoding the media',
          4: 'MEDIA_ERR_SRC_NOT_SUPPORTED - Media format not supported'
        };
        console.error('Error code:', errorCode, '-', errorMessages[errorCode] || 'Unknown error');

        // Emit error event with user-friendly message
        console.log('Emitting audioLoadError event:', errorCode);
        this.audioLoadError.emit({
          code: errorCode,
          message: this.getUserFriendlyErrorMessage(errorCode)
        });
      }
    }
  }

  private getUserFriendlyErrorMessage(errorCode: number): string {
    switch (errorCode) {
      case 2: return 'Audio file could not be loaded. Please check if the server is running.';
      case 3: return 'Audio file format is corrupted or invalid.';
      case 4: return 'Audio format not supported by your browser.';
      default: return 'Audio playback failed. Please try again.';
    }
  }

  onAudioEnded() {
    console.log('Audio ended event triggered');
    this.audioEnded.emit();
  }

  onCanPlayThrough() {
    console.log('Audio can play through - audio loaded successfully');
  }

  startDrag(event: MouseEvent) {
    this.isDragging = true;
    this.dragStartX = event.clientX;
    this.dragStartY = event.clientY;
    this.initialLeft = this.popupLeft;
    this.initialTop = this.popupTop;

    document.addEventListener('mousemove', this.onMouseMove);
    document.addEventListener('mouseup', this.onMouseUp);
    event.preventDefault();
  }

  private onMouseMove = (event: MouseEvent) => {
    if (!this.isDragging) return;

    const deltaX = event.clientX - this.dragStartX;
    const deltaY = event.clientY - this.dragStartY;

    this.popupLeft = Math.max(0, Math.min(window.innerWidth - 400, this.initialLeft + deltaX));
    this.popupTop = Math.max(0, Math.min(window.innerHeight - 200, this.initialTop + deltaY));
  };

  private onMouseUp = () => {
    this.isDragging = false;
    this.cleanup();
  };

  private cleanup() {
    document.removeEventListener('mousemove', this.onMouseMove);
    document.removeEventListener('mouseup', this.onMouseUp);
  }

  getPopupStyle() {
    return {
      'left.px': this.popupLeft,
      'top.px': this.popupTop
    };
  }
}