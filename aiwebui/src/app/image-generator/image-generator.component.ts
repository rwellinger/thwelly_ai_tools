import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { ApiConfigService } from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-image-generator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule],
  templateUrl: './image-generator.component.html',
  styleUrl: './image-generator.component.css'
})
export class ImageGeneratorComponent implements OnInit {
  promptForm!: FormGroup;
  isLoading = false;
  result = '';
  generatedImageUrl = '';
  showImageModal = false;

  constructor(
    private fb: FormBuilder,
    private apiConfig: ApiConfigService,
    private notificationService: NotificationService
  ) {}

  ngOnInit() {
    this.promptForm = this.fb.group({
      prompt: ['', Validators.required],
      size: ['1024x1024', Validators.required]
    });
  }

  async onSubmit() {
    if (this.promptForm.valid) {
      this.isLoading = true;
      this.result = '';
      this.notificationService.loading('Generating image...');

      try {
        const formValue = this.promptForm.value;
        const response = await fetch(this.apiConfig.endpoints.image.generate, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: formValue.prompt,
            size: formValue.size
          })
        });

        const data = await response.json();

        if (data.url) {
          this.generatedImageUrl = data.url;
          this.notificationService.success('Image generated successfully!');
        } else {
          this.notificationService.error('Error generating image.');
        }
      } catch (error: any) {
        this.notificationService.error(`Error: ${error.message}`);
      } finally {
        this.isLoading = false;
      }
    }
  }

  downloadImage() {
    if (this.generatedImageUrl) {
      const link = document.createElement('a');
      link.href = this.generatedImageUrl;
      link.target = '_blank';
      link.download = `generated-image-${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  }

  openImageModal() {
    this.showImageModal = true;
  }

  closeImageModal() {
    this.showImageModal = false;
  }
}
