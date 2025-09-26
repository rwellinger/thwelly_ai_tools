import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
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
  private http = inject(HttpClient);
  private apiConfig = inject(ApiConfigService);
  private promptConfig = inject(PromptConfigService);

  async improveImagePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('image', 'enhance'));
    if (!template) {
      throw new Error('Image enhance template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateLlama3Simple, {
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }

  async improveMusicStylePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('music', 'enhance'));
    if (!template) {
      throw new Error('Music enhance template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateLlama3Simple, {
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }

  async generateLyrics(inputText: string): Promise<string> {
    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateLyrics, {
        input_text: inputText
      })
    );
    return data.response;
  }

  async translateLyric(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('lyrics', 'translate'));
    if (!template) {
      throw new Error('Lyrics translate template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateGptOssSimple, {
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }

  async translateMusicStylePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('music', 'translate'));
    if (!template) {
      throw new Error('Music translate template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateGptOssSimple, {
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }

  async translateImagePrompt(prompt: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('image', 'translate'));
    if (!template) {
      throw new Error('Image translate template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateGptOssSimple, {
        pre_condition: template.pre_condition,
        prompt: prompt,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }

  async generateTitle(inputText: string): Promise<string> {
    const template = await firstValueFrom(this.promptConfig.getPromptTemplateAsync('titel', 'generate'));
    if (!template) {
      throw new Error('Title generate template not found');
    }

    const data: ChatResponse = await firstValueFrom(
      this.http.post<ChatResponse>(this.apiConfig.endpoints.chat.generateLlama3Simple, {
        pre_condition: template.pre_condition,
        prompt: inputText,
        post_condition: template.post_condition
      })
    );
    return data.response;
  }
}
