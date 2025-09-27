import {Component, OnInit, ViewEncapsulation, inject, HostListener, ViewChild} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {SongService} from '../../services/song.service';
import {HeaderComponent} from '../../shared/header/header.component';
import {FooterComponent} from '../../shared/footer/footer.component';
import {ApiConfigService} from '../../services/api-config.service';
import {NotificationService} from '../../services/notification.service';
import {ChatService} from '../../services/chat.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatCardModule} from '@angular/material/card';
import {PopupAudioPlayerComponent} from '../../shared/popup-audio-player/popup-audio-player.component';
import {SongDetailPanelComponent} from '../../shared/song-detail-panel/song-detail-panel.component';
import {ProgressOverlayComponent} from '../../shared/progress-overlay/progress-overlay.component';
import {ProgressService} from '../../services/progress.service';

@Component({
    selector: 'app-song-generator',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, MatCardModule, PopupAudioPlayerComponent, SongDetailPanelComponent, ProgressOverlayComponent],
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
    audioUrl: string | null = null;
    showPopupPlayer = false;
    currentSongTitle = '';
    currentSongId: string | null = null;

    @ViewChild(SongDetailPanelComponent) songDetailPanel!: SongDetailPanelComponent;

    private fb = inject(FormBuilder);
    private songService = inject(SongService);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);

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
                    console.log('Song ID stored:', this.currentSongId);
                }
                await this.checkSongStatus(data.task_id, false);
            } else {
                this.notificationService.error('Error initiating song generation.');
                this.result = 'Error initiating song generation.';
            }
        } catch (err: any) {
            this.notificationService.error(`Error: ${err.message}`);
            this.result = `Error: ${err.message}`;
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
                    console.log('Instrumental ID stored:', this.currentSongId);
                }
                await this.checkSongStatus(data.task_id, true);
            } else {
                this.notificationService.error('Error initiating instrumental generation.');
                this.result = 'Error initiating instrumental generation.';
            }
        } catch (err: any) {
            this.notificationService.error(`Error: ${err.message}`);
            this.result = `Error: ${err.message}`;
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
                this.notificationService.error(`Error fetching status: ${error.message}`);
                this.result = `Error fetching status: ${error.message}`;
                completed = true;
            }
        }

        this.isLoading = false;
    }

    async renderResultTask(data: any): Promise<void> {
        console.log('=== renderResultTask called ===');
        console.log('data:', data);
        console.log('currentSongId:', this.currentSongId);

        // Only use DB loading - no more MUREKA result fallback
        if (this.currentSongId && (data.status === 'SUCCESS' || data.status === 'succeeded')) {
            console.log('Song generated successfully, refreshing detail panel');
            this.result = '';
            // Einfach das Detail Panel refreshen - Daten sind bereits in DB
            if (this.songDetailPanel) {
                console.log('Calling reloadSong with songId:', this.currentSongId);
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
        // Bei PROGRESS oder anderen Status einfach nichts machen
    }



    playAudio(mp3Url: string, songId: string, choiceNumber?: number) {
        if (this.currentlyPlaying === songId) {
            this.stopAudio();
        } else {
            this.audioUrl = mp3Url;
            this.currentlyPlaying = songId;
            this.currentSongTitle = `Generated Song (Choice ${choiceNumber || 'Unknown'})`;
            this.showPopupPlayer = true;
        }
    }

    stopAudio() {
        this.audioUrl = null;
        this.currentlyPlaying = null;
        this.showPopupPlayer = false;
        this.currentSongTitle = '';
    }

    onAudioLoadError(error: {code: number, message: string}) {
        console.log('Audio load error handled:', error);
        this.notificationService.error(`Audio Error: ${error.message}`);
        this.stopAudio(); // Close the player when error occurs
    }

    onPopupPlayerClose() {
        this.stopAudio();
    }

    onPopupPlayerEnded() {
        this.stopAudio();
    }

    onCanPlayThrough() {
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

    onPlayAudio(event: {url: string, id: string, choiceNumber: number}) {
        this.playAudio(event.url, event.id, event.choiceNumber);
    }


    onDownloadStems(url: string) {
        this.downloadStems(url);
    }

    onCopyLyrics() {
        // No-op: Shared component handles this
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
            this.notificationService.error(`Error improving prompt: ${error.message}`);
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
            this.notificationService.error(`Error generating lyrics: ${error.message}`);
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
            this.notificationService.error(`Error translating lyrics: ${error.message}`);
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

    selectLyricsAction(action: 'generate' | 'translate') {
        this.closeLyricsDropdown();

        if (action === 'generate') {
            this.generateLyrics();
        } else if (action === 'translate') {
            this.translateLyrics();
        }
    }

    toggleStyleDropdown() {
        this.showStyleDropdown = !this.showStyleDropdown;
    }

    closeStyleDropdown() {
        this.showStyleDropdown = false;
    }

    selectStyleAction(action: 'enhance' | 'translate') {
        this.closeStyleDropdown();

        if (action === 'enhance') {
            this.improvePrompt();
        } else if (action === 'translate') {
            this.translateStylePrompt();
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
            this.notificationService.error(`Error translating style prompt: ${error.message}`);
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
            this.notificationService.error(`Error generating title: ${error.message}`);
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
