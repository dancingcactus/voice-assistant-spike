"""
Conversation Manager - Core module for handling user conversations.

Responsibilities:
- Managing conversation history
- Constructing prompts for the LLM
- Coordinating with LLM Integration
- Emitting events for other systems (Story Engine, Character System)
"""

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.message import Message, ConversationContext, LLMResponse, ToolCall
from integrations.llm_integration import LLMIntegration
from core.character_system import CharacterSystem
from core.tool_system import ToolSystem
from tools.tool_base import ToolContext

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation flow and LLM interaction."""

    def __init__(
        self,
        llm_integration: Optional[LLMIntegration] = None,
        character_system: Optional[CharacterSystem] = None,
        tool_system: Optional[ToolSystem] = None,
        max_history: int = 10,
        default_character: str = "delilah",
        max_tool_calls: int = 5
    ):
        """
        Initialize the Conversation Manager.

        Args:
            llm_integration: LLM integration instance (creates one if not provided)
            character_system: Character system instance (creates one if not provided)
            tool_system: Tool system instance (creates one if not provided)
            max_history: Maximum number of messages to keep in history
            default_character: Default character ID to use
            max_tool_calls: Maximum tool calls per turn (circuit breaker)
        """
        self.llm = llm_integration or LLMIntegration()
        self.character_system = character_system or CharacterSystem()
        self.tool_system = tool_system or ToolSystem()
        self.max_history = max_history
        self.default_character = default_character
        self.max_tool_calls = max_tool_calls

        # Store active conversations by session_id
        self.conversations: Dict[str, ConversationContext] = {}

        logger.info(
            f"Conversation Manager initialized "
            f"(max_history={max_history}, default_character={default_character}, "
            f"max_tool_calls={max_tool_calls})"
        )

    def get_or_create_conversation(
        self,
        session_id: str,
        user_id: str = "default_user"
    ) -> ConversationContext:
        """
        Get existing conversation or create a new one.

        Args:
            session_id: Unique session identifier
            user_id: User identifier

        Returns:
            ConversationContext for this session
        """
        if session_id not in self.conversations:
            self.conversations[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                history=[],
                metadata={}
            )
            logger.info(f"Created new conversation for session {session_id}")

        return self.conversations[session_id]

    def _build_system_prompt(
        self,
        context: ConversationContext,
        character_id: Optional[str] = None,
        user_message: Optional[str] = None
    ) -> str:
        """
        Build the system prompt for the LLM using Character System.

        Args:
            context: Conversation context
            character_id: Character to use (defaults to default_character)
            user_message: Latest user message for voice mode selection

        Returns:
            System prompt string
        """
        char_id = character_id or self.default_character

        # If we have a user message, select the appropriate voice mode
        if user_message:
            voice_mode_selection = self.character_system.select_voice_mode(
                char_id, user_message, context.metadata
            )

            if voice_mode_selection:
                logger.debug(
                    f"Selected voice mode: {voice_mode_selection.mode.name} "
                    f"(confidence: {voice_mode_selection.confidence:.2f}) - "
                    f"{voice_mode_selection.reasoning}"
                )
                return self.character_system.build_system_prompt(
                    char_id, voice_mode_selection.mode
                )

        # Fallback to character prompt without specific voice mode
        return self.character_system.build_system_prompt(char_id)

    def _manage_history(self, context: ConversationContext):
        """
        Manage conversation history to prevent it from growing too large.

        Keeps only the most recent messages up to max_history.

        Args:
            context: Conversation context to manage
        """
        if len(context.history) > self.max_history:
            # Keep only the most recent messages
            context.history = context.history[-self.max_history:]
            logger.debug(f"Trimmed conversation history to {self.max_history} messages")

    def _prepare_messages(
        self,
        context: ConversationContext,
        user_message: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Prepare messages for the LLM API call.

        Args:
            context: Conversation context
            user_message: Latest user message for voice mode selection

        Returns:
            List of message dicts in OpenAI format
        """
        messages = []

        # Add system prompt (with voice mode selection based on user message)
        system_prompt = self._build_system_prompt(context, user_message=user_message)
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # Add conversation history
        for msg in context.history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    async def handle_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str = "default_user"
    ) -> Dict[str, Any]:
        """
        Handle an incoming user message and generate a response.

        Args:
            session_id: Unique session identifier
            user_message: User's message text
            user_id: User identifier

        Returns:
            Dict containing:
                - text: Assistant's response text
                - metadata: Additional information (tokens, response_time, etc.)
        """
        try:
            # Get or create conversation
            context = self.get_or_create_conversation(session_id, user_id)

            # Add user message to history
            user_msg = Message(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow()
            )
            context.history.append(user_msg)

            logger.info(f"Processing user message in session {session_id}: {user_message[:50]}...")

            # Prepare messages for LLM (pass user_message for voice mode selection)
            messages = self._prepare_messages(context, user_message=user_message)

            # Get tool definitions
            tools = self.tool_system.get_openai_functions() if self.tool_system.list_tools() else None

            # Generate response from LLM (with tool calling if tools available)
            llm_response = self.llm.generate_response(
                messages=messages,
                temperature=0.7,
                tools=tools
            )

            # Handle tool calls if present
            tool_call_count = 0
            while llm_response.get("tool_calls") and tool_call_count < self.max_tool_calls:
                tool_call_count += 1
                logger.info(f"Processing tool call {tool_call_count}/{self.max_tool_calls}")

                # Add assistant message with tool calls to history
                assistant_msg = Message(
                    role="assistant",
                    content=llm_response.get("content", ""),
                    timestamp=datetime.utcnow()
                )
                context.history.append(assistant_msg)

                # Execute each tool call
                tool_results = []
                for tool_call in llm_response["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}

                    # Create tool context
                    tool_context = ToolContext(
                        user_id=user_id,
                        session_id=session_id,
                        character_id=self.default_character,
                        metadata=context.metadata
                    )

                    # Execute tool
                    result = await self.tool_system.execute_tool(
                        tool_name,
                        tool_context,
                        arguments
                    )

                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": tool_name,
                        "content": result.message
                    })

                # Add tool results to messages for next LLM call
                messages = self._prepare_messages(context, user_message=None)
                for tool_result in tool_results:
                    messages.append(tool_result)

                # Get next LLM response with tool results
                llm_response = self.llm.generate_response(
                    messages=messages,
                    temperature=0.7,
                    tools=tools
                )

            # Circuit breaker: if max tool calls reached
            if tool_call_count >= self.max_tool_calls:
                logger.warning(f"Hit tool call limit ({self.max_tool_calls}) for session {session_id}")

            # Extract final response text
            response_text = llm_response.get("content", "")

            if not response_text:
                # Handle case where there's no content
                response_text = "I've completed the task."
                logger.warning(f"No content in final LLM response for session {session_id}")

            # Add final assistant message to history
            assistant_msg = Message(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            context.history.append(assistant_msg)

            # Manage history size
            self._manage_history(context)

            # Build response
            response = {
                "text": response_text,
                "metadata": {
                    "session_id": session_id,
                    "tokens_used": llm_response["usage"]["total_tokens"],
                    "response_time": llm_response["response_time"],
                    "finish_reason": llm_response["finish_reason"],
                    "tool_calls_made": tool_call_count
                }
            }

            logger.info(
                f"Generated response for session {session_id} "
                f"(tokens: {llm_response['usage']['total_tokens']}, "
                f"time: {llm_response['response_time']:.2f}s, "
                f"tool_calls: {tool_call_count})"
            )

            # TODO: Phase 5 - Check for story beat injection
            # TODO: Phase 6 - Generate TTS audio

            return response

        except Exception as e:
            logger.error(f"Error handling user message: {str(e)}", exc_info=True)
            return {
                "text": "I'm sorry, I encountered an error processing your message. Please try again.",
                "metadata": {
                    "error": str(e),
                    "session_id": session_id
                }
            }

    def get_conversation_history(
        self,
        session_id: str
    ) -> List[Message]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of messages in conversation history
        """
        if session_id in self.conversations:
            return self.conversations[session_id].history
        return []

    def clear_conversation(self, session_id: str):
        """
        Clear conversation history for a session.

        Args:
            session_id: Session identifier
        """
        if session_id in self.conversations:
            del self.conversations[session_id]
            logger.info(f"Cleared conversation for session {session_id}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation manager statistics.

        Returns:
            Dict with active conversations count and LLM statistics
        """
        return {
            "active_conversations": len(self.conversations),
            "llm_stats": self.llm.get_statistics()
        }
