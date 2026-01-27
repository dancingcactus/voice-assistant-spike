"""
Conversation Manager - Core module for handling user conversations.

Responsibilities:
- Managing conversation history
- Constructing prompts for the LLM
- Coordinating with LLM Integration
- Emitting events for other systems (Story Engine, Character System)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.message import Message, ConversationContext, LLMResponse, ToolCall
from integrations.llm_integration import LLMIntegration

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation flow and LLM interaction."""

    def __init__(
        self,
        llm_integration: Optional[LLMIntegration] = None,
        max_history: int = 10
    ):
        """
        Initialize the Conversation Manager.

        Args:
            llm_integration: LLM integration instance (creates one if not provided)
            max_history: Maximum number of messages to keep in history
        """
        self.llm = llm_integration or LLMIntegration()
        self.max_history = max_history

        # Store active conversations by session_id
        self.conversations: Dict[str, ConversationContext] = {}

        logger.info(f"Conversation Manager initialized (max_history={max_history})")

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

    def _build_system_prompt(self, context: ConversationContext) -> str:
        """
        Build the system prompt for the LLM.

        In Phase 2, this is a simple prompt. Later phases will integrate
        with Character System for personality-driven prompts.

        Args:
            context: Conversation context

        Returns:
            System prompt string
        """
        # Simple prompt for Phase 2
        # TODO: Phase 3 - Integrate with Character System
        return (
            "You are a helpful AI assistant. Provide clear, concise, and friendly responses. "
            "If the user asks about cooking, recipes, or food, be enthusiastic and helpful. "
            "Keep responses conversational and natural."
        )

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

    def _prepare_messages(self, context: ConversationContext) -> List[Dict[str, str]]:
        """
        Prepare messages for the LLM API call.

        Args:
            context: Conversation context

        Returns:
            List of message dicts in OpenAI format
        """
        messages = []

        # Add system prompt
        system_prompt = self._build_system_prompt(context)
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

            # Prepare messages for LLM
            messages = self._prepare_messages(context)

            # Generate response from LLM
            llm_response = self.llm.generate_response(
                messages=messages,
                temperature=0.7
            )

            # Extract response text
            response_text = llm_response.get("content", "")

            if not response_text:
                # Handle case where there's no content (e.g., only tool calls)
                response_text = "I'm not sure how to respond to that."
                logger.warning(f"No content in LLM response for session {session_id}")

            # Add assistant message to history
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
                    "finish_reason": llm_response["finish_reason"]
                }
            }

            logger.info(
                f"Generated response for session {session_id} "
                f"(tokens: {llm_response['usage']['total_tokens']}, "
                f"time: {llm_response['response_time']:.2f}s)"
            )

            # TODO: Phase 4 - Handle tool calls if present
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
