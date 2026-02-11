/**
 * DiagramLegend Component
 *
 * Displays a legend explaining the color coding used in story beat flow diagrams.
 * Shows all possible beat statuses with their corresponding colors and meanings.
 */

import React from 'react';
import './DiagramLegend.css';

export interface LegendItem {
  status: string;
  color: string;
  emoji: string;
  description: string;
}

const LEGEND_ITEMS: LegendItem[] = [
  {
    status: 'Completed',
    color: '#10b981', // green
    emoji: '🟢',
    description: 'Beat has been delivered',
  },
  {
    status: 'In Progress',
    color: '#f59e0b', // yellow/amber
    emoji: '🟡',
    description: 'Beat is ready and can be triggered',
  },
  {
    status: 'Not Started',
    color: '#3b82f6', // blue
    emoji: '🔵',
    description: 'Beat has not yet been triggered',
  },
  {
    status: 'Locked',
    color: '#6b7280', // gray
    emoji: '⚫',
    description: 'Prerequisites not met',
  },
];

interface DiagramLegendProps {
  /**
   * Whether to show the legend in compact mode (horizontal layout)
   * @default false
   */
  compact?: boolean;

  /**
   * Custom CSS class name
   */
  className?: string;
}

export const DiagramLegend: React.FC<DiagramLegendProps> = ({
  compact = false,
  className = '',
}) => {
  return (
    <div className={`diagram-legend ${compact ? 'diagram-legend--compact' : ''} ${className}`}>
      <h4 className="diagram-legend__title">Status Legend</h4>
      <div className="diagram-legend__items">
        {LEGEND_ITEMS.map((item) => (
          <div key={item.status} className="diagram-legend__item">
            <span
              className="diagram-legend__color-box"
              style={{ backgroundColor: item.color }}
              aria-label={item.status}
            />
            <span className="diagram-legend__emoji" aria-hidden="true">
              {item.emoji}
            </span>
            <div className="diagram-legend__text">
              <span className="diagram-legend__status">{item.status}</span>
              {!compact && (
                <span className="diagram-legend__description">{item.description}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DiagramLegend;
