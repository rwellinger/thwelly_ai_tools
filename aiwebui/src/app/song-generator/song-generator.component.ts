import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { SongService } from '../services/song.service';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';

@Component({
  selector: 'app-song-generator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent],
  templateUrl: './song-generator.component.html',
  styleUrl: './song-generator.component.css'
})
export class SongGeneratorComponent implements OnInit {
  songForm!: FormGroup;
  isLoading = false;
  loadingMessage = '';
  result = '';

  constructor(
    private fb: FormBuilder,
    private songService: SongService
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
          const resultData = data.result.result;
          const id = resultData.id;
          const modelUsed = resultData.model;

          const infoHtml = `
            <div class="info-box">
                <strong>ID:</strong> ${id}<br>
                <strong>Model used:</strong> ${modelUsed}
            </div>
            <table class="result-table">
                <thead>
                    <tr>
                        <th>Song Id</th>
                        <th>Duration</th>
                        <th>FLAC File</th>
                        <th>MP3 File</th>
                    </tr>
                </thead>
                <tbody>
                    ${resultData.choices.map((choice: any) => {
                      const song_id = choice.id;
                      const durationMilliseconds = choice.duration;
                      const totalSeconds = Math.floor(durationMilliseconds / 1000);
                      const minutes = Math.floor(totalSeconds / 60);
                      const seconds = totalSeconds % 60;
                      const formattedMinutes = String(minutes).padStart(2, '0');
                      const formattedSeconds = String(seconds).padStart(2, '0');
                      const flacFilename = choice.flac_url.split('/').pop();
                      const mp3Filename = choice.url.split('/').pop();
                      
                      return `
                        <tr>
                            <td>${song_id}</td>
                            <td>${formattedMinutes}:${formattedSeconds}</td>
                            <td><a href="${choice.flac_url}">${flacFilename}</a></td>
                            <td><a href="${choice.url}">${mp3Filename}</a></td>
                        </tr>
                      `;
                    }).join('')}
                </tbody>
            </table>
          `;
          
          this.result = infoHtml;
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
}
