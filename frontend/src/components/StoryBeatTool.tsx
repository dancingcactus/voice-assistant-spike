/**
 * Story Beat Tool Component
 *
 * Provides visualization and testing interface for story beats and chapters.
 */

import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import mermaid from 'mermaid';
import { apiClient, type ChapterSummary, type BeatSummary, type BeatDetail, type ChapterProgressSummary } from '../services/api';
import './StoryBeatTool.css';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    darkMode: true,
    background: '#1a1a1a',
    primaryColor: '#4a90e2',
    secondaryColor: '#6c757d',
    tertiaryColor: '#28a745',
  }
});

interface StoryBeatToolProps {
  userId: string;
}

export function StoryBeatTool({ userId }: StoryBeatToolProps) {
  const [selectedChapter, setSelectedChapter] = useState<number | null>(null);
  const [selectedBeat, setSelectedBeat] = useState<BeatSummary | null>(null);
  const [showBeatDetail, setShowBeatDetail] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const diagramRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();

  // Fetch chapters
  const { data: chapters, isLoading: chaptersLoading } = useQuery({
    queryKey: ['chapters', userId],
    queryFn: () => apiClient.listChapters(userId),
  });

  // Fetch user progress
  const { data: progress } = useQuery({
    queryKey: ['progress', userId],
    queryFn: () => apiClient.getUserStoryProgress(userId),
  });

  // Set initial chapter selection
  useEffect(() => {
    if (chapters && !selectedChapter) {
      const currentChapter = chapters.find(ch => ch.is_current);
      if (currentChapter) {
        setSelectedChapter(currentChapter.id);
      }
    }
  }, [chapters, selectedChapter]);

  // Fetch beats for selected chapter
  const { data: beats, isLoading: beatsLoading } = useQuery({
    queryKey: ['beats', selectedChapter, userId],
    queryFn: () => selectedChapter ? apiClient.listChapterBeats(selectedChapter, userId) : Promise.resolve([]),
    enabled: selectedChapter !== null,
  });

  // Fetch beat detail
  const { data: beatDetail } = useQuery({
    queryKey: ['beatDetail', selectedChapter, selectedBeat?.id, userId],
    queryFn: () => selectedChapter && selectedBeat
      ? apiClient.getBeatDetail(selectedChapter, selectedBeat.id, userId)
      : Promise.resolve(null),
    enabled: selectedChapter !== null && selectedBeat !== null && showBeatDetail,
  });

  // Fetch diagram
  const { data: diagram } = useQuery({
    queryKey: ['diagram', selectedChapter],
    queryFn: () => selectedChapter ? apiClient.getChapterDiagram(selectedChapter) : Promise.resolve(null),
    enabled: selectedChapter !== null,
  });

  // Render diagram
  useEffect(() => {
    if (diagram && diagramRef.current) {
      const renderDiagram = async () => {
        try {
          diagramRef.current!.innerHTML = '';
          const { svg } = await mermaid.render('chapter-diagram', diagram.diagram);
          diagramRef.current!.innerHTML = svg;
        } catch (error) {
          console.error('Failed to render diagram:', error);
          diagramRef.current!.innerHTML = '<p style="color: #e74c3c;">Failed to render diagram</p>';
        }
      };
      renderDiagram();
    }
  }, [diagram]);

  // Trigger beat mutation
  const triggerBeatMutation = useMutation({
    mutationFn: ({ beatId, variant, stage }: { beatId: string; variant: string; stage?: number }) =>
      apiClient.triggerBeat(userId, beatId, variant, stage),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['beats', selectedChapter, userId] });
      queryClient.invalidateQueries({ queryKey: ['progress', userId] });
      queryClient.invalidateQueries({ queryKey: ['chapters', userId] });
      setShowBeatDetail(false);
      setSelectedBeat(null);
    },
  });

  const handleTriggerBeat = (beatId: string, variant: string, stage?: number) => {
    if (confirm(`Trigger beat "${beatId}" with variant "${variant}"${stage ? ` (stage ${stage})` : ''}?`)) {
      triggerBeatMutation.mutate({ beatId, variant, stage });
    }
  };

  // Filter beats
  const filteredBeats = beats?.filter(beat => {
    if (filterStatus === 'all') return true;
    return beat.status === filterStatus;
  }) || [];

  if (chaptersLoading) {
    return <div className="story-beat-tool"><p>Loading...</p></div>;
  }

  return (
    <div className="story-beat-tool">
      <div className="tool-header">
        <h2>Story Beat Tool</h2>
        {progress && (
          <div className="progress-summary">
            <span>Chapter {progress.current_chapter}</span>
            <span>{progress.beats_delivered}/{progress.beats_total} beats</span>
            <span>{progress.interaction_count} interactions</span>
          </div>
        )}
      </div>

      <div className="tool-layout">
        {/* Left sidebar: Chapter navigation */}
        <div className="chapter-nav">
          <h3>Chapters</h3>
          {chapters?.map(chapter => (
            <button
              key={chapter.id}
              className={`chapter-btn ${selectedChapter === chapter.id ? 'active' : ''} ${chapter.is_locked ? 'locked' : ''} ${chapter.is_completed ? 'completed' : ''}`}
              onClick={() => setSelectedChapter(chapter.id)}
              disabled={chapter.is_locked}
            >
              <span className="chapter-number">{chapter.id}</span>
              <span className="chapter-title">{chapter.title}</span>
              {chapter.is_current && <span className="badge current">Current</span>}
              {chapter.is_completed && <span className="badge completed">✓</span>}
              {chapter.is_locked && <span className="badge locked">🔒</span>}
            </button>
          ))}
        </div>

        {/* Main content */}
        <div className="main-content">
          {/* Beat list */}
          <div className="beats-section">
            <div className="beats-header">
              <h3>Story Beats</h3>
              <div className="beat-filters">
                <button
                  className={filterStatus === 'all' ? 'active' : ''}
                  onClick={() => setFilterStatus('all')}
                >
                  All ({beats?.length || 0})
                </button>
                <button
                  className={filterStatus === 'delivered' ? 'active' : ''}
                  onClick={() => setFilterStatus('delivered')}
                >
                  Delivered ({beats?.filter(b => b.status === 'delivered').length || 0})
                </button>
                <button
                  className={filterStatus === 'ready' ? 'active' : ''}
                  onClick={() => setFilterStatus('ready')}
                >
                  Ready ({beats?.filter(b => b.status === 'ready').length || 0})
                </button>
                <button
                  className={filterStatus === 'locked' ? 'active' : ''}
                  onClick={() => setFilterStatus('locked')}
                >
                  Locked ({beats?.filter(b => b.status === 'locked').length || 0})
                </button>
              </div>
            </div>

            {beatsLoading ? (
              <p>Loading beats...</p>
            ) : (
              <div className="beats-list">
                {filteredBeats.map(beat => (
                  <div
                    key={beat.id}
                    className={`beat-card ${beat.status}`}
                    onClick={() => {
                      setSelectedBeat(beat);
                      setShowBeatDetail(true);
                    }}
                  >
                    <div className="beat-header">
                      <h4>{beat.id.replace(/_/g, ' ')}</h4>
                      <div className="beat-badges">
                        {beat.required && <span className="badge required">Required</span>}
                        <span className={`badge status ${beat.status}`}>{beat.status}</span>
                        <span className="badge type">{beat.type}</span>
                      </div>
                    </div>
                    {beat.delivery_info && (
                      <div className="delivery-info">
                        <span>Delivered: {new Date(beat.delivery_info.timestamp || '').toLocaleString()}</span>
                        <span>Variant: {beat.delivery_info.variant}</span>
                        {beat.delivery_info.stage && <span>Stage: {beat.delivery_info.stage}</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Chapter diagram */}
          <div className="diagram-section">
            <h3>Chapter Flow</h3>
            <div ref={diagramRef} className="diagram-container"></div>
          </div>
        </div>
      </div>

      {/* Beat detail modal */}
      {showBeatDetail && selectedBeat && beatDetail && (
        <div className="modal-overlay" onClick={() => setShowBeatDetail(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{beatDetail.id.replace(/_/g, ' ')}</h2>
              <button className="close-btn" onClick={() => setShowBeatDetail(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="beat-meta">
                <span><strong>Type:</strong> {beatDetail.type}</span>
                <span><strong>Priority:</strong> {beatDetail.priority}</span>
                <span><strong>Required:</strong> {beatDetail.required ? 'Yes' : 'No'}</span>
                <span><strong>Status:</strong> <span className={`badge ${selectedBeat.status}`}>{selectedBeat.status}</span></span>
              </div>

              <div className="beat-section">
                <h3>Trigger Conditions</h3>
                <pre>{JSON.stringify(beatDetail.trigger, null, 2)}</pre>
              </div>

              {beatDetail.conditions && (
                <div className="beat-section">
                  <h3>Additional Conditions</h3>
                  <pre>{JSON.stringify(beatDetail.conditions, null, 2)}</pre>
                </div>
              )}

              {beatDetail.variants && (
                <div className="beat-section">
                  <h3>Variants</h3>
                  {Object.entries(beatDetail.variants).map(([variant, data]: [string, any]) => (
                    <div key={variant} className="variant-card">
                      <h4>{variant}</h4>
                      <p><strong>Delivery:</strong> {data.delivery}</p>
                      <p className="variant-content">{data.content}</p>
                      <button
                        onClick={() => handleTriggerBeat(beatDetail.id, variant)}
                        disabled={triggerBeatMutation.isPending}
                        className="trigger-btn"
                      >
                        Trigger {variant}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {beatDetail.stages && (
                <div className="beat-section">
                  <h3>Progression Stages</h3>
                  {beatDetail.stages.map((stage: any) => (
                    <div key={stage.stage} className="stage-card">
                      <h4>Stage {stage.stage}</h4>
                      {Object.entries(stage.variants).map(([variant, data]: [string, any]) => (
                        <div key={variant} className="variant-card">
                          <h5>{variant}</h5>
                          <p><strong>Delivery:</strong> {data.delivery}</p>
                          <p className="variant-content">{data.content}</p>
                          <button
                            onClick={() => handleTriggerBeat(beatDetail.id, variant, stage.stage)}
                            disabled={triggerBeatMutation.isPending}
                            className="trigger-btn"
                          >
                            Trigger stage {stage.stage} - {variant}
                          </button>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}

              {beatDetail.user_status.delivered && (
                <div className="beat-section delivered-status">
                  <h3>Delivery Status</h3>
                  <p><strong>Delivered:</strong> {new Date(beatDetail.user_status.timestamp || '').toLocaleString()}</p>
                  <p><strong>Variant:</strong> {beatDetail.user_status.variant}</p>
                  {beatDetail.user_status.stage && <p><strong>Stage:</strong> {beatDetail.user_status.stage}</p>}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
