/**
 * Keyboard Shortcuts Hook
 * Provides global keyboard navigation for the dashboard
 */

import { useEffect } from 'react';

export type ShortcutHandler = (e: KeyboardEvent) => void;

interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  handler: ShortcutHandler;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[], enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in input fields
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? (e.ctrlKey || e.metaKey) : true;
        const metaMatch = shortcut.meta ? e.metaKey : true;
        const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey;
        const altMatch = shortcut.alt ? e.altKey : !e.altKey;
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase();

        if (keyMatch && ctrlMatch && metaMatch && shiftMatch && altMatch) {
          e.preventDefault();
          shortcut.handler(e);
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [shortcuts, enabled]);
}

// Predefined shortcuts for common actions
export const SHORTCUTS = {
  ESCAPE: { key: 'Escape', description: 'Close modal/dialog' },
  CMD_K: { key: 'k', ctrl: true, description: 'Open search' },
  CMD_U: { key: 'u', ctrl: true, description: 'User switcher' },
  NUMBER_1: { key: '1', description: 'Go to Home' },
  NUMBER_2: { key: '2', description: 'Go to Story Beats' },
  NUMBER_3: { key: '3', description: 'Go to Memory' },
  NUMBER_4: { key: '4', description: 'Go to User Testing' },
  NUMBER_5: { key: '5', description: 'Go to Tool Calls' },
  NUMBER_6: { key: '6', description: 'Go to Characters' },
  QUESTION: { key: '?', shift: true, description: 'Show keyboard shortcuts' },
};
