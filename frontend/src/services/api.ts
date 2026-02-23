/**
 * API Client for Observability Dashboard
 */

// Observability API is mounted at /api/v1
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

export interface AutoAdvanceNotification {
  beat_id: string;
  name: string;
  chapter_id: number;
  ready_since: string;
  content: string;
  notified: boolean;
}

export interface UntriggerBeatResponse {
  beat_id: string;
  stage?: number;
  untriggered: string[];
  dependencies_affected: string[];
  explanation: string;
  dry_run: boolean;
  timestamp: string;
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

export type ToolCallStatus = 'success' | 'error' | 'timeout';

export interface ToolCallLog {
  call_id: string;
  session_id?: string;
  interaction_id?: string;
  timestamp: string;
  duration_ms: number;
  tool_name: string;
  character?: string;
  user_id: string;
  request: Record<string, any>;
  response: Record<string, any>;
  status: ToolCallStatus;
  error_message?: string;
  reasoning?: string;
  conversation_context?: string;
  is_replay: boolean;
  replayed_from?: string;
}

export interface ToolCallFilterOptions {
  tool_name?: string;
  character?: string;
  status?: ToolCallStatus;
  limit?: number;
  offset?: number;
}

export interface ToolUsageStats {
  tool_name: string;
  total_calls: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  avg_duration_ms: number;
  min_duration_ms: number;
  max_duration_ms: number;
  last_used?: string;
}

export interface CharacterUsageStats {
  character: string;
  total_calls: number;
  success_count: number;
  error_count: number;
  success_rate: number;
  most_used_tool?: string;
  avg_duration_ms: number;
}

export interface ToolCallStatistics {
  total_calls: number;
  total_successes: number;
  total_errors: number;
  overall_success_rate: number;
  avg_duration_ms: number;
  earliest_call?: string;
  latest_call?: string;
  by_tool: ToolUsageStats[];
  by_character: CharacterUsageStats[];
  slowest_calls: ToolCallLog[];
  recent_errors: ToolCallLog[];
}

// Character interfaces
export interface CharacterSummary {
  id: string;
  name: string;
  display_name?: string;
  nickname?: string;
  role: string;
  description?: string;
  num_voice_modes: number;
  num_capabilities: number;
  has_story_arc: boolean;
  has_tool_instructions: boolean;
}

export interface VoiceMode {
  id: string;
  name: string;
  triggers: string[];
  characteristics: string[];
  example_phrases: string[];
  response_style: string;
}

export interface Personality {
  core_traits: string[];
  speech_patterns: string[];
  mannerisms?: string[];
}

export interface ContextAwareness {
  remembers?: string[];
  tracks?: string[];
}

export interface StoryArc {
  chapter_1?: string;
  internal_conflict?: string;
  coping_mechanism?: string;
}

export interface CharacterRelationship {
  dynamic: string;
  interaction_style: string;
  running_gags?: string[];
}

export interface Character {
  id: string;
  name: string;
  display_name?: string;
  nickname?: string;
  role: string;
  description?: string;
  personality: Personality;
  voice_modes: VoiceMode[];
  context_awareness?: ContextAwareness;
  tool_instructions?: Record<string, Record<string, any>>;
  story_arc?: StoryArc;
  capabilities: string[];
  relationships?: Record<string, CharacterRelationship>;
}

export interface VoiceModeSelection {
  mode: VoiceMode;
  confidence: number;
  reasoning?: string;
}

export interface SystemPromptRequest {
  voice_mode_id?: string;
  user_id?: string;
}

export interface SystemPromptResponse {
  character_id: string;
  character_name: string;
  prompt: string;
  token_estimate: number;
}

export interface PromptSection {
  text: string;
  token_estimate: number;
}

export interface PromptBreakdown {
  character_id: string;
  character_name: string;
  sections: Record<string, PromptSection>;
  total_token_estimate: number;
}

export interface CharacterStatistics {
  character_id: string;
  character_name: string;
  total_interactions: number;
  most_used_voice_mode: string;
  average_response_length: number;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  conversation_id: string;
  turn_id: string;
  fields: Record<string, unknown>;
}

export interface LogsResponse {
  logs: LogEntry[];
}

export interface LogGroup {
  turn_id: string | null;
  conversation_id: string;
  start_timestamp: string;
  headline: string | null;
  level_counts: Record<string, number>;
  entry_count: number;
}

export interface FileLoggingStatus {
  enabled: boolean;
  path: string | null;
  size_bytes: number | null;
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

