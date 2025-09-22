import {Component, OnInit, inject, HostListener} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {HeaderComponent} from '../shared/header/header.component';
import {FooterComponent} from '../shared/footer/footer.component';
import {ApiConfigService} from '../services/api-config.service';
import {NotificationService} from '../services/notification.service';
import {ImageService} from '../services/image.service';
import {ChatService} from '../services/chat.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {ImageDetailPanelComponent} from '../shared/image-detail-panel/image-detail-panel.component';

@Component({
    selector: 'app-image-generator',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, HeaderComponent, FooterComponent, MatSnackBarModule, ImageDetailPanelComponent],
    templateUrl: './image-generator.component.html',
    styleUrl: './image-generator.component.scss'
})
export class ImageGeneratorComponent implements OnInit {
    promptForm!: FormGroup;
    isLoading = false;
    isImprovingPrompt = false;
    showPromptDropdown = false;
    result = '';
    generatedImageUrl = '';
    showImageModal = false;
    generatedImageData: any = null;

    private fb = inject(FormBuilder);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private imageService = inject(ImageService);
    private chatService = inject(ChatService);

    ngOnInit() {
        this.promptForm = this.fb.group({
            prompt: ['', Validators.required],
            size: ['1024x1024', Validators.required]
        });

        // Load saved form data
        const savedData = this.imageService.loadFormData();
        if (savedData.prompt) this.promptForm.patchValue(savedData);

        // Save form data on changes
        this.promptForm.valueChanges.subscribe(value => {
            this.imageService.saveFormData(value);
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
                    headers: {'Content-Type': 'application/json'},
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
        // But we can update the local data if needed
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

    async improvePrompt() {
        const currentPrompt = this.promptForm.get('prompt')?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error('Please enter a prompt first');
            return;
        }

        this.isImprovingPrompt = true;
        try {
            const improvedPrompt = await this.chatService.improveImagePrompt(currentPrompt);
            this.promptForm.patchValue({prompt: improvedPrompt});
        } catch (error: any) {
            this.notificationService.error(`Error improving prompt: ${error.message}`);
        } finally {
            this.isImprovingPrompt = false;
        }
    }

    togglePromptDropdown() {
        this.showPromptDropdown = !this.showPromptDropdown;
    }

    closePromptDropdown() {
        this.showPromptDropdown = false;
    }

    selectPromptAction(action: 'enhance') {
        this.closePromptDropdown();

        if (action === 'enhance') {
            this.improvePrompt();
        }
    }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: Event) {
        const target = event.target as HTMLElement;
        const dropdown = target.closest('.prompt-dropdown-container');

        if (!dropdown && this.showPromptDropdown) {
            this.closePromptDropdown();
        }
    }

    resetForm() {
        this.promptForm.reset({size: '1024x1024'});
        this.imageService.clearFormData();
        this.generatedImageUrl = '';
        this.generatedImageData = null;
    }
}
