import {Component, OnInit, ViewEncapsulation, ViewChild, ElementRef} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {SongService} from '../services/song.service';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {DisplayNamePipe} from '../pipes/display-name.pipe';
import {PopupAudioPlayerComponent} from '../shared/popup-audio-player/popup-audio-player.component';

@Component({
  selector: 'app-song-view',
  standalone: true,
  imports: [CommonModule, FormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, DisplayNamePipe, PopupAudioPlayerComponent],
  templateUrl: './song-view.component.html',
  styleUrl: './song-view.component.css',
  encapsulation: ViewEncapsulation.None
})
export class SongViewComponent implements OnInit {
  // Songs list and pagination
  songs: any[] = [];
  filteredSongs: any[] = [];
  selectedSong: any = null;
  pagination: any = {
    total: 0,
    limit: 50,
    offset: 0,
    has_more: false
  };

  // Search and sort
  searchTerm: string = '';
  sortDirection: 'asc' | 'desc' = 'desc';

  // UI state
  isLoading = false;
  isLoadingSongs = false;
  loadingMessage = '';

  // Keep consistent pagination - show more items
  itemsPerPage = 50;

  // Audio and features
  currentlyPlaying: string | null = null;
  audioUrl: string | null = null;
  stemDownloadUrl: string | null = null;
  showPopupPlayer = false;
  currentSongTitle = '';

  // Modal state
  showModal = false;
  modalTitle = '';
  modalContent = '';
  modalType: 'lyrics' | 'prompt' | '' = '';

  // Lyrics dialog state
  showLyricsDialog = false;

  // Make Math available in template
  Math = Math;

  // Selection mode state
  isSelectionMode = false;
  selectedSongIds: Set<string> = new Set();

  // Inline editing state
  editingTitle = false;
  editTitleValue = '';

  @ViewChild('titleInput') titleInput!: ElementRef;

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
      
      this.applyFilterAndSort();

