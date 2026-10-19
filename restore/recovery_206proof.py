"""Selectors for the source-backed 206proof.com forum editions."""
from __future__ import annotations

from urllib.parse import urlsplit


def select_latest_vanilla(rows: list[dict]) -> list[dict]:
    """Select the latest valid Vanilla HTML capture per exact URL through 2012.

    Query strings and host aliases remain distinct because they can represent
    different pages or independently archived source records.
    """
    selected: dict[str, dict] = {}
    for row in rows:
        if row.get("statuscode") != "200" or row.get("mimetype") != "text/html":
            continue
        timestamp = str(row.get("timestamp", ""))
        if len(timestamp) < 4 or not timestamp[:4].isdigit() or not 2008 <= int(timestamp[:4]) <= 2012:
            continue
        try:
            path = urlsplit(row.get("original", "")).path
            _ = urlsplit(row.get("original", "")).port
        except ValueError:
            continue
        if not path.startswith("/forum/"):
            continue
        key = row["original"]
        previous = selected.get(key)
        if previous is None or timestamp > str(previous.get("timestamp", "")):
            selected[key] = row
    return sorted(selected.values(), key=lambda row: row["original"])
