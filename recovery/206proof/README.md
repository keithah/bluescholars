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

The local candidate renderer is `restore/proof206.py`. It produces the `206proof/` edition hub and separate 2007 Vanilla, 2008–2012 Vanilla, 2012–2013 community, and 2013–2014 vBulletin routes during `restore build --candidate`. Original 2007 theme CSS has no successful indexed capture; the candidate uses same-site Vanilla CSS from 2010 with a visible notice and source timestamp. This is a documented legibility fallback, not a claim that the 2007 appearance is fully recovered. Posting forms and scripts are disabled, and unmatched same-site links point to labeled gap pages.

The latest build is a local unreviewed candidate. After each HTML batch, update the asset and media indexes, run the candidate build, then validate it with `restore check --candidate --base-path /bluescholars`. The latest attempt covered 1,360 of 5,137 selected Vanilla routes; 3,777 remain queued. Continue in bounded batches. Do not copy original posts, images, or audio to public output before rights review.
