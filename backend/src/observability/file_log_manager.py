"""
Runtime file logging manager for the observability system.

Provides a singleton that can attach/detach a RotatingFileHandler at runtime,
writing JSON Lines to a safe path under the project's ``logs/`` directory.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .json_formatter import JsonFormatter

# Logs directory is at the project root (four levels up from this file's src/observability/)
LOGS_DIR = (Path(__file__).parent.parent.parent.parent / "logs").resolve()


def _safe_path(filename: str) -> Path:
    """
    Validate that filename is a plain name (no path separators or traversal)
    and resolve it under LOGS_DIR.

    Raises ValueError on invalid input.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("filename must be a plain name, not a path")
    resolved = (LOGS_DIR / filename).resolve()
    if not str(resolved).startswith(str(LOGS_DIR)):
        raise ValueError("path escapes logs/ directory")
    return resolved


class FileLogManager:
    """
    Singleton that owns the lifecycle of an optional RotatingFileHandler.

    Usage::

        mgr = FileLogManager.instance()
        mgr.enable("aperture-assist.log")
        mgr.disable()
        print(mgr.status())
    """

    _instance: Optional["FileLogManager"] = None

    def __init__(self) -> None:
        self._handler: Optional[logging.handlers.RotatingFileHandler] = None
        self._path: Optional[Path] = None

    @classmethod
    def instance(cls) -> "FileLogManager":
        """Return (or create) the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def _reset(cls) -> None:
        """Reset singleton (for testing only)."""
        if cls._instance is not None:
            cls._instance.disable()
        cls._instance = None

    def enable(self, filename: str) -> None:
        """
        Attach a RotatingFileHandler writing JSON Lines to ``logs/<filename>``.

        Idempotent: if already enabled with the same file, this is a no-op.
        If enabled with a different file, the old handler is first disabled.
        """
        path = _safe_path(filename)

        if self._handler is not None:
            if self._path == path:
                return  # already enabled, same file
            self.disable()

        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        from core.logging_context import CorrelationFilter

        handler = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        handler.setFormatter(JsonFormatter())
        handler.addFilter(CorrelationFilter())
        handler.setLevel(logging.DEBUG)

        logging.getLogger().addHandler(handler)
        self._handler = handler
        self._path = path

    def disable(self) -> None:
        """Detach and close the file handler (if active)."""
        if self._handler is None:
            return
        logging.getLogger().removeHandler(self._handler)
        self._handler.close()
        self._handler = None
        self._path = None

    def status(self) -> dict:
        """Return current file logging state."""
        if self._handler is None or self._path is None:
            return {"enabled": False, "path": None, "size_bytes": None}

        size_bytes: Optional[int] = None
        try:
            size_bytes = self._path.stat().st_size
        except OSError:
            pass

        return {
            "enabled": True,
            "path": str(self._path.relative_to(LOGS_DIR.parent)),
            "size_bytes": size_bytes,
        }
