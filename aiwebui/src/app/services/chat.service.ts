import { Injectable, inject } from '@angular/core';
import { ApiConfigService } from './api-config.service';

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

  async improveImagePrompt(prompt: string): Promise<string> {
    const response = await fetch(this.apiConfig.endpoints.chat.generateLlama3Simple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: 'One-sentence DALL-E prompt:',
        prompt: prompt,
        post_condition: 'Only respond with the prompt.'
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }

  async improveMusicStylePrompt(prompt: string): Promise<string> {
    const response = await fetch(this.apiConfig.endpoints.chat.generateLlama3Simple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: 'One-sentence Suno Music Style prompt:',
        prompt: prompt,
        post_condition: 'Only respond with the prompt.'
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
    const response = await fetch(this.apiConfig.endpoints.chat.generateGptOssSimple, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pre_condition: 'By a britisch songwriter and translate this lyric text to britisch english:',
        prompt: prompt,
        post_condition: 'Only respond with the translation.'
      })
    });

    if (!response.ok) {
      throw new Error(`Chat API error: ${response.status}`);
    }

    const data: ChatResponse = await response.json();
    return data.response;
  }
}
