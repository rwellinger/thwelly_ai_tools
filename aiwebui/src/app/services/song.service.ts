import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ApiConfigService } from './api-config.service';

interface FetchOptions {
  timeout?: number;
  method?: string;
  headers?: Record<string, string>;
  body?: string;
  signal?: AbortSignal;
}

interface SongFormData extends Record<string, unknown> {
  lyrics?: string;
  prompt?: string;
  model?: string;
}

interface SongGenerateResponse {
  task_id: string;
  status: string;
  message?: string;
}

interface SongStatusResponse {
  task_id: string;
  status: string;
  result?: {
    error?: string;
    [key: string]: unknown;
  };
  error?: string;
}

interface TasksResponse {
  tasks: unknown[];
  total: number;
}

interface SongsResponse {
  songs: unknown[];
  pagination?: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

interface SongDetailResponse extends Record<string, unknown> {
  song_id: string;
  lyrics: string;
  prompt: string;
  model: string;
  status: string;
  audio_url?: string;
  created_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class SongService {
  private readonly STORAGE_KEY = 'songFormData';

  private http = inject(HttpClient);
  private apiConfig = inject(ApiConfigService);

  async fetchWithTimeout(resource: string, options: FetchOptions = {}): Promise<Response> {
    const { timeout = 30000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(resource, { ...options, signal: controller.signal });
      clearTimeout(id);
      return response;
    } catch (e: unknown) {
      clearTimeout(id);
      if (e instanceof Error && e.name === 'AbortError') throw new Error('Request timed out');
      throw e;
    }
  }

  loadFormData(): SongFormData {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  }

  saveFormData(data: SongFormData): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
  }

  clearFormData(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }

  async generateSong(lyrics: string, prompt: string, model: string): Promise<SongGenerateResponse> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.generate, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lyrics, model, prompt }),
      timeout: 60000
    });
    return response.json();
  }

  async checkSongStatus(taskId: string): Promise<SongStatusResponse> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.status(taskId), { timeout: 60000 });
    return response.json();
  }

  async getTasks(): Promise<TasksResponse> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.tasks, { timeout: 30000 });
    return response.json();
  }

  async getSongs(limit: number = 20, offset: number = 0, status?: string, search: string = '',
                sort_by: string = 'created_at', sort_direction: string = 'desc'): Promise<SongsResponse> {
    // Build URL with parameters
    const url = new URL(this.apiConfig.endpoints.song.list(limit, offset, status).split('?')[0], window.location.origin);
    url.searchParams.set('limit', limit.toString());
    url.searchParams.set('offset', offset.toString());
    url.searchParams.set('sort_by', sort_by);
    url.searchParams.set('sort_direction', sort_direction);

    if (status) {
      url.searchParams.set('status', status);
    }
    if (search.trim()) {
      url.searchParams.set('search', search.trim());
    }

    const response = await this.fetchWithTimeout(
      url.toString(),
      { timeout: 30000 }
    );
    return response.json();
  }

  async getSongById(songId: string): Promise<SongDetailResponse> {
    const response = await this.fetchWithTimeout(
      this.apiConfig.endpoints.song.detail(songId),
      { timeout: 30000 }
    );
    return response.json();
  }

  async updateChoiceRating(choiceId: string, rating: number | null): Promise<any> {
    const response = await this.fetchWithTimeout(
      this.apiConfig.endpoints.song.updateChoiceRating(choiceId),
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rating }),
        timeout: 30000
      }
    );
    return response.json();
  }
}
