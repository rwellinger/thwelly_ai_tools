import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiConfigService } from './api-config.service';

@Injectable({
  providedIn: 'root'
})
export class SongService {
  private readonly STORAGE_KEY = 'songFormData';

  constructor(
    private http: HttpClient,
    private apiConfig: ApiConfigService
  ) { }

  async fetchWithTimeout(resource: string, options: any = {}): Promise<Response> {
    const { timeout = 30000 } = options;
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);
    
    try {
      const response = await fetch(resource, { ...options, signal: controller.signal });
      clearTimeout(id);
      return response;
    } catch (e: any) {
      clearTimeout(id);
      if (e.name === 'AbortError') throw new Error('Request timed out');
      throw e;
    }
  }

  loadFormData(): any {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  }

  saveFormData(data: any): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
  }

  clearFormData(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }

  async generateSong(lyrics: string, prompt: string, model: string): Promise<any> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.generate, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lyrics, model, prompt }),
      timeout: 60000
    });
    return response.json();
  }

  async checkSongStatus(taskId: string): Promise<any> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.status(taskId), { timeout: 60000 });
    return response.json();
  }

  async getTasks(): Promise<any> {
    const response = await this.fetchWithTimeout(this.apiConfig.endpoints.song.tasks, { timeout: 30000 });
    return response.json();
  }
}
