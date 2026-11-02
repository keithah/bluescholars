"""Shared detection of spam-injected or parked-domain captures."""
from __future__ import annotations
import re

# Whole words only: substring matching flagged genuine political posts,
# because "socialist", "socialism" and "Socialisme" all contain "cialis".
SPAM_TERMS = re.compile(
    r"\b(?:cialis|viagra|levitra|phentermine|online pharmacy|casino bonus|domain is for sale)\b",
    re.IGNORECASE)


def contains_spam_terms(text: str) -> bool:
    return SPAM_TERMS.search(text) is not None
