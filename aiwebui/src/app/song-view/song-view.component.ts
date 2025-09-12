import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {SongService} from '../services/song.service';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-song-view',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule],
  templateUrl: './song-view.component.html',
  styleUrl: './song-view.component.css',
  encapsulation: ViewEncapsulation.None
})
export class SongViewComponent implements OnInit {
  viewForm!: FormGroup;
  tasks: any[] = [];
  isLoading = false;
  loadingMessage = '';
  result = '';
  resultData: any = null;
  successMessage = '';
  choices: any[] = [];
  stemDownloadUrl: string | null = null;
  currentlyPlaying: string | null = null;
  audioUrl: string | null = null;

  constructor(
    private fb: FormBuilder,
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
    this.viewForm = this.fb.group({
      taskSelect: ['']
    });

    this.loadTasks();
  }

  async loadTasks() {
    try {
      const response = await this.songService.fetchWithTimeout(this.apiConfig.endpoints.redis.keys);
      const data = await response.json();
      this.tasks = data.tasks || [];
    } catch (error: any) {
      this.notificationService.error(`Error loading tasks: ${error.message}`);
      this.result = `Error loading tasks: ${error.message}`;
    }
  }

  async onSubmit() {
    const taskId = this.viewForm.get('taskSelect')?.value;
    if (!taskId) {
      this.notificationService.error('No task ID selected.');
      return;
    }

    this.isLoading = true;
    this.loadingMessage = 'Fetching result…';
    this.result = '';
    this.stemDownloadUrl = null;
    this.notificationService.loading('Fetching result...');

    try {
      const data = await this.songService.checkSongStatus(taskId);

      if (data.status === 'SUCCESS') {
        this.renderResultTask(data.result || data);
        this.notificationService.success('Task result loaded successfully!');
      } else if (data.status === 'FAILURE' || data.status === 'FAILED') {
        const errorMessage = data.error || 'Job failed.';
        this.notificationService.error(`Job failed: ${errorMessage}`);
        this.result = `Job failed: ${errorMessage}`;
        this.resultData = null;
        this.choices = [];
      } else {
        this.notificationService.error(`Error Status: ${data.status}`);
        this.result = `Error Status: ${data.status}`;
        this.resultData = null;
        this.choices = [];
      }
    } catch (error: any) {
      this.notificationService.error(`ExError: ${error.message}`);
      this.result = `ExError: ${error.message}`;
    } finally {
      this.isLoading = false;
    }
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
        this.result += '<p>Stem generation failed or incomplete.</p>';
      }
    } catch (error: any) {
      this.stemDownloadUrl = null;
      this.notificationService.error(`Error generating stem: ${error.message}`);
      this.result += `<p>Error generating stem: ${error.message}</p>`;
    } finally {
      this.isLoading = false;
    }
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
    this.notificationService.info('Audio is ready to play');
  }

  async deleteTask() {
    const taskId = this.viewForm.get('taskSelect')?.value;
    if (!taskId) {
      this.notificationService.error('No task ID selected.');
      return;
    }

    this.isLoading = true;
    this.loadingMessage = 'Deleting task...';
    this.successMessage = '';
    this.notificationService.loading('Deleting task...');

    try {
      const response = await fetch(this.apiConfig.endpoints.redis.deleteTask(taskId), {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'}
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'SUCCESS') {
        this.notificationService.success('Task successfully deleted!');
        this.successMessage = 'Task successfully deleted!';
        this.viewForm.get('taskSelect')?.setValue('');
        this.result = '';
        this.resultData = null;
        this.choices = [];
        await this.loadTasks();
        
        setTimeout(() => {
          this.successMessage = '';
        }, 3000);
      } else {
        this.notificationService.error(`Delete failed: ${data.status}`);
        this.result = `Delete failed: ${data.status}`;
      }
    } catch (error: any) {
      this.notificationService.error(`Error deleting task: ${error.message}`);
      this.result = `Error deleting task: ${error.message}`;
    } finally {
      this.isLoading = false;
    }
  }
}
