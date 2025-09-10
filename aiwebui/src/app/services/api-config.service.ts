import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiConfigService {
  private readonly baseUrl = environment.apiUrl;

  // API Endpoints
  readonly endpoints = {
    song: {
      generate: `${this.baseUrl}/api/song/generate`,
      status: (taskId: string) => `${this.baseUrl}/api/song/status/${taskId}`,
      tasks: `${this.baseUrl}/api/song/tasks`,
      stems: `${this.baseUrl}/api/song/stems`
    },
    image: {
      generate: `${this.baseUrl}/api/image/generate`,
      status: (taskId: string) => `${this.baseUrl}/api/image/status/${taskId}`,
      tasks: `${this.baseUrl}/api/image/tasks`
    },
    redis: {
      keys: `${this.baseUrl}/api/redis/keys`
    },
    billing: {
      info: `${this.baseUrl}/api/billing/info`
    }
  };

  getBaseUrl(): string {
    return this.baseUrl;
  }

  getEndpoint(category: keyof typeof this.endpoints, action: string, ...params: any[]): string {
    const endpoint = (this.endpoints[category] as any)[action];
    return typeof endpoint === 'function' ? endpoint(...params) : endpoint;
  }
}