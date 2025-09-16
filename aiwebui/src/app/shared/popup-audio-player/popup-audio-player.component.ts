import { Component, Input, Output, EventEmitter, OnDestroy, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-popup-audio-player',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './popup-audio-player.component.html',
  styleUrl: './popup-audio-player.component.css',
  encapsulation: ViewEncapsulation.None
})
export class PopupAudioPlayerComponent implements OnDestroy {
  @Input() audioUrl: string | null = null;
  @Input() songTitle: string = 'Audio Player';
  @Input() visible: boolean = false;
  @Output() closePlayer = new EventEmitter<void>();
  @Output() audioEnded = new EventEmitter<void>();

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

  onAudioEnded() {
    this.audioEnded.emit();
  }

  onCanPlayThrough() {
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