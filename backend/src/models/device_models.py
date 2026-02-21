"""
Device models for observability.

Data models for device information exposed via observability API.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DeviceInfo(BaseModel):
    """Information about a device for observability."""
    device_id: str = Field(..., description="Device identifier")
    name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type (light, switch, sensor, etc.)")
    state: str = Field(..., description="Device state (on, off, unavailable, etc.)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Device attributes (brightness, temperature, etc.)")
    friendly_name: Optional[str] = Field(None, description="User-friendly device name")
    area: Optional[str] = Field(None, description="Area/room where device is located")
    last_updated: Optional[datetime] = Field(None, description="Last time device state was updated")


class DevicesStatus(BaseModel):
    """Status of all devices."""
    total_devices: int = Field(..., description="Total number of devices")
    available_devices: int = Field(..., description="Number of available devices")
    unavailable_devices: int = Field(..., description="Number of unavailable devices")
    devices: list[DeviceInfo] = Field(default_factory=list, description="List of all devices")
