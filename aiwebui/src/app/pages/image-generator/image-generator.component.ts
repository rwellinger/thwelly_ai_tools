import {Component, OnInit, inject, HostListener} from '@angular/core';
import {FormBuilder, FormGroup, ReactiveFormsModule, Validators} from '@angular/forms';
import {CommonModule} from '@angular/common';
import {HttpClient} from '@angular/common/http';
import {firstValueFrom} from 'rxjs';
import {ImageBlobService} from '../../services/ui/image-blob.service';
import {ApiConfigService} from '../../services/config/api-config.service';
import {NotificationService} from '../../services/ui/notification.service';
import {ImageService} from '../../services/business/image.service';
import {ChatService} from '../../services/config/chat.service';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {MatCardModule} from '@angular/material/card';
import {MatButtonModule} from '@angular/material/button';
import {ImageDetailPanelComponent} from '../../components/image-detail-panel/image-detail-panel.component';
import {ProgressService} from '../../services/ui/progress.service';

@Component({
    selector: 'app-image-generator',
    standalone: true,
    imports: [CommonModule, ReactiveFormsModule, MatSnackBarModule, MatCardModule, MatButtonModule, ImageDetailPanelComponent],
    templateUrl: './image-generator.component.html',
    styleUrl: './image-generator.component.scss'
})
export class ImageGeneratorComponent implements OnInit {
    promptForm!: FormGroup;
    isLoading = false;
    isImprovingPrompt = false;
    isTranslatingPrompt = false;
    showPromptDropdown = false;
    isGeneratingTitle = false;
    showTitleDropdown = false;
    result = '';
    generatedImageUrl = '';
    generatedImageBlobUrl = '';
    showImageModal = false;
    generatedImageId: string | null = null;
    generatedImageData: any = null;

    private fb = inject(FormBuilder);
    private http = inject(HttpClient);
    private apiConfig = inject(ApiConfigService);
    private notificationService = inject(NotificationService);
    private imageService = inject(ImageService);
    private chatService = inject(ChatService);
    private progressService = inject(ProgressService);
    private imageBlobService = inject(ImageBlobService);

    ngOnInit() {
        this.promptForm = this.fb.group({
            title: [''],
            prompt: ['', Validators.required],
            size: ['1024x1024', Validators.required]
        });

        // Load saved form data
        const savedData = this.imageService.loadFormData();
        if (savedData.prompt || savedData['title']) this.promptForm.patchValue(savedData);

        // Save form data on changes
        this.promptForm.valueChanges.subscribe(value => {
            this.imageService.saveFormData(value);
        });
    }

    async onSubmit() {
        console.error('DEBUG: Form submitted');
        console.error('DEBUG: Form valid?', this.promptForm.valid);
        console.error('DEBUG: Form errors:', this.promptForm.errors);
        if (this.promptForm.valid) {
            console.error('DEBUG: Form is valid');
            this.isLoading = true;
            this.result = '';

            try {
                const formValue = this.promptForm.value;
                console.error('DEBUG: Form values:', formValue);
                console.error('DEBUG: API URL:', this.apiConfig.endpoints.image.generate);
                console.error('DEBUG: Request payload:', {
                    title: formValue.title?.trim() || null,
                    prompt: formValue.prompt,
                    size: formValue.size
                });

                console.error('DEBUG: Starting API call...');
                const data = await firstValueFrom(
                    this.http.post<any>(this.apiConfig.endpoints.image.generate, {
                        title: formValue.title?.trim() || null,
                        prompt: formValue.prompt,
                        size: formValue.size
                    })
                );
                console.error('DEBUG: API call completed:', data);

                if (data.url) {
                    // Store the generated image URL and ID
                    console.error('DEBUG: Image generated:', data);
                    console.error('DEBUG: Image URL:', data.url);
                    console.error('DEBUG: Image ID:', data.id);
                    this.generatedImageUrl = data.url || '';
                    this.generatedImageId = data.id || null;

                    // Create image object for direct display
                    this.generatedImageData = {
                        id: data.id || null,
                        url: data.url,
                        prompt: formValue.prompt,
                        title: formValue.title?.trim() || null,
                        size: formValue.size,
                        model_used: 'DALL-E 3',
                        created_at: new Date().toISOString()
                    };

                    // Load blob URL for modal display
                    if (data.url) {
                        this.imageBlobService.getImageBlobUrl(data.url).subscribe({
                            next: (blobUrl) => {
                                this.generatedImageBlobUrl = blobUrl;
                            },
                            error: (error) => {
                                console.error('Failed to load image blob:', error);
                                this.generatedImageBlobUrl = '';
                            }
                        });
                    }
                } else {
                    this.notificationService.error('Error generating image.');
                }
            } catch (error: any) {
                console.error('DEBUG: Image generation failed:', error);
                console.error('DEBUG: Error message:', error.message);
                console.error('DEBUG: Full error object:', error);
                this.notificationService.error(`Error: ${error.message}`);
            } finally {
                this.isLoading = false;
            }
        } else {
            console.error('DEBUG: Form is INVALID');
            console.error('DEBUG: Form value:', this.promptForm.value);
            console.error('DEBUG: All form errors:');
            Object.keys(this.promptForm.controls).forEach(key => {
                const control = this.promptForm.get(key);
                if (control && control.errors) {
                    console.error(`DEBUG: ${key} errors:`, control.errors);
                }
            });
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
    onTitleChanged() {
        // Title changes are handled by the detail panel component
        // No action needed here as the component handles its own DB updates
    }

    onDownloadImage() {
        if (this.generatedImageData?.url) {
            // Use authenticated download via ImageBlobService
            const filename = this.getImageFilename();
            this.imageBlobService.downloadImage(this.generatedImageData.url, filename);
        }
    }

    private getImageFilename(): string {
        const title = this.generatedImageData?.title || this.generatedImageData?.prompt || 'image';
        const sanitized = title.replace(/[^a-zA-Z0-9]/g, '_').substring(0, 50);
        return `${sanitized}.png`;
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
            const improvedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.improveImagePrompt(currentPrompt),
                'Enhancing Prompt...',
                'AI is improving your image prompt'
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(improvedPrompt)});
        } catch (error: any) {
            this.notificationService.error(`Error improving prompt: ${error.message}`);
        } finally {
            this.isImprovingPrompt = false;
        }
    }

    async translatePrompt() {
        const currentPrompt = this.promptForm.get('prompt')?.value?.trim();
        if (!currentPrompt) {
            this.notificationService.error('Please enter a prompt first');
            return;
        }

        this.isTranslatingPrompt = true;
        try {
            const translatedPrompt = await this.progressService.executeWithProgress(
                () => this.chatService.translateImagePrompt(currentPrompt),
                'Translating Prompt...',
                'AI is translating your image prompt to English'
            );
            this.promptForm.patchValue({prompt: this.removeQuotes(translatedPrompt)});
        } catch (error: any) {
            this.notificationService.error(`Error translating prompt: ${error.message}`);
        } finally {
            this.isTranslatingPrompt = false;
        }
    }

    togglePromptDropdown() {
        this.showPromptDropdown = !this.showPromptDropdown;
    }

    closePromptDropdown() {
        this.showPromptDropdown = false;
    }

    selectPromptAction(action: 'enhance' | 'translate') {
        this.closePromptDropdown();

        if (action === 'enhance') {
            this.improvePrompt();
        } else if (action === 'translate') {
            this.translatePrompt();
        }
    }

    // Title generation methods
    async generateTitle() {
        // Determine input text based on priority: title > prompt > default
        let inputText = this.promptForm.get('title')?.value?.trim();
        if (!inputText) {
            inputText = this.promptForm.get('prompt')?.value?.trim();
        }
        if (!inputText) {
            inputText = 'image';
        }

        this.isGeneratingTitle = true;
        try {
            const generatedTitle = await this.progressService.executeWithProgress(
                () => this.chatService.generateTitle(inputText),
                'Generating Title...',
                'AI is creating a title for your image'
            );
            this.promptForm.patchValue({title: this.removeQuotes(generatedTitle)});
        } catch (error: any) {
            this.notificationService.error(`Error generating title: ${error.message}`);
        } finally {
            this.isGeneratingTitle = false;
        }
    }

    toggleTitleDropdown() {
        this.showTitleDropdown = !this.showTitleDropdown;
    }

    closeTitleDropdown() {
        this.showTitleDropdown = false;
    }

    selectTitleAction(action: 'generate') {
        this.closeTitleDropdown();

        if (action === 'generate') {
            this.generateTitle();
        }
    }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: Event) {
        const target = event.target as HTMLElement;
        const promptDropdown = target.closest('.prompt-dropdown-container');
        const titleDropdown = target.closest('.title-dropdown-container');

        if (!promptDropdown && this.showPromptDropdown) {
            this.closePromptDropdown();
        }
        if (!titleDropdown && this.showTitleDropdown) {
            this.closeTitleDropdown();
        }
    }

    resetForm() {
        this.promptForm.reset({size: '1024x1024', title: ''});
        this.imageService.clearFormData();
        this.generatedImageUrl = '';
        this.generatedImageBlobUrl = '';
        this.generatedImageId = null;
        this.generatedImageData = null;
    }

    private removeQuotes(text: string): string {
        if (!text) return text;
        return text.replace(/^["']|["']$/g, '').trim();
    }
}
