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
      generate: `${this.baseUrl}/api/v1/song/generate`,
      status: (taskId: string) => `${this.baseUrl}/api/v1/song/status/${taskId}`,
      tasks: `${this.baseUrl}/api/v1/song/tasks`,
      stems: `${this.baseUrl}/api/v1/song/stems`
    },
    image: {
      generate: `${this.baseUrl}/api/v1/image/generate`,
      status: (taskId: string) => `${this.baseUrl}/api/v1/image/status/${taskId}`,
      tasks: `${this.baseUrl}/api/v1/image/tasks`
    },
    redis: {
      keys: `${this.baseUrl}/api/v1/redis/keys`
    },
    billing: {
      info: `${this.baseUrl}/api/v1/song/mureka-account`
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
