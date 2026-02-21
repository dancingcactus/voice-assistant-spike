/**
 * Tools View - Container for all tool tabs (Lists, Memories, Timers, Devices)
 */

import { useState } from 'react';
import { apiClient } from '../../services/api';
import { ListsTool } from './Lists/ListsTool';
import { TimersTool } from './Timers/TimersTool';
import { DevicesTool } from './Devices/DevicesTool';
import { MemoryTool } from '../MemoryTool';
import './ToolsView.css';

interface ToolsViewProps {
  userId: string;
}

export function ToolsView({ userId }: ToolsViewProps) {
  const [currentTool, setCurrentTool] = useState<'lists' | 'memories' | 'timers' | 'devices'>('lists');

  return (
    <div className="tools-view">
      <div className="tools-header">
        <h2>🛠️ Tools</h2>
        <nav className="tools-nav">
          <button
            className={currentTool === 'lists' ? 'active' : ''}
            onClick={() => setCurrentTool('lists')}
          >
            📋 Lists
          </button>
          <button
            className={currentTool === 'memories' ? 'active' : ''}
            onClick={() => setCurrentTool('memories')}
          >
            🧠 Memories
          </button>
          <button
            className={currentTool === 'timers' ? 'active' : ''}
            onClick={() => setCurrentTool('timers')}
          >
            ⏱️ Timers
          </button>
          <button
            className={currentTool === 'devices' ? 'active' : ''}
            onClick={() => setCurrentTool('devices')}
          >
            💡 Devices
          </button>
        </nav>
      </div>

      <div className="tool-content">
        {currentTool === 'lists' && (
          <ListsTool userId={userId} apiClient={apiClient} />
        )}
        
        {currentTool === 'memories' && (
          <MemoryTool userId={userId} />
        )}
        
        {currentTool === 'timers' && (
          <TimersTool apiClient={apiClient} />
        )}
        
        {currentTool === 'devices' && (
          <DevicesTool apiClient={apiClient} />
        )}
      </div>
    </div>
  );
}
