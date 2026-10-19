# Local 206proof recovery checkpoint

This directory is a resumable source checkpoint; it is not part of the public static site. `all-events-all-status.json` and `all-events-200.json` preserve the complete returned CDX query rows and response hashes. `recovered-resources.json` records each requested capture, validation result, actual replay timestamp, and content-addressed raw file. Do not remove `raw/` if resuming.

From the project root:

```bash
.venv311/bin/python scripts/recover_206proof_vanilla.py --limit 160 --delay 0.6
.venv311/bin/python scripts/index_206proof_assets.py
.venv311/bin/python scripts/index_206proof_media.py
.venv311/bin/python scripts/recover_206proof_assets.py
```

The Vanilla command selects the latest HTTP-200 HTML response per exact URL for 2008–2012. It preserves host aliases, paths, and query strings. It attempts only the next 160 unattempted captures; rerun to continue. Asset recovery uses the source-reference map and shares the same manifest. The index and raw captures remain local until a later publication/rights review determines what belongs in a public site build.
