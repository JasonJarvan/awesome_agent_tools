---
slug: sp5a-watcher-v1.1
status: active
domains:
  - crawl-pipeline
  - credentials
updated_at: 2026-06-07
task_type: feature
---

# SP-5a v1.1 — empirical Zhihu API field study (Stage-0 gate)

> **Methodology gate** (per `docs/sendbox/toOrchestrator/from-bilibilicrawlorche-sp5a-watermark-correction.md`):
> crawl the REAL API → document each attribute's true meaning → **user reviews + edits this doc** → only
> then implement watermark/paging/classifier logic. Do NOT armchair field semantics from a reference repo.
>
> **Provenance:** live crawl 2026-06-07, real SP-1 cookies (account `jasonjarvan`, 15 `.zhihu.com` cookies),
> direct connect (`trust_env=False`), plain cookie + browser headers, **NO `x-zse-96`**. Three endpoints hit
> against the real account `zhao-cheng-57-99-79`. Probe script: throwaway `/tmp/zhihu_api_probe.py` (not committed).

## 0. Headline corrections (vs SP-5a v1 design)

1. **The favorite-time field DOES exist** — SP-5a v1 design §2's "no reliable favorited-time field" is a
   **confirmed bug**. Each collection item carries a **top-level `created`** (sibling to `content`) = the
   time the item was added to the collection. v1 looked at `content.created` (authoring time) and missed it.
2. **BUT items are NOT ordered by favorite-time** → the deferred "fav-time early-STOP paging optimization"
   is **NOT safely available** as the SubOrche letter assumed. A high-watermark *filter* is possible; an
   *early-stop* is not (without a verified sort param). See §3.
3. **A rich per-item content excerpt is in the LIST response** (no full fetch needed) → enables
   classify-from-list and survives the 专栏-403 fetch gap. See §4.

## 1. `GET /api/v4/me`  (resolve `me` → url_token)  — HTTP 200, unsigned ✓

Works with plain cookie, no signing. Resolves the current cookie user. Fields used:

| field | meaning | v1.1 use |
|---|---|---|
| `url_token` | the account's stable handle (here `zhao-cheng-57-99-79`) | resolve config `url_token: me` → this |
| `id` | opaque internal user id | (not needed) |
| `name` | display name (`晓日晨`) | logging only |

**Residual-risk RESOLVED:** `me` support is safe to ship — `/api/v4/me` is plain-cookie/200.

## 2. `GET /api/v4/people/{url_token}/collections`  (Mode-1 discovery)  — HTTP 200 ✓

`paging = {is_start, is_end, next (full cursor URL), previous, totals: 35}` — both a cursor `next` AND a
`totals`. The account has **35 collections** (20 per page). Each `data[]` collection object:

| field | meaning | v1.1 use |
|---|---|---|
| `id` (int) | collection id | feed the existing per-collection poll loop |
| `title` | collection name (e.g. `技术-AI生成`) | subfolder name for discovered collections |
| **`is_default`** (bool) | **`true` ONLY for the default `我的收藏`** (here id=721323262) | **lets the future classifier target the default inbox**; lets v1.1 special-case it if desired |
| `item_count` (int) | # items in the collection (109, 94, 212…) | logging / future progress; could skip empty (item_count=0) collections |
| `updated_time` (epoch) | last change to the collection | **the list is sorted by this DESC** (我的收藏 first) |
| `is_public`, `description`, `creator`, counts… | metadata | not needed by the watcher |

**Ordering:** collections come back **`updated_time` DESC** (most-recently-touched first). `我的收藏` was
first only because it was most-recently updated, not because it is default.

**Default collection identified:** `我的收藏` = id `721323262`, `is_default=true`, `item_count=109`.

## 3. `GET /api/v4/collections/{id}/items`  (the watermark fields)  — HTTP 200 ✓

`paging = {is_start, is_end, next, previous, totals}`. Each `data[]` item has top-level keys
**`['content', 'created']`**.

| field | meaning | evidence | v1.1 use |
|---|---|---|---|
| **top-level `created`** (ISO8601 str, e.g. `2026-05-23T09:00:04+08:00`) | **the FAVORITE time** — when the item was added to this collection | present on every item, sibling to `content` | the real fav-time watermark candidate |
| `content.created` / `content.created_time` (epoch int) | the **content's authoring** time (≠ favorite time) | article: `created=1779498004`; answer: `created_time=1755446550` | NOT a fav-time; do not use as watermark |
| `content.type` | `"article"` / `"answer"` / … | — | dedup key + excerpt-field selection |
| `content.id` | content id | — | dedup key `f"{type}:{id}"` (unchanged from v1) |
| `content.url` | canonical content URL | article→`zhuanlan.zhihu.com/p/{id}`, answer→`/question/{q}/answer/{id}` | fed to SP-2 `fetch()` (unchanged) |

### 3.1 CRITICAL: items are NOT ordered by favorite-time → no safe early-stop

Top-level `created` across the first 3 items of two collections (offset 0–2):

