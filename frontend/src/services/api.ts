/**
 * API Client for Observability Dashboard
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const API_AUTH_TOKEN = import.meta.env.VITE_API_AUTH_TOKEN || 'dev_token_12345';

export interface UserSummary {
  user_id: string;
  current_chapter: number;
  interaction_count: number;
  created_at?: string;
  updated_at?: string;
}

export interface UserDetail {
  user_id: string;
  preferences: {
    dietary_restrictions: string[];
    cooking_skill_level: string | null;
    favorite_foods: string[];
    disliked_foods: string[];
    custom_preferences: Record<string, any>;
  };
  conversation_history: {
    messages: any[];
    summary: string | null;
    last_interaction: string | null;
  };
  device_preferences: {
    devices: Record<string, any>;
    custom_scenes: Record<string, any>;
  };
  story_progress: {
    current_chapter: number;
    beats_delivered: Record<string, any>;
    interaction_count: number;
    first_interaction: string | null;
    chapter_start_time: string | null;
    custom_story_data: Record<string, any>;
  };
  created_at?: string;
  updated_at?: string;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
}

export interface ChapterSummary {
  id: number;
  title: string;
  description: string;
  is_current: boolean;
  is_completed: boolean;
  is_locked: boolean;
}

export interface BeatDeliveryInfo {
  timestamp?: string;
  variant?: string;
  stage?: number;
}

export interface BeatSummary {
  id: string;
  type: string;
  required: boolean;
  priority: string;
  status: string;
  delivery_info?: BeatDeliveryInfo;
}

export interface BeatDetail {
  id: string;
  type: string;
  required: boolean;
  priority: string;
  trigger: any;
  variants?: any;
  stages?: any;
  conditions?: any;
  user_status: {
    delivered: boolean;
    timestamp?: string;
    variant?: string;
    stage?: number;
  };
}

export interface ChapterProgressSummary {
  current_chapter: number;
  beats_total: number;
  beats_delivered: number;
  beats_ready: number;
  interaction_count: number;
  chapter_start_time?: string;
}

export interface ChapterDiagram {
  chapter_id: number;
  diagram: string;
  format: string;
}

export interface Memory {
  memory_id: string;
  category: string;
  content: string;
  source: string;
  importance: number;
  verified: boolean;
  created_at: string;
  last_accessed?: string | null;
  access_count: number;
  metadata: Record<string, any>;
}

export interface CreateMemoryRequest {
  category: string;
  content: string;
  source: string;
  importance?: number;
  verified?: boolean;
  metadata?: Record<string, any>;
}

export interface UpdateMemoryRequest {
  category?: string;
  content?: string;
  importance?: number;
  verified?: boolean;
  metadata?: Record<string, any>;
}

export interface ContextPreview {
  total_memories: number;
  context_memories: number;
  estimated_tokens: number;
  by_category: Record<string, number>;
  memories: Array<{
    memory_id: string;
    category: string;
    content: string;
    importance: number;
    tokens: number;
  }>;
}

export interface UserWithType {
  user_id: string;
  type: 'production' | 'test' | 'unknown';
  current_chapter: number;
  interaction_count: number;
  created_at: string;
  tags: string[];
}

export interface UserStateSummary {
  user_id: string;
  type: 'production' | 'test' | 'unknown';
  created_at: string;
  updated_at: string;
  tags: string[];
  profile: {
    interaction_count: number;
    first_interaction: string | null;
    last_interaction: string | null;
  };
  story_progress: {
    current_chapter: number;
    beats_delivered: number;
    chapter_start_time: string;
  };
  memory_count: number;
  device_count: number;
}

export interface CreateTestUserRequest {
  starting_chapter?: number;
  initial_memories?: Array<{
    content: string;
    category?: string;
    importance?: number;
    verified?: boolean;
    source?: string;
    metadata?: Record<string, any>;
  }>;
  tags?: string[];
  user_id?: string;
}

class ApiClient {
  private baseUrl: string;
  private authToken: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
    this.authToken = API_AUTH_TOKEN;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.authToken}`,
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // User endpoints
  async listUsers(): Promise<UserSummary[]> {
    return this.request<UserSummary[]>('/users');
  }

  async getUser(userId: string): Promise<UserDetail> {
    return this.request<UserDetail>(`/users/${userId}`);
  }

  // Story endpoints
  async listChapters(userId: string): Promise<ChapterSummary[]> {
    return this.request<ChapterSummary[]>(`/story/chapters?user_id=${userId}`);
  }

  async listChapterBeats(chapterId: number, userId: string): Promise<BeatSummary[]> {
    return this.request<BeatSummary[]>(`/story/chapters/${chapterId}/beats?user_id=${userId}`);
  }

  async getBeatDetail(chapterId: number, beatId: string, userId: string): Promise<BeatDetail> {
    return this.request<BeatDetail>(`/story/chapters/${chapterId}/beats/${beatId}?user_id=${userId}`);
  }

  async getUserStoryProgress(userId: string): Promise<ChapterProgressSummary> {
    return this.request<ChapterProgressSummary>(`/story/users/${userId}/progress`);
  }

  async getChapterDiagram(chapterId: number): Promise<ChapterDiagram> {
    return this.request<ChapterDiagram>(`/story/chapters/${chapterId}/diagram`);
  }

  async triggerBeat(userId: string, beatId: string, variant: string = 'standard', stage?: number): Promise<any> {
    return this.request<any>(`/story/users/${userId}/beats/${beatId}/trigger`, {
      method: 'POST',
      body: JSON.stringify({ variant, stage }),
    });
  }

  // Memory endpoints
  async listMemories(userId: string, category?: string, minImportance?: number): Promise<Memory[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (minImportance !== undefined) params.append('min_importance', minImportance.toString());
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.request<Memory[]>(`/memory/users/${userId}${query}`);
  }

  async getMemory(memoryId: string, userId: string): Promise<Memory> {
    return this.request<Memory>(`/memory/${memoryId}?user_id=${userId}`);
  }

  async createMemory(userId: string, memory: CreateMemoryRequest): Promise<Memory> {
    return this.request<Memory>(`/memory/users/${userId}`, {
      method: 'POST',
      body: JSON.stringify(memory),
    });
  }

  async updateMemory(memoryId: string, userId: string, updates: UpdateMemoryRequest): Promise<Memory> {
    return this.request<Memory>(`/memory/${memoryId}?user_id=${userId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteMemory(memoryId: string, userId: string): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>(`/memory/${memoryId}?user_id=${userId}`, {
      method: 'DELETE',
    });
  }

  async getContextPreview(userId: string, minImportance: number = 3): Promise<ContextPreview> {
    return this.request<ContextPreview>(`/memory/users/${userId}/context?min_importance=${minImportance}`);
  }

  // User Testing endpoints
  async listUsersWithType(): Promise<UserWithType[]> {
    return this.request<UserWithType[]>('/users/test/list');
  }

  async createTestUser(request: CreateTestUserRequest): Promise<{ status: string; message: string; user: any }> {
    return this.request<{ status: string; message: string; user: any }>('/users/test', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getUserStateSummary(userId: string): Promise<UserStateSummary> {
    return this.request<UserStateSummary>(`/users/${userId}/state`);
  }

  async deleteTestUser(userId: string): Promise<{ user_id: string; deleted: boolean; summary: any }> {
    return this.request<{ user_id: string; deleted: boolean; summary: any }>(`/users/${userId}`, {
      method: 'DELETE',
    });
  }

  async exportUserData(userId: string): Promise<any> {
    return this.request<any>(`/users/${userId}/export`, {
      method: 'POST',
    });
  }
}

export const apiClient = new ApiClient();
