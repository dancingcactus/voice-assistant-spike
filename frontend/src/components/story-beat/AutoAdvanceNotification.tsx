/**
 * Auto-Advance Notification Component
 *
 * Displays a sticky banner when auto-advance beats are ready for delivery.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient, type AutoAdvanceNotification as AutoAdvanceNotificationType } from '../../services/api';
import './AutoAdvanceNotification.css';

interface AutoAdvanceNotificationProps {
  userId: string;
  beats: AutoAdvanceNotificationType[];
}

export function AutoAdvanceNotification({ userId, beats }: AutoAdvanceNotificationProps) {
  const queryClient = useQueryClient();

  // Deliver beat mutation
  const deliverBeatMutation = useMutation({
    mutationFn: (beatId: string) => apiClient.deliverAutoAdvanceBeat(userId, beatId),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['autoAdvanceReady', userId] });
      queryClient.invalidateQueries({ queryKey: ['beats'] });
      queryClient.invalidateQueries({ queryKey: ['storyProgress', userId] });
      queryClient.invalidateQueries({ queryKey: ['progress', userId] });
    },
  });

  const handleDeliver = (beat: AutoAdvanceNotificationType) => {
    if (confirm(`Continue story with "${beat.name}"?`)) {
      deliverBeatMutation.mutate(beat.beat_id);
    }
  };

  if (beats.length === 0) {
    return null;
  }

  // Show the first ready beat
  const beat = beats[0];

  return (
    <div className="auto-advance-notification">
      <div className="notification-header">
        <span className="notification-icon">📖</span>
        <h3>Story Update Available</h3>
      </div>
      <div className="notification-content">
        <h4>{beat.name}</h4>
        <p className="content-preview">
          {beat.content.substring(0, 150)}
          {beat.content.length > 150 ? '...' : ''}
        </p>
      </div>
      <div className="notification-actions">
        <button
          className="btn-primary"
          onClick={() => handleDeliver(beat)}
          disabled={deliverBeatMutation.isPending}
        >
          {deliverBeatMutation.isPending ? 'Delivering...' : 'Continue Story'}
        </button>
        {beats.length > 1 && (
          <span className="more-beats">+{beats.length - 1} more</span>
        )}
      </div>
    </div>
  );
}
