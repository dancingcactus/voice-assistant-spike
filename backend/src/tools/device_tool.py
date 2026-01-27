"""Device Control Tool - control smart home devices."""
from typing import List, Optional
import logging

from tools.tool_base import (
    Tool,
    ToolContext,
    ToolResult,
    ToolResultStatus,
    ToolParameter
)
from integrations.device_controller import DeviceController, VirtualDeviceController

logger = logging.getLogger(__name__)


class DeviceTool(Tool):
    """Tool for controlling smart home devices."""

    def __init__(self, device_controller: Optional[DeviceController] = None):
        """
        Initialize the device tool.

        Args:
            device_controller: Device controller instance (creates virtual controller if not provided)
        """
        self.device_controller = device_controller or VirtualDeviceController()
        super().__init__()

    @property
    def name(self) -> str:
        return "control_device"

    @property
    def description(self) -> str:
        return (
            "Control smart home devices like lights, thermostats, switches, fans, and doors. "
            "Use this to turn devices on/off, set brightness, adjust temperature, or control other device features."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="device_name",
                type="string",
                description="Name of the device to control (e.g., 'kitchen light', 'thermostat', 'garage door')",
                required=True
            ),
            ToolParameter(
                name="action",
                type="string",
                description="Action to perform: 'turn_on', 'turn_off', 'set_brightness', 'set_temperature', 'open', 'close'",
                required=True,
                enum=["turn_on", "turn_off", "set_brightness", "set_temperature", "open", "close", "set_speed"]
            ),
            ToolParameter(
                name="value",
                type="number",
                description="Value for the action (brightness: 0-100, temperature: degrees F, speed: 1-3)",
                required=False
            ),
        ]

    async def execute(self, context: ToolContext, **kwargs) -> ToolResult:
        """Execute device control action."""
        device_name = kwargs.get("device_name")
        action = kwargs.get("action")

        # Find the device
        device = self.device_controller.find_device_by_name(device_name)

        if not device:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Device not found: {device_name}",
                error="DEVICE_NOT_FOUND"
            )

        # Route to appropriate handler
        if action == "turn_on":
            return await self._turn_on(device.id, device.name)
        elif action == "turn_off":
            return await self._turn_off(device.id, device.name)
        elif action == "set_brightness":
            value = kwargs.get("value")
            return await self._set_brightness(device.id, device.name, value)
        elif action == "set_temperature":
            value = kwargs.get("value")
            return await self._set_temperature(device.id, device.name, value)
        elif action == "open":
            return await self._open(device.id, device.name)
        elif action == "close":
            return await self._close(device.id, device.name)
        elif action == "set_speed":
            value = kwargs.get("value")
            return await self._set_speed(device.id, device.name, value)
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Invalid action: {action}",
                error="INVALID_ACTION"
            )

    async def _turn_on(self, device_id: str, device_name: str) -> ToolResult:
        """Turn a device on."""
        success = await self.device_controller.set_state(device_id, {"on": True})

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} turned on",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to turn on {device_name}",
                error="OPERATION_FAILED"
            )

    async def _turn_off(self, device_id: str, device_name: str) -> ToolResult:
        """Turn a device off."""
        success = await self.device_controller.set_state(device_id, {"on": False})

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} turned off",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to turn off {device_name}",
                error="OPERATION_FAILED"
            )

    async def _set_brightness(
        self,
        device_id: str,
        device_name: str,
        value: Optional[float]
    ) -> ToolResult:
        """Set device brightness."""
        if value is None:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="brightness value is required",
                error="MISSING_PARAMETER"
            )

        brightness = int(value)
        success = await self.device_controller.set_state(
            device_id,
            {"on": True, "brightness": brightness}
        )

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} set to {brightness}% brightness",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to set brightness for {device_name}",
                error="OPERATION_FAILED"
            )

    async def _set_temperature(
        self,
        device_id: str,
        device_name: str,
        value: Optional[float]
    ) -> ToolResult:
        """Set thermostat temperature."""
        if value is None:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="temperature value is required",
                error="MISSING_PARAMETER"
            )

        temp = int(value)
        success = await self.device_controller.set_state(
            device_id,
            {"target_temperature": temp}
        )

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} set to {temp}°F",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to set temperature for {device_name}",
                error="OPERATION_FAILED"
            )

    async def _open(self, device_id: str, device_name: str) -> ToolResult:
        """Open a door or similar device."""
        success = await self.device_controller.set_state(device_id, {"position": "open"})

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} opened",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to open {device_name}",
                error="OPERATION_FAILED"
            )

    async def _close(self, device_id: str, device_name: str) -> ToolResult:
        """Close a door or similar device."""
        success = await self.device_controller.set_state(device_id, {"position": "closed"})

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} closed",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to close {device_name}",
                error="OPERATION_FAILED"
            )

    async def _set_speed(
        self,
        device_id: str,
        device_name: str,
        value: Optional[float]
    ) -> ToolResult:
        """Set fan speed."""
        if value is None:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="speed value is required",
                error="MISSING_PARAMETER"
            )

        # Map numeric value to speed names
        speed_value = int(value)
        if speed_value == 1:
            speed = "low"
        elif speed_value == 2:
            speed = "medium"
        elif speed_value == 3:
            speed = "high"
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message="speed must be 1 (low), 2 (medium), or 3 (high)",
                error="INVALID_VALUE"
            )

        success = await self.device_controller.set_state(
            device_id,
            {"on": True, "speed": speed}
        )

        if success:
            return ToolResult(
                status=ToolResultStatus.SUCCESS,
                message=f"{device_name} set to {speed} speed",
                data=self.device_controller.get_state(device_id)
            )
        else:
            return ToolResult(
                status=ToolResultStatus.ERROR,
                message=f"Failed to set speed for {device_name}",
                error="OPERATION_FAILED"
            )
