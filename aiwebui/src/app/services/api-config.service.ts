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
      status: (taskId: string) => `${this.baseUrl}/api/v1/song/task/status/${taskId}`,
      tasks: `${this.baseUrl}/api/v1/song/tasks`,
      stems: `${this.baseUrl}/api/v1/song/stem/generate`,
      list: (limit?: number, offset?: number, status?: string) => {
        const params = new URLSearchParams();
        if (limit !== undefined) params.append('limit', limit.toString());
        if (offset !== undefined) params.append('offset', offset.toString());
        if (status) params.append('status', status);
        const query = params.toString();
        return `${this.baseUrl}/api/v1/song/list${query ? '?' + query : ''}`;
      },
      detail: (songId: string) => `${this.baseUrl}/api/v1/song/${songId}`
    },
    image: {
      generate: `${this.baseUrl}/api/v1/image/generate`,
      status: (taskId: string) => `${this.baseUrl}/api/v1/image/status/${taskId}`,
      tasks: `${this.baseUrl}/api/v1/image/tasks`,
      list: (limit?: number, offset?: number) => `${this.baseUrl}/api/v1/image/list${limit !== undefined || offset !== undefined ? '?' : ''}${limit !== undefined ? `limit=${limit}` : ''}${limit !== undefined && offset !== undefined ? '&' : ''}${offset !== undefined ? `offset=${offset}` : ''}`,
      detail: (id: string) => `${this.baseUrl}/api/v1/image/${id}`
    },
    redis: {
      keys: `${this.baseUrl}/api/v1/redis/list/keys`,
      deleteTask: (taskId: string) => `${this.baseUrl}/api/v1/redis/${taskId}`
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
