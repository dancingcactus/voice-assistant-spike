/**
 * Tests for App.tsx – user-switching behaviour
 *
 * Verifies that the chat-message list is cleared whenever the active user
 * changes so that one user's history is never visible to another user.
 */

import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { Message } from '../services/websocket';
import App from '../App';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Capture the onMessage callback so tests can drive incoming messages.
// Must use vi.hoisted because vi.mock factories are hoisted to the top of the
// file and cannot reference variables declared later.
const { capturedCallbacks } = vi.hoisted(() => ({
  capturedCallbacks: { onMessage: null as ((msg: Message) => void) | null },
}));

vi.mock('../services/websocket', () => {
  class MockWebSocketService {
    connect = vi.fn();
    disconnect = vi.fn();
    sendMessage = vi.fn();
    onMessage(handler: (msg: Message) => void) {
      capturedCallbacks.onMessage = handler;
    }
    onStatus() { /* no-op */ }
    onError() { /* no-op */ }
  }
  return { WebSocketService: MockWebSocketService };
});

vi.mock('../services/api', () => ({
  apiClient: {
    listUsers: vi.fn().mockResolvedValue([
      { user_id: 'user_justin', current_chapter: 1, interaction_count: 0 },
      { user_id: 'user_alice', current_chapter: 1, interaction_count: 0 },
    ]),
    getAutoAdvanceReady: vi.fn().mockResolvedValue([]),
    deliverAutoAdvanceBeat: vi.fn().mockResolvedValue({}),
  },
}));

vi.mock('../components/AudioPlayer', () => ({ AudioPlayer: () => null }));
vi.mock('../components/VoiceInput', () => ({ VoiceInput: () => null }));

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function pushAssistantMessage(content: string) {
  const msg: Message = {
    role: 'assistant',
    content,
    timestamp: new Date().toISOString(),
  };
  act(() => { capturedCallbacks.onMessage!(msg); });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('App – user switching clears chat history', () => {
  beforeEach(() => {
    capturedCallbacks.onMessage = null;
    vi.clearAllMocks();
  });

  it('clears messages when the selected user changes', async () => {
    render(<App />);

    // Wait for the user dropdown to be populated
    await waitFor(() =>
      expect(screen.getByRole('option', { name: /user_alice/i })).toBeInTheDocument()
    );

    // Simulate an assistant message arriving over the WebSocket
    pushAssistantMessage('Hello there!');
    expect(screen.getByText('Hello there!')).toBeInTheDocument();

    // Switch to a different user
    fireEvent.change(
      screen.getByRole('combobox', { name: /user/i }),
      { target: { value: 'user_alice' } }
    );

    // The previous user's message must be gone
    expect(screen.queryByText('Hello there!')).not.toBeInTheDocument();
  });
});

