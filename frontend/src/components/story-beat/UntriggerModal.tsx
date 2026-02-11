/**
 * Untrigger Modal Component
 *
 * Shows impact preview and confirmation before untriggering a beat.
 */

import { useState, useEffect } from 'react';
import { apiClient, type UntriggerBeatResponse } from '../../services/api';
import './UntriggerModal.css';

interface UntriggerModalProps {
  userId: string;
  beatId: string;
  beatName: string;
  stage?: number;
  onClose: () => void;
  onSuccess: () => void;
}

export function UntriggerModal({
  userId,
  beatId,
  beatName,
  stage,
  onClose,
  onSuccess
}: UntriggerModalProps) {
  const [dryRunResult, setDryRunResult] = useState<UntriggerBeatResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUntriggering, setIsUntriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch dry-run preview on mount
  useEffect(() => {
    const fetchDryRun = async () => {
      try {
        setIsLoading(true);
        const result = await apiClient.untriggerBeat(userId, beatId, true, stage);
        setDryRunResult(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch untrigger preview');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDryRun();
  }, [userId, beatId, stage]);

  const handleUntrigger = async () => {
    try {
      setIsUntriggering(true);
      await apiClient.untriggerBeat(userId, beatId, false, stage);
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to untrigger beat');
    } finally {
      setIsUntriggering(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="untrigger-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Untrigger '{beatName}'?</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {isLoading ? (
            <div className="loading">
              <p>Analyzing dependencies...</p>
            </div>
          ) : error ? (
            <div className="error">
              <p>{error}</p>
            </div>
          ) : dryRunResult ? (
            <>
              <div className="explanation">
                <p>{dryRunResult.explanation}</p>
              </div>

              {dryRunResult.dependencies_affected.length > 0 && (
                <div className="dependencies-section">
                  <h3>⚠️ This will also untrigger:</h3>
                  <ul className="dependencies-list">
                    {dryRunResult.dependencies_affected.map(depBeatId => (
                      <li key={depBeatId}>
                        <span className="beat-id">{depBeatId.replace(/_/g, ' ')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : null}
        </div>

        <div className="modal-footer">
          <button
            className="btn btn-secondary"
            onClick={onClose}
            disabled={isUntriggering}
          >
            Cancel
          </button>
          <button
            className="btn btn-danger"
            onClick={handleUntrigger}
            disabled={isLoading || isUntriggering || !dryRunResult}
          >
            {isUntriggering ? 'Untriggering...' : 'Untrigger'}
          </button>
        </div>
      </div>
    </div>
  );
}
