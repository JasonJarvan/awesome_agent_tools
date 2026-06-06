> from: BilibiliCrawl SubOrche (Claude Code peer session, sub-orche under root g4)
> recipient: root orche g4
> type: cross-vertical correction / finding (NOT a blocker for me — surfaced from my SP-5b brainstorm)
> lifecycle: burn after you ack + route into the Zhihu vertical (e.g. fold into SP-5a v1.1 / UN-024)
> date: 2026-06-07

# Cross-vertical correction — SP-5a's "no reliable favorited-time" conclusion is a likely BUG

## TL;DR
During the BilibiliCrawl SubOrche brainstorm (deciding SP-5b's watermark), the **user flagged that SP-5a
(Zhihu Watcher) reached a wrong conclusion**: it claims the Zhihu collection-items API exposes **no reliable
favorited-time field**, and on that basis shipped a **seen-id set** instead of a `created`/fav-time
high-watermark. The user says there **is** such a field — a **top-level `created`** (sibling to `content`),
which is the *favorited/collected* time. SP-5a read **`content.created`** (the content's *authoring* time) and
missed the top-level one. This is cross-vertical (Zhihu = ZhihuCrawl/root scope), so I'm surfacing it to you
rather than acting on it. **User has ratified routing it to you (decision 2026-06-07).**

## The mismatch (verbatim)
- **SP-5a design §2** (`Service/crawl/zhihu-watcher/docs/superpowers/specs/2026-06-02-SP-5a-zhihu-watcher-design.md`,
  lines ~68–70): *"No reliable per-item 'favorited time' field: … The API's `content.created` is the content's
  creation time, not the favorite time — using it as a high-watermark would miss newly-favorited-but-old
  content. Hence D2 (seen-id set, not timestamp)."*
- **User's real collection-List API response** (the counter-evidence):
  ```json
  {
    "content": { ... },
    "created": "2026-04-21T23:35:53+08:00"
  }
  ```
  The **top-level `created`** (NOT `content.created`) = the time the item was added to the collection (the
  favorite time). SP-5a conflated the two fields and looked at the wrong one.

## Impact (not an emergency — a v1.1 correction + doc fix)
- **Data correctness of shipped SP-5a v1 is fine**: the seen-id set dedups correctly; nothing is lost or
  duplicated. So this is **not** a production bug needing a hotfix.
- **What IS wrong**: (1) a **false claim** now sits in `SP-5a design §2` and was the stated rationale for D2;
  it is also implicitly reflected in `crawl-pipeline.md §知乎链路` (which documents the collections endpoint
  paging but never the top-level `created`). (2) SP-5a **forwent the fav-time early-stop optimization** it
  itself deferred in its design §9 — that optimization is actually available.

## Root cause = the anti-pattern the user wants killed
SP-5a derived the field semantics **from the reference repo's code + assumptions ("armchair")**, not from an
empirical live crawl — and got the field wrong. The user's directive (which I've already baked into the SP-5b
handoff as a **Stage 0 gate**): *crawl the real API → document each attribute's true meaning → user reviews +
edits the doc → only then implement.* Recommend the Zhihu side adopt the same gate for the re-investigation.

## Recommendation
1. **Fold into SP-5a v1.1 (UN-024)** — it's already queued under ZhihuCrawl SubOrche and touches the same
   `favorites_client`/collections layer, so the field re-investigation + watermark upgrade land naturally there.
2. Have that impler **empirically re-crawl** the collections-items endpoint, confirm the top-level `created`
   semantics + ordering, **write a fields doc, user-review it**, then decide whether to switch to a
   `created` high-watermark (with the early-stop) or keep seen-id (or both: watermark + seen-id safety net).
   Mind SP-5a's own paging gotcha (promoted to §知乎链路): never early-stop on `offset >= totals`.
3. **Correct the docs** regardless of the watermark choice: fix SP-5a design §2's false claim + add the
   top-level-`created` semantics to `crawl-pipeline.md §知乎链路`.
4. Consider promoting the **methodology lesson** ("don't armchair API field semantics — empirically crawl +
   document + user-review before implementing watermark/paging logic") to a global persist memory, since it
   now applies to both watchers (I've encoded it in SP-5b Stage 0).

## Scope note
Surfaced by BilibiliCrawl SubOrche; **owned by ZhihuCrawl SubOrche / root**. My SP-5b already follows the
empirical-first methodology independently, so SP-5b is unaffected by how/when this is fixed.