  async getChapterDiagram(chapterId: number, userId?: string): Promise<ChapterDiagram> {
    const params = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
    return this.request<ChapterDiagram>(`/story/chapters/${chapterId}/diagram${params}`);
  }

  async triggerBeat(userId: string, beatId: string, variant: string = 'standard', stage?: number): Promise<any> {
    return this.request<any>(`/story/users/${userId}/beats/${beatId}/trigger`, {
      method: 'POST',
      body: JSON.stringify({ variant, stage }),
    });
  }

  async untriggerBeat(userId: string, beatId: string, dryRun: boolean = false, stage?: number | null): Promise<UntriggerBeatResponse> {
    const params = new URLSearchParams();
    params.append('dry_run', String(dryRun));
    // Only add stage if it's a valid number (not null, undefined, or NaN)
    if (stage !== undefined && stage !== null && !isNaN(stage)) {
      params.append('stage', String(stage));
    }

    return this.request<UntriggerBeatResponse>(`/story/users/${userId}/beats/${beatId}/untrigger?${params.toString()}`, {
      method: 'POST',
    });
  }

  async getAutoAdvanceReady(userId: string): Promise<AutoAdvanceNotification[]> {
    return this.request<AutoAdvanceNotification[]>(`/story/auto-advance-ready/${userId}`);
  }

  async deliverAutoAdvanceBeat(userId: string, beatId: string): Promise<{ status: string; message: string; beat_id: string; content: string }> {
    return this.request<{ status: string; message: string; beat_id: string; content: string }>(
      `/story/auto-advance/${userId}/${beatId}`,
      { method: 'POST' }
    );
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

  // Tool Call endpoints
  async listToolCalls(userId: string, filters?: ToolCallFilterOptions): Promise<ToolCallLog[]> {
    const params = new URLSearchParams({ user_id: userId });
    if (filters?.tool_name) params.append('tool_name', filters.tool_name);
    if (filters?.character) params.append('character', filters.character);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters?.offset !== undefined) params.append('offset', filters.offset.toString());

    return this.request<ToolCallLog[]>(`/tool-calls?${params.toString()}`);
  }

  async getToolCallDetail(callId: string, userId: string): Promise<ToolCallLog> {
    return this.request<ToolCallLog>(`/tool-calls/${callId}?user_id=${userId}`);
  }

  async getToolCallStatistics(userId: string, hours?: number): Promise<ToolCallStatistics> {
    const params = new URLSearchParams({ user_id: userId });
    if (hours !== undefined) params.append('hours', hours.toString());
    return this.request<ToolCallStatistics>(`/tool-calls/stats?${params.toString()}`);
  }

  async getAvailableTools(userId: string): Promise<{ tools: string[] }> {
    return this.request<{ tools: string[] }>(`/tool-calls/metadata/tools?user_id=${userId}`);
  }

  async getAvailableCharacters(userId: string): Promise<{ characters: string[] }> {
    return this.request<{ characters: string[] }>(`/tool-calls/metadata/characters?user_id=${userId}`);
  }

  // Character endpoints
  async listCharacters(): Promise<{ characters: CharacterSummary[] }> {
    return this.request<{ characters: CharacterSummary[] }>('/characters');
  }

  async getCharacter(characterId: string): Promise<Character> {
    return this.request<Character>(`/characters/${characterId}`);
  }

