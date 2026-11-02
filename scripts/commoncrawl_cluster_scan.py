#!/usr/bin/env python3
"""Query Common Crawl CDX shards directly on data.commoncrawl.org.

Binary-searches each collection's cluster.idx with byte-range requests, then
range-fetches only the compressed CDX blocks that can hold a domain. This
avoids index.commoncrawl.org, which often answers HTTP 502/503/504 or refuses
connections. Results were checked against the index API on two known pairs
and matched row for row. Resumable: OUT maps "COLLECTION|label" to a query
outcome; only pairs whose outcome is "failed" are queried.
Usage: python scripts/commoncrawl_cluster_scan.py OUT.json [EXTRA.json]
EXTRA maps a label to a list of SURT key prefixes; every collection already
named in OUT is queried for each new label.
"""
import gzip, json, sys, time, pathlib, requests

OUT = pathlib.Path(sys.argv[1])
BASE = "https://data.commoncrawl.org/cc-index/collections/{}/indexes/"
SURT = {"bluescholars.com": "com,bluescholars", "prometheusbrown.com": "com,prometheusbrown",
        "sabzi.co": "co,sabzi", "masslinemedia.com": "com,masslinemedia",
        "bluescholars.livejournal.com": "com,livejournal,bluescholars"}
FIELDS = ("timestamp", "url", "mime", "digest", "status", "filename", "offset", "length")
s = requests.Session()
s.headers["User-Agent"] = "BlueScholarsRestoration/0.1 (historical research; sequential)"
state = json.loads(OUT.read_text())


def get(url, start, end):
    for attempt in range(4):
        try:
            r = s.get(url, headers={"Range": f"bytes={start}-{end}"}, timeout=60)
            if r.status_code in (200, 206):
                time.sleep(0.15)
                return r.content
            err = f"HTTP {r.status_code}"
        except requests.RequestException as exc:
            err = f"{type(exc).__name__}: {exc}"[:200]
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(err)


def size(url):
    r = s.head(url, timeout=60)
    r.raise_for_status()
    return int(r.headers["content-length"])


def line_at(url, pos, total):
    """First complete cluster.idx line starting after byte pos (or at 0)."""
    chunk = get(url, pos, min(pos + 4095, total - 1))
    if pos:
        nl = chunk.find(b"\n")
        if nl < 0:
            return None, None
        start = pos + nl + 1
        chunk = chunk[nl + 1:]
    else:
        start = 0
    end = chunk.find(b"\n")
    if end < 0:
        return None, None
    return start, chunk[:end].decode("utf-8", "replace")


def blocks_for(col, prefixes):
    """cluster.idx lines (blocks) that may contain keys starting with any prefix."""
    url = BASE.format(col) + "cluster.idx"
    total = size(url)
    lo_key = min(prefixes)
    hi_key = max(prefixes) + "￿"
    # Binary search for the last line whose key < lo_key.
    lo, hi = 0, total
    best = 0
    while hi - lo > 4096:
        mid = (lo + hi) // 2
        start, line = line_at(url, mid, total)
        if line is None or line.split(" ")[0] >= lo_key:
            hi = mid
        else:
            best, lo = start, mid
    out, pos = [], best
    while pos < total:
        chunk = get(url, pos, min(pos + 65535, total - 1))
        lines = chunk.split(b"\n")
        if pos + len(chunk) < total:
            lines = lines[:-1]  # drop partial line
        for raw in lines:
            pos += len(raw) + 1
            line = raw.decode("utf-8", "replace")
            if not line:
                continue
            key = line.split(" ")[0]
            if key > hi_key:
                return out
            out.append(line.split("\t"))
        if not lines:
            break
    return out


def rows_for(col, domain):
    p = SURT[domain]
    prefixes = p if isinstance(p, list) else [p + ")", p + ","]
    blocks = blocks_for(col, prefixes)
    rows = []
    for i, b in enumerate(blocks):
        shard, off, length = b[1], int(b[2]), int(b[3])
        data = gzip.decompress(get(BASE.format(col) + shard, off, off + length - 1))
        for raw in data.decode("utf-8", "replace").splitlines():
            key, ts, js = raw.split(" ", 2)
            if not key.startswith(tuple(prefixes)):
                continue
            rec = json.loads(js)
            if rec.get("status") != "200":
                continue
            rec["timestamp"] = ts
            rows.append({k: rec.get(k) for k in FIELDS})
    return rows, len(blocks)


if len(sys.argv) > 2:
    SURT.update(json.loads(pathlib.Path(sys.argv[2]).read_text()))
    cols = sorted({k.split("|")[0] for k in state})
    for label in json.loads(pathlib.Path(sys.argv[2]).read_text()):
        for col in cols:
            state.setdefault(col + "|" + label, {"outcome": "failed", "error": "not yet queried"})
todo = [k for k, v in state.items() if v.get("outcome") == "failed"]
print(len(todo), "failed pairs to retry", flush=True)
by_col = {}
for k in todo:
    col, dom = k.split("|")
    by_col.setdefault(col, []).append(dom)
for col in sorted(by_col):
    for dom in by_col[col]:
        key = col + "|" + dom
        rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "via": "cluster.idx"}
        try:
            rows, nblocks = rows_for(col, dom)
            rec.update(outcome="ok" if rows else "empty", rows=rows, blocks=nblocks)
        except Exception as exc:
            rec.update(outcome="failed", error=f"{type(exc).__name__}: {exc}"[:300])
        state[key] = rec
        OUT.write_text(json.dumps(state))
        print(col, dom, rec["outcome"], len(rec.get("rows", [])), rec.get("error", ""), flush=True)
