"""
WebSocket endpoint for real-time communication
Phase 2: LLM integration via ConversationManager
"""
import json
import uuid
from typing import Dict
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

from models.message import WebSocketMessage, UserMessage, AssistantResponse
from core.conversation_manager import ConversationManager
from core.story_engine import StoryEngine
from core.tool_system import ToolSystem
from core.memory_manager import MemoryManager
from integrations.tts_integration import create_tts_provider
from tools.timer_tool import TimerTool
from tools.device_tool import DeviceTool
from tools.memory_tool import MemoryTool
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Memory Manager (Phase 7)
data_dir = Path(__file__).parent.parent.parent.parent / "data"
memory_manager = MemoryManager(data_dir=str(data_dir))
logger.info(f"Memory Manager initialized (data_dir: {data_dir})")

# Initialize Tool System and register tools
tool_system = ToolSystem()
tool_system.register_tool(TimerTool())
tool_system.register_tool(DeviceTool())
tool_system.register_tool(MemoryTool())

logger.info(f"Registered tools: {tool_system.list_tools()}")

# Initialize Story Engine with correct path (relative to project root)
story_dir = Path(__file__).parent.parent.parent.parent / "story"
story_engine = StoryEngine(story_dir=str(story_dir), memory_manager=memory_manager)

# Initialize TTS Provider (optional - only if ElevenLabs is configured)
tts_provider = None
try:
    if os.getenv("ELEVENLABS_API_KEY") and os.getenv("ELEVENLABS_VOICE_ID"):
        tts_provider = create_tts_provider("elevenlabs")
        logger.info("TTS provider initialized (ElevenLabs)")
    else:
        logger.info("TTS provider disabled (no API keys configured)")
except Exception as e:
    logger.warning(f"Failed to initialize TTS provider: {str(e)}")


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"✅ WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"❌ WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: WebSocketMessage):
        """Send a message to a specific connection"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message.model_dump(mode='json'))

    async def send_error(self, session_id: str, error: str):
        """Send an error message"""
        message = WebSocketMessage(
            type="error",
            data={"error": error}
        )
        await self.send_message(session_id, message)


# Global connection manager and conversation manager
manager = ConnectionManager()
conversation_manager = ConversationManager(
    tool_system=tool_system,
    story_engine=story_engine,
    tts_provider=tts_provider,
    memory_manager=memory_manager
)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time conversation
    Phase 1: Echo functionality for testing
    """
    session_id = str(uuid.uuid4())

    await manager.connect(websocket, session_id)

    # Send connection success message
    await manager.send_message(
        session_id,
        WebSocketMessage(
            type="status",
            data={
                "status": "connected",
                "session_id": session_id,
                "message": "Connected to Aperture Assist"
            }
        )
    )

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_text()

            try:
                # Parse incoming message
                message_data = json.loads(data)

                # Handle user messages with ConversationManager
                if message_data.get("type") == "user_message":
                    user_text = message_data.get("data", {}).get("text", "")
                    input_mode = message_data.get("data", {}).get("input_mode", "chat")  # "voice" or "chat"
                    user_id = message_data.get("data", {}).get("user_id", "user_justin")  # Get user_id from message

                    logger.info(f"📨 Received from {session_id} (user: {user_id}): {user_text} (mode: {input_mode})")

                    # Send typing indicator
                    await manager.send_message(
                        session_id,
                        WebSocketMessage(
                            type="status",
                            data={"status": "thinking"}
                        )
                    )

                    # Get response from ConversationManager (with LLM)
                    result = await conversation_manager.handle_user_message(
                        session_id=session_id,
                        user_id=user_id,
                        user_message=user_text,
                        input_mode=input_mode
                    )

                    # Build assistant response
                    metadata = result.get("metadata", {})
                    response = AssistantResponse(
                        text=result["text"],
                        audio_url=metadata.get("audio_url"),
                        character="delilah",
                        metadata=metadata
                    )

                    # Send primary (Delilah) response
                    await manager.send_message(
                        session_id,
                        WebSocketMessage(
                            type="assistant_response",
                            data=response.model_dump(mode='json')
                        )
                    )

                    logger.info(
                        f"📤 Sent to {session_id}: {response.text[:50]}... "
                        f"(tokens: {result['metadata'].get('tokens_used', 0)})"
                    )

                    # Send secondary character response as a separate message if present
                    coordination = result.get("coordination")
                    if coordination:
                        secondary_response = AssistantResponse(
                            text=coordination["text"],
                            character=coordination["character"],
                            metadata={}
                        )
                        await manager.send_message(
                            session_id,
                            WebSocketMessage(
                                type="assistant_response",
                                data=secondary_response.model_dump(mode='json')
                            )
                        )
                        logger.info(
                            f"📤 Sent coordination from {coordination['character']} "
                            f"to {session_id}: {coordination['text'][:50]}..."
                        )

            except json.JSONDecodeError:
                await manager.send_error(session_id, "Invalid JSON format")
            except Exception as e:
                await manager.send_error(session_id, f"Error processing message: {str(e)}")

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"❌ WebSocket error for {session_id}: {str(e)}")
        manager.disconnect(session_id)
