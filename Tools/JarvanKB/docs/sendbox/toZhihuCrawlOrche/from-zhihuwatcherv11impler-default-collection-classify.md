> from: ZhihuWatcherV11Impler session (Claude Opus 4.8 1M, 2026-06-07)
> recipient: ZhihuCrawl SubOrche (my parent)
> mode: finding / new-SP proposal (NOT part of SP-5a v1.1 — see §3)
> purpose: propose "知乎默认收藏夹自动分类" as a NEW SP after v1.1; record the empirical basis +
>   recommended form so you can brainstorm/spawn it
> lifecycle: persist until you brainstorm it into an SP (or the user defers); then burn

# Finding / proposal — auto-classify the default collection (我的收藏)

The user wants items in the **default collection `我的收藏`** auto-classified into category folders. I
investigated the form + the data; summary below. **This is a separate SP, not v1.1** (§3).

## 1. Why it is NOT in the Engine, NOT in SP-5a-as-is, NOT in SP-3-as-is

- **Engine:** frozen, "one URL → Markdown", no LLM. Classification has no place there (the symmetric opposite
  of the ARTICLE-fetch gap, which DOES belong in the Engine — see my other letter
  `from-zhihuwatcherv11impler-engine-article-403-gap.md`).
- **SP-5a Watcher as-is:** has a **locked "no LLM / vault-agnostic" boundary** (design §1). Classification
  reopens that boundary → a deliberate, recorded change (CLAUDE.md add-only invariant), not a stealth add.
- **SP-3 Skill as-is:** the classify *capability* lives here (`zhihu_crawl.classify.classify(result,
  output_root, client)` + `jarvankb_common.LLMClient`; SP-0 §7/307 = "分类 = Skill 层 vague_path"), but SP-3
  is a one-shot CLI — it does **not** watch/poll. So it is the capability source, not the feature's home.

## 2. Recommended form (for your brainstorm)

**A new SP that extends the Watcher with an opt-in per-target `classify` mode, reusing a SHARED classifier
extracted from SP-3** (lifted into `jarvankb_common` / `Engine/common`, beside `LLMClient`) — not a fork.
Scope it to the **default collection only**: named collections are already user-categorized (subfolder =
collection name); only the default `我的收藏` is a flat inbox that needs LLM bucketing.

Empirical findings that make this clean (live crawl 2026-06-07, in the v1.1 fields doc
`Service/crawl/zhihu-watcher/docs/RepoMem/temp/sp5a-watcher-v1.1/api-fields-empirical.md`):

- **`is_default: true`** on the people/collections object cleanly flags `我的收藏` (id `721323262`) → trivial
  to target the default inbox without heuristics.
- **The collection-items LIST already carries a ~200-char body excerpt per item** (`content.excerpt_title`
  for articles, `content.excerpt` for answers). So the watcher can **classify from the list alone**:
  1. **no full fetch needed just to classify** (cheap);
  2. **the only content path for 专栏 — which is now PERMANENT.** SP-2 v1.2 found 专栏 `/api/v4/articles/{id}`
     is `x-zse-96`-gated and the user chose **no signer** (UN-028) → 专栏 full content is unfetchable via the
     engine. So the list excerpt is the *only* way to get 专栏 text for classification (and even a stub save).
- **The category vocabulary already exists.** The user set `output_dir` =
  `/home/shenzhou/Documents/Obsidian/JasonJarvan/ResourceBase资源库/Zhihu知乎`, which already holds **~33
  curated subfolders** (技术-*/生涯-*/娱乐-*/知识-*/赚钱-* + a flat `我的收藏/`). That is exactly what SP-3's
  `classify.existing_subfolders(output_root)` reads → the classifier buckets default-inbox items into these
  existing folders, no new taxonomy to invent.
- **Shared-classifier shape:** make it accept a generic `(title, lead_text)`. The **watcher** supplies
  `lead_text` from the list excerpt; the **Skill** supplies it from `content_markdown` (its current
  `_lead_text` lead — equal-or-richer, so SP-3 needs no change). One classifier, two input sources.

> Alternative (if you want SP-5a's boundary kept absolutely pure): a downstream classifier stage in the
> SP-6/SP-7 ingester layer. I do **not** recommend it first: SP-6/SP-7 are still placeholders (would block
> this), and a downstream stage loses the "this came from the default inbox" context the watcher already has.

## 3. Dependencies & ordering — AFTER v1.1, depends on it

- Rides on **v1.1's Mode-1 by-user discovery** (which surfaces `我的收藏` via `is_default`). I am already
  giving v1.1 the **near-zero-cost forward-compat hook**: `list_user_collections` preserves `is_default`, and
  the item parse preserves the excerpt fields — so this SP needs no re-fetch.
- Requires the **shared-classifier extraction** (touches SP-3) → cross-module → your call to coordinate.
- Reopens the SP-5a no-LLM boundary → needs explicit user sign-off + a boundary-change record.
- **Does NOT block v1.1.** v1.1 ships the two resolution modes + the watermark correction + 403-backoff;
  this classifier SP is a clean follow-on.

## 4. Request

When the user greenlights it, brainstorm this into its own SP (own spec/plan) and spawn an impler. The data
+ recommended form above should make the brainstorm short. Ping me (`toZhihuWatcherV11Impler/`) only if you
want the v1.1 forward-compat hook shaped differently.

— ZhihuWatcherV11Impler
