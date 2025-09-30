import {Component, OnInit, ViewEncapsulation, inject, HostListener, ViewChild, ElementRef} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {MatDialog} from '@angular/material/dialog';
import {SongService} from '../../services/business/song.service';
import {ApiConfigService} from '../../services/config/api-config.service';
import {NotificationService} from '../../services/ui/notification.service';
import {ChatService} from '../../services/config/chat.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatCardModule} from '@angular/material/card';
import {SongDetailPanelComponent} from '../../components/song-detail-panel/song-detail-panel.component';
import {ProgressService} from '../../services/ui/progress.service';
import {LyricArchitectModalComponent} from '../../components/lyric-architect-modal/lyric-architect-modal.component';
import {LyricArchitectureService} from '../../services/lyric-architecture.service';
import {MusicStyleChooserModalComponent} from '../../components/music-style-chooser-modal/music-style-chooser-modal.component';
import {MusicStyleChooserService} from '../../services/music-style-chooser.service';

@Component({
    selector: 'app-song-generator',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, MatSnackBarModule, MatCardModule, SongDetailPanelComponent],
    templateUrl: './song-generator.component.html',
    styleUrl: './song-generator.component.scss',
    encapsulation: ViewEncapsulation.None
})
export class SongGeneratorComponent implements OnInit {
    songForm!: FormGroup;
    isLoading = false;
    isImprovingPrompt = false;
    isTranslatingLyrics = false;
    isGeneratingLyrics = false;
    isTranslatingStylePrompt = false;
    isGeneratingTitle = false;
    showLyricsDropdown = false;
    showStyleDropdown = false;
    showTitleDropdown = false;
    loadingMessage = '';
    result = '';
    currentlyPlaying: string | null = null;
    currentSongId: string | null = null;

    // Audio player state
    audioUrl: string | null = null;
    currentSongTitle: string = '';
    isPlaying = false;
    currentTime = 0;
    duration = 0;
    volume = 1;
    isMuted = false;
    isLoaded = false;

    @ViewChild(SongDetailPanelComponent) songDetailPanel!: SongDetailPanelComponent;
    @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

    private fb = inject(FormBuilder);
    private songService = inject(SongService);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private dialog = inject(MatDialog);
    private architectureService = inject(LyricArchitectureService);
    private musicStyleChooserService = inject(MusicStyleChooserService);

    ngOnInit() {
        this.songForm = this.fb.group({
            lyrics: ['', Validators.required],
            prompt: ['', Validators.required],
            model: ['auto', Validators.required],
            title: ['', [Validators.maxLength(50)]],
            isInstrumental: [false]
        });

        // Load saved form data
        const savedData = this.songService.loadFormData();
        if (savedData.lyrics || savedData.isInstrumental || savedData.title) {
            this.songForm.patchValue(savedData);
        }

        // Update validators when isInstrumental changes
        this.songForm.get('isInstrumental')?.valueChanges.subscribe(isInstrumental => {
            this.updateValidators(isInstrumental);
        });

        // Save form data on changes
        this.songForm.valueChanges.subscribe(value => {
            this.songService.saveFormData(value);
        });

        // Initialize validators based on current state
        this.updateValidators(this.songForm.get('isInstrumental')?.value || false);
    }

    async onSubmit() {
        if (this.songForm.valid) {
            const isInstrumental = this.songForm.get('isInstrumental')?.value;
            if (isInstrumental) {
                await this.generateInstrumental();
            } else {
                await this.generateSong();
            }
        }
    }

    resetForm() {
        this.songForm.reset({model: 'auto', isInstrumental: false});
        this.songService.clearFormData();
        this.result = '';
    }


    async generateSong() {
        const formValue = this.songForm.value;
        this.isLoading = true;
        this.result = '';

        try {
            const data = await this.songService.generateSong(
                formValue.lyrics.trim(),
                formValue.prompt.trim(),
                formValue.model,
                formValue.title?.trim() || undefined
            );

            if (data.task_id) {
                // Store song_id if provided by backend
                if (data.song_id) {
                    this.currentSongId = data.song_id;
                }
                await this.checkSongStatus(data.task_id, false);
            } else {
                // Business logic error (not HTTP error)
                this.notificationService.error('Error initiating song generation.');
                this.result = 'Error initiating song generation.';
                this.isLoading = false;  // Reset loading state
            }
        } catch (err: any) {
            // Error notification is handled by error.interceptor
            this.result = `Error: ${err.message || 'Song generation failed'}`;
            this.isLoading = false;  // Reset loading state on error
        }
    }

