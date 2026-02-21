/**
 * Devices Tool - View device status and control
 */

import { useQuery } from '@tanstack/react-query';
import './DevicesTool.css';
import { LoadingSpinner } from '../../LoadingSpinner';

interface DeviceInfo {
  device_id: string;
  name: string;
  device_type: string;
  state: string;
  attributes: Record<string, any>;
  friendly_name?: string;
  area?: string;
}

interface DevicesStatus {
  total_devices: number;
  available_devices: number;
  unavailable_devices: number;
  devices: DeviceInfo[];
}

interface DevicesToolProps {
  apiClient: any;
}

export function DevicesTool({ apiClient }: DevicesToolProps) {
  const { data: devicesData, isLoading, error } = useQuery<DevicesStatus>({
    queryKey: ['devices'],
    queryFn: () => apiClient.getDevicesStatus(),
    refetchInterval: 5000, // Refetch every 5 seconds
  });

  if (isLoading) {
    return <LoadingSpinner text="Loading devices..." />;
  }

  if (error) {
    return <div className="error">Error loading devices: {String(error)}</div>;
  }

  if (!devicesData || devicesData.total_devices === 0) {
    return (
      <div className="devices-tool">
        <div className="empty-state">
          <h3>No devices found</h3>
          <p>No smart home devices are configured.</p>
        </div>
      </div>
    );
  }

  const getDeviceIcon = (type: string): string => {
    const icons: Record<string, string> = {
      'light': '💡',
      'switch': '🔌',
      'sensor': '📡',
      'climate': '🌡️',
      'lock': '🔒',
      'camera': '📷',
      'media_player': '📺',
    };
    return icons[type] || '🔧';
  };

  const getStateColor = (state: string): string => {
    if (state === 'on') return 'state-on';
    if (state === 'off') return 'state-off';
    if (state === 'unavailable') return 'state-unavailable';
    return 'state-unknown';
  };

  return (
    <div className="devices-tool">
      <div className="devices-header">
        <h3>Devices</h3>
        <div className="devices-summary">
          <span className="stat available">{devicesData.available_devices} available</span>
          <span className="stat-separator">/</span>
          <span className="stat total">{devicesData.total_devices} total</span>
        </div>
      </div>

      <div className="devices-stats">
        <div className="stat-card">
          <span className="stat-value">{devicesData.total_devices}</span>
          <span className="stat-label">Total Devices</span>
        </div>
        <div className="stat-card">
          <span className="stat-value available">{devicesData.available_devices}</span>
          <span className="stat-label">Available</span>
        </div>
        <div className="stat-card">
          <span className="stat-value unavailable">{devicesData.unavailable_devices}</span>
          <span className="stat-label">Unavailable</span>
        </div>
      </div>

      <div className="devices-container">
        {devicesData.devices.map((device) => (
          <div key={device.device_id} className={`device-card ${getStateColor(device.state)}`}>
            <div className="device-icon">{getDeviceIcon(device.device_type)}</div>
            <div className="device-info">
              <div className="device-name">{device.friendly_name || device.name}</div>
              <div className="device-type">{device.device_type}</div>
              {device.area && <div className="device-area">📍 {device.area}</div>}
            </div>
            <div className="device-state">
              <span className={`state-badge ${getStateColor(device.state)}`}>
                {device.state}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