  async getCharacterVoiceModes(characterId: string): Promise<{ voice_modes: VoiceMode[] }> {
    return this.request<{ voice_modes: VoiceMode[] }>(`/characters/${characterId}/voice-modes`);
  }

  async testVoiceModeSelection(
    characterId: string,
    userInput: string,
    context?: Record<string, any>
  ): Promise<VoiceModeSelection> {
    const params = new URLSearchParams({ user_input: userInput });
    if (context) {
      params.append('context', JSON.stringify(context));
    }
    return this.request<VoiceModeSelection>(
      `/characters/${characterId}/test-voice-mode?${params.toString()}`,
      { method: 'POST' }
    );
  }

  async getSystemPrompt(
    characterId: string,
    request: SystemPromptRequest
  ): Promise<SystemPromptResponse> {
    return this.request<SystemPromptResponse>(`/characters/${characterId}/system-prompt`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getPromptBreakdown(
    characterId: string,
    voiceModeId?: string,
    userId?: string
  ): Promise<PromptBreakdown> {
    const params = new URLSearchParams();
    if (voiceModeId) params.append('voice_mode_id', voiceModeId);
    if (userId) params.append('user_id', userId);
    return this.request<PromptBreakdown>(
      `/characters/${characterId}/prompt-breakdown?${params.toString()}`
    );
  }

  async getCharacterStatistics(
    characterId: string,
    userId?: string
  ): Promise<CharacterStatistics> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    return this.request<CharacterStatistics>(
      `/characters/${characterId}/statistics?${params.toString()}`
    );
  }

  async getCharacterToolInstructions(
    characterId: string,
    toolName?: string
  ): Promise<{ tool_instructions: Record<string, any> }> {
    const params = new URLSearchParams();
    if (toolName) params.append('tool_name', toolName);
    return this.request<{ tool_instructions: Record<string, any> }>(
      `/characters/${characterId}/tool-instructions?${params.toString()}`
    );
  }

  // Logs endpoint
  async getLogs(limit: number = 200, level?: string, turnId?: string, conversationId?: string, order?: string): Promise<LogsResponse> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (level) params.append('level', level);
    if (turnId) params.append('turn_id', turnId);
    if (conversationId) params.append('conversation_id', conversationId);
    if (order) params.append('order', order);
    return this.request<LogsResponse>(`/logs?${params.toString()}`);
  }

  async getLogGroups(): Promise<{ groups: LogGroup[] }> {
    return this.request<{ groups: LogGroup[] }>('/logs/groups');
  }

  async getLogsForTurn(turnId: string, limit: number = 200): Promise<LogsResponse> {
    const params = new URLSearchParams({ turn_id: turnId, limit: limit.toString() });
    return this.request<LogsResponse>(`/logs?${params.toString()}`);
  }

  async getFileLoggingStatus(): Promise<FileLoggingStatus> {
    return this.request<FileLoggingStatus>('/logs/file-logging');
  }

  async setFileLogging(enabled: boolean, filename: string): Promise<FileLoggingStatus> {
    return this.request<FileLoggingStatus>('/logs/file-logging', {
      method: 'POST',
      body: JSON.stringify({ enabled, filename }),
    });
  }
  // Lists endpoints
  async getLists(userId: string): Promise<any> {
    return this.request<any>(`/lists/users/${userId}`);
  }

  async getList(userId: string, listName: string, includeCompleted: boolean = false): Promise<any> {
    const params = new URLSearchParams();
    if (includeCompleted) params.append('include_completed', 'true');
    return this.request<any>(`/lists/users/${userId}/${encodeURIComponent(listName)}?${params.toString()}`);
  }

  // Timers endpoints
  async getTimersStatus(): Promise<any> {
    return this.request<any>('/timers/status');
  }

  // Devices endpoints
  async getDevicesStatus(): Promise<any> {
    return this.request<any>('/devices/status');
  }
}

export const apiClient = new ApiClient();
