"""
WebSocket endpoint for real-time communication
Phase 1: Basic echo functionality
"""
import json
import uuid
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from datetime import datetime

try:
    from ..models.message import WebSocketMessage, UserMessage, AssistantResponse
except ImportError:
    from models.message import WebSocketMessage, UserMessage, AssistantResponse

router = APIRouter()


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


# Global connection manager
manager = ConnectionManager()


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

                # For Phase 1, just echo back the message
                if message_data.get("type") == "user_message":
                    user_text = message_data.get("data", {}).get("text", "")

                    print(f"📨 Received from {session_id}: {user_text}")

                    # Echo response (will be replaced with LLM in Phase 2)
                    response = AssistantResponse(
                        text=f"Echo: {user_text}",
                        character="delilah",
                        metadata={
                            "phase": "1",
                            "mode": "echo"
                        }
                    )

                    # Send response
                    await manager.send_message(
                        session_id,
                        WebSocketMessage(
                            type="assistant_response",
                            data=response.model_dump(mode='json')
                        )
                    )

                    print(f"📤 Sent to {session_id}: {response.text}")

            except json.JSONDecodeError:
                await manager.send_error(session_id, "Invalid JSON format")
            except Exception as e:
                await manager.send_error(session_id, f"Error processing message: {str(e)}")

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        print(f"❌ WebSocket error for {session_id}: {str(e)}")
        manager.disconnect(session_id)
