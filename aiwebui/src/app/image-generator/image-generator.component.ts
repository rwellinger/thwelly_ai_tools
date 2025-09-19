import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { ApiConfigService } from '../services/api-config.service';
import { NotificationService } from '../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import {MatIcon} from "@angular/material/icon";
import {ImageDetailPanelComponent} from '../shared/image-detail-panel/image-detail-panel.component';

@Component({
  selector: 'app-image-generator',
  standalone: true,
    imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, MatIcon, ImageDetailPanelComponent],
  templateUrl: './image-generator.component.html',
  styleUrl: './image-generator.component.scss'
})
export class ImageGeneratorComponent implements OnInit {
  promptForm!: FormGroup;
  isLoading = false;
  result = '';
  generatedImageUrl = '';
  showImageModal = false;
  generatedImageData: any = null;

  private fb = inject(FormBuilder);
  private apiConfig = inject(ApiConfigService);
  private notificationService = inject(NotificationService);

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
          // Create data object for shared component
          this.generatedImageData = {
            url: data.url,
            prompt: formValue.prompt,
            size: formValue.size,
            model_used: 'DALL-E 3',
            created_at: new Date().toISOString()
          };
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

  // Handlers for shared image detail panel
  onTitleChanged(newTitle: string) {
    // For generated images, we don't need to save titles to backend
    // but we can update the local data if needed
    if (this.generatedImageData) {
      this.generatedImageData.title = newTitle;
    }
  }

  onDownloadImage() {
    this.downloadImage();
  }

  onPreviewImage() {
    this.openImageModal();
  }
}
