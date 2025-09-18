import {Component, Input, Output, EventEmitter, ViewChild, ElementRef} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';

@Component({
    selector: 'app-song-detail-panel',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './song-detail-panel.component.html',
    styleUrl: './song-detail-panel.component.scss'
})
export class SongDetailPanelComponent {
    @Input() song: any = null;
    @Input() showEditTitle: boolean = true;
    @Input() showEditTags: boolean = true;
    @Input() title: string = 'Song Details';
    @Input() showMetaInfo: string[] = ['job_id', 'model', 'status', 'created', 'completed'];
    @Input() placeholderText: string = 'Select a song from the list to view details';
    @Input() placeholderIcon: string = 'fas fa-music';
    @Input() currentlyPlayingId: string | null = null;

    @Output() titleChanged = new EventEmitter<string>();
    @Output() tagsChanged = new EventEmitter<string[]>();
    @Output() downloadFlac = new EventEmitter<string>();
    @Output() playAudio = new EventEmitter<{ url: string, id: string, choiceNumber: number }>();
    @Output() generateStem = new EventEmitter<string>();
    @Output() downloadStems = new EventEmitter<string>();
    @Output() copyLyrics = new EventEmitter<void>();

    @ViewChild('titleInput') titleInput!: ElementRef;
    @ViewChild('lyricsTextarea') lyricsTextarea!: ElementRef;

    // Component state
    editingTitle = false;
    editTitleValue = '';
    editingTags = false;
    selectedTags: string[] = [];
    showLyricsDialog = false;

    // Tag categories from song-view
    tagCategories = {
        style: ['pop', 'rock', 'alternative', 'jazz', 'classical', 'electronic', 'hip-hop', 'country', 'folk', 'blues', 'reggae'],
        theme: ['love', 'friendship', 'adventure', 'nostalgia', 'hope', 'struggle', 'celebration', 'mystery', 'nature', 'dreams']
    };

    // Title editing methods
    startEditTitle() {
        if (!this.showEditTitle || !this.song) return;
        this.editingTitle = true;
        this.editTitleValue = this.getDisplayTitle(this.song);
        setTimeout(() => {
            this.titleInput?.nativeElement?.focus();
        });
    }

    saveTitle() {
        if (!this.song) return;
        this.titleChanged.emit(this.editTitleValue);
        this.editingTitle = false;
    }

    cancelEditTitle() {
        this.editingTitle = false;
        this.editTitleValue = '';
    }

    // Tags editing methods
    startEditTags() {
        if (!this.showEditTags || !this.song) return;
        this.editingTags = true;
        this.selectedTags = this.song.tags ? this.song.tags.split(',').map((tag: string) => tag.trim()) : [];
    }

    saveTags() {
        this.tagsChanged.emit(this.selectedTags);
        this.editingTags = false;
    }

    cancelEditTags() {
        this.editingTags = false;
        this.selectedTags = [];
    }

    toggleTag(tag: string) {
        const index = this.selectedTags.indexOf(tag);
        if (index > -1) {
            this.selectedTags.splice(index, 1);
        } else {
            this.selectedTags.push(tag);
        }
    }

    isTagSelected(tag: string): boolean {
        return this.selectedTags.includes(tag);
    }

    getSelectedTagsDisplay(): string {
        if (!this.song?.tags) return 'No tags';
        return this.song.tags;
    }

    // Audio methods
    onPlayAudio(url: string, id: string, choiceNumber: number) {
        this.playAudio.emit({url, id, choiceNumber});
    }

    onDownloadFlac(url: string) {
        this.downloadFlac.emit(url);
    }

    onGenerateStem(url: string) {
        this.generateStem.emit(url);
    }

    onDownloadStems(url: string) {
        this.downloadStems.emit(url);
    }

    // Lyrics methods
    openLyricsDialog() {
        this.showLyricsDialog = true;
    }

    closeLyricsDialog() {
        this.showLyricsDialog = false;
    }

    copyLyricsToClipboard() {
        this.copyLyrics.emit();
    }

    // Utility methods
    getDisplayTitle(song: any): string {
        if (!song) return '';
        return song.title || song.lyrics?.slice(0, 50) + (song.lyrics?.length > 50 ? '...' : '') || 'Untitled Song';
    }

    formatDateDetailed(dateString: string): string {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('de-DE', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDateShort(dateString: string): string {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('de-DE');
    }

    shouldShowMetaInfo(type: string): boolean {
        return this.showMetaInfo.includes(type);
    }
}
