import { Injectable } from '@angular/core';

export interface PromptTemplate {
  pre_condition: string;
  post_condition: string;
  description?: string;
  version?: string;
  model_hint?: string;
}

export type PromptCategory = Record<string, PromptTemplate>;

export type PromptTemplates = Record<string, PromptCategory>;

@Injectable({
  providedIn: 'root'
})
export class PromptConfigService {
  private templates: PromptTemplates = {
    image: {
      enhance: {
        pre_condition: 'One-sentence DALL-E prompt:',
        post_condition: 'Only respond with the prompt.',
        description: 'Enhances image generation prompts for DALL-E',
        version: '1.0',
        model_hint: 'llama3'
      },
      translate: {
        pre_condition: 'Translate this image prompt to english:',
        post_condition: 'Only respond with the translation.',
        description: 'Translates image prompts to English',
        version: '1.0',
        model_hint: 'gpt-oss'
      }
    },
    music: {
      enhance: {
        pre_condition: 'One-sentence Suno Music Style prompt without artist names or band names:',
        post_condition: 'Only respond with the prompt.',
        description: 'Enhances music style prompts for Suno without artist references',
        version: '1.0',
        model_hint: 'llama3'
      },
      translate: {
        pre_condition: 'Translate this music style description to english:',
        post_condition: 'Only respond with the translation.',
        description: 'Translates music style descriptions to English',
        version: '1.0',
        model_hint: 'gpt-oss'
      }
    },
    lyrics: {
      generate: {
        pre_condition: 'Generate song lyrics from this text:',
        post_condition: 'Only respond with the lyrics.',
        description: 'Generates song lyrics from input text',
        version: '1.0',
        model_hint: 'llama3'
      },
      translate: {
        pre_condition: 'By a britisch songwriter and translate this lyric text to britisch english:',
        post_condition: 'Only respond with the translation.',
        description: 'Translates lyrics to British English',
        version: '1.0',
        model_hint: 'gpt-oss'
      }
    }
  };

  getPromptTemplate(category: string, action: string): PromptTemplate | null {
    const categoryTemplates = this.templates[category];
    if (!categoryTemplates) {
      return null;
    }

    return categoryTemplates[action] || null;
  }

  getAllTemplates(): PromptTemplates {
    return this.templates;
  }

  getCategoryTemplates(category: string): PromptCategory | null {
    return this.templates[category] || null;
  }
}