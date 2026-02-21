"""
Shared utility functions for the core conversation system.
"""

import re

# Compiled regex for affirmation detection — covers common short confirmatory phrases.
# Deliberately excludes longer messages that might happen to contain an affirmation word
# (e.g., "yes, but can you make it vegetarian?" should NOT trigger deferred task execution).
_AFFIRMATION_PATTERN = re.compile(
    r"^\s*(?:"
    r"that(?:'s|\s+is)?\s+(?:looks?\s+)?(?:good|great|perfect|wonderful|amazing|awesome)"
    r"|sounds?\s+(?:good|great|perfect|wonderful|amazing|awesome)"
    r"|(?:yes|yeah|yep|yup|yea)"
    r"|sure"
    r"|ok(?:ay)?"
    r"|perfect"
    r"|great"
    r"|love\s+it"
    r"|(?:let'?s?\s+)?do\s+it"
    r"|go\s+(?:ahead|for\s+it)"
    r"|that\s+works?"
    r"|(?:go\s+)?(?:ahead\s+)?please"
    r"|(?:yes\s+)?please"
    r"|exactly"
    r"|absolutely"
    r"|(?:that'?s?\s+)?(?:spot[\s-]on|perfect)"
    r")\s*[.!]*\s*$",
    re.IGNORECASE,
)


def is_affirmation(text: str) -> bool:
    """
    Return True if *text* is a short, standalone confirmatory response.

    Designed to detect user approval of a preceding suggestion so that
    deferred subtasks (e.g., building a shopping list after a meal is chosen)
    can be triggered.  Only matches short phrases — anything that continues
    into a substantive new question or instruction returns False.

    Args:
        text: The user's message text.

    Returns:
        True if the message is a simple affirmation, False otherwise.

    Examples:
        >>> is_affirmation("That looks good")
        True
        >>> is_affirmation("Sounds great!")
        True
        >>> is_affirmation("Yes please")
        True
        >>> is_affirmation("Yes, but can you make it vegetarian?")
        False
        >>> is_affirmation("Can you add more garlic?")
        False
        >>> is_affirmation("")
        False
    """
    if not text or not text.strip():
        return False

    # Strip punctuation at the end and normalise whitespace before matching
    cleaned = text.strip()

    # Reject anything that looks like a follow-up question or instruction
    # (contains a question mark mid-sentence, or is longer than ~60 chars)
    if len(cleaned) > 60:
        return False

    return bool(_AFFIRMATION_PATTERN.match(cleaned))
