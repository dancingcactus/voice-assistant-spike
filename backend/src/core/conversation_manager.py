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
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.message import Message, ConversationContext, LLMResponse, ToolCall
from models.user_state import ConversationMessage
from integrations.llm_integration import LLMIntegration
from integrations.tts_integration import TTSProvider
from core.character_system import CharacterSystem
from core.tool_system import ToolSystem
from core.story_engine import StoryEngine
from core.memory_manager import MemoryManager
from tools.tool_base import ToolContext
from pathlib import Path

logger = logging.getLogger(__name__)

# Import observability modules with error handling
try:
    import sys
    # Ensure src directory is in path for observability imports
    src_dir = Path(__file__).parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from observability.tool_call_access import ToolCallDataAccess
    from observability.tool_call_models import ToolCallLog, ToolCallStatus
    OBSERVABILITY_AVAILABLE = True
    logger.info("Tool call logging enabled")
except ImportError as e:
    logger.warning(f"Tool call logging unavailable: {e}")
    OBSERVABILITY_AVAILABLE = False
    ToolCallDataAccess = None
    ToolCallLog = None
    ToolCallStatus = None


class ConversationManager:
    """Manages conversation flow and LLM interaction."""

    def __init__(
        self,
        llm_integration: Optional[LLMIntegration] = None,
        character_system: Optional[CharacterSystem] = None,
        tool_system: Optional[ToolSystem] = None,
        story_engine: Optional[StoryEngine] = None,
        tts_provider: Optional[TTSProvider] = None,
        memory_manager: Optional[MemoryManager] = None,
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
            story_engine: Story engine instance (creates one if not provided)
            tts_provider: TTS provider instance (optional, for voice output)
            memory_manager: Memory manager instance (creates one if not provided)
            max_history: Maximum number of messages to keep in history
            default_character: Default character ID to use
            max_tool_calls: Maximum tool calls per turn (circuit breaker)
        """
        self.llm = llm_integration or LLMIntegration()
        self.character_system = character_system or CharacterSystem()
        self.tool_system = tool_system or ToolSystem()
        self.story_engine = story_engine or StoryEngine()
        self.tts_provider = tts_provider  # Optional - voice output
        self.memory_manager = memory_manager or MemoryManager()
        self.max_history = max_history
        self.default_character = default_character
        self.max_tool_calls = max_tool_calls

        # Store active conversations by session_id (in-memory for current session)
        self.conversations: Dict[str, ConversationContext] = {}

        # Initialize tool call logger if observability is available
        if OBSERVABILITY_AVAILABLE:
            data_dir = Path(__file__).parent.parent.parent / "data"
            self.tool_call_logger = ToolCallDataAccess(data_dir=str(data_dir))
        else:
            self.tool_call_logger = None

        logger.info(
            f"Conversation Manager initialized "
            f"(max_history={max_history}, default_character={default_character}, "
            f"max_tool_calls={max_tool_calls}, tts={self.tts_provider is not None}, "
            f"memory={self.memory_manager is not None}, "
            f"tool_logging={self.tool_call_logger is not None})"
        )

    def get_or_create_conversation(
        self,
        session_id: str,
        user_id: str = "default_user"
    ) -> ConversationContext:
        """
        Get existing conversation or create a new one.
        Loads conversation history from persistent storage via Memory Manager.

        Args:
            session_id: Unique session identifier
            user_id: User identifier

        Returns:
            ConversationContext for this session
        """
        if session_id not in self.conversations:
            # Load user state from persistent storage
            user_state = self.memory_manager.load_user_state(user_id)

            # Convert stored conversation messages to Message objects
            history = []
            for conv_msg in user_state.conversation_history.messages:
                history.append(Message(
                    role=conv_msg.role,
                    content=conv_msg.content,
                    timestamp=conv_msg.timestamp
                ))

            self.conversations[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                history=history,
                metadata={}
            )
            logger.info(f"Created/loaded conversation for session {session_id} (user: {user_id}, {len(history)} messages)")

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
        user_id: str = "default_user",
        input_mode: str = "chat"
    ) -> Dict[str, Any]:
        """
        Handle an incoming user message and generate a response.

        Args:
            session_id: Unique session identifier
            user_message: User's message text
            user_id: User identifier
            input_mode: Input method ("voice" or "chat") - affects TTS generation

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

            # Save user message to persistent storage
            self.memory_manager.add_conversation_message(user_id, user_msg, "user")

            # Increment interaction count for story progression
            self.memory_manager.increment_interaction_count(user_id)

            logger.info(f"Processing user message in session {session_id}: {user_message[:50]}...")

            # Select voice mode for this response (store for TTS later)
            voice_mode = None
            voice_mode_selection = self.character_system.select_voice_mode(
                self.default_character, user_message, context.metadata
            )
            if voice_mode_selection:
                voice_mode = voice_mode_selection.mode.name.lower()
                logger.debug(f"Selected voice mode: {voice_mode}")

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

                    # Start timing
                    start_time = time.time()
                    call_id = f"call_{uuid.uuid4().hex[:12]}"
                    timestamp = datetime.now()

                    # Execute tool
                    try:
                        result = await self.tool_system.execute_tool(
                            tool_name,
                            tool_context,
                            arguments
                        )

                        # Calculate duration
                        duration_ms = int((time.time() - start_time) * 1000)

                        # Determine status
                        from tools.tool_base import ToolResultStatus
                        status = ToolCallStatus.SUCCESS if result.status == ToolResultStatus.SUCCESS else ToolCallStatus.ERROR

                        # Log the tool call if logger is available
                        if self.tool_call_logger and OBSERVABILITY_AVAILABLE:
                            try:
                                log_entry = ToolCallLog(
                                    call_id=call_id,
                                    timestamp=timestamp,
                                    duration_ms=duration_ms,
                                    tool_name=tool_name,
                                    character=self.default_character,
                                    user_id=user_id,
                                    request=arguments,
                                    response=result.data or {"message": result.message},
                                    status=status,
                                    error_message=result.error if result.error else None,
                                    session_id=session_id,
                                )
                                self.tool_call_logger.append_tool_call(log_entry)
                                logger.info(f"✅ Logged tool call: {call_id} - {tool_name}")
                            except Exception as log_error:
                                logger.error(f"Failed to log tool call: {log_error}", exc_info=True)

                    except Exception as e:
                        # Calculate duration even on error
                        duration_ms = int((time.time() - start_time) * 1000)

                        # Log the failed tool call if logger is available
                        if self.tool_call_logger and OBSERVABILITY_AVAILABLE:
                            try:
                                log_entry = ToolCallLog(
                                    call_id=call_id,
                                    timestamp=timestamp,
                                    duration_ms=duration_ms,
                                    tool_name=tool_name,
                                    character=self.default_character,
                                    user_id=user_id,
                                    request=arguments,
                                    response={"error": str(e)},
                                    status=ToolCallStatus.ERROR,
                                    error_message=str(e),
                                    session_id=session_id,
                                )
                                self.tool_call_logger.append_tool_call(log_entry)
                                logger.info(f"✅ Logged failed tool call: {call_id} - {tool_name}")
                            except Exception as log_error:
                                logger.error(f"Failed to log tool call error: {log_error}", exc_info=True)

                        # Re-raise the exception
                        raise

                    # Notify Story Engine about tool execution
                    self.story_engine.on_tool_executed(user_id, tool_name)

                    # Store last tool used for story beat context
                    context.metadata["last_tool_used"] = tool_name

                    tool_results.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": tool_name,
                        "content": result.message
                    })

                # Rebuild messages with assistant's tool call message + tool results
                messages = self._prepare_messages(context, user_message=None)

                # Add assistant message with tool_calls
                messages.append({
                    "role": "assistant",
                    "content": llm_response.get("content") or "",
                    "tool_calls": llm_response["tool_calls"]
                })

                # Add tool results
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

            # Phase 5: Check for story beat injection
            story_beat_injected = False
            story_beat_info = None

            # Emit event to Story Engine
            self.story_engine.on_user_message(user_id)

            # Check if we should inject a story beat
            beat_context = {
                "user_message": user_message,
                "task_completed": tool_call_count > 0,
                "tool_used": context.metadata.get("last_tool_used"),
                "response_length": len(response_text)
            }

            beat_result = self.story_engine.should_inject_beat(user_id, beat_context)

            if beat_result:
                beat, stage, variant_type = beat_result
                beat_content_result = self.story_engine.get_beat_content(beat, stage, variant_type)

                if beat_content_result:
                    beat_content, delivery_type = beat_content_result

                    # Inject beat based on delivery type
                    if delivery_type == "append":
                        response_text = f"{response_text}\n\n{beat_content}"
                    elif delivery_type == "replace":
                        response_text = beat_content

                    # Mark beat as delivered
                    self.story_engine.mark_beat_stage_delivered(user_id, beat.id, stage)

                    story_beat_injected = True
                    story_beat_info = {
                        "beat_id": beat.id,
                        "stage": stage,
                        "variant": variant_type,
                        "delivery": delivery_type
                    }

                    logger.info(
                        f"Injected story beat '{beat.id}' (stage {stage}, {variant_type}) "
                        f"into response for session {session_id}"
                    )

            # Check for chapter progression
            next_chapter = self.story_engine.check_chapter_progression(user_id)
            if next_chapter:
                logger.info(f"User {user_id} progressed to Chapter {next_chapter}")

            # Add final assistant message to history (with story beat if injected)
            assistant_msg = Message(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            context.history.append(assistant_msg)

            # Save assistant message to persistent storage
            self.memory_manager.add_conversation_message(user_id, assistant_msg, "assistant")

            # Manage history size (in-memory context only)
            self._manage_history(context)

            # Build response
            response = {
                "text": response_text,
                "metadata": {
                    "session_id": session_id,
                    "tokens_used": llm_response["usage"]["total_tokens"],
                    "response_time": llm_response["response_time"],
                    "finish_reason": llm_response["finish_reason"],
                    "tool_calls_made": tool_call_count,
                    "story_beat_injected": story_beat_injected
                }
            }

            if story_beat_info:
                response["metadata"]["story_beat"] = story_beat_info

            logger.info(
                f"Generated response for session {session_id} "
                f"(tokens: {llm_response['usage']['total_tokens']}, "
                f"time: {llm_response['response_time']:.2f}s, "
                f"tool_calls: {tool_call_count}, "
                f"story_beat: {story_beat_injected})"
            )

            # Phase 6: Generate TTS audio (only for voice input mode)
            if self.tts_provider and input_mode == "voice":
                try:
                    audio_path = self.tts_provider.generate_speech(
                        text=response_text,
                        character_id=self.default_character,
                        voice_mode=voice_mode
                    )

                    if audio_path:
                        response["metadata"]["audio_url"] = f"/{audio_path}"
                        logger.info(f"Generated TTS audio: {audio_path}")
                    else:
                        logger.warning("TTS generation returned no audio path")

                except Exception as e:
                    logger.error(f"Error generating TTS: {str(e)}", exc_info=True)
                    # Don't fail the request if TTS fails - just log and continue

            # Store voice mode in metadata for potential manual TTS generation later
            if voice_mode:
                response["metadata"]["voice_mode"] = voice_mode

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
