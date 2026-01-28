"""Device Controller - manages virtual and real smart home devices."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """Types of devices supported."""
    LIGHT = "light"
    THERMOSTAT = "thermostat"
    SWITCH = "switch"
    DOOR = "door"
    FAN = "fan"


class DeviceCapability(str, Enum):
    """Capabilities that devices can have."""
    ON_OFF = "on_off"
    BRIGHTNESS = "brightness"
    TEMPERATURE = "temperature"
    SPEED = "speed"
    POSITION = "position"  # For doors, shades, etc.


class Device(BaseModel):
    """Represents a smart home device."""
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    type: DeviceType = Field(..., description="Type of device")
    capabilities: List[DeviceCapability] = Field(..., description="Device capabilities")
    state: Dict[str, Any] = Field(default_factory=dict, description="Current device state")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")

    def supports_capability(self, capability: DeviceCapability) -> bool:
        """Check if device supports a capability."""
        return capability in self.capabilities


class DeviceController(ABC):
    """Abstract base class for device controllers."""

    @abstractmethod
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        pass

    @abstractmethod
    def list_devices(self, device_type: Optional[DeviceType] = None) -> List[Device]:
        """List all devices, optionally filtered by type."""
        pass

    @abstractmethod
    def get_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a device."""
        pass

    @abstractmethod
    async def set_state(
        self,
        device_id: str,
        state_updates: Dict[str, Any]
    ) -> bool:
        """
        Update device state.

        Args:
            device_id: Device to update
            state_updates: State changes to apply

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def find_device_by_name(self, name: str) -> Optional[Device]:
        """Find a device by name or alias (fuzzy matching)."""
        pass


class VirtualDeviceController(DeviceController):
    """
    Virtual device controller for testing and development.

    Maintains virtual devices in memory without actual hardware control.
    """

    def __init__(self):
        """Initialize virtual device controller with test devices."""
        self.devices: Dict[str, Device] = {}
        self._initialize_devices()
        logger.info(f"Virtual Device Controller initialized with {len(self.devices)} devices")

    def _initialize_devices(self):
        """Create virtual test devices from PRD."""
        test_devices = [
            Device(
                id="kitchen_light",
                name="Kitchen Light",
                type=DeviceType.LIGHT,
                capabilities=[DeviceCapability.ON_OFF, DeviceCapability.BRIGHTNESS],
                state={"on": False, "brightness": 100},
                aliases=["kitchen", "kitchen lights"]
            ),
            Device(
                id="living_room_light",
                name="Living Room Light",
                type=DeviceType.LIGHT,
                capabilities=[DeviceCapability.ON_OFF, DeviceCapability.BRIGHTNESS],
                state={"on": False, "brightness": 100},
                aliases=["living room", "living room lights"]
            ),
            Device(
                id="bedroom_light",
                name="Bedroom Light",
                type=DeviceType.LIGHT,
                capabilities=[DeviceCapability.ON_OFF],
                state={"on": False},
                aliases=["bedroom", "bedroom lights"]
            ),
            Device(
                id="porch_light",
                name="Porch Light",
                type=DeviceType.LIGHT,
                capabilities=[DeviceCapability.ON_OFF],
                state={"on": False},
                aliases=["porch", "porch lights", "front porch"]
            ),
            Device(
                id="main_floor_thermostat",
                name="Main Floor Thermostat",
                type=DeviceType.THERMOSTAT,
                capabilities=[DeviceCapability.TEMPERATURE],
                state={
                    "mode": "heat",
                    "target_temperature": 70,
                    "current_temperature": 68,
                    "min_temp": 60,
                    "max_temp": 85
                },
                aliases=["main floor", "downstairs thermostat", "first floor thermostat"]
            ),
            Device(
                id="upstairs_thermostat",
                name="Upstairs Thermostat",
                type=DeviceType.THERMOSTAT,
                capabilities=[DeviceCapability.TEMPERATURE],
                state={
                    "mode": "heat",
                    "target_temperature": 70,
                    "current_temperature": 69,
                    "min_temp": 60,
                    "max_temp": 85
                },
                aliases=["upstairs", "second floor thermostat"]
            ),
            Device(
                id="greenhouse_thermostat",
                name="Greenhouse Thermostat",
                type=DeviceType.THERMOSTAT,
                capabilities=[DeviceCapability.TEMPERATURE],
                state={
                    "mode": "heat",
                    "target_temperature": 75,
                    "current_temperature": 72,
                    "min_temp": 50,
                    "max_temp": 90
                },
                aliases=["greenhouse"]
            ),
            Device(
                id="coffee_maker",
                name="Coffee Maker",
                type=DeviceType.SWITCH,
                capabilities=[DeviceCapability.ON_OFF],
                state={"on": False},
                aliases=["coffee"]
            ),
            Device(
                id="ceiling_fan",
                name="Ceiling Fan",
                type=DeviceType.FAN,
                capabilities=[DeviceCapability.ON_OFF, DeviceCapability.SPEED],
                state={"on": False, "speed": "medium"},
                aliases=["fan", "ceiling fan"]
            ),
            Device(
                id="garage_door",
                name="Garage Door",
                type=DeviceType.DOOR,
                capabilities=[DeviceCapability.POSITION],
                state={"position": "closed"},
                aliases=["garage"]
            ),
        ]

        for device in test_devices:
            self.devices[device.id] = device

    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        return self.devices.get(device_id)

    def list_devices(self, device_type: Optional[DeviceType] = None) -> List[Device]:
        """List all devices, optionally filtered by type."""
        if device_type:
            return [d for d in self.devices.values() if d.type == device_type]
        return list(self.devices.values())

    def get_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a device."""
        device = self.get_device(device_id)
        return device.state if device else None

    async def set_state(
        self,
        device_id: str,
        state_updates: Dict[str, Any]
    ) -> bool:
        """Update device state."""
        device = self.get_device(device_id)

        if not device:
            logger.warning(f"Device not found: {device_id}")
            return False

        # Validate state updates based on device capabilities
        for key, value in state_updates.items():
            if key == "on" and not device.supports_capability(DeviceCapability.ON_OFF):
                logger.warning(f"Device {device_id} does not support on/off")
                return False

            if key == "brightness":
                if not device.supports_capability(DeviceCapability.BRIGHTNESS):
                    logger.warning(f"Device {device_id} does not support brightness")
                    return False
                # Validate brightness range
                if not (0 <= value <= 100):
                    logger.warning(f"Invalid brightness value: {value}")
                    return False

            if key == "target_temperature":
                if not device.supports_capability(DeviceCapability.TEMPERATURE):
                    logger.warning(f"Device {device_id} does not support temperature")
                    return False
                # Validate temperature range
                min_temp = device.state.get("min_temp", 50)
                max_temp = device.state.get("max_temp", 90)
                if not (min_temp <= value <= max_temp):
                    logger.warning(
                        f"Temperature {value} out of range [{min_temp}-{max_temp}]"
                    )
                    return False

        # Apply updates
        device.state.update(state_updates)
        logger.info(f"Updated {device_id} state: {state_updates}")
        return True

    def find_device_by_name(self, name: str) -> Optional[Device]:
        """Find a device by name or alias (fuzzy matching)."""
        name_lower = name.lower()

        # Exact match on name
        for device in self.devices.values():
            if device.name.lower() == name_lower:
                return device

        # Exact match on alias
        for device in self.devices.values():
            if name_lower in [alias.lower() for alias in device.aliases]:
                return device

        # Partial match on name
        for device in self.devices.values():
            if name_lower in device.name.lower():
                return device

        # Partial match on alias
        for device in self.devices.values():
            for alias in device.aliases:
                if name_lower in alias.lower():
                    return device

        return None
