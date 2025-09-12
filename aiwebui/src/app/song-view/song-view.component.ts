import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import {CommonModule} from '@angular/common';
import {SongService} from '../services/song.service';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { DisplayNamePipe } from '../pipes/display-name.pipe';

@Component({
  selector: 'app-song-view',
  standalone: true,
  imports: [CommonModule, HeaderComponent, FooterComponent, MatSnackBarModule, DisplayNamePipe],
  templateUrl: './song-view.component.html',
  styleUrl: './song-view.component.css',
  encapsulation: ViewEncapsulation.None
})
export class SongViewComponent implements OnInit {
  // Songs list and pagination
  songs: any[] = [];
  selectedSong: any = null;
  pagination: any = {
    total: 0,
    limit: 20,
    offset: 0,
    has_more: false
  };
  
  // UI state
  isLoading = false;
  isLoadingSongs = false;
  loadingMessage = '';
  successMessage = '';
  
  // Audio and features
  currentlyPlaying: string | null = null;
  audioUrl: string | null = null;
  stemDownloadUrl: string | null = null;

  // Modal state
  showModal = false;
  modalTitle = '';
  modalContent = '';
  modalType: 'lyrics' | 'prompt' | '' = '';

  // Make Math available in template
  Math = Math;

  constructor(
    private songService: SongService,
    private apiConfig: ApiConfigService,
    private notificationService: NotificationService
  ) {
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  ngOnInit() {
    (window as any).angularComponentRef = this;
    this.loadSongs();
  }

  async loadSongs() {
    this.isLoadingSongs = true;
    try {
      const data = await this.songService.getSongs(this.pagination.limit, this.pagination.offset, 'SUCCESS');
      this.songs = data.songs || [];
      this.pagination = data.pagination || this.pagination;
      
      // Auto-select first song if available and none selected
      if (this.songs.length > 0 && !this.selectedSong) {
        await this.selectSong(this.songs[0]);
      }
    } catch (error: any) {
      this.notificationService.error(`Error loading songs: ${error.message}`);
    } finally {
      this.isLoadingSongs = false;
    }
  }

  async selectSong(song: any) {
    this.isLoading = true;
    this.loadingMessage = 'Loading song details...';
    this.stemDownloadUrl = null;
    this.selectedSong = null;
    this.stopAudio();
    
    try {
      // If song already has choices, use it directly
      if (song.choices && song.choices.length > 0) {
        this.selectedSong = song;
        this.notificationService.success('Song details loaded!');
      } else {
        // Otherwise fetch full details
        const data = await this.songService.getSongById(song.id);
        this.selectedSong = data;
        this.notificationService.success('Song details loaded!');
      }
    } catch (error: any) {
      this.notificationService.error(`Error loading song: ${error.message}`);
      this.selectedSong = null;
    } finally {
      this.isLoading = false;
    }
  }

  // Pagination methods
  async nextPage() {
    if (!this.pagination.has_more) return;
    
    this.pagination.offset += this.pagination.limit;
    await this.loadSongs();
  }
  
  async previousPage() {
    if (this.pagination.offset === 0) return;
    
    this.pagination.offset = Math.max(0, this.pagination.offset - this.pagination.limit);
    await this.loadSongs();
  }
  
  async loadMore() {
    if (!this.pagination.has_more) return;
    
    this.isLoadingSongs = true;
    try {
      const newOffset = this.pagination.offset + this.pagination.limit;
      const data = await this.songService.getSongs(this.pagination.limit, newOffset, 'SUCCESS');
      
      // Append new songs to existing list
      this.songs = [...this.songs, ...(data.songs || [])];
      this.pagination = data.pagination || this.pagination;
      this.pagination.offset = newOffset;
    } catch (error: any) {
      this.notificationService.error(`Error loading more songs: ${error.message}`);
    } finally {
      this.isLoadingSongs = false;
    }
  }

  // Utility methods
  getSongPreview(song: any): string {
    if (!song.lyrics) return 'No lyrics';
    // Use similar logic to DisplayNamePipe but for 20 chars
    const lyrics = song.lyrics.trim();
    return lyrics.length > 20 ? lyrics.substring(0, 17) + '...' : lyrics;
  }
  
  getSongTitle(song: any): string {
    return song.prompt || 'Untitled Song';
  }
  
  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  clearSelection() {
    this.selectedSong = null;
    this.stopAudio();
    this.stemDownloadUrl = null;
  }

  // Modal methods
  showLyrics(song: any) {
    this.modalTitle = `Lyrics - ${this.getSongTitle(song)}`;
    this.modalContent = song.lyrics || 'No lyrics available';
    this.modalType = 'lyrics';
    this.showModal = true;
  }

  showPrompt(song: any) {
    this.modalTitle = `Style Prompt - ${this.getSongTitle(song)}`;
    this.modalContent = song.prompt || 'No style prompt available';
    this.modalType = 'prompt';
    this.showModal = true;
  }

  closeModal() {
    this.showModal = false;
    this.modalTitle = '';
    this.modalContent = '';
    this.modalType = '';
  }

  async copyToClipboard() {
    try {
      await navigator.clipboard.writeText(this.modalContent);
      this.notificationService.success('Content copied to clipboard!');
    } catch (error) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = this.modalContent;
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        this.notificationService.success('Content copied to clipboard!');
      } catch (err) {
        this.notificationService.error('Failed to copy to clipboard');
      }
      document.body.removeChild(textArea);
    }
  }

  // Audio player methods
  playAudio(mp3Url: string, choiceId: string) {
    if (this.currentlyPlaying === choiceId) {
      this.stopAudio();
    } else {
      this.audioUrl = mp3Url;
      this.currentlyPlaying = choiceId;
    }
  }

  stopAudio() {
    this.audioUrl = null;
    this.currentlyPlaying = null;
  }

  onCanPlayThrough() {
    this.notificationService.info('Audio is ready to play');
  }

  // Stem generation method
  async generateStem(mp3Url: string) {
    this.isLoading = true;
    this.loadingMessage = 'Generating stems...';
    this.notificationService.loading('Generating stems...');

    try {
      const response = await Promise.race([
        fetch(this.apiConfig.endpoints.song.stems, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({url: mp3Url})
        }),
        this.delay(120000).then(() => {
          throw new Error('Timeout after 2 minutes');
        })
      ]);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'SUCCESS' && data.result && data.result.zip_url) {
        this.stemDownloadUrl = data.result.zip_url;
        this.notificationService.success('Stems generated successfully!');
      } else {
        this.stemDownloadUrl = null;
        this.notificationService.error('Stem generation failed or incomplete.');
      }
    } catch (error: any) {
      this.stemDownloadUrl = null;
      this.notificationService.error(`Error generating stem: ${error.message}`);
    } finally {
      this.isLoading = false;
    }
  }

  private formatDurationFromMs(durationMs: number): string {
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
  }
}