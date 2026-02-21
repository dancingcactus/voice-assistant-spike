/**
 * Timers Tool - View active and completed timers
 */

import { useQuery } from '@tanstack/react-query';
import './TimersTool.css';
import { LoadingSpinner } from '../../LoadingSpinner';
import { useEffect, useState } from 'react';

interface TimerInfo {
  duration_seconds: number;
  label?: string;
  time_remaining: number;
  is_expired: boolean;
}

interface TimersStatus {
  session_id: string;
  active_timers: number;
  timers: TimerInfo[];
}

interface TimersToolProps {
  apiClient: any;
}

export function TimersTool({ apiClient }: TimersToolProps) {
  const [now, setNow] = useState(Date.now());

  // Update every second for live countdown
  useEffect(() => {
    const interval = setInterval(() => {
      setNow(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const { data: timersData, isLoading, error } = useQuery<TimersStatus[]>({
    queryKey: ['timers'],
    queryFn: () => apiClient.getTimersStatus(),
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}m ${secs}s`;
    }
    return `${secs}s`;
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading timers..." />;
  }

  if (error) {
    return <div className="error">Error loading timers: {String(error)}</div>;
  }

  const totalActive = timersData?.reduce((sum, session) => sum + session.active_timers, 0) || 0;
  const allTimers = timersData?.flatMap(session => 
    session.timers.map(timer => ({ ...timer, session_id: session.session_id }))
  ) || [];

  if (allTimers.length === 0) {
    return (
      <div className="timers-tool">
        <div className="empty-state">
          <h3>No active timers</h3>
          <p>No timers are currently running.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="timers-tool">
      <div className="timers-header">
        <h3>Timers</h3>
        <div className="timer-summary">
          <span className="stat">{totalActive} active</span>
        </div>
      </div>

      <div className="timers-container">
        {allTimers.map((timer, index) => {
          const sessionTimerKey = `${(timer as any).session_id}-${index}`;
          const isExpired = timer.is_expired;
          const progress = isExpired ? 100 : ((timer.duration_seconds - timer.time_remaining) / timer.duration_seconds) * 100;

          return (
            <div key={sessionTimerKey} className={`timer-card ${isExpired ? 'expired' : ''}`}>
              <div className="timer-info">
                <div className="timer-label">
                  {timer.label || 'Timer'}
                </div>
                <div className="timer-time">
                  {isExpired ? (
                    <span className="expired-text">Expired</span>
                  ) : (
                    <span className="remaining-time">{formatTime(timer.time_remaining)}</span>
                  )}
                </div>
                <div className="timer-duration">
                  Duration: {formatTime(timer.duration_seconds)}
                </div>
              </div>
              <div className="timer-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
