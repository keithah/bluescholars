# Additional request observations — October 15, 2026

These results supplement the per-resource manifest. They are not site payload downloads.

| Probe | Observed result | Interpretation |
| --- | --- | --- |
| Direct original-homepage `20210529010817id_` request from execution environment | DNS resolution failure for web.archive.org | No response bytes or origin status obtained. |
| Same raw-homepage probe through web reader | URL inaccessible | Does not establish a missing snapshot. |
| Domain CDX JSON request | Inaccessible through reader | The full capture index was not obtained. |
| June 11, 2016 date-based third-listing request | Inaccessible | Toolbar advertises that date, but good page content and exact timestamp remain unverified. |
| June 2016 Shop date probe | Inaccessible | A search lead only. |
| October 2013 Shop date probe | Inaccessible | A search lead only. |
| Availability API near June 2016 for the third listing | Inaccessible | No closest-snapshot result was obtained. |
| Original July 19, 2019 blog request | Redirected to 20190719224804 and displayed a provider error | Wrong source for blog content; a different 2020 capture is readable. |
| Homepage photograph ordinary wrapper | Resolved to 20210529010844 | Exact asset capture established, 27 seconds later than reference HTML. |
| Four Eugene image-context (`im_`) requests | Images displayed | Positive visual response, no local binaries saved. |
| Four Eugene ordinary-wrapper requests | Tool cache misses | Exact resolved asset captures not established; does not negate positive image-context observations. |
| All eleven archived YouTube players | Error pages; nine player titles available in metadata | Embed IDs known; video binaries and current playback unverified. |

The 42-image tally describes the best established state for each original image URL using the inspected image-context requests: five displayed, three reported 404, thirty-four tool cache misses. It is not a tally of every HTTP request or every replay modifier.