      // Auto-select first song if available and none selected
      if (this.filteredSongs.length > 0 && !this.selectedSong) {
        await this.selectSong(this.filteredSongs[0]);
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
      } else {
        // Otherwise fetch full details
          this.selectedSong = await this.songService.getSongById(song.id);
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

  // Title editing methods
  getDisplayTitle(song: any): string {
    if (song.title && song.title.trim()) {
      return song.title.trim();
    }
    // Fallback to lyrics preview like before (using DisplayNamePipe logic)
    if (song.lyrics && song.lyrics.trim()) {
      const lyrics = song.lyrics.trim();
      return lyrics.length > 30 ? lyrics.substring(0, 27) + '...' : lyrics;
    }
    // Final fallback
    return 'Untitled Song';
  }

  startEditTitle() {
    if (!this.selectedSong) return;

    this.editingTitle = true;
    // Use current title if exists, otherwise use generated title as template
    this.editTitleValue = this.selectedSong.title || this.getDisplayTitle(this.selectedSong);

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
    if (!this.selectedSong) return;

    this.isLoading = true;
    try {
      const response = await fetch(this.apiConfig.endpoints.song.update(this.selectedSong.id), {
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

      const updatedSong = await response.json();

      // Update selected song with new data (ensure all fields are preserved)
      this.selectedSong = {
        ...this.selectedSong,
        title: updatedSong.title,
        updated_at: updatedSong.updated_at
      };

      // Update in songs list too
      const songIndex = this.songs.findIndex(song => song.id === this.selectedSong!.id);
      if (songIndex !== -1) {
        this.songs[songIndex] = {
          ...this.songs[songIndex],
          title: updatedSong.title
        };
        this.applyFilterAndSort(); // Refresh filtered list
      }

      this.editingTitle = false;
      this.editTitleValue = '';

      this.notificationService.success('Title updated successfully!');

    } catch (error: any) {
      this.notificationService.error(`Error updating title: ${error.message}`);
    } finally {
      this.isLoading = false;
    }
  }

  formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString();
  }

  formatDateShort(dateString: string): string {
    return new Date(dateString).toLocaleDateString('de-CH', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  }

  formatDateDetailed(dateString: string): string {
    return new Date(dateString).toLocaleDateString('de-CH', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // Client-side filter and sort
  applyFilterAndSort() {
    let filtered = [...this.songs];

    // Apply search filter (search in title and fallback to lyrics)
    if (this.searchTerm.trim()) {
      const term = this.searchTerm.toLowerCase().trim();
      filtered = filtered.filter(song => {
        const displayTitle = this.getDisplayTitle(song).toLowerCase();
        return displayTitle.includes(term) || song.lyrics?.toLowerCase().includes(term);
      });
    }

    // Apply sort by created date
    filtered.sort((a, b) => {
      const dateA = new Date(a.created_at).getTime();
      const dateB = new Date(b.created_at).getTime();
      return this.sortDirection === 'desc' ? dateB - dateA : dateA - dateB;
    });

    this.filteredSongs = filtered;
  }

  onSearchChange(searchTerm: string) {
    this.searchTerm = searchTerm;
    this.applyFilterAndSort();
  }

  toggleSort() {
    this.sortDirection = this.sortDirection === 'desc' ? 'asc' : 'desc';
    this.applyFilterAndSort();
  }

  clearSelection() {
    this.selectedSong = null;
    this.stopAudio();
    this.stemDownloadUrl = null;
  }

  // Selection mode methods
  toggleSelectionMode() {
    this.isSelectionMode = !this.isSelectionMode;
    if (!this.isSelectionMode) {
      this.selectedSongIds.clear();
    }
  }

  toggleSongSelection(songId: string) {
    if (this.selectedSongIds.has(songId)) {
      this.selectedSongIds.delete(songId);
    } else {
      this.selectedSongIds.add(songId);
    }
  }

  selectAllSongs() {
    this.filteredSongs.forEach(song => {
      this.selectedSongIds.add(song.id);
    });
  }

  deselectAllSongs() {
    this.selectedSongIds.clear();
  }

  onSelectAllChange(event: Event) {
    const checkbox = event.target as HTMLInputElement;
    if (checkbox.checked) {
      this.selectAllSongs();
    } else {
      this.deselectAllSongs();
    }
  }

  async bulkDeleteSongs() {
    if (this.selectedSongIds.size === 0) {
      this.notificationService.error('No songs selected for deletion');
      return;
    }

    const confirmation = confirm(`Are you sure you want to delete ${this.selectedSongIds.size} selected song(s)?`);
    if (!confirmation) {
      return;
    }

    this.isLoading = true;
    try {
      const response = await fetch(this.apiConfig.endpoints.song.bulkDelete, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ids: Array.from(this.selectedSongIds)
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();

      // Show detailed result notification
      if (result.summary) {
        const { deleted, not_found, errors } = result.summary;
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
      this.selectedSongIds.clear();
      this.isSelectionMode = false;

      // Clear selected song if it was deleted
      if (this.selectedSong && this.selectedSongIds.has(this.selectedSong.id)) {
        this.selectedSong = null;
        this.stopAudio();
      }

      // Reload current page
      await this.loadSongs();

    } catch (error: any) {
      this.notificationService.error(`Error deleting songs: ${error.message}`);
    } finally {
      this.isLoading = false;
    }
  }

  // Modern pagination methods
  getVisiblePages(): (number | string)[] {
    const totalPages = Math.ceil(this.pagination.total / this.pagination.limit);
    const current = Math.floor(this.pagination.offset / this.pagination.limit) + 1;
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
      this.pagination.offset = pageIndex * this.pagination.limit;
      this.loadSongs();
    }
  }

  trackByPage(index: number, page: number | string): number | string {
    return page;
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

  // Lyrics dialog methods
  openLyricsDialog() {
    if (!this.selectedSong?.lyrics) return;
    this.showLyricsDialog = true;
  }

  closeLyricsDialog() {
    this.showLyricsDialog = false;
  }

  async copyLyricsToClipboard() {
    if (!this.selectedSong?.lyrics) return;

    try {
      await navigator.clipboard.writeText(this.selectedSong.lyrics);
      this.notificationService.success('Lyrics copied to clipboard!');
    } catch (error) {
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = this.selectedSong.lyrics;
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        document.execCommand('copy');
        this.notificationService.success('Lyrics copied to clipboard!');
      } catch (err) {
        this.notificationService.error('Failed to copy lyrics to clipboard');
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
      this.currentSongTitle = this.getSongTitle(this.selectedSong) + ` (Choice ${choiceId})`;
      this.showPopupPlayer = true;
    }
  }

  stopAudio() {
    this.audioUrl = null;
    this.currentlyPlaying = null;
    this.showPopupPlayer = false;
    this.currentSongTitle = '';
  }

  onPopupPlayerClose() {
    this.stopAudio();
  }

  onPopupPlayerEnded() {
    this.stopAudio();
  }

  onCanPlayThrough() {
  }

  downloadFlac(flacUrl: string) {
    // Create a temporary anchor element to trigger the download
    const link = document.createElement('a');
    link.href = flacUrl;
    link.download = ''; // This will use the filename from the URL
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  downloadStems(stemsUrl: string) {
    // Create a temporary anchor element to trigger the download
    const link = document.createElement('a');
    link.href = stemsUrl;
    link.download = ''; // This will use the filename from the URL
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
}
