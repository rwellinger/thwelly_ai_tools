import { Injectable } from '@angular/core';

interface ImageFormData extends Record<string, unknown> {
  prompt?: string;
  size?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ImageService {
  private readonly STORAGE_KEY = 'imageFormData';

  loadFormData(): ImageFormData {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  }

  saveFormData(data: ImageFormData): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
  }

  clearFormData(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }
}