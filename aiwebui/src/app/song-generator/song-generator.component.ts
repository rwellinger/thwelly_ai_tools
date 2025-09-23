import {Component, OnInit, ViewEncapsulation, inject, HostListener} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {SongService} from '../services/song.service';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {ChatService} from '../services/chat.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {PopupAudioPlayerComponent} from '../shared/popup-audio-player/popup-audio-player.component';
import {SongDetailPanelComponent} from '../shared/song-detail-panel/song-detail-panel.component';
import {ProgressOverlayComponent} from '../shared/progress-overlay/progress-overlay.component';
import {ProgressService} from '../services/progress.service';

@Component({
    selector: 'app-song-generator',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, PopupAudioPlayerComponent, SongDetailPanelComponent, ProgressOverlayComponent],
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
    showLyricsDropdown = false;
    showStyleDropdown = false;
    loadingMessage = '';
    result = '';
    currentlyPlaying: string | null = null;
    audioUrl: string | null = null;
    resultData: any = null;
    generatedSongData: any = null;
    choices: any[] = [];
    stemDownloadUrls = new Map<string, string>();
    showPopupPlayer = false;
    currentSongTitle = '';

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
            model: ['auto', Validators.required]
        });

        // Load saved form data
        const savedData = this.songService.loadFormData();
        if (savedData.lyrics) this.songForm.patchValue(savedData);

        // Save form data on changes
        this.songForm.valueChanges.subscribe(value => {
            this.songService.saveFormData(value);
        });
    }

    async onSubmit() {
        if (this.songForm.valid) {
            await this.generateSong();
        }
    }

    resetForm() {
        this.songForm.reset({model: 'auto'});
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
                formValue.model
            );

            if (data.task_id) {
                await this.checkSongStatus(data.task_id);
            } else {
                this.notificationService.error('Error initiating song generation.');
                this.result = 'Error initiating song generation.';
            }
        } catch (err: any) {
            this.notificationService.error(`Error: ${err.message}`);
            this.result = `Error: ${err.message}`;
        }
    }

    async checkSongStatus(taskId: string) {
        let completed = false;
        let interval = 5000;

        while (!completed) {
            try {
                const data = await this.songService.checkSongStatus(taskId);

                if (data.status === 'SUCCESS') {
                    this.renderResultTask(data.result);
                    completed = true;
                } else if (data.status === 'FAILURE') {
                    const errorMessage = data.result?.error || data.result || 'Song generation failed';
                    this.notificationService.error(`Song generation failed: ${errorMessage}`);
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

    renderResultTask(data: any): void {
        let result;

        if (data && data.result && data.result.choices) {
            result = data.result;
        } else if (data && data.choices) {
            result = data;
        } else {
            this.result = 'Not yet loaded...';
            this.resultData = null;
            this.choices = [];
            return;
        }

        if (!result.choices || !Array.isArray(result.choices)) {
            this.result = 'Not yet loaded...';
            this.resultData = null;
            this.choices = [];
            return;
        }
        this.resultData = {
            id: result.id,
            model: result.model,
            createdAt: result.created_at,
            finishedAt: result.finished_at,
            formattedDuration: this.formatDuration(result.finished_at - result.created_at),
            createdAtFormatted: new Date(result.finished_at * 1000).toUTCString()
        };

        this.choices = result.choices.map((choice: any) => ({
            ...choice,
            formattedDuration: this.formatDurationFromMs(choice.duration),
            stemDownloadUrl: this.stemDownloadUrls.get(choice.mp3_url || choice.url) || null
        }));

        // Create data object for shared component with field mapping for compatibility
        this.generatedSongData = {
            job_id: result.id,
            model: result.model,
            status: 'completed',
            created_at: new Date(result.created_at * 1000).toISOString(),
            completed_at: new Date(result.finished_at * 1000).toISOString(),
            lyrics: this.songForm.get('lyrics')?.value,
            prompt: this.songForm.get('prompt')?.value,
            choices: this.choices.map((choice: any) => ({
                ...choice,
                mp3_url: choice.url || choice.mp3_url,  // Map API field 'url' to expected 'mp3_url'
                flac_url: choice.flac_url,               // Keep existing flac_url
                stemDownloadUrl: choice.stemDownloadUrl  // Include stem download URL
            }))
        };

        this.result = '';
    }

    private formatDuration(durationSeconds: number): string {
        const totalSeconds = Math.floor(durationSeconds);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    private formatDurationFromMs(durationMs: number): string {
        const totalSeconds = Math.floor(durationMs / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
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

    async generateStem(mp3Url: string) {
        this.isLoading = true;
        this.loadingMessage = 'Generating stems...';

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
                // noinspection ExceptionCaughtLocallyJS
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.status === 'SUCCESS' && data.result && data.result.zip_url) {
                this.stemDownloadUrls.set(mp3Url, data.result.zip_url);
                this.updateChoicesWithStems();
            } else {
                this.notificationService.error('Stem generation failed or incomplete.');
                this.result += '<p>Stem generation failed or incomplete.</p>';
            }
        } catch (error: any) {
            this.notificationService.error(`Error generating stem: ${error.message}`);
            this.result += `<p>Error generating stem: ${error.message}</p>`;
        } finally {
            this.isLoading = false;
        }
    }

    // Handlers for shared song detail panel
    onTitleChanged(newTitle: string) {
        // For generated songs, we don't need to save titles to backend
        if (this.generatedSongData) {
            this.generatedSongData.title = newTitle;
        }
    }

    onTagsChanged(newTags: string[]) {
        // For generated songs, we don't need to save tags to backend
        if (this.generatedSongData) {
            this.generatedSongData.tags = newTags.join(', ');
        }
    }

    onDownloadFlac(url: string) {
        this.downloadFlac(url);
    }

    onPlayAudio(event: {url: string, id: string, choiceNumber: number}) {
        this.playAudio(event.url, event.id, event.choiceNumber);
    }

    onGenerateStem(url: string) {
        this.generateStem(url);
    }

    onDownloadStems(url: string) {
        this.downloadStems(url);
    }

    onCopyLyrics() {
        // Simple clipboard copy for generated songs
        if (this.generatedSongData?.lyrics) {
            navigator.clipboard.writeText(this.generatedSongData.lyrics);
        }
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

        if (!lyricsDropdown && this.showLyricsDropdown) {
            this.closeLyricsDropdown();
        }

        if (!styleDropdown && this.showStyleDropdown) {
            this.closeStyleDropdown();
        }
    }

    private updateChoicesWithStems() {
        // Update choices with stem download URLs
        this.choices = this.choices.map(choice => ({
            ...choice,
            stemDownloadUrl: this.stemDownloadUrls.get(choice.mp3_url || choice.url) || null
        }));

        // Update generatedSongData for the shared component
        if (this.generatedSongData) {
            this.generatedSongData.choices = this.choices.map((choice: any) => ({
                ...choice,
                mp3_url: choice.url || choice.mp3_url,
                flac_url: choice.flac_url,
                stemDownloadUrl: choice.stemDownloadUrl
            }));
        }
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, '').trim();
    }
}
