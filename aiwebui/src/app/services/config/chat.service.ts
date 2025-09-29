import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiConfigService } from './api-config.service';
import { PromptConfigService } from './prompt-config.service';
import { LyricArchitectureService } from '../lyric-architecture.service';
import { MusicStyleChooserService } from '../music-style-chooser.service';
import { firstValueFrom } from 'rxjs';

interface UnifiedChatRequest {
  pre_condition: string;
  post_condition: string;
  input_text: string;
  temperature?: number;
  max_tokens?: number;
  model?: string;
}


export interface ChatResponse {
  model: string;
  created_at: string;
  response: string;
  done: boolean;
  done_reason: string;
  total_duration: number;
  load_duration: number;
  prompt_eval_count: number;
  prompt_eval_duration: number;
  eval_count: number;
  eval_duration: number;
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);
  private apiConfig = inject(ApiConfigService);
  private promptConfig = inject(PromptConfigService);
  private architectureService = inject(LyricArchitectureService);
  private musicStyleChooserService = inject(MusicStyleChooserService);

  private async validateAndCallUnified(category: string, action: string, inputText: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync(category, action));
    if (!template) {
      throw new Error(`Template ${category}/${action} not found in database`);
    }

    // Validate template has all required parameters
    if (!template.model) {
      throw new Error(`Template ${category}/${action} is missing model parameter`);
    }
    if (template.temperature === undefined || template.temperature === null) {
      throw new Error(`Template ${category}/${action} is missing temperature parameter`);
    }
    if (!template.max_tokens) {
      throw new Error(`Template ${category}/${action} is missing max_tokens parameter`);
    }

    const request: UnifiedChatRequest = {
      pre_condition: template.pre_condition || '',
      post_condition: template.post_condition || '',
      input_text: inputText,
      temperature: template.temperature,
      max_tokens: template.max_tokens,
      model: template.model
    };

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateUnified, request)
    );
    return data.response;
  }

  async improveImagePrompt(prompt: string): Promise<string> {
    return this.validateAndCallUnified('image', 'enhance', prompt);
  }

  async improveMusicStylePrompt(prompt: string): Promise<string> {
    return this.improveMusicStylePromptWithChooser(prompt);
  }

  async improveMusicStylePromptWithChooser(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('music', 'enhance'));
    if (!template) {
      throw new Error(`Template music/enhance not found in database`);
    }

    // Get current style chooser configuration
    const stylePrompt = this.musicStyleChooserService.generateStylePrompt();
    // Enhance pre_condition with style chooser if it exists
    let enhancedPreCondition = template.pre_condition || '';
    if (stylePrompt.trim()) {
      enhancedPreCondition = `Style preferences: ${stylePrompt}\n\n${enhancedPreCondition}`;
    }

    // Validate template has all required parameters
    if (!template.model) {
      throw new Error(`Template music/enhance is missing model parameter`);
    }
    if (template.temperature === undefined || template.temperature === null) {
      throw new Error(`Template music/enhance is missing temperature parameter`);
    }
    if (!template.max_tokens) {
      throw new Error(`Template music/enhance is missing max_tokens parameter`);
    }

    const request: UnifiedChatRequest = {
      pre_condition: enhancedPreCondition,
      post_condition: template.post_condition || '',
      input_text: prompt,
      temperature: template.temperature,
      max_tokens: template.max_tokens,
      model: template.model
    };

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateUnified, request)
    );
    return data.response;
  }

  async generateLyrics(inputText: string): Promise<string> {
    return this.generateLyricsWithArchitecture(inputText);
  }

  async generateLyricsWithArchitecture(inputText: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('lyrics', 'generate'));
    if (!template) {
      throw new Error(`Template lyrics/generate not found in database`);
    }

    // Get current architecture configuration
    const architectureString = this.architectureService.generateArchitectureString();
    // Enhance pre_condition with architecture if it exists
    let enhancedPreCondition = template.pre_condition || '';
    if (architectureString.trim()) {
      enhancedPreCondition = architectureString + '\n\n' + enhancedPreCondition;
    }

    // Validate template has all required parameters
    if (!template.model) {
      throw new Error(`Template lyrics/generate is missing model parameter`);
    }
    if (template.temperature === undefined || template.temperature === null) {
      throw new Error(`Template lyrics/generate is missing temperature parameter`);
    }
    if (!template.max_tokens) {
      throw new Error(`Template lyrics/generate is missing max_tokens parameter`);
    }

    const request: UnifiedChatRequest = {
      pre_condition: enhancedPreCondition,
      post_condition: template.post_condition || '',
      input_text: inputText,
      temperature: template.temperature,
      max_tokens: template.max_tokens,
      model: template.model
    };

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateUnified, request)
    );
    return data.response;
  }

  async translateLyric(prompt: string): Promise<string> {
    return this.validateAndCallUnified('lyrics', 'translate', prompt);
  }

  async translateMusicStylePrompt(prompt: string): Promise<string> {
    return this.validateAndCallUnified('music', 'translate', prompt);
  }

  async translateImagePrompt(prompt: string): Promise<string> {
    return this.validateAndCallUnified('image', 'translate', prompt);
  }

  async generateTitle(inputText: string): Promise<string> {
    return this.validateAndCallUnified('titel', 'generate', inputText);
  }
}
