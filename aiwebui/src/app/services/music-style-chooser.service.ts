import { Injectable } from '@angular/core';
import {
  MusicStyleChooserConfig,
  DEFAULT_STYLE_CHOOSER_CONFIG,
  MUSIC_STYLE_CATEGORIES
} from '../models/music-style-chooser.model';

@Injectable({
  providedIn: 'root'
})
export class MusicStyleChooserService {
  private readonly STORAGE_KEY = 'music-style-chooser-config';

  constructor() {}

  getConfig(): MusicStyleChooserConfig {
    const stored = localStorage.getItem(this.STORAGE_KEY);
    if (stored) {
      try {
        const config = JSON.parse(stored);
        return {
          selectedStyles: config.selectedStyles || [],
          selectedThemes: config.selectedThemes || [],
          selectedInstruments: config.selectedInstruments || [], // Backward compatibility
          lastModified: new Date(config.lastModified || new Date())
        };
      } catch (error) {
        console.warn('Failed to parse music style chooser config, using default:', error);
      }
    }
    return { ...DEFAULT_STYLE_CHOOSER_CONFIG };
  }

  saveConfig(config: MusicStyleChooserConfig): void {
    const toSave = {
      ...config,
      lastModified: new Date()
    };
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(toSave));
  }

  resetToDefault(): MusicStyleChooserConfig {
    const defaultConfig = { ...DEFAULT_STYLE_CHOOSER_CONFIG };
    this.saveConfig(defaultConfig);
    return defaultConfig;
  }

  toggleStyle(style: string): MusicStyleChooserConfig {
    const config = this.getConfig();
    const index = config.selectedStyles.indexOf(style);

    if (index > -1) {
      config.selectedStyles.splice(index, 1);
    } else {
      if (MUSIC_STYLE_CATEGORIES.style.includes(style)) {
        config.selectedStyles.push(style);
      }
    }

    this.saveConfig(config);
    return config;
  }

  toggleTheme(theme: string): MusicStyleChooserConfig {
    const config = this.getConfig();
    const index = config.selectedThemes.indexOf(theme);

    if (index > -1) {
      config.selectedThemes.splice(index, 1);
    } else {
      if (MUSIC_STYLE_CATEGORIES.theme.includes(theme)) {
        config.selectedThemes.push(theme);
      }
    }

    this.saveConfig(config);
    return config;
  }

  toggleInstrument(instrument: string): MusicStyleChooserConfig {
    const config = this.getConfig();
    const index = config.selectedInstruments.indexOf(instrument);

    if (index > -1) {
      config.selectedInstruments.splice(index, 1);
    } else {
      if (MUSIC_STYLE_CATEGORIES.instruments.includes(instrument)) {
        config.selectedInstruments.push(instrument);
      }
    }

    this.saveConfig(config);
    return config;
  }

  generateStylePrompt(config?: MusicStyleChooserConfig, isInstrumental?: boolean): string {
    const currentConfig = config || this.getConfig();

    // Ensure all arrays exist with fallbacks
    const styles = currentConfig.selectedStyles || [];
    const themes = currentConfig.selectedThemes || [];
    let instruments = currentConfig.selectedInstruments || [];

    // Remove vocals if instrumental mode (including legacy 'vocals')
    if (isInstrumental) {
      instruments = instruments.filter(i => i !== 'male-voice' && i !== 'female-voice' && i !== 'vocals');
    }

    if (styles.length === 0 && themes.length === 0 && instruments.length === 0) {
      return '';
    }

    let prompt = '';

    if (styles.length > 0) {
      prompt = styles.join(', ') + ' music';
    } else {
      prompt = 'music';
    }

    if (instruments.length > 0) {
      // Separate voice instruments from other instruments
      const voiceInstruments = instruments.filter(i => i === 'male-voice' || i === 'female-voice');
      const otherInstruments = instruments.filter(i => i !== 'male-voice' && i !== 'female-voice');

      if (otherInstruments.length > 0) {
        prompt += ' with ' + otherInstruments.join(', ');
      }

      if (voiceInstruments.length > 0) {
        const voice = voiceInstruments[0].replace('-voice', ' vocals');
        if (otherInstruments.length > 0) {
          prompt += ', ' + voice;
        } else {
          prompt += ' with ' + voice;
        }
      }
    }

    if (themes.length > 0) {
      prompt += ' with themes of ' + themes.join(', ');
    }

    return prompt;
  }

  isStyleSelected(style: string, config?: MusicStyleChooserConfig): boolean {
    const currentConfig = config || this.getConfig();
    return (currentConfig.selectedStyles || []).includes(style);
  }

  isThemeSelected(theme: string, config?: MusicStyleChooserConfig): boolean {
    const currentConfig = config || this.getConfig();
    return (currentConfig.selectedThemes || []).includes(theme);
  }

  isInstrumentSelected(instrument: string, config?: MusicStyleChooserConfig): boolean {
    const currentConfig = config || this.getConfig();
    return (currentConfig.selectedInstruments || []).includes(instrument);
  }

  getAvailableStyles(): string[] {
    return [...MUSIC_STYLE_CATEGORIES.style];
  }

  getAvailableThemes(): string[] {
    return [...MUSIC_STYLE_CATEGORIES.theme];
  }

  getAvailableInstruments(): string[] {
    return [...MUSIC_STYLE_CATEGORIES.instruments];
  }
}