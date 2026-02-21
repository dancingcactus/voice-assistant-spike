/**
 * Audio Queue Service
 * 
 * Manages sequential playback of audio files for multi-character responses.
 * Ensures characters finish speaking before the next character starts.
 */

export class AudioQueue {
  private queue: string[] = [];
  private isPlaying = false;
  private currentAudio: HTMLAudioElement | null = null;
  private onQueueEmptyCallback: (() => void) | null = null;

  /**
   * Add an audio URL to the playback queue.
   * If no audio is currently playing, starts playback immediately.
   * 
   * @param audioUrl - URL of the audio file to play
   */
  async enqueue(audioUrl: string): Promise<void> {
    this.queue.push(audioUrl);
    
    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  /**
   * Add multiple audio URLs to the queue at once.
   * 
   * @param audioUrls - Array of audio URLs to play in sequence
   */
  async enqueueMultiple(audioUrls: string[]): Promise<void> {
    this.queue.push(...audioUrls);
    
    if (!this.isPlaying) {
      await this.playNext();
    }
  }

  /**
   * Play the next audio file in the queue.
   * Automatically continues to the next item when playback completes.
   */
  private async playNext(): Promise<void> {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      
      // Notify listener that queue is empty
      if (this.onQueueEmptyCallback) {
        this.onQueueEmptyCallback();
      }
      
      return;
    }

    this.isPlaying = true;
    const audioUrl = this.queue.shift()!;

    this.currentAudio = new Audio(audioUrl);

    // Set up event handlers
    this.currentAudio.onended = () => {
      this.currentAudio = null;
      this.playNext();
    };

    this.currentAudio.onerror = (error) => {
      console.error('Audio playback error:', error, 'URL:', audioUrl);
      this.currentAudio = null;
      this.playNext(); // Continue to next item despite error
    };

    try {
      await this.currentAudio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
      this.currentAudio = null;
      this.playNext(); // Continue to next item despite error
    }
  }

  /**
   * Clear the queue and stop current playback.
   * Use this when user sends a new message mid-playback.
   */
  clear(): void {
    this.queue = [];
    
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    
    this.isPlaying = false;
  }

  /**
   * Pause current audio playback without clearing the queue.
   */
  pause(): void {
    if (this.currentAudio) {
      this.currentAudio.pause();
    }
  }

  /**
   * Resume paused audio playback.
   */
  async resume(): Promise<void> {
    if (this.currentAudio && this.currentAudio.paused) {
      try {
        await this.currentAudio.play();
      } catch (error) {
        console.error('Failed to resume audio:', error);
      }
    }
  }

  /**
   * Check if audio is currently playing.
   */
  get playing(): boolean {
    return this.isPlaying;
  }

  /**
   * Get the number of audio files queued.
   */
  get length(): number {
    return this.queue.length;
  }

  /**
   * Set a callback to be invoked when the queue becomes empty.
   * 
   * @param callback - Function to call when playback completes
   */
  onQueueEmpty(callback: () => void): void {
    this.onQueueEmptyCallback = callback;
  }
}

// Create a singleton instance for global use
export const audioQueue = new AudioQueue();
