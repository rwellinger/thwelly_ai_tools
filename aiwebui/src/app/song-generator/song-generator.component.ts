import { Component, OnInit, ViewEncapsulation } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SongService } from '../services/song.service';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { ApiConfigService } from '../services/api-config.service';

@Component({
  selector: 'app-song-generator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent],
  templateUrl: './song-generator.component.html',
  styleUrl: './song-generator.component.css',
  encapsulation: ViewEncapsulation.None
})
export class SongGeneratorComponent implements OnInit {
  songForm!: FormGroup;
  isLoading = false;
  loadingMessage = '';
  result = '';
  currentlyPlaying: string | null = null;
  audioUrl: string | null = null;
  resultData: any = null;
  choices: any[] = [];
  stemDownloadUrl: string | null = null;

  constructor(
    private fb: FormBuilder,
    private songService: SongService,
    private apiConfig: ApiConfigService
  ) {}

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
    this.songForm.reset({ model: 'auto' });
    this.songService.clearFormData();
    this.result = '';
  }

  async generateSong() {
    const formValue = this.songForm.value;
    this.isLoading = true;
    this.loadingMessage = 'Starting song generation...';
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
        this.result = 'Error initiating song generation.';
      }
    } catch (err: any) {
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
          this.result = `<div class="error-box">Error: ${errorMessage}</div>`;
          completed = true;
        } else {
          const murekaStatus = data.progress?.mureka_status || "Initialize";
          this.loadingMessage = `Processing (${murekaStatus}) ... Please wait until finished.`;
          interval = Math.min(interval * 1.5, 60000);
          await new Promise(resolve => setTimeout(resolve, interval));
        }
      } catch (error: any) {
        this.result = `Error fetching status: ${error.message}`;
        completed = true;
      }
    }
    
    this.isLoading = false;
  }

  renderResultTask(data: any): void {
    if (!data || !data.result || !data.result.choices || !Array.isArray(data.result.choices)) {
      this.result = 'Not yet loaded...';
      this.resultData = null;
      this.choices = [];
      return;
    }

    const result = data.result;
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
      formattedDuration: this.formatDurationFromMs(choice.duration)
    }));

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

  playAudio(mp3Url: string, songId: string) {
    if (this.currentlyPlaying === songId) {
      this.stopAudio();
    } else {
      this.audioUrl = mp3Url;
      this.currentlyPlaying = songId;
    }
  }

  stopAudio() {
    this.audioUrl = null;
    this.currentlyPlaying = null;
  }

  onCanPlayThrough() {
    console.log('Audio is ready to play');
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
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
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'SUCCESS' && data.result && data.result.zip_url) {
        this.stemDownloadUrl = data.result.zip_url;
      } else {
        this.stemDownloadUrl = null;
        this.result += '<p>Stem generation failed or incomplete.</p>';
      }
    } catch (error: any) {
      this.stemDownloadUrl = null;
      this.result += `<p>Error generating stem: ${error.message}</p>`;
      console.error('Error generating stem:', error);
    } finally {
      this.isLoading = false;
    }
  }
}
