/**
 * Keyboard Shortcuts Modal
 * Displays all available keyboard shortcuts
 */

import './KeyboardShortcutsModal.css';

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  // Navigation
  { keys: ['1'], description: 'Go to Home', category: 'Navigation' },
  { keys: ['2'], description: 'Go to Story Beats', category: 'Navigation' },
  { keys: ['3'], description: 'Go to Memory', category: 'Navigation' },
  { keys: ['4'], description: 'Go to User Testing', category: 'Navigation' },
  { keys: ['5'], description: 'Go to Tool Calls', category: 'Navigation' },
  { keys: ['6'], description: 'Go to Characters', category: 'Navigation' },

  // Global Actions
  { keys: ['Ctrl/Cmd', 'K'], description: 'Open search (coming soon)', category: 'Global' },
  { keys: ['Ctrl/Cmd', 'U'], description: 'Focus user selector', category: 'Global' },
  { keys: ['Esc'], description: 'Close modal/dialog', category: 'Global' },
  { keys: ['?'], description: 'Show keyboard shortcuts', category: 'Global' },
];

export function KeyboardShortcutsModal({ isOpen, onClose }: KeyboardShortcutsModalProps) {
  if (!isOpen) return null;

  const categories = Array.from(new Set(shortcuts.map(s => s.category)));

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="shortcuts-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Keyboard Shortcuts</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="modal-content">
          {categories.map(category => (
            <div key={category} className="shortcut-category">
              <h3>{category}</h3>
              <div className="shortcuts-list">
                {shortcuts
                  .filter(s => s.category === category)
                  .map((shortcut, index) => (
                    <div key={index} className="shortcut-item">
                      <div className="shortcut-keys">
                        {shortcut.keys.map((key, i) => (
                          <span key={i}>
                            <kbd className="key">{key}</kbd>
                            {i < shortcut.keys.length - 1 && <span className="key-separator">+</span>}
                          </span>
                        ))}
                      </div>
                      <div className="shortcut-description">{shortcut.description}</div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <p>Press <kbd className="key">Esc</kbd> to close</p>
        </div>
      </div>
    </div>
  );
}
