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
    @Input() showEditWorkflow: boolean = true;
    @Input() showRating: boolean = true;
    @Input() title: string = 'Song Details';
    @Input() showMetaInfo: string[] = ['job_id', 'model', 'status', 'created', 'completed'];
    @Input() placeholderText: string = 'Select a song from the list to view details';
    @Input() placeholderIcon: string = 'fas fa-music';
    @Input() currentlyPlayingId: string | null = null;

    @Output() titleChanged = new EventEmitter<string>();
    @Output() tagsChanged = new EventEmitter<string[]>();
    @Output() workflowChanged = new EventEmitter<string>();
    @Output() downloadFlac = new EventEmitter<string>();
    @Output() playAudio = new EventEmitter<{ url: string, id: string, choiceNumber: number }>();
    @Output() generateStem = new EventEmitter<string>();
    @Output() downloadStems = new EventEmitter<string>();
    @Output() copyLyrics = new EventEmitter<void>();
    @Output() updateRating = new EventEmitter<{ choiceId: string, rating: number | null }>();

    @ViewChild('titleInput') titleInput!: ElementRef;
    @ViewChild('lyricsTextarea') lyricsTextarea!: ElementRef;

    // Component state
    editingTitle = false;
    editTitleValue = '';
    editingTags = false;
    selectedTags: string[] = [];
    editingWorkflow = false;
    selectedWorkflow = '';
    showLyricsDialog = false;

    // Tag categories from song-view
    tagCategories = {
        style: ['pop', 'rock', 'alternative', 'jazz', 'classical', 'electronic', 'hip-hop', 'country', 'folk', 'blues', 'reggae'],
        theme: ['love', 'friendship', 'adventure', 'nostalgia', 'hope', 'struggle', 'celebration', 'mystery', 'nature', 'dreams']
    };

    // Workflow options
    workflowOptions = [
        { value: '', label: 'No Workflow' },
        { value: 'inUse', label: 'In Use' },
        { value: 'onWork', label: 'On Work' },
        { value: 'notUsed', label: 'Not Used' }
    ];

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

    // Workflow editing methods
    startEditWorkflow() {
        if (!this.showEditWorkflow || !this.song) return;
        this.editingWorkflow = true;
        this.selectedWorkflow = this.song.workflow || '';
    }

    saveWorkflow() {
        this.workflowChanged.emit(this.selectedWorkflow);
        this.editingWorkflow = false;
    }

    cancelEditWorkflow() {
        this.editingWorkflow = false;
        this.selectedWorkflow = '';
    }

    getWorkflowDisplay(): string {
        if (!this.song?.workflow) return 'No Workflow';
        const option = this.workflowOptions.find(opt => opt.value === this.song.workflow);
        return option?.label || this.song.workflow;
    }

    // Audio methods
    onPlayAudio(url: string, id: string, choiceNumber: number) {
        this.playAudio.emit({url, id, choiceNumber});
    }

    onDownloadFlac(url: string) {
        this.downloadFlac.emit(url);
    }

    onGenerateStem(choiceId: string) {
        this.generateStem.emit(choiceId);
    }

    onDownloadStems(url: string) {
        this.downloadStems.emit(url);
    }

    onUpdateRating(choiceId: string, rating: number | null) {
        this.updateRating.emit({ choiceId, rating });
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

    formatDuration(createdAt: string, completedAt: string): string {
        if (!createdAt || !completedAt) return '';

        const created = new Date(createdAt);
        const completed = new Date(completedAt);
        const diffMs = completed.getTime() - created.getTime();

        if (diffMs < 0) return '';

        const totalMinutes = Math.floor(diffMs / (1000 * 60));
        const hours = Math.floor(totalMinutes / 60);
        const minutes = totalMinutes % 60;

        if (hours > 0) {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}h`;
        } else {
            return `${minutes.toString().padStart(2, '0')}:${Math.floor((diffMs % (1000 * 60)) / 1000).toString().padStart(2, '0')}m`;
        }
    }

    formatDateShort(dateString: string): string {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString('de-DE');
    }

    shouldShowMetaInfo(type: string): boolean {
        return this.showMetaInfo.includes(type);
    }
}