    async generateInstrumental() {
        const formValue = this.songForm.value;
        this.isLoading = true;
        this.result = '';

        try {
            const data = await this.songService.generateInstrumental(
                formValue.title.trim(),
                formValue.prompt.trim(),
                formValue.model
            );

            if (data.task_id) {
                // Store song_id if provided by backend
                if (data.song_id) {
                    this.currentSongId = data.song_id;
                }
                await this.checkSongStatus(data.task_id, true);
            } else {
                // Business logic error (not HTTP error)
                this.notificationService.error('Error initiating instrumental generation.');
                this.result = 'Error initiating instrumental generation.';
                this.isLoading = false;  // Reset loading state
            }
        } catch (err: any) {
            // Error notification is handled by error.interceptor
            this.result = `Error: ${err.message || 'Instrumental generation failed'}`;
            this.isLoading = false;  // Reset loading state on error
        }
    }

    async checkSongStatus(taskId: string, isInstrumental: boolean = false) {
        let completed = false;
        let interval = 5000;

        while (!completed) {
            try {
                const data = isInstrumental
                    ? await this.songService.checkInstrumentalStatus(taskId)
                    : await this.songService.checkSongStatus(taskId);

                if (data.status === 'SUCCESS') {
                    await this.renderResultTask(data.result);
                    completed = true;
                } else if (data.status === 'FAILURE') {
                    const errorMessage = data.result?.error || data.result || `${isInstrumental ? 'Instrumental' : 'Song'} generation failed`;
                    this.notificationService.error(`${isInstrumental ? 'Instrumental' : 'Song'} generation failed: ${errorMessage}`);
                    this.result = `<div class="error-box">Error: ${errorMessage}</div>`;
                    completed = true;
                } else {
                    const statusText = this.getStatusText(data);
                    this.loadingMessage = `${statusText} ... Please wait until finished.`;
                    interval = Math.min(interval * 1.5, 60000);
                    await new Promise(resolve => setTimeout(resolve, interval));
                }
            } catch (error: any) {
                // Error notification is handled by error.interceptor
                this.result = `Error fetching status: ${error.message || 'Status check failed'}`;
                completed = true;
            }
        }

        this.isLoading = false;
    }

    async renderResultTask(data: any): Promise<void> {
        // Only use DB loading - no more MUREKA result fallback
        if (this.currentSongId && (data.status === 'SUCCESS' || data.status === 'succeeded')) {
            this.result = '';
            // Einfach das Detail Panel refreshen - Daten sind bereits in DB
            if (this.songDetailPanel) {
                // Sicherstellen dass die songId gesetzt ist bevor wir reloadSong aufrufen
                this.songDetailPanel.songId = this.currentSongId;
                await this.songDetailPanel.reloadSong();
            }
            return;
        } else if (data.status === 'FAILURE') {
            // Nur bei FAILURE Fehler zeigen
            this.result = 'Error: Song generation failed.';
            this.notificationService.error('Song generation failed');
        }
    }



    // Event handlers for song detail panel
    onPlayAudio(event: {url: string, id: string, choiceNumber: number}) {
        this.onPlayAudioInternal(event.url, event.id);
    }

    // Audio methods
    onPlayAudioInternal(url: string, id: string) {
        if (this.currentlyPlaying === id) {
            this.stopAudio();
        } else {
            this.playAudioInternal(url, id);
        }
    }

