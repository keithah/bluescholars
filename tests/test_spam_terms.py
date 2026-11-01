from restore.artist_sites import _is_compromised_html
from restore.spam import contains_spam_terms


def test_political_words_are_not_pharmacy_spam():
    # "socialist", "socialism" and Godard's "Socialisme" all contain "cialis".
    body=b'<html><head><title>TRAILER: Socialisme | Prometheus Brown</title></head><body>A socialist state; socialism.</body></html>'
    assert not _is_compromised_html(body)
    assert not contains_spam_terms('mccain calls obama a socialist')


def test_injected_pharmacy_and_casino_spam_is_still_detected():
    assert _is_compromised_html(b'<html><head><title>Cialis Get Viagra</title></head><body></body></html>')
    assert contains_spam_terms('buy cheap viagra online')
    assert contains_spam_terms('best casino bonus today')
    assert contains_spam_terms('this domain is for sale')
