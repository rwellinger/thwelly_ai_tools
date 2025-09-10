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
        this.result = this.renderResultTask(data.result);
      } else if (data.status === 'FAILED') {
        this.result = 'Job failed.';
      } else {
        this.result = `Unknown status: ${data.status}`;
      }
    } catch (error: any) {
      this.result = `Error: ${error.message}`;
      console.error('Fetch error:', error);
    } finally {
      this.isLoading = false;
    }
  }

  renderResultTask(data: any): string {
    if (!data || !data.result || !data.result.choices || !Array.isArray(data.result.choices)) {
      return '<p>Not yet loaded...</p>';
    }

    const result = data.result;
    const id = result.id;
    const modelUsed = result.model;
    const createdAt = result.created_at;
    const finishedAt = result.finished_at;
    const createdAtMs = createdAt * 1000;
    const finishedAtMs = finishedAt * 1000;
    const durationMs = finishedAtMs - createdAtMs;
    const totalSeconds = Math.floor(durationMs / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    const formattedDuration = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

    const infoHtml = `
      <div class="info-box">
          <p><strong>ID:</strong> ${id}</p>
          <p><strong>Model used:</strong> ${modelUsed}</p>
          <p><strong>Created:</strong> ${new Date(finishedAtMs).toUTCString()}</p>
          <p><strong>Duration:</strong> ${formattedDuration} Minutes</p>
      </div>
    `;

    const tableRows = result.choices.map((choice: any) => {
      const song_id = choice.id;
      const durationMs = choice.duration;
      const totalSeconds = Math.floor(durationMs / 1000);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      const formattedMinutes = String(minutes).padStart(2, '0');
      const formattedSeconds = String(seconds).padStart(2, '0');

      return `
        <tr>
            <td>${song_id}</td>
            <td>${formattedMinutes}:${formattedSeconds}</td>
            <td><a href="${choice.flac_url}">FLAC-Download</a></td>
            <td><a href="${choice.url}">MP3-Download</a></td>
            <td><button type="button" style="background-color: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px;"
                onclick="window.angularComponentRef.generateStem('${choice.url}')">Generate</button></td>
        </tr>
      `;
    }).join('');

    return `
      ${infoHtml}
      <table class="result-table">
          <thead>
              <tr>
                  <th>Song Id</th>
                  <th>Duration</th>
                  <th>FLAC File</th>
                  <th>MP3 File</th>
                  <th>Stem</th>
              </tr>
          </thead>
          <tbody>
              ${tableRows}
          </tbody>
      </table>
    `;
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
