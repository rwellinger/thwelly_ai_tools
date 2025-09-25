import { Injectable, inject } from '@angular/core';
import { ApiConfigService } from './api-config.service';
import { PromptConfigService } from './prompt-config.service';
import { firstValueFrom } from 'rxjs';

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
  private apiConfig = inject(ApiConfigService);
  private promptConfig = inject(PromptConfigService);

  async improveImagePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('image', 'enhance'));
    if (!template) {
      throw new Error('Image enhance template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateLlama3Simple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async improveMusicStylePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('music', 'enhance'));
    if (!template) {
      throw new Error('Music enhance template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateLlama3Simple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async generateLyrics(inputText: string): Promise<string> {
    const response = await fetch(this.apiConfig.endpoints.chat.generateLyrics, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_text: inputText
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async translateLyric(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('lyrics', 'translate'));
    if (!template) {
      throw new Error('Lyrics translate template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateGptOssSimple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async translateMusicStylePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('music', 'translate'));
    if (!template) {
      throw new Error('Music translate template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateGptOssSimple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async translateImagePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('image', 'translate'));
    if (!template) {
      throw new Error('Image translate template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateGptOssSimple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async generateTitle(inputText: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('titel', 'generate'));
    if (!template) {
      throw new Error('Title generate template not found');
    }

    const response = await fetch(this.apiConfig.endpoints.chat.generateLlama3Simple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: template.pre_condition,
        prompt: inputText,
        post_condition: template.post_condition
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }
}
