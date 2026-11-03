"""Input and output screening for the SolidMove chat surface.

Apple App Review Guideline 1.2 requires apps carrying user-generated content,
and by extension conversational AI, to filter objectionable material and give
users a way to report or block it. Guideline 5.1.2 adds consent requirements
for data collection. This module covers the filtering half: every model call
passes its prompt and its completion through here before either is shown.

No external service is required. Patterns are deliberately conservative:
they block clear categories and redact credentials and personal data rather
than attempting to judge tone.
"""

import re
from dataclasses import dataclass, field
from typing import List

MAX_INPUT_CHARS = 4_000
MAX_OUTPUT_CHARS = 8_000

_BLOCKED = {
    "child_sexual_content": [
        r"\b(child|minor|underage|preteen)\b.{0,40}\b(sexual|nude|explicit|porn)\b",
        r"\bcsam\b",
    ],
    "self_harm_instructions": [
        r"\b(how (to|do i)|best way to|painless way to)\b.{0,40}\b(kill myself|suicide|end my life|self[- ]harm)\b",
        r"\b(suicide method|lethal dose)\b",
    ],
    "weapons_and_explosives": [
        r"\b(how (to|do i)|instructions? (for|to))\b.{0,40}\b(make|build|assemble)\b.{0,30}\b(bomb|explosive|pipe bomb|ied|nerve agent)\b",
        r"\b(untraceable|ghost) gun\b.{0,30}\b(build|make|blueprint)\b",
    ],
    "credential_theft": [
        r"\b(steal|harvest|phish|dump)\b.{0,30}\b(passwords?|credentials?|card numbers?|cvv)\b",
        r"\bkeylogger\b.{0,30}\b(install|deploy|code)\b",
    ],
    "doxxing": [
        r"\b(home address|residential address|personal phone number) of\b",
        r"\bwhere does\b.{0,40}\blive\b.{0,20}\bexactly\b",
    ],
}

_REDACTIONS = [
    # Payment card numbers, spaced or hyphenated
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[redacted-card]"),
    # Nigerian and international phone numbers
    (re.compile(r"(?:\+?234|0)[789]\d{9}\b"), "[redacted-phone]"),
    (re.compile(r"\+\d{1,3}[\s-]?\d{6,14}\b"), "[redacted-phone]"),
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]{2,}\b"), "[redacted-email]"),
    # Bearer tokens and API keys pasted into chat
    (re.compile(r"\b(?:sk|pk|ghp|gho|xoxb)-[A-Za-z0-9_\-]{12,}\b"), "[redacted-token]"),
]

# Prompt-injection markers are not blocked outright (they are common in
# legitimate security questions) but are flagged for logging.
_INJECTION = [
    re.compile(r"ignore (all )?(previous|prior|above) instructions", re.I),
    re.compile(r"you are now (in )?(developer|dan|god) mode", re.I),
    re.compile(r"reveal (your|the) (system )?prompt", re.I),
]


@dataclass
class ModerationResult:
    allowed: bool
    text: str
    categories: List[str] = field(default_factory=list)
    redactions: List[str] = field(default_factory=list)
    flagged: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "categories": self.categories,
            "redactions": self.redactions,
            "flagged": self.flagged,
        }


def _truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit]


def _scan(text: str) -> List[str]:
    hits = []
    for category, patterns in _BLOCKED.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                hits.append(category)
                break
    return hits


def _redact(text: str):
    found = []
    for pattern, replacement in _REDACTIONS:
        text, count = pattern.subn(replacement, text)
        if count:
            found.append(replacement.strip("[]"))
    return text, sorted(set(found))


def screen_input(text: str) -> ModerationResult:
    """Screen a user prompt before it reaches the model."""
    text = _truncate((text or "").strip(), MAX_INPUT_CHARS)
    categories = _scan(text)
    flagged = [p.pattern for p in _INJECTION if p.search(text)]
    cleaned, redactions = _redact(text)
    return ModerationResult(
        allowed=not categories,
        text=cleaned,
        categories=categories,
        redactions=redactions,
        flagged=flagged,
    )


def screen_output(text: str) -> ModerationResult:
    """Screen a model completion before it reaches the user."""
    text = _truncate((text or "").strip(), MAX_OUTPUT_CHARS)
    categories = _scan(text)
    cleaned, redactions = _redact(text)
    return ModerationResult(
        allowed=not categories,
        text=cleaned,
        categories=categories,
        redactions=redactions,
    )
