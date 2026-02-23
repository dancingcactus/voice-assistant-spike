"""
Conversation Manager - Core module for handling user conversations.

Responsibilities:
- Managing conversation history and session context
- Routing user messages through the TurnClassifier → ConversationRouter → CharacterExecutor pipeline
- Emitting events for other systems (Story Engine, Character System)
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from models.message import Message, ConversationContext
from integrations.llm_integration import LLMIntegration
from integrations.tts_integration import TTSProvider
from core.character_system import CharacterSystem
from core.tool_system import ToolSystem
from core.story_engine import StoryEngine
from core.memory_manager import MemoryManager

from core.conversation_state import ConversationStateManager
from core.turn_classifier import TurnClassifier
from core.conversation_router import ConversationRouter
from core.character_executor import CharacterExecutor
from models.routing import CoordinationMode, TurnType
from config.character_assignments import get_available_characters
from core.logging_context import generate_id, set_correlation_ids, conversation_id_var, turn_id_var

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation flow through the character routing pipeline."""

    def __init__(
        self,
        llm_integration: Optional[LLMIntegration] = None,
        character_system: Optional[CharacterSystem] = None,
        tool_system: Optional[ToolSystem] = None,
        story_engine: Optional[StoryEngine] = None,
        tts_provider: Optional[TTSProvider] = None,
        memory_manager: Optional[MemoryManager] = None,
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

        logger.info(
            f"Conversation Manager initialized "
            f"(max_history={max_history}, default_character={default_character}, "
            f"max_tool_calls={max_tool_calls}, tts={self.tts_provider is not None}, "
            f"memory={self.memory_manager is not None})"
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

    # Named limits used across the orchestration path
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
                    "Orchestrator: Coordination state expired — clearing (session=%s)", session_id
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
                    "Orchestrator: TurnClassifier → %s (confidence=%.2f, session=%s)",
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
                    "Orchestrator: AFFIRMATION — executing pending character '%s' (session=%s)",
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
                        "Orchestrator: %s — clearing pending state (session=%s)",
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
                "Orchestrator: Router → primary='%s', followup=%s, rationale=%r (session=%s)",
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
                    "Orchestrator: Stored pending followup → '%s' (session=%s)",
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
                    logger.error("Orchestrator: TTS failed: %s", tts_err)

            return response

        except Exception as exc:
            logger.error(
                "Orchestration failed: %s — falling back to single-character delilah",
                exc,
                exc_info=True,
            )
            return {
                "text": "I'm sorry, I encountered an error. Please try again.",
                "metadata": {
                    "error": str(exc),
                    "session_id": session_id,
                    "orchestration_error": True,
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
                "Orchestrator: Secondary character '%s' execution failed: %s",
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
            _turn_start = time.monotonic()
            # Generate correlation IDs for this turn
            turn_id = generate_id()
            set_correlation_ids(conversation_id_var.get(), turn_id)
            logger.info("Turn start", extra={"turn_type": "handle_user_message", "coordination_mode": "idle"})

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

            result = await self._orchestrate_character_turn(
                session_id=session_id,
                user_id=user_id,
                user_message=user_message,
                context=context,
                input_mode=input_mode,
            )
            # Inject turn_id into the response so the frontend can link chat bubbles to log groups
            result.setdefault("metadata", {})["turn_id"] = turn_id
            _elapsed_ms = (time.monotonic() - _turn_start) * 1000
            logger.info("Turn complete", extra={"latency_ms": _elapsed_ms})
            return result

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