    private playAudioInternal(mp3Url: string, choiceId: string) {
        this.audioUrl = mp3Url;
        this.currentlyPlaying = choiceId;
        // Get song title from current song via song detail panel
        const currentSong = this.songDetailPanel?.song;
        const songTitle = currentSong?.title || 'Generated Song';
        this.currentSongTitle = songTitle.length > 40 ? songTitle.substring(0, 37) + '...' : songTitle;

        // Wait for audio element to be ready
        setTimeout(() => {
            if (this.audioPlayer?.nativeElement) {
                this.audioPlayer.nativeElement.volume = this.volume;
                this.audioPlayer.nativeElement.play();
            }
        }, 100);
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
        this.isLoaded = false;
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
            this.isLoaded = true;
        }
    }

    onPlay() {
        this.isPlaying = true;
    }

    onPause() {
        this.isPlaying = false;
    }

    onSeek(event: Event) {
        const target = event.target as HTMLInputElement;
        const seekTime = parseFloat(target.value);
        if (this.audioPlayer?.nativeElement) {
            this.audioPlayer.nativeElement.currentTime = seekTime;
        }
    }

    toggleMute() {
        if (!this.audioPlayer?.nativeElement) return;

        this.isMuted = !this.isMuted;
        this.audioPlayer.nativeElement.muted = this.isMuted;
    }

    onVolumeChange(event: Event) {
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

    onDownloadStems(url: string) {
        this.downloadStems(url);
    }

    onCopyLyrics() {
        // No-op: Panel handles this internally
    }

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    private getStatusText(data: any): string {
        // Check for specific internal progress statuses first
        if (data.progress?.status) {
            switch (data.progress.status) {
                case 'SLOT_ACQUIRED':
                    return 'Acquiring Mureka slot';
                case 'GENERATION_STARTED':
                    return 'Starting song generation';
                case 'POLLING':
                    return 'Processing with Mureka';
                default:
                    break;
            }
        }

        // Check for mureka-specific status
        if (data.progress?.mureka_status) {
            switch (data.progress.mureka_status) {
                case 'preparing':
                    return 'Preparing song generation';
                case 'queued':
                    return 'Queued for processing';
                case 'running':
                    return 'Generating song with AI';
                case 'timeouted':
                    return 'Processing (timeout handling)';
                default:
                    return `Processing with Mureka (${data.progress.mureka_status})`;
            }
        }

        // Fallback to general celery status
        switch (data.status) {
            case 'PENDING':
                return 'Initializing request';
            case 'PROGRESS':
                return 'Processing request';
            default:
                return 'Processing';
        }
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


    // Handlers for shared song detail panel - now handled directly by the shared component
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onTitleChanged(_newTitle: string) {
        // No-op: Shared component handles this
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onTagsChanged(_newTags: string[]) {
        // No-op: Shared component handles this
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onWorkflowChanged(_newWorkflow: string) {
        // No-op: Shared component handles this
    }

    onDownloadFlac(url: string) {
        this.downloadFlac(url);
    }


    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    onUpdateRating(_event: { choiceId: string, rating: number | null }) {
        // No-op: Shared component handles this
    }

    async improvePrompt() {
        const currentPrompt = this.songForm.get('prompt')?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error('Please enter a music style prompt first');
            return;
        }

        this.isImprovingPrompt = true;
        try {
            const improvedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.improveMusicStylePrompt(currentPrompt),
                'Enhancing Style Prompt...',
                'AI is improving your music style description'
            );
            this.songForm.patchValue({prompt: this.removeQuotes(improvedPrompt)});
        } catch (error: any) {
            // Error notification is handled by error.interceptor
        } finally {
            this.isImprovingPrompt = false;
        }
    }

    async generateLyrics() {
        const currentText = this.songForm.get('lyrics')?.value?.trim();
        if (!currentText) {
            this.notificationService.error('Please enter text first');
            return;
        }

        this.isGeneratingLyrics = true;
        try {
            const generatedLyrics = await this.progressService.executeWithProgress(
                () => this.chatService.generateLyrics(currentText),
                'Creating Lyrics...',
                'AI is generating song lyrics from your text'
            );
            this.songForm.patchValue({lyrics: this.removeQuotes(generatedLyrics)});
        } catch (error: any) {
            // Error notification is handled by error.interceptor
        } finally {
            this.isGeneratingLyrics = false;
        }
    }

    async translateLyrics() {
        const currentLyrics = this.songForm.get('lyrics')?.value?.trim();
        if (!currentLyrics) {
            this.notificationService.error('Please enter lyrics first');
            return;
        }

        this.isTranslatingLyrics = true;
        try {
            const translatedLyrics = await this.progressService.executeWithProgress(
                () => this.chatService.translateLyric(currentLyrics),
                'Translating Lyrics...',
                'AI is translating your lyrics to English'
            );
            this.songForm.patchValue({lyrics: this.removeQuotes(translatedLyrics)});
        } catch (error: any) {
            // Error notification is handled by error.interceptor
        } finally {
            this.isTranslatingLyrics = false;
        }
    }

    toggleLyricsDropdown() {
        this.showLyricsDropdown = !this.showLyricsDropdown;
    }

    closeLyricsDropdown() {
        this.showLyricsDropdown = false;
    }

    selectLyricsAction(action: 'generate' | 'translate' | 'architecture') {
        this.closeLyricsDropdown();

        if (action === 'generate') {
            this.generateLyrics();
        } else if (action === 'translate') {
            this.translateLyrics();
        } else if (action === 'architecture') {
            this.openLyricArchitectModal();
        }
    }

    openLyricArchitectModal(): void {
        const dialogRef = this.dialog.open(LyricArchitectModalComponent, {
            width: '800px',
            maxWidth: '90vw',
            maxHeight: '90vh',
            disableClose: false,
            autoFocus: true
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && result.architectureString) {
                this.notificationService.success('Song architecture updated successfully');
            }
        });
    }

    openMusicStyleChooserModal(): void {
        const isInstrumental = this.isInstrumental();
        const dialogRef = this.dialog.open(MusicStyleChooserModalComponent, {
            width: '1100px',
            maxWidth: '95vw',
            maxHeight: '90vh',
            disableClose: false,
            autoFocus: true,
            data: { isInstrumental }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result && result.stylePrompt) {
                // Apply the generated style prompt to the form
                this.songForm.patchValue({
                    prompt: result.stylePrompt
                });
                this.notificationService.success('Music style selection applied successfully');
            }
        });
    }

    toggleStyleDropdown() {
        this.showStyleDropdown = !this.showStyleDropdown;
    }

    closeStyleDropdown() {
        this.showStyleDropdown = false;
    }

    selectStyleAction(action: 'enhance' | 'translate' | 'chooser') {
        this.closeStyleDropdown();

        if (action === 'enhance') {
            this.improvePrompt();
        } else if (action === 'translate') {
            this.translateStylePrompt();
        } else if (action === 'chooser') {
            this.openMusicStyleChooserModal();
        }
    }

    async translateStylePrompt() {
        const currentPrompt = this.songForm.get('prompt')?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error('Please enter a music style prompt first');
            return;
        }

        this.isTranslatingStylePrompt = true;
        try {
            const translatedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.translateMusicStylePrompt(currentPrompt),
                'Translating Style Prompt...',
                'AI is translating your music style description to English'
            );
            this.songForm.patchValue({prompt: this.removeQuotes(translatedPrompt)});
        } catch (error: any) {
            // Error notification is handled by error.interceptor
        } finally {
            this.isTranslatingStylePrompt = false;
        }
    }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: Event) {
        const target = event.target as HTMLElement;
        const lyricsDropdown = target.closest('.lyrics-dropdown-container');
        const styleDropdown = target.closest('.style-dropdown-container');
        const titleDropdown = target.closest('.title-dropdown-container');

        if (!lyricsDropdown && this.showLyricsDropdown) {
            this.closeLyricsDropdown();
        }

        if (!styleDropdown && this.showStyleDropdown) {
            this.closeStyleDropdown();
        }

        if (!titleDropdown && this.showTitleDropdown) {
            this.closeTitleDropdown();
        }
    }


    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, '').trim();
    }

    private updateValidators(isInstrumental: boolean) {
        const lyricsControl = this.songForm.get('lyrics');
        const titleControl = this.songForm.get('title');

        if (isInstrumental) {
            // For instrumental: lyrics not required, title is required
            lyricsControl?.clearValidators();
            titleControl?.setValidators([Validators.required, Validators.maxLength(50)]);
        } else {
            // For normal songs: lyrics required, title optional
            lyricsControl?.setValidators([Validators.required]);
            titleControl?.setValidators([Validators.maxLength(50)]);
        }

        lyricsControl?.updateValueAndValidity();
        titleControl?.updateValueAndValidity();
    }

    isInstrumental(): boolean {
        return this.songForm.get('isInstrumental')?.value || false;
    }

    setMode(mode: 'song' | 'instrumental') {
        const isInstrumental = mode === 'instrumental';
        this.songForm.patchValue({isInstrumental: isInstrumental});
    }

    async generateTitle() {
        const isInstrumental = this.isInstrumental();
        let inputText = '';

        // Priority logic: Title > Lyrics (non-instrumental) / Style (instrumental) > Fallback
        const currentTitle = this.songForm.get('title')?.value?.trim();
        const currentLyrics = this.songForm.get('lyrics')?.value?.trim();
        const currentStyle = this.songForm.get('prompt')?.value?.trim();

        if (currentTitle) {
            inputText = currentTitle;
        } else if (isInstrumental && currentStyle) {
            // For instrumental: use style prompt
            inputText = currentStyle;
        } else if (!isInstrumental && currentLyrics) {
            // For regular songs: use lyrics
            inputText = currentLyrics;
        } else {
            // Fallback constant
            inputText = 'Generate a creative song title';
        }

        this.isGeneratingTitle = true;
        try {
            const generatedTitle = await this.progressService.executeWithProgress(
                () => this.chatService.generateTitle(inputText),
                'Generating Title...',
                'AI is creating a song title for you'
            );
            this.songForm.patchValue({title: this.removeQuotes(generatedTitle)});
        } catch (error: any) {
            // Error notification is handled by error.interceptor
        } finally {
            this.isGeneratingTitle = false;
        }
    }

    toggleTitleDropdown() {
        this.showTitleDropdown = !this.showTitleDropdown;
    }

    closeTitleDropdown() {
        this.showTitleDropdown = false;
    }

    selectTitleAction(action: 'generate') {
        this.closeTitleDropdown();

        if (action === 'generate') {
            this.generateTitle();
        }
    }
}
