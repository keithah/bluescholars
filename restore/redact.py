"""Remove credential-shaped values from public source derivatives."""
from __future__ import annotations
import re

_GOOGLE_MAPS_KEY = re.compile(rb'("googleMapsStaticApiKey"\s*:\s*")[^"\\]*(")')
_STRIPE_PUBLISHABLE_KEY = re.compile(rb'pk_(?:live|test)_[A-Za-z0-9]{20,}')


def public_credential_fields(body: bytes) -> list[str]:
    """Return names of credential-shaped fields present in archived bytes."""
    fields = []
    if _GOOGLE_MAPS_KEY.search(body):
        fields.append("googleMapsStaticApiKey")
    if _STRIPE_PUBLISHABLE_KEY.search(body):
        fields.append("Stripe publishable API key")
    return fields


def redact_public_credentials(body: bytes) -> tuple[bytes, int]:
    """Redact credential-shaped API values without changing other source bytes."""
    body, maps_count = _GOOGLE_MAPS_KEY.subn(rb'\1\2', body)
    body, stripe_count = _STRIPE_PUBLISHABLE_KEY.subn(b'[redacted-publishable-key]', body)
    return body, maps_count + stripe_count
