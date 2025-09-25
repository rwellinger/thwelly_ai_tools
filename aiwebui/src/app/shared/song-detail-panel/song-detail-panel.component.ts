import {Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnInit, OnChanges, SimpleChanges, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {SongService} from '../../services/song.service';
import {NotificationService} from '../../services/notification.service';
import {ApiConfigService} from '../../services/api-config.service';

@Component({
    selector: 'app-song-detail-panel',
    standalone: true,
    imports: [CommonModule, FormsModule],
    templateUrl: './song-detail-panel.component.html',
    styleUrl: './song-detail-panel.component.scss'
})
export class SongDetailPanelComponent implements OnInit, OnChanges {
    @Input() song: any = null;
    @Input() songId: string | null = null;
    @Input() showEditTitle: boolean = true;
    @Input() showEditTags: boolean = true;
    @Input() showEditWorkflow: boolean = true;
    @Input() showRating: boolean = true;
    @Input() title: string = 'Song Details';
    @Input() showMetaInfo: string[] = ['job_id', 'model', 'status', 'created', 'completed'];
    @Input() placeholderText: string = 'Select a song from the list to view details';
    @Input() placeholderIcon: string = 'fas fa-music';
    @Input() currentlyPlayingId: string | null = null;

    // Component state
    isLoading = false;
    loadingError: string | null = null;

    // Stem generation tracking
    public stemGenerationInProgress = new Set<string>();

    @Output() titleChanged = new EventEmitter<string>();
    @Output() tagsChanged = new EventEmitter<string[]>();
    @Output() workflowChanged = new EventEmitter<string>();
    @Output() downloadFlac = new EventEmitter<string>();
    @Output() playAudio = new EventEmitter<{ url: string, id: string, choiceNumber: number }>();
    @Output() downloadStems = new EventEmitter<string>();
    @Output() copyLyrics = new EventEmitter<void>();
    @Output() updateRating = new EventEmitter<{ choiceId: string, rating: number | null }>();

    @ViewChild('titleInput') titleInput!: ElementRef;
    @ViewChild('lyricsTextarea') lyricsTextarea!: ElementRef;

    // Services
    private songService = inject(SongService);
    private notificationService = inject(NotificationService);
    private apiConfigService = inject(ApiConfigService);

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

    async saveTitle() {
        if (!this.song || !this.songId) return;

        try {
            const response = await fetch(this.apiConfigService.endpoints.song.update(this.songId), {
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

            this.editingTitle = false;
            this.titleChanged.emit(this.editTitleValue);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`Error updating title: ${error.message}`);
        }
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

    async saveTags() {
        if (!this.song || !this.songId) return;

        try {
            const tagsString = this.selectedTags.join(', ');

            const response = await fetch(this.apiConfigService.endpoints.song.update(this.songId), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    tags: tagsString
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.editingTags = false;
            this.tagsChanged.emit(this.selectedTags);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`Error updating tags: ${error.message}`);
        }
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

    async saveWorkflow() {
        if (!this.song || !this.songId) return;

        try {
            const response = await fetch(this.apiConfigService.endpoints.song.update(this.songId), {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    workflow: this.selectedWorkflow
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.editingWorkflow = false;
            this.workflowChanged.emit(this.selectedWorkflow);

            // Auto-refresh to show updated data
            await this.reloadSong();

        } catch (error: any) {
            this.notificationService.error(`Error updating workflow: ${error.message}`);
        }
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

    async onGenerateStem(choiceId: string) {
        this.stemGenerationInProgress.add(choiceId);

        try {
            const response = await Promise.race([
                fetch(this.apiConfigService.endpoints.song.stems, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({choice_id: choiceId})
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
                await this.reloadSong();
            } else {
                this.notificationService.error('Stem generation failed or incomplete.');
            }


        } catch (error: any) {
            this.notificationService.error(`Error generating stem: ${error.message}`);
        } finally {
            this.stemGenerationInProgress.delete(choiceId);
        }
    }

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }


    onDownloadStems(url: string) {
        this.downloadStems.emit(url);
    }

    async onUpdateRating(choiceId: string, rating: number | null) {
        console.log('=== Rating Update ===');
        console.log('choiceId:', choiceId);
        console.log('new rating:', rating);
        console.log('current choice data:', this.song?.choices?.find((c: any) => c.id === choiceId));

        try {
            await this.songService.updateChoiceRating(choiceId, rating);

            this.updateRating.emit({ choiceId, rating });

            // Auto-refresh to show updated rating
            await this.reloadSong();

        } catch (error: any) {
            console.error('Rating update error:', error);
            this.notificationService.error(`Error updating rating: ${error.message}`);
        }
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

    ngOnInit() {
        if (this.songId) {
            this.loadSongFromDB(this.songId);
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes['songId'] && this.songId && this.songId !== changes['songId'].previousValue) {
            this.loadSongFromDB(this.songId);
        }
    }

    public async reloadSong() {
        if (this.songId) {
            await this.loadSongFromDB(this.songId);
        }
    }

    private async loadSongFromDB(songId: string) {
        this.isLoading = true;
        this.loadingError = null;

        try {
            const response = await this.songService.getSongById(songId);
            if (response && (response as any).data) {
                this.song = (response as any).data;
            } else {
                this.song = response;
            }
            console.log('Song loaded in detail panel:', this.song);
        } catch (error: any) {
            this.loadingError = `Failed to load song: ${error.message}`;
            this.notificationService.error(`Error loading song details: ${error.message}`);
            this.song = null;
        } finally {
            this.isLoading = false;
        }
    }
}
