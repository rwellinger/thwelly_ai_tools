import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Subject } from 'rxjs';

import {
  MusicStyleChooserConfig,
  MUSIC_STYLE_CATEGORIES
} from '../../models/music-style-chooser.model';
import { MusicStyleChooserService } from '../../services/music-style-chooser.service';
import { NotificationService } from '../../services/ui/notification.service';

@Component({
  selector: 'app-music-style-chooser-modal',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './music-style-chooser-modal.component.html',
  styleUrl: './music-style-chooser-modal.component.scss'
})
export class MusicStyleChooserModalComponent implements OnInit, OnDestroy {
  config: MusicStyleChooserConfig = { selectedStyles: [], selectedThemes: [], selectedInstruments: [], lastModified: new Date() };
  availableStyles: string[] = MUSIC_STYLE_CATEGORIES.style;
  availableThemes: string[] = MUSIC_STYLE_CATEGORIES.theme;
  availableInstruments: string[] = MUSIC_STYLE_CATEGORIES.instruments;
  isInstrumental = false;

  private destroy$ = new Subject<void>();

  private styleChooserService = inject(MusicStyleChooserService);
  private notificationService = inject(NotificationService);
  private dialogRef = inject(MatDialogRef<MusicStyleChooserModalComponent>);
  private data = inject<{ isInstrumental?: boolean }>(MAT_DIALOG_DATA);

  constructor() {
    this.isInstrumental = this.data?.isInstrumental || false;
  }

  ngOnInit(): void {
    this.loadConfig();
    this.filterInstrumentsForMode();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  loadConfig(): void {
    this.config = this.styleChooserService.getConfig();
  }

  filterInstrumentsForMode(): void {
    // Clean up legacy 'vocals' from saved config
    this.config.selectedInstruments = this.config.selectedInstruments.filter(
      instrument => instrument !== 'vocals'
    );

    if (this.isInstrumental) {
      // Remove male-voice and female-voice for instrumental mode
      this.availableInstruments = MUSIC_STYLE_CATEGORIES.instruments.filter(
        instrument => instrument !== 'male-voice' && instrument !== 'female-voice'
      );
      // Also remove them from selected instruments if they were previously selected
      this.config.selectedInstruments = this.config.selectedInstruments.filter(
        instrument => instrument !== 'male-voice' && instrument !== 'female-voice'
      );
    } else {
      // Show all instruments for normal mode
      this.availableInstruments = [...MUSIC_STYLE_CATEGORIES.instruments];

      // Auto-select male-voice if no voice is selected yet
      const hasMaleVoice = this.config.selectedInstruments.includes('male-voice');
      const hasFemaleVoice = this.config.selectedInstruments.includes('female-voice');

      if (!hasMaleVoice && !hasFemaleVoice) {
        this.config.selectedInstruments.push('male-voice');
      }
    }
  }

  toggleStyle(style: string): void {
    try {
      this.config = this.styleChooserService.toggleStyle(style);
    } catch (error: any) {
      console.error('Error toggling style:', error);
      this.notificationService.error(error.message);
    }
  }

  toggleTheme(theme: string): void {
    try {
      this.config = this.styleChooserService.toggleTheme(theme);
    } catch (error: any) {
      console.error('Error toggling theme:', error);
      this.notificationService.error(error.message);
    }
  }

  toggleInstrument(instrument: string): void {
    try {
      // Handle voice selection for non-instrumental mode
      if (!this.isInstrumental && (instrument === 'male-voice' || instrument === 'female-voice')) {
        const isCurrentlySelected = this.isInstrumentSelected(instrument);

        if (!isCurrentlySelected) {
          // Deselect the other voice first
          const otherVoice = instrument === 'male-voice' ? 'female-voice' : 'male-voice';
          if (this.isInstrumentSelected(otherVoice)) {
            this.config = this.styleChooserService.toggleInstrument(otherVoice);
          }
        }
      }

      this.config = this.styleChooserService.toggleInstrument(instrument);
    } catch (error: any) {
      console.error('Error toggling instrument:', error);
      this.notificationService.error(error.message);
    }
  }

  isStyleSelected(style: string): boolean {
    return this.styleChooserService.isStyleSelected(style, this.config);
  }

  isThemeSelected(theme: string): boolean {
    return this.styleChooserService.isThemeSelected(theme, this.config);
  }

  isInstrumentSelected(instrument: string): boolean {
    return this.styleChooserService.isInstrumentSelected(instrument, this.config);
  }

  reset(): void {
    this.config = this.styleChooserService.resetToDefault();
    this.notificationService.success('Music style selection reset');
  }

  save(): void {
    try {
      // Validate voice selection for non-instrumental mode
      if (!this.isInstrumental) {
        const hasMaleVoice = this.isInstrumentSelected('male-voice');
        const hasFemaleVoice = this.isInstrumentSelected('female-voice');

        if (!hasMaleVoice && !hasFemaleVoice) {
          this.notificationService.error('Please select either male or female voice for lyrics mode');
          return;
        }
      }

      this.styleChooserService.saveConfig(this.config);
      const stylePrompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);

      this.dialogRef.close({
        config: this.config,
        stylePrompt: stylePrompt
      });
    } catch (error: any) {
      this.notificationService.error(`Error saving configuration: ${error.message}`);
    }
  }

  cancel(): void {
    this.dialogRef.close();
  }

  getPreviewText(): string {
    const prompt = this.styleChooserService.generateStylePrompt(this.config, this.isInstrumental);
    return prompt || 'No styles, instruments, or themes selected';
  }

  getSelectionSummary(): string {
    const stylesCount = this.config.selectedStyles.length;
    const themesCount = this.config.selectedThemes.length;
    const instrumentsCount = this.config.selectedInstruments.length;

    if (stylesCount === 0 && themesCount === 0 && instrumentsCount === 0) {
      return 'No selection';
    }

    const parts = [];
    if (stylesCount > 0) {
      parts.push(`${stylesCount} style${stylesCount > 1 ? 's' : ''}`);
    }
    if (instrumentsCount > 0) {
      parts.push(`${instrumentsCount} instrument${instrumentsCount > 1 ? 's' : ''}`);
    }
    if (themesCount > 0) {
      parts.push(`${themesCount} theme${themesCount > 1 ? 's' : ''}`);
    }

    return parts.join(', ') + ' selected';
  }
}