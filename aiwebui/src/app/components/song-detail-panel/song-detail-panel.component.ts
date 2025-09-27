import {Component, Input, Output, EventEmitter, ViewChild, ElementRef, OnInit, OnChanges, SimpleChanges, inject} from '@angular/core';
import {CommonModule} from '@angular/common';
import {FormsModule} from '@angular/forms';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {SongService} from '../../services/business/song.service';
import {NotificationService} from '../../services/ui/notification.service';
import {ApiConfigService} from '../../services/config/api-config.service';

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
    @Input() isGenerating: boolean = false;

    // Component state
    isLoading = false;
    loadingError: string | null = null;

    // Stem generation tracking
    public stemGenerationInProgress = new Set<string>();

    // Audio player state
    audioUrl: string | null = null;
    currentlyPlaying: string | null = null;
    currentSongTitle: string = '';
    isPlaying = false;
    currentTime = 0;
    duration = 0;
    volume = 1;

    @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

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
    private http = inject(HttpClient);

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
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    title: this.editTitleValue.trim()
                })
            );

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

            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    tags: tagsString
                })
            );

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
            await firstValueFrom(
                this.http.put<any>(this.apiConfigService.endpoints.song.update(this.songId), {
                    workflow: this.selectedWorkflow
                })
            );

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
        if (this.currentlyPlaying === id) {
            this.stopAudio();
        } else {
            this.playAudioInternal(url, id, choiceNumber);
        }
    }

    private playAudioInternal(mp3Url: string, choiceId: string, choiceNumber?: number) {
        this.audioUrl = mp3Url;
        this.currentlyPlaying = choiceId;
        this.currentSongTitle = this.getDisplayTitle(this.song) + ` (Choice ${choiceNumber || 'Unknown'})`;

        // Wait for audio element to be ready
        setTimeout(() => {
            if (this.audioPlayer?.nativeElement) {
                this.audioPlayer.nativeElement.load();
                this.audioPlayer.nativeElement.play();
            }
        });
    }

    playPauseAudio() {
        if (!this.audioPlayer?.nativeElement) return;

        if (this.isPlaying) {
            this.audioPlayer.nativeElement.pause();
        } else {
            this.audioPlayer.nativeElement.play();
        }
    }

    stopAudio() {
        if (this.audioPlayer?.nativeElement) {
            this.audioPlayer.nativeElement.pause();
            this.audioPlayer.nativeElement.currentTime = 0;
        }
        this.currentlyPlaying = null;
        this.audioUrl = null;
        this.isPlaying = false;
        this.currentTime = 0;
    }

    onTimeUpdate() {
        if (this.audioPlayer?.nativeElement) {
            this.currentTime = this.audioPlayer.nativeElement.currentTime;
            this.duration = this.audioPlayer.nativeElement.duration || 0;
        }
    }

    onLoadedMetadata() {
        if (this.audioPlayer?.nativeElement) {
            this.duration = this.audioPlayer.nativeElement.duration;
        }
    }

    onPlay() {
        this.isPlaying = true;
    }

    onPause() {
        this.isPlaying = false;
    }

    seekTo(event: Event) {
        const target = event.target as HTMLInputElement;
        const seekTime = parseFloat(target.value);

        if (this.audioPlayer?.nativeElement) {
            this.audioPlayer.nativeElement.currentTime = seekTime;
        }
    }

    setVolume(event: Event) {
        const target = event.target as HTMLInputElement;
        this.volume = parseFloat(target.value);

        if (this.audioPlayer?.nativeElement) {
            this.audioPlayer.nativeElement.volume = this.volume;
        }
    }

    formatTime(seconds: number): string {
        if (isNaN(seconds)) return '0:00';

        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    onDownloadFlac(url: string) {
        this.downloadFlac.emit(url);
    }

    async onGenerateStem(choiceId: string) {
        this.stemGenerationInProgress.add(choiceId);

        try {
            const data = await Promise.race([
                firstValueFrom(
                    this.http.post<any>(this.apiConfigService.endpoints.song.stems, {
                        choice_id: choiceId
                    })
                ),
                this.delay(120000).then(() => {
                    throw new Error('Timeout after 2 minutes');
                })
            ]);

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
        } catch (error: any) {
            this.loadingError = `Failed to load song: ${error.message}`;
            this.notificationService.error(`Error loading song details: ${error.message}`);
            this.song = null;
        } finally {
            this.isLoading = false;
        }
    }

    // Check if a song is instrumental
    isInstrumental(song: any): boolean {
        return song?.is_instrumental === true;
    }

    // Get the appropriate icon class for a song
    getSongIcon(song: any): string {
        return this.isInstrumental(song) ? 'fa-guitar' : 'fa-microphone';
    }

    // Get the song type display text
    getSongTypeText(song: any): string {
        return this.isInstrumental(song) ? 'Instrumental' : 'With Vocals';
    }
}
