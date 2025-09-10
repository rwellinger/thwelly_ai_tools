import {Component, OnInit, ViewEncapsulation} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {SongService} from '../services/song.service';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';

@Component({
  selector: 'app-song-view',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent],
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
  choices: any[] = [];

  constructor(
    private fb: FormBuilder,
    private songService: SongService,
    private apiConfig: ApiConfigService
  ) {
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
      this.result = `Error loading tasks: ${error.message}`;
      console.error('Error loading task IDs:', error);
    }
  }

  async onSubmit() {
    const taskId = this.viewForm.get('taskSelect')?.value;
    if (!taskId) {
      console.error('No task ID selected.');
      return;
    }

    this.isLoading = true;
    this.loadingMessage = 'Fetching result…';
    this.result = '';

    try {
      const data = await this.songService.checkSongStatus(taskId);

      if (data.status === 'SUCCESS' && data.result) {
        this.renderResultTask(data.result);
      } else if (data.status === 'FAILED') {
        this.result = 'Job failed.';
        this.resultData = null;
        this.choices = [];
      } else {
        this.result = `Unknown status: ${data.status}`;
        this.resultData = null;
        this.choices = [];
      }
    } catch (error: any) {
      this.result = `Error: ${error.message}`;
      console.error('Fetch error:', error);
    } finally {
      this.isLoading = false;
    }
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

  async generateStem(mp3Url: string) {
    this.isLoading = true;
    this.loadingMessage = 'Generating stems...';

    try {
      const response = await fetch(this.apiConfig.endpoints.song.stems, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({url: mp3Url})
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.status === 'SUCCESS' && data.result && data.result.zip_url) {
        this.result += `
          <p><strong>Download Stems: </strong><a href="${data.result.zip_url}" target="_blank">Download</a></p>
        `;
      } else {
        this.result += '<p>Stem generation failed or incomplete.</p>';
      }
    } catch (error: any) {
      this.result += `<p>Error generating stem: ${error.message}</p>`;
      console.error('Error generating stem:', error);
    } finally {
      this.isLoading = false;
    }
  }
}