- `我的收藏` (721323262): `[0]=2026-05-23`, `[1]=2026-05-13`, `[2]=2026-05-30` — non-monotonic.
- `生涯-育儿` (343827655): `[0]=2025-08-18` (≈1yr old), `[1]=2026-05-05`, `[2]=2026-05-04` — item[0] far older than the next two.

⇒ The default item ordering is **NOT favorite-time-descending** (the exact sort key was not determined —
possibly content recency / pinned / internal). **Consequence:** a naive "stop paging when an item is older
than the watermark" would MISS newer items buried after older ones (e.g. in 育儿 it would stop at item[0]
and never see [1]/[2]). **Early-stop is unsafe.** A high-watermark *filter* (skip items whose top-level
`created <= watermark` while still paging the whole list) is safe but only saves fetch+save work, not the
listing work. If a true early-stop is wanted, a follow-up must probe for an `order_by`/`sort` query param.

### 3.2 Watermark recommendation (for user review)

Keep the **seen-id set as the correctness backbone** (robust regardless of ordering — already shipped, already
proven). The empirical add is: **parse and expose the top-level `created`** so we *can* offer an optional
"only save items favorited on/after `<date>`" filter (useful to avoid back-filling years of history on a
brand-new `me`/by-user watch of 35 collections × hundreds of items). **Do NOT implement the early-stop.**

## 4. Content excerpt fields (the classifier-input question)

A rich body excerpt is present in the LIST response, under **different keys per type**:

| content.type | excerpt field (≈200-char body lead) | title field | other |
|---|---|---|---|
| `article` (专栏) | **`excerpt_title`** (NB: misnamed — it is a BODY lead, not the title) | `content.title` (the real title) | `content.excerpt` is absent/None |
| `answer` | **`excerpt`** | `content.question.title` (answers have no own title; `content.title` is None) | `content.excerpt_title` absent/None |

Both excerpts are ~200 chars of real opening text, **HTML-entity-escaped** (e.g. `&#34;`, `[图片]` image
placeholders) → need `html.unescape` + light cleanup. Example (article): `excerpt_title` = *"Polymarket上一个叫
Coinman two的地址，一年多的时间，做了3237次预测…"*. Example (answer): `excerpt` = *"那是没有用对错题本。现在请把你手上的错题本…"*.

### 4.1 Is the excerpt a good classification input? — YES, for the WATCHER

`(title, excerpt)` from the list is a near-equivalent of what SP-3's classifier reconstructs from a FULL
fetch (`classify._lead_text(content_markdown, 240)` strips markdown to a ~240-char lead). So the watcher can
classify **from the list alone**, with two wins:
1. **No full fetch needed just to classify** (cheaper; one list call already has everything).
2. **Survives the 专栏-403 fetch gap — and that gap is PERMANENT** — the excerpt is in the list even though
   SP-2 cannot fetch 专栏 full content. SP-2 v1.2 found 专栏 `/api/v4/articles/{id}` is `x-zse-96`-gated and
   the user chose **no signer** (UN-028) → 专栏 full content is unfetchable via the engine for the foreseeable
   future. So the list **excerpt is the only 专栏 content path**; a default-collection classifier (and even a
   stub save) can still work on 专栏 items.

Caveat: an excerpt is shorter than full content → slightly weaker signal for long/rambling pieces; acceptable
for a folder-bucket classification (not a summarization).

### 4.2 Does this hold for the "Skill" (SP-3, answer-ID / URL crawl)? — NO, and it doesn't need to

SP-3 is given a single URL and fetches the FULL content via the engine; it does **not** go through the
collection-items list, so it has **no list excerpt**. But it already has the full body, and
`_lead_text(content_markdown)` gives an **equal-or-richer** lead than a 200-char excerpt → SP-3's current
classification input is fine and needs no change. (Side note: the answer detail the engine fetches does carry
its own `excerpt`, but SP-3 doesn't need it — full content lead ≥ excerpt.)

**Design implication for the shared classifier (future classifier SP):** make the classifier accept a generic
`(title, lead_text)` pair and be agnostic to the lead's origin. The **watcher** supplies `lead_text` from the
list excerpt (cheap, pre-fetch, 403-proof); the **Skill** supplies it from `content_markdown`. One classifier,
two input sources — no fork, no watcher-side fetch-just-to-classify.

## 5. Open questions for the user (Stage-0 review)

1. **Watermark:** OK to keep seen-id as the backbone + add an *optional* "favorited on/after `<date>`" filter
   (parsed from top-level `created`), and **skip the early-stop** (unsafe per §3.1)? Or do you want a follow-up
   probe for a sort param to enable a true early-stop?
2. **First-sync flood:** a fresh `me`/by-user watch = 35 collections × up to ~200 items each. Want a default
   "favorited since deploy" guard (via the filter above) so v1.1 doesn't back-fill years on first run?
3. **Empty collections:** skip `item_count == 0` collections during discovery? (cheap; e.g. `产品思维`=0.)
4. **Doc fixes (will do regardless):** correct SP-5a design §2's false claim; add top-level-`created` semantics
   + the "not fav-time-ordered" caveat to `crawl-pipeline.md §知乎链路`; promote the methodology lesson
   ("empirically crawl + document + user-review before watermark/paging logic") to global persist at Step 8.
