import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { HeaderComponent } from '../shared/header/header.component';
import { FooterComponent } from '../shared/footer/footer.component';
import { ApiConfigService } from '../services/api-config.service';

@Component({
  selector: 'app-image-generator',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent],
  templateUrl: './image-generator.component.html',
  styleUrl: './image-generator.component.css'
})
export class ImageGeneratorComponent implements OnInit {
  promptForm!: FormGroup;
  isLoading = false;
  result = '';

  constructor(
    private fb: FormBuilder,
    private apiConfig: ApiConfigService
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
          this.result = `<img src="${data.url}" alt="Generated Image" style="max-width: 100%; height: auto;">`;
        } else {
          this.result = 'Error generating image.';
        }
      } catch (error: any) {
        this.result = `Error: ${error.message}`;
      } finally {
        this.isLoading = false;
      }
    }
  }
}
