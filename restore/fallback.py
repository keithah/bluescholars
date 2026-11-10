"""Send unrecovered pages to the closest recovered copy of the same page.

A page missing from one edition often survives in another. Browsing should
open that saved copy instead of a placeholder: the latest copy captured no
later than the edition being browsed, or failing that the earliest later one.
"""
from __future__ import annotations

import html
import re
from urllib.parse import unquote

RECOVERED = ('recovered', 'recovered_from_feed', 'derived_from_capture')
# Latest capture each Blue Scholars edition stands for.
EDITION_END = {'2007': '20081231235959', '2009': '20121231235959'}
LATEST = '29991231235959'


def page_keys(url: str) -> list[tuple]:
    """Identity keys for one original page URL, strongest first."""
    rest = str(url).split('://', 1)[-1]
    host, _, rest = rest.partition('/')
    host = host.lower().split(':')[0].removeprefix('www.')
    rest = rest.split('#', 1)[0]
    path, _, query = rest.partition('?')
    path = unquote(path).lower().strip('/')
    keys: list[tuple] = [('url', host, path, query)]
    stem = re.sub(r'\.(?:html?|php)$', '', path).rstrip('/')
    # A query-only URL such as /?p=12 is not the homepage.
    if stem or not query:
        keys.append(('path', host, stem))
    last = stem.rsplit('/', 1)[-1]
    # WordPress posts move between date-based and flat permalinks.
    if '-' in last and len(last) >= 8:
        keys.append(('slug', host, last))
    return keys


def choose(candidates: list[dict], limit: str) -> dict:
    """Latest capture not after limit, else the earliest later capture."""
    def stamp(row):
        return str(row.get('actual_capture') or '')
    before = [row for row in candidates if stamp(row) <= limit]
    if before:
        return max(before, key=lambda row: (stamp(row), row['path']))
    return min(candidates, key=lambda row: (stamp(row), row['path']))


def edition_limit(path: str) -> str:
    return EDITION_END.get(path.strip('/').split('/', 1)[0], LATEST)


def page_fallbacks(page_report: list[dict]) -> dict[str, dict]:
    """Map each unrecovered page path to the recovered row that should open."""
    index: dict[tuple, list[dict]] = {}
    for row in page_report:
        if row.get('status') in RECOVERED and row.get('canonical_url'):
            for key in page_keys(row['canonical_url']):
                index.setdefault(key, []).append(row)
    fallbacks = {}
    for row in page_report:
        if row.get('status') != 'not_recovered' or not row.get('canonical_url'):
            continue
        for key in page_keys(row['canonical_url']):
            candidates = [c for c in index.get(key, []) if c['path'] != row['path']]
            if candidates:
                fallbacks[row['path']] = choose(candidates, edition_limit(row['path']))
                break
    return fallbacks


def capture_label(stamp: str) -> str:
    stamp = str(stamp or '')
    if len(stamp) >= 8 and stamp[:8].isdigit():
        return f'{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}'
    return 'another edition'


def redirect_page(target: str, capture: str) -> str:
    """A placeholder replacement that opens the saved copy at once."""
    href = html.escape(target, quote=True)
    when = html.escape(capture_label(capture))
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta http-equiv="refresh" content="0; url={href}">'
            '<title>Opening the closest saved copy</title></head><body><main>'
            '<p>This page was not saved in this edition.</p>'
            f'<p><a href="{href}">Open the closest saved copy ({when})</a></p>'
            '</main></body></html>')
