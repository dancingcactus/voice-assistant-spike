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
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.message import Message, ConversationContext, LLMResponse, ToolCall
from models.user_state import ConversationMessage
from integrations.llm_integration import LLMIntegration
from integrations.tts_integration import TTSProvider
from core.character_system import CharacterSystem
from core.tool_system import ToolSystem
from tools.tool_base import ToolContext, ToolResultStatus
from core.story_engine import StoryEngine
from core.memory_manager import MemoryManager
from pathlib import Path

# Phase 5.1 imports
from core.conversation_state import ConversationStateManager
from core.turn_classifier import TurnClassifier
from core.conversation_router import ConversationRouter
from core.character_executor import CharacterExecutor
from models.routing import CoordinationMode, TurnType
from config.character_assignments import get_available_characters

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
        # Phase 5.1 injectable dependencies
        state_manager: Optional[ConversationStateManager] = None,
        turn_classifier: Optional[TurnClassifier] = None,
        conversation_router: Optional[ConversationRouter] = None,
        character_executor: Optional[CharacterExecutor] = None,
        max_history: int = 10,
        default_character: str = "delilah",
        max_tool_calls: int = 5,
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
            state_manager: Coordination state manager (auto-created if None)
            turn_classifier: Turn classifier (auto-created if None)
            conversation_router: Conversation router (auto-created if None)
            character_executor: Character executor (auto-created if None)
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

        # Phase 5.1 components
        self.state_manager = state_manager or ConversationStateManager()
        self.turn_classifier = turn_classifier or TurnClassifier(llm=self.llm)
        self.conversation_router = conversation_router or ConversationRouter(llm=self.llm)
        self.character_executor = character_executor or CharacterExecutor(
            llm_integration=self.llm,
            character_system=self.character_system,
            tool_system=self.tool_system,
            story_engine=self.story_engine,
            max_tool_calls=self.max_tool_calls,
        )

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

        # Load user memories
        from observability.memory_access import MemoryAccessor
        memory_accessor = MemoryAccessor(str(Path(__file__).parent.parent.parent / "data"))
        memories = memory_accessor.get_all_memories(context.user_id)

        # Group memories by category
        memory_context = {
            "dietary_restrictions": [],
            "preferences": [],
            "facts": [],
            "relationships": [],
            "events": []
        }

        for memory in memories:
            if memory.category == "dietary_restriction":
                memory_context["dietary_restrictions"].append(memory)
            elif memory.category == "preference":
                memory_context["preferences"].append(memory)
            elif memory.category == "fact":
                memory_context["facts"].append(memory)
            elif memory.category == "relationship":
                memory_context["relationships"].append(memory)
            elif memory.category == "event":
                memory_context["events"].append(memory)

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
                    char_id, voice_mode_selection.mode, memory_context=memory_context
                )

        # Fallback to character prompt without specific voice mode
        return self.character_system.build_system_prompt(char_id, memory_context=memory_context)

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

    # ------------------------------------------------------------------
    # Orchestration path
    # ------------------------------------------------------------------

    # Named limits used across the Phase 5.1 path
    _MAX_HANDOFF_ITEMS = 20          # Cap on structured items passed to secondary (token budget)
    _MAX_CONTEXT_EXCERPT = 500       # Character limit for context excerpts passed to secondary

    def _get_chapter_for_user(self, user_id: str) -> int:
        """Return the current story chapter for a user."""
        try:
            user_state = self.memory_manager.load_user_state(user_id)
            return user_state.story_progress.current_chapter
        except Exception:
            return 1

    def _build_secondary_task(
        self,
        followup: Dict[str, Any],
        primary_text: str,
    ) -> str:
        """
        Build the task description string passed to the secondary CharacterExecutor.

        If the followup dict contains an ``items`` list (populated from
        ``request_handoff`` arguments), those are injected.  Otherwise the
        ``task_summary`` is used verbatim with a snippet of the primary character's
        response appended so the secondary has enough context.
        """
        task_summary = followup.get("task_summary") or followup.get("pending_task") or ""
        items: List[str] = followup.get("items") or []

        if items:
            items_str = ", ".join(f'"{i}"' for i in items[:self._MAX_HANDOFF_ITEMS])  # cap for prompt length
            return f"{task_summary}\n\nItems from previous response: {items_str}"

        # No structured items — give the secondary a short excerpt of primary text
        excerpt = primary_text[:self._MAX_CONTEXT_EXCERPT].strip()
        if excerpt:
            return f"{task_summary}\n\nContext from previous character:\n{excerpt}"
        return task_summary

    def _assemble_multi_response(
        self,
        session_id: str,
        user_id: str,
        fragments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Assemble a multi-character response dict from a list of fragment dicts."""
        full_text = " ".join(f["text"] for f in fragments if f.get("text"))
        characters = [f["character"] for f in fragments]
        return {
            "text": full_text,
            "metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "phase51": True,
                "characters": characters,
                "fragments": fragments,
                "character_count": len(fragments),
            },
        }

    async def _orchestrate_character_turn(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        context,  # ConversationContext
        input_mode: str = "chat",
    ) -> Dict[str, Any]:
        """
        Orchestrate a single conversation turn through the routing pipeline.

        Implements the TurnClassifier → ConversationRouter → CharacterExecutor
        pipeline: classifies the turn type, routes to the appropriate primary
        character, executes that character, and handles any secondary character
        follow-up (either via an explicit ``request_handoff`` tool call or a
        router-proposed pending follow-up confirmed on the next turn).

        Falls back to a single-character Delilah response on any unhandled
        exception so the conversation is never silently dropped.
        """
        try:
            chapter_id = self._get_chapter_for_user(user_id)
            available_chars = get_available_characters(chapter_id)
            history_snapshot = [
                {"role": m.role, "content": m.content} for m in context.history
            ]

            # ── Step 1: Get current coordination state ──────────────────────
            coord_state = self.state_manager.get_state(context)

            # ── Step 2: Silently expire stale pending state ──────────────────
            if (
                coord_state.mode != CoordinationMode.IDLE
                and self.state_manager.is_expired(coord_state)
            ):
                logger.info(
                    "Phase 5.1: Coordination state expired — clearing (session=%s)", session_id
                )
                self.state_manager.clear(context)
                coord_state = self.state_manager.get_state(context)

            # ── Step 3: Classify turn when something is pending ──────────────
            turn_type = TurnType.NEW_REQUEST
            if coord_state.mode != CoordinationMode.IDLE:
                classification = self.turn_classifier.classify(
                    user_message,
                    history_snapshot[-4:],
                    coord_state,
                )
                turn_type = classification.turn_type
                logger.info(
                    "Phase 5.1: TurnClassifier → %s (confidence=%.2f, session=%s)",
                    turn_type,
                    classification.confidence,
                    session_id,
                )

            # ── Step 4: Execute pending character on AFFIRMATION ─────────────
            if (
                turn_type == TurnType.AFFIRMATION
                and coord_state.mode == CoordinationMode.PROPOSING
                and coord_state.pending_character
            ):
                logger.info(
                    "Phase 5.1: AFFIRMATION — executing pending character '%s' (session=%s)",
                    coord_state.pending_character,
                    session_id,
                )
                self.state_manager.set_awaiting_action(
                    context,
                    pending_character=coord_state.pending_character,
                    pending_task=coord_state.pending_task or "",
                )
                pending_followup = {
                    "character": coord_state.pending_character,
                    "task_summary": coord_state.pending_task or "",
                    "items": [],
                }
                return await self._execute_secondary_and_assemble(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=user_message,
                    context=context,
                    primary_text=coord_state.proposed_summary or "",
                    followup=pending_followup,
                    input_mode=input_mode,
                    history_snapshot=history_snapshot,
                )

            # ── Step 5: Clear state on topic change or rejection ─────────────
            if turn_type in (TurnType.REJECTION, TurnType.NEW_REQUEST):
                if coord_state.mode != CoordinationMode.IDLE:
                    logger.info(
                        "Phase 5.1: %s — clearing pending state (session=%s)",
                        turn_type,
                        session_id,
                    )
                    self.state_manager.clear(context)

            # ── Step 6: Route to primary character ───────────────────────────
            routing = self.conversation_router.route(
                user_message=user_message,
                recent_history=history_snapshot[-6:],
                available_characters=available_chars,
                chapter_id=chapter_id,
            )
            logger.info(
                "Phase 5.1: Router → primary='%s', followup=%s, rationale=%r (session=%s)",
                routing.primary_character,
                routing.pending_followup.character if routing.pending_followup else None,
                routing.rationale,
                session_id,
            )

            # ── Step 7: Execute primary character ────────────────────────────
            primary_response = await self.character_executor.execute(
                character=routing.primary_character,
                task_description=user_message,
                context=context,
                session_id=session_id,
                user_id=user_id,
            )

            # ── Step 8: Determine if secondary execution is needed ────────────
            handoff_signal = primary_response.handoff_signal  # from request_handoff tool
            router_followup = routing.pending_followup

            # Only execute the secondary immediately when the character explicitly
            # called request_handoff.  A router pending_followup is stored as
            # PROPOSING state so the user can confirm on the next turn.
            if handoff_signal and handoff_signal.get("to_character") in available_chars:
                followup: Optional[Dict[str, Any]] = {
                    "character": handoff_signal.get("to_character", ""),
                    "task_summary": handoff_signal.get("task_summary", ""),
                    "items": handoff_signal.get("items") or [],
                    "source": "handoff_tool",
                }
                # Execute secondary immediately — both characters respond this turn
                return await self._execute_secondary_and_assemble(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=user_message,
                    context=context,
                    primary_text=primary_response.text,
                    followup=followup,
                    input_mode=input_mode,
                    history_snapshot=history_snapshot,
                    primary_fragment={
                        "character": primary_response.character,
                        "text": primary_response.text,
                        "voice_mode": primary_response.voice_mode,
                    },
                )

            # ── Step 9: Store pending followup from router for next turn ──────
            if router_followup and router_followup.character in available_chars:
                self.state_manager.set_proposing(
                    context,
                    pending_character=router_followup.character,
                    pending_task=router_followup.task_summary,
                    proposed_summary=primary_response.text[:self._MAX_CONTEXT_EXCERPT],
                )
                logger.info(
                    "Phase 5.1: Stored pending followup → '%s' (session=%s)",
                    router_followup.character,
                    session_id,
                )

            # ── Step 10: Single-character response ───────────────────────────
            response_text = primary_response.text
            fragments = [
                {
                    "character": primary_response.character,
                    "text": response_text,
                    "voice_mode": primary_response.voice_mode,
                }
            ]

            # Persist to history
            assistant_msg = Message(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow(),
            )
            context.history.append(assistant_msg)
            self.memory_manager.add_conversation_message(user_id, assistant_msg, "assistant")
            self._manage_history(context)

            response = {
                "text": response_text,
                "metadata": {
                    "session_id": session_id,
                    "user_id": user_id,
                    "phase51": True,
                    "character": primary_response.character,
                    "characters": [primary_response.character],
                    "fragments": fragments,
                    "tool_calls_made": primary_response.tool_calls_made,
                    "voice_mode": primary_response.voice_mode,
                },
            }

            # TTS (voice input only)
            if self.tts_provider and input_mode == "voice":
                try:
                    audio_path = self.tts_provider.generate_speech(
                        text=response_text,
                        character_id=primary_response.character,
                        voice_mode=primary_response.voice_mode,
                    )
                    if audio_path:
                        response["metadata"]["audio_url"] = f"/{audio_path}"
                except Exception as tts_err:
                    logger.error("Phase 5.1: TTS failed: %s", tts_err)

            return response

        except Exception as exc:
            logger.error(
                "Phase 5.1 orchestration failed: %s — falling back to single-character delilah",
                exc,
                exc_info=True,
            )
            return {
                "text": "I'm sorry, I encountered an error. Please try again.",
                "metadata": {
                    "error": str(exc),
                    "session_id": session_id,
                    "phase51_error": True,
                },
            }

    async def _execute_secondary_and_assemble(
        self,
        session_id: str,
        user_id: str,
        user_message: str,
        context,  # ConversationContext
        primary_text: str,
        followup: Dict[str, Any],
        input_mode: str,
        history_snapshot: List[Dict],
        primary_fragment: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the secondary character and assemble the full two-character response.

        ``primary_fragment`` is optional — if not provided (e.g., pending-affirmation
        path), the response only contains the secondary character's fragment.
        """
        secondary_task = self._build_secondary_task(followup, primary_text)
        secondary_char = followup["character"]

        try:
            secondary_response = await self.character_executor.execute(
                character=secondary_char,
                task_description=secondary_task,
                context=context,
                session_id=session_id,
                user_id=user_id,
            )
        except Exception as sec_exc:
            logger.error(
                "Phase 5.1: Secondary character '%s' execution failed: %s",
                secondary_char,
                sec_exc,
                exc_info=True,
            )
            # Return primary-only response rather than failing completely
            secondary_response = None

        # Clear coordination state — execution is done
        self.state_manager.clear(context)

        fragments = []
        if primary_fragment:
            fragments.append(primary_fragment)
        if secondary_response:
            fragments.append(
                {
                    "character": secondary_response.character,
                    "text": secondary_response.text,
                    "voice_mode": secondary_response.voice_mode,
                }
            )

        full_text = " ".join(f["text"] for f in fragments if f.get("text"))

        # Persist combined text to history
        assistant_msg = Message(
            role="assistant",
            content=full_text,
            timestamp=datetime.utcnow(),
        )
        context.history.append(assistant_msg)
        self.memory_manager.add_conversation_message(user_id, assistant_msg, "assistant")
        self._manage_history(context)

        return {
            "text": full_text,
            "metadata": {
                "session_id": session_id,
                "user_id": user_id,
                "phase51": True,
                "characters": [f["character"] for f in fragments],
                "fragments": fragments,
                "character_count": len(fragments),
            },
        }

    # Keywords that suggest Hank should weigh in on task/list management
    _COORDINATION_KEYWORDS = [
        "shopping list", "grocery list", "to-do list", "todo list",
        "task list", "checklist", "remind me", "don't forget",
        "add to list", "make a list", "write down", "note that",
        "pick up", "need to buy", "need to get", "grab some", "grab a"
    ]

    # Sentinel the LLM returns when it has nothing to add
    _COORDINATION_SILENT = "SILENT"
    async def _handle_character_coordination(
        self,
        context: ConversationContext,
        user_message: str,
        primary_response: str,
        user_id: str,
        session_id: str,
        current_chapter: int
    ) -> Optional[str]:
        """
        Generate a secondary character response when the task warrants coordination.

        Called after the primary character (Delilah) responds to check whether a
        second crew member should weigh in — for example, Hank stepping in to
        acknowledge a shopping list or task management request.

        Only activates in chapter 2 or later, when Hank has joined the crew.

        Args:
            context: Current conversation context
            user_message: The user's original message
            primary_response: The primary character's response text
            user_id: User identifier
            session_id: Session identifier
            current_chapter: The user's current story chapter

        Returns:
            Secondary character's response text, or None if coordination is not needed
        """
        # Coordination only available in chapter 2+ (Hank must be unlocked)
        if current_chapter < 2:
            return None

        secondary_character_id = "hank"
        if secondary_character_id not in self.character_system.characters:
            return None

        # Check whether the user message signals a coordination need.
        # We only scan the user message — NOT Delilah's response — to avoid
        # triggering Hank every time Delilah herself mentions "shopping list".
        user_lower = user_message.lower()
        if not any(kw in user_lower for kw in self._COORDINATION_KEYWORDS):
            return None

        logger.info(
            f"Coordination triggered for session {session_id}: "
            f"secondary character '{secondary_character_id}'"
        )

        # Build a focused prompt for the secondary character
        crew_context = self.character_system.build_crew_context(secondary_character_id)
        secondary_system_prompt = self.character_system.build_system_prompt(
            secondary_character_id,
            crew_context=crew_context
        )

        # Include the full exchange so Hank has the context he needs.
        # The prompt is deliberately restrictive: Hank should only speak if
        # he has a specific task-management or list-tracking contribution.
        # If he has nothing concrete to add, he should say nothing at all.
        secondary_messages = [
            {"role": "system", "content": secondary_system_prompt},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": primary_response},
            {
                "role": "user",
                "content": (
                    "Hank, if the user is specifically asking you to track a list, "
                    "manage tasks, or set a reminder, give one brief acknowledgment in "
                    "your voice (one or two sentences at most). "
                    "If Delilah has already fully covered it or there is nothing "
                    f"concrete for you to add, stay silent and reply with only the word: {self._COORDINATION_SILENT}"
                )
            }
        ]

        try:
            secondary_response = self.llm.generate_response(
                messages=secondary_messages,
                temperature=0.7
            )
            content = secondary_response.get("content", "").strip()
            # Hank signals he has nothing to add with the sentinel word
            if content and content.upper() != self._COORDINATION_SILENT:
                logger.info(
                    f"Secondary character '{secondary_character_id}' responded "
                    f"({secondary_response['usage']['total_tokens']} tokens)"
                )
                return content
            logger.debug(f"Secondary character '{secondary_character_id}' chose to stay silent")
        except Exception as e:
            logger.warning(f"Secondary character coordination failed: {e}")

        return None

    async def handle_user_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str = "default_user",
        input_mode: str = "chat"
    ) -> Dict[str, Any]:
        """
        Handle an incoming user message and generate a response.

        Sets up the conversation context (history, persistence, interaction count),
        then delegates to ``_orchestrate_character_turn`` for routing and execution.

        Args:
            session_id: Unique session identifier
            user_message: User's message text
            user_id: User identifier
            input_mode: Input method ("voice" or "chat") - affects TTS generation

        Returns:
            Dict containing:
                - text: Assistant's response text
                - metadata: Additional information (characters, fragments, phase51, etc.)
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

            return await self._orchestrate_character_turn(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message,
                context=context,
                input_mode=input_mode,
            )

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
