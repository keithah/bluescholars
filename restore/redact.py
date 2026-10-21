"""Remove credential-shaped values from public source derivatives."""
from __future__ import annotations
import re

_GOOGLE_MAPS_KEY = re.compile(rb'("googleMapsStaticApiKey"\s*:\s*")[^"\\]*(")')
_STRIPE_PUBLISHABLE_KEY = re.compile(rb'pk_(?:live|test)_[A-Za-z0-9]{20,}')


def redact_public_credentials(body: bytes) -> tuple[bytes, int]:
    """Redact credential-shaped API values without changing other source bytes."""
    body, maps_count = _GOOGLE_MAPS_KEY.subn(rb'\1\2', body)
    body, stripe_count = _STRIPE_PUBLISHABLE_KEY.subn(b'[redacted-publishable-key]', body)
    return body, maps_count + stripe_count
