/**
 * Character Tool Component
 *
 * Provides visualization and testing interface for character definitions,
 * voice modes, and system prompts.
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  apiClient,
  type CharacterSummary,
  type VoiceMode,
  type VoiceModeSelection,
} from '../services/api';
import './CharacterTool.css';

interface CharacterToolProps {
  userId: string;
}

type TabType = 'overview' | 'voice-modes' | 'system-prompt' | 'tool-instructions';

export function CharacterTool({ userId }: CharacterToolProps) {
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [testInput, setTestInput] = useState<string>('');
  const [testResult, setTestResult] = useState<VoiceModeSelection | null>(null);
  const [selectedVoiceMode, setSelectedVoiceMode] = useState<string | null>(null);
  const [showPromptBreakdown, setShowPromptBreakdown] = useState(false);

  // Fetch all characters
  const { data: charactersData, isLoading: charactersLoading } = useQuery({
    queryKey: ['characters'],
    queryFn: () => apiClient.listCharacters(),
  });

  const characters = charactersData?.characters || [];

  // Fetch selected character detail
  const { data: character } = useQuery({
    queryKey: ['character', selectedCharacterId],
    queryFn: () => selectedCharacterId ? apiClient.getCharacter(selectedCharacterId) : Promise.resolve(null),
    enabled: selectedCharacterId !== null,
  });

  // Fetch voice modes
  const { data: voiceModesData } = useQuery({
    queryKey: ['character-voice-modes', selectedCharacterId],
    queryFn: () => selectedCharacterId ? apiClient.getCharacterVoiceModes(selectedCharacterId) : Promise.resolve(null),
    enabled: selectedCharacterId !== null && activeTab === 'voice-modes',
  });

  const voiceModes = voiceModesData?.voice_modes || [];

  // Fetch system prompt
  const { data: systemPrompt, isLoading: promptLoading } = useQuery({
    queryKey: ['system-prompt', selectedCharacterId, selectedVoiceMode, userId],
    queryFn: () => selectedCharacterId
      ? apiClient.getSystemPrompt(selectedCharacterId, {
          voice_mode_id: selectedVoiceMode || undefined,
          user_id: userId,
        })
      : Promise.resolve(null),
    enabled: selectedCharacterId !== null && activeTab === 'system-prompt',
  });

  // Fetch prompt breakdown
  const { data: promptBreakdown } = useQuery({
    queryKey: ['prompt-breakdown', selectedCharacterId, selectedVoiceMode, userId],
    queryFn: () => selectedCharacterId
      ? apiClient.getPromptBreakdown(selectedCharacterId, selectedVoiceMode || undefined, userId)
      : Promise.resolve(null),
    enabled: selectedCharacterId !== null && activeTab === 'system-prompt' && showPromptBreakdown,
  });

  // Fetch tool instructions
  const { data: toolInstructionsData } = useQuery({
    queryKey: ['character-tool-instructions', selectedCharacterId],
    queryFn: () => selectedCharacterId
      ? apiClient.getCharacterToolInstructions(selectedCharacterId)
      : Promise.resolve(null),
    enabled: selectedCharacterId !== null && activeTab === 'tool-instructions',
  });

  const toolInstructions = toolInstructionsData?.tool_instructions || {};

  // Set initial character selection
  if (characters.length > 0 && !selectedCharacterId) {
    setSelectedCharacterId(characters[0].id);
  }

  const handleTestVoiceMode = async () => {
    if (!selectedCharacterId || !testInput.trim()) return;

    try {
      const result = await apiClient.testVoiceModeSelection(selectedCharacterId, testInput);
      setTestResult(result);
    } catch (error) {
      console.error('Failed to test voice mode:', error);
    }
  };

  const formatTokenCount = (tokens: number): string => {
    return tokens.toLocaleString();
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.9) return '#28a745';
    if (confidence >= 0.7) return '#ffc107';
    return '#dc3545';
  };

  if (charactersLoading) {
    return <div className="character-tool loading">Loading characters...</div>;
  }

  if (characters.length === 0) {
    return <div className="character-tool empty">No characters found</div>;
  }

  return (
    <div className="character-tool">
      {/* Character Selector */}
      <div className="character-selector">
        <h3>Characters</h3>
        <div className="character-list">
          {characters.map((char: CharacterSummary) => (
            <button
              key={char.id}
              className={`character-card ${selectedCharacterId === char.id ? 'selected' : ''}`}
              onClick={() => {
                setSelectedCharacterId(char.id);
                setTestResult(null);
                setSelectedVoiceMode(null);
              }}
            >
              <div className="character-name">{char.name}</div>
              {char.nickname && <div className="character-nickname">"{char.nickname}"</div>}
              <div className="character-role">{char.role}</div>
              <div className="character-stats">
                <span title="Voice Modes">{char.num_voice_modes} modes</span>
                <span title="Capabilities">{char.num_capabilities} capabilities</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Character Detail */}
      {character && (
        <div className="character-detail">
          <div className="character-header">
            <h2>{character.name}</h2>
            {character.nickname && <span className="nickname">"{character.nickname}"</span>}
            <div className="role">{character.role}</div>
            {character.description && <p className="description">{character.description}</p>}
          </div>

          {/* Tabs */}
          <div className="tabs">
            <button
              className={activeTab === 'overview' ? 'active' : ''}
              onClick={() => setActiveTab('overview')}
            >
              Overview
            </button>
            <button
              className={activeTab === 'voice-modes' ? 'active' : ''}
              onClick={() => setActiveTab('voice-modes')}
            >
              Voice Modes ({character.voice_modes.length})
            </button>
            <button
              className={activeTab === 'system-prompt' ? 'active' : ''}
              onClick={() => setActiveTab('system-prompt')}
            >
              System Prompt
            </button>
            {character.tool_instructions && (
              <button
                className={activeTab === 'tool-instructions' ? 'active' : ''}
                onClick={() => setActiveTab('tool-instructions')}
              >
                Tool Instructions
              </button>
            )}
          </div>

          {/* Tab Content */}
          <div className="tab-content">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <div className="overview-tab">
                <section className="personality-section">
                  <h3>Core Personality</h3>
                  <ul>
                    {character.personality.core_traits.map((trait, i) => (
                      <li key={i}>{trait}</li>
                    ))}
                  </ul>
                </section>

                <section className="speech-patterns-section">
                  <h3>Speech Patterns</h3>
                  <ul>
                    {character.personality.speech_patterns.map((pattern, i) => (
                      <li key={i}>{pattern}</li>
                    ))}
                  </ul>
                </section>

                {character.personality.mannerisms && character.personality.mannerisms.length > 0 && (
                  <section className="mannerisms-section">
                    <h3>Mannerisms</h3>
                    <ul>
                      {character.personality.mannerisms.map((mannerism, i) => (
                        <li key={i}>{mannerism}</li>
                      ))}
                    </ul>
                  </section>
                )}

                <section className="capabilities-section">
                  <h3>Capabilities</h3>
                  <ul>
                    {character.capabilities.map((capability, i) => (
                      <li key={i}>{capability}</li>
                    ))}
                  </ul>
                </section>

                {character.story_arc && (
                  <section className="story-arc-section">
                    <h3>Story Arc (Chapter 1)</h3>
                    {character.story_arc.chapter_1 && <p>{character.story_arc.chapter_1}</p>}
                    {character.story_arc.internal_conflict && (
                      <div className="conflict">
                        <strong>Internal Conflict:</strong> {character.story_arc.internal_conflict}
                      </div>
                    )}
                    {character.story_arc.coping_mechanism && (
                      <div className="coping">
                        <strong>Coping Mechanism:</strong> {character.story_arc.coping_mechanism}
                      </div>
                    )}
                  </section>
                )}
              </div>
            )}

            {/* Voice Modes Tab */}
            {activeTab === 'voice-modes' && (
              <div className="voice-modes-tab">
                <div className="voice-mode-tester">
                  <h3>Test Voice Mode Selection</h3>
                  <div className="test-input-group">
                    <input
                      type="text"
                      placeholder="Enter user input to test..."
                      value={testInput}
                      onChange={(e) => setTestInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleTestVoiceMode()}
                    />
                    <button onClick={handleTestVoiceMode} disabled={!testInput.trim()}>
                      Test
                    </button>
                  </div>

                  {testResult && (
                    <div className="test-result">
                      <div className="result-header">
                        <strong>Selected Mode: {testResult.mode.name}</strong>
                        <span
                          className="confidence"
                          style={{ color: getConfidenceColor(testResult.confidence) }}
                        >
                          {(testResult.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                      {testResult.reasoning && (
                        <div className="reasoning">{testResult.reasoning}</div>
                      )}
                    </div>
                  )}
                </div>

                <div className="voice-modes-list">
                  {voiceModes.map((mode: VoiceMode) => (
                    <div key={mode.id} className="voice-mode-card">
                      <h4>{mode.name}</h4>
                      <div className="response-style">{mode.response_style}</div>

                      <div className="triggers">
                        <strong>Triggers:</strong>
                        <ul>
                          {mode.triggers.slice(0, 5).map((trigger, i) => (
                            <li key={i}>{trigger}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="characteristics">
                        <strong>Characteristics:</strong>
                        <ul>
                          {mode.characteristics.map((char, i) => (
                            <li key={i}>{char}</li>
                          ))}
                        </ul>
                      </div>

                      <div className="examples">
                        <strong>Example Phrases:</strong>
                        <ul>
                          {mode.example_phrases.slice(0, 3).map((example, i) => (
                            <li key={i} className="example-phrase">"{example}"</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* System Prompt Tab */}
            {activeTab === 'system-prompt' && (
              <div className="system-prompt-tab">
                <div className="prompt-controls">
                  <div className="control-group">
                    <label>Voice Mode:</label>
                    <select
                      value={selectedVoiceMode || ''}
                      onChange={(e) => setSelectedVoiceMode(e.target.value || null)}
                    >
                      <option value="">All modes (default)</option>
                      {character.voice_modes.map((mode) => (
                        <option key={mode.id} value={mode.id}>
                          {mode.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="control-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={showPromptBreakdown}
                        onChange={(e) => setShowPromptBreakdown(e.target.checked)}
                      />
                      Show token breakdown
                    </label>
                  </div>
                </div>

                {promptLoading ? (
                  <div className="loading">Loading system prompt...</div>
                ) : systemPrompt ? (
                  <>
                    <div className="prompt-stats">
                      <span className="token-count">
                        {formatTokenCount(systemPrompt.token_estimate)} tokens
                      </span>
                      <span className="character-name">{systemPrompt.character_name}</span>
                    </div>

                    {showPromptBreakdown && promptBreakdown && (
                      <div className="prompt-breakdown">
                        <h4>Token Breakdown by Section</h4>
                        {Object.entries(promptBreakdown.sections).map(([section, data]) => (
                          <div key={section} className="breakdown-section">
                            <div className="section-header">
                              <span className="section-name">{section.replace('_', ' ')}</span>
                              <span className="section-tokens">
                                {formatTokenCount(data.token_estimate)} tokens
                              </span>
                            </div>
                          </div>
                        ))}
                        <div className="breakdown-total">
                          <strong>Total:</strong> {formatTokenCount(promptBreakdown.total_token_estimate)} tokens
                        </div>
                      </div>
                    )}

                    <div className="prompt-display">
                      <pre>{systemPrompt.prompt}</pre>
                    </div>
                  </>
                ) : null}
              </div>
            )}

            {/* Tool Instructions Tab */}
            {activeTab === 'tool-instructions' && (
              <div className="tool-instructions-tab">
                {Object.entries(toolInstructions).map(([toolName, instructions]: [string, any]) => (
                  <div key={toolName} className="tool-instruction-card">
                    <h3>{toolName}</h3>

                    {instructions.general_guidance && (
                      <div className="guidance">
                        <p>{instructions.general_guidance}</p>
                      </div>
                    )}

                    {instructions.when_to_use && (
                      <div className="when-to-use">
                        <h4>When to use:</h4>
                        <ul>
                          {instructions.when_to_use.map((condition: string, i: number) => (
                            <li key={i}>{condition}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {instructions.when_NOT_to_use && (
                      <div className="when-not-to-use">
                        <h4>When NOT to use:</h4>
                        <ul>
                          {instructions.when_NOT_to_use.map((condition: string, i: number) => (
                            <li key={i}>{condition}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {instructions.importance_guidelines && (
                      <div className="importance-guidelines">
                        <h4>Importance Ratings:</h4>
                        <ul>
                          {Object.entries(instructions.importance_guidelines).map(([level, desc]: [string, any]) => (
                            <li key={level}>
                              <strong>{level}:</strong> {desc}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {instructions.examples && instructions.examples.length > 0 && (
                      <div className="examples">
                        <h4>Examples:</h4>
                        {instructions.examples.slice(0, 3).map((example: any, i: number) => (
                          <div key={i} className="example">
                            <div className="example-user">User: "{example.user_says}"</div>
                            <div className="example-action">Action: {example.action}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
