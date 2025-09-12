import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'displayName',
  standalone: true
})
export class DisplayNamePipe implements PipeTransform {
  private nlp: any = null;
  private compromiseLoadState: 'loading' | 'loaded' | 'failed' = 'loading';
  private loadAttempts = 0;
  private maxLoadAttempts = 3;

  constructor() {
    this.loadCompromise();
  }

  private async loadCompromise() {
    this.loadAttempts++;
    try {
      console.log(`Attempting to load compromise (attempt ${this.loadAttempts})`);
      const compromise = await import('compromise');
      this.nlp = compromise.default;
      this.compromiseLoadState = 'loaded';
      console.log('Compromise loaded successfully');
    } catch (error) {
      console.error('Failed to load compromise:', error);
      this.compromiseLoadState = 'failed';
      
      // Retry logic
      if (this.loadAttempts < this.maxLoadAttempts) {
        console.log(`Retrying compromise load in 2 seconds (attempt ${this.loadAttempts + 1}/${this.maxLoadAttempts})`);
        setTimeout(() => this.loadCompromise(), 2000);
      } else {
        console.error(`Compromise loading failed after ${this.maxLoadAttempts} attempts. Using fallback strategy.`);
      }
    }
  }

  transform(prompt: string): string {
    if (!prompt || prompt.trim() === '') {
      return 'Unnamed Image';
    }

    if (this.nlp) {
      try {
        const doc = this.nlp(prompt);
        const sentences = doc.sentences();
        
        if (sentences.length > 0) {
          const firstSentence = sentences.out('text')[0];
          if (firstSentence && firstSentence.length > 0) {
            return firstSentence.length > 50 ? firstSentence.substring(0, 47) + '...' : firstSentence;
          }
        }
      } catch (error) {
        console.warn('Compromise processing failed, using fallback:', error);
      }
    }

    // Intelligent fallback if compromise fails or isn't loaded yet
    return this.intelligentFallback(prompt);
  }

  private intelligentFallback(prompt: string): string {
    console.log(`Using intelligent fallback for: "${prompt}"`);
    
    // 1. First try to find sentence boundaries
    const sentenceEnd = /[.!?]+\s+/;
    const sentenceMatch = prompt.match(sentenceEnd);
    
    if (sentenceMatch && sentenceMatch.index !== undefined) {
      const sentence = prompt.substring(0, sentenceMatch.index + 1).trim();
      if (sentence.length <= 50) {
        console.log('Fallback: Found complete sentence');
        return sentence;
      }
    }
    
    // 2. If too long, try to break at conjunctions
    if (prompt.length > 50) {
      const conjunctions = /\s+(und|mit|oder|sowie|plus|außerdem)\s+/i;
      const conjunctionMatch = prompt.match(conjunctions);
      
      if (conjunctionMatch && conjunctionMatch.index !== undefined && conjunctionMatch.index <= 47) {
        const part = prompt.substring(0, conjunctionMatch.index).trim();
        if (part.length > 20) { // Only if meaningful length
          console.log('Fallback: Split at conjunction');
          return part + '...';
        }
      }
    }
    
    // 3. Break at word boundary, never mid-word
    if (prompt.length > 50) {
      const truncated = prompt.substring(0, 47);
      const lastSpace = truncated.lastIndexOf(' ');
      const result = (lastSpace > 25 ? truncated.substring(0, lastSpace) : truncated) + '...';
      console.log('Fallback: Split at word boundary');
      return result;
    }
    
    console.log('Fallback: Using full prompt (short enough)');
    return prompt;
  }
}