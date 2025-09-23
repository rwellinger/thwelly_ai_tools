import { Component, OnInit, OnDestroy, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subject, debounceTime, distinctUntilChanged, takeUntil } from 'rxjs';
import { PromptTemplate, PromptTemplateUpdate } from '../../models/prompt-template.model';
import { PromptTemplateService } from '../../services/prompt-template.service';
import { NotificationService } from '../../services/notification.service';
import { MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-prompt-templates',
  standalone: true,
  imports: [CommonModule, FormsModule, MatSnackBarModule],
  templateUrl: './prompt-templates.component.html',
  styleUrl: './prompt-templates.component.scss'
})
export class PromptTemplatesComponent implements OnInit, OnDestroy {
  // Template data
  templates: PromptTemplate[] = [];
  filteredTemplates: PromptTemplate[] = [];
  selectedTemplate: PromptTemplate | null = null;

  // UI state
  isLoading = false;
  loadingMessage = '';

  // Search functionality
  searchTerm: string = '';
  private searchSubject = new Subject<string>();
  private destroy$ = new Subject<void>();

  // Editing state
  editingTemplate: PromptTemplate | null = null;
  editForm = {
    pre_condition: '',
    post_condition: '',
    description: '',
    model: '',
    temperature: null as number | null,
    max_tokens: null as number | null
  };

  // Available models
  availableModels = [
    { value: 'llama3.2:3b', label: 'Llama 3.2 3B' },
    { value: 'gpt-oss:20b', label: 'GPT-OSS 20B' },
    { value: 'deepseek-r1:8b', label: 'DeepSeek R1 8B' },
    { value: 'gemma3:4b', label: 'Gemma 3 4B' }
  ];

  // Temperature options (0.0 to 2.0 in 0.1 steps)
  temperatureOptions = Array.from({length: 21}, (_, i) => {
    const value = (i * 0.1);
    return { value: Math.round(value * 10) / 10, label: value.toFixed(1) };
  });

  @ViewChild('searchInput') searchInput!: ElementRef;
  @ViewChild('preConditionTextarea') preConditionTextarea!: ElementRef;

  private promptService = inject(PromptTemplateService);
  private notificationService = inject(NotificationService);

  constructor() {
    // Setup search debouncing
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(searchTerm => {
      this.searchTerm = searchTerm;
      this.applyFilter();
      // Maintain focus on search input
      if (document.activeElement === this.searchInput?.nativeElement) {
        setTimeout(() => this.searchInput.nativeElement.focus(), 0);
      }
    });
  }

  ngOnInit(): void {
    this.loadTemplates();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  async loadTemplates(): Promise<void> {
    this.isLoading = true;
    this.loadingMessage = 'Loading prompt templates...';

    try {
      this.templates = await this.promptService.getAllTemplates().toPromise() || [];
      this.applyFilter();

      // Auto-select first template if available and none selected
      if (this.filteredTemplates.length > 0 && !this.selectedTemplate) {
        this.selectTemplate(this.filteredTemplates[0]);
      }
    } catch (error: any) {
      this.notificationService.error(`Error loading templates: ${error.message}`);
      this.templates = [];
      this.filteredTemplates = [];
    } finally {
      this.isLoading = false;
    }
  }

  applyFilter(): void {
    if (!this.searchTerm.trim()) {
      this.filteredTemplates = [...this.templates];
    } else {
      const term = this.searchTerm.toLowerCase();
      this.filteredTemplates = this.templates.filter(template =>
        template.category.toLowerCase().includes(term) ||
        template.action.toLowerCase().includes(term) ||
        template.description?.toLowerCase().includes(term) ||
        template.pre_condition.toLowerCase().includes(term) ||
        template.post_condition.toLowerCase().includes(term)
      );
    }
  }

  onSearchChange(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.searchSubject.next(value);
  }

  clearSearch(): void {
    this.searchTerm = '';
    this.searchSubject.next('');
  }

  selectTemplate(template: PromptTemplate): void {
    this.selectedTemplate = template;
    this.cancelEdit(); // Clear any ongoing edits
  }

  startEdit(): void {
    if (!this.selectedTemplate) return;

    this.editingTemplate = { ...this.selectedTemplate };
    this.editForm = {
      pre_condition: this.selectedTemplate.pre_condition,
      post_condition: this.selectedTemplate.post_condition,
      description: this.selectedTemplate.description || '',
      model: this.selectedTemplate.model || '',
      temperature: this.selectedTemplate.temperature || null,
      max_tokens: this.selectedTemplate.max_tokens || null
    };

    // Focus pre_condition textarea after view updates
    setTimeout(() => {
      if (this.preConditionTextarea) {
        this.preConditionTextarea.nativeElement.focus();
      }
    }, 100);
  }

  cancelEdit(): void {
    this.editingTemplate = null;
    this.editForm = {
      pre_condition: '',
      post_condition: '',
      description: '',
      model: '',
      temperature: null,
      max_tokens: null
    };
  }

  async saveTemplate(): Promise<void> {
    if (!this.selectedTemplate || !this.editingTemplate) return;

    this.isLoading = true;
    this.loadingMessage = 'Saving template...';

    try {
      const update: PromptTemplateUpdate = {
        pre_condition: this.editForm.pre_condition.trim(),
        post_condition: this.editForm.post_condition.trim(),
        description: this.editForm.description.trim(),
        model: this.editForm.model || undefined,
        temperature: this.editForm.temperature || undefined,
        max_tokens: this.editForm.max_tokens || undefined
      };

      const updatedTemplate = await this.promptService.updateTemplateAsync(
        this.selectedTemplate.category,
        this.selectedTemplate.action,
        update
      );

      // Update local data
      const templateIndex = this.templates.findIndex(t =>
        t.category === this.selectedTemplate!.category &&
        t.action === this.selectedTemplate!.action
      );

      if (templateIndex !== -1) {
        this.templates[templateIndex] = updatedTemplate;
        this.selectedTemplate = updatedTemplate;
      }

      this.applyFilter();
      this.cancelEdit();
    } catch (error: any) {
      this.notificationService.error(`Error saving template: ${error.message}`);
    } finally {
      this.isLoading = false;
    }
  }

  getTemplateDisplayName(template: PromptTemplate): string {
    return `${template.category} / ${template.action}`;
  }

  formatDate(dateString: string): string {
    try {
      return new Date(dateString).toLocaleDateString('de-CH', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  }

  trackByTemplate(index: number, template: PromptTemplate): string {
    return `${template.category}-${template.action}`;
  }

  getTokensToWordsHint(tokens: number | null | undefined): string {
    if (!tokens || tokens === null || tokens === undefined) return '';
    // Rough estimation: 1 token ≈ 0.75 words
    const words = Math.round(tokens * 0.75);
    return `(ca. ${words} words)`;
  }
}
