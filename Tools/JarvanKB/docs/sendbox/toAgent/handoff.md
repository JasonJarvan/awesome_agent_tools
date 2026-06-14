> from: JarvanKB maintainer (Zhihu sections by ZhihuCrawl SubOrche, 2026-06-14)
> recipient: any calling agent (Hermes / Claude Code / scripted client)
> purpose: stable consumer-facing contract for using JarvanKB tools
> lifecycle: persist — changes flow through RepoMem.merge HITL (same gate as `persist/` docs)

# JarvanKB — Caller Agent Handoff

JarvanKB is a **pure tool collection** (skills + services), agnostic to who calls it. This letter is the
single entry point a calling agent reads to learn **when** to use a tool, **how** to invoke it, **what
credentials** to verify first, and **what to do on failure**.

> **Status (2026-06-14):** Zhihu sections (SP-3 skill, SP-5a watcher, SP-1 cookie pre-flight, LLM) are
> COMPLETE and live-verified. Bilibili sections are owned by the **BilibiliCrawl SubOrche** (SP-4b/5b);
> the ingester layer (SP-6 CrawlMdSaver / SP-7 Thino) is owned by **MainOrche** — both marked TODO below.
> The pre-R5 Tingwu / Playwright-CDP design is **dead** — ignore any older reference to it.

## 1. Trigger conditions — when to reach for JarvanKB
- You have a **Zhihu URL** (answer / 专栏 article / question) and want it saved as Markdown (optionally
  auto-filed into a knowledge-base folder) → **`zhihu-crawl` skill** (§2.A).
- You have a **Bilibili video** (BV / URL) and want metadata + transcript Markdown → **`bilibili-crawl` skill**
  (§2.B — BiliOrc).
- You want a folder of **favorited content** kept in sync automatically (no per-item call) → the **watcher
  services** run autonomously and populate an output dir; you just read the resulting Markdown (§2.C).
- You want crawled content **merged with your own notes** / ingested into an Obsidian vault → ingester layer
  (§2.D — MainOrche/SP-6/SP-7, not yet built).

## 2. Tool catalog

### 2.A `zhihu-crawl` (SP-3 skill) — Zhihu URL → Markdown  ✅ live-verified
- **Agent entry**: `Skill/crawl/zhihu-crawl/SKILL.md` (agentskills.io format — Claude Code / Codex / OpenClaw / Hermes).
- **Install**: `pip install -e Engine/common -e Engine/zhihu -e Skill/crawl/zhihu-crawl`.
- **Python**: `from zhihu_crawl import save_zhihu, SaveResult`
  `save_zhihu(url, save_path=None, *, with_comments=False, comment_limit=None, profile=None, config_path=None) -> SaveResult`
- **CLI**: `zhihu-crawl <url> [--out PATH] [--comments] [--comment-limit N] [--json] [--profile NAME] [--config PATH]`
- **Save-path semantics**: `save_path` ending in `.md` = **explicit** (write there verbatim); a directory /
  `output_root` / `None` / empty = **vague** → the skill calls the LLM to classify into a subfolder under
  `output_root` (and may propose a new subfolder).
- **Output** (`SaveResult`, also `--json` for machine parse): `{path, title, type, url, category, was_vague, proposed_new}`.
- **Exit codes**: `0` ok · `1` config/cookie/LLM error · `2` `ZhihuFetchError` (engine fetch failed).
- **Contract**: `Skill/crawl/zhihu-crawl/docs/interface.md` (frozen). Pure consumer of the frozen SP-2 engine
  + `jarvankb_common.LLMClient` — does not hold its own engine/LLM internals.

### 2.B `bilibili-crawl` (SP-4b skill) — Bilibili video → transcript Markdown  ✅ live-verified
> **TODO — owned by BilibiliCrawl SubOrche.** Mirror of §2.A's shape (URL → cookie → frozen SP-4a engine →
> save + vague-path classify). Contract: `Skill/crawl/bilibili-crawl/docs/interface.md` (frozen);
> agent entry `Skill/crawl/bilibili-crawl/SKILL.md`. Cookie domain = `bilibili.com` (no dot). BiliOrc to
> fill the invocation/exit-code/config detail + the BN (BiliNote) transcribe dependency here.

### 2.C Watcher services (SP-5a Zhihu / SP-5b Bilibili) — autonomous favorites sync
- **You do NOT call these.** They run as daemons (APScheduler), poll the user's favorites on a schedule, and
  write Markdown into a configured `output_dir`. A calling agent simply **reads** the resulting files.
- **SP-5a Zhihu** ✅: `python -m zhihu_watcher [--config PATH] [--once]`; config = `targets` (collection / user),
  `output_dir`, `state_dir`, `cookie_source`, `only_after`, backoff. Contract:
  `Service/crawl/zhihu-watcher/docs/interface.md`. (SP-5a **v1.2** will add opt-in LLM auto-classify of the
  default collection — in flight, owned by MainOrche.)
- **SP-5b Bilibili**: TODO — BiliOrc.

### 2.D Ingester layer (SP-6 CrawlMdSaver / SP-7 ThinoIngester) — merge-with-notes + Obsidian/Thino
> **TODO — owned by MainOrche.** Not yet built. SP-6 = register crawl skills, input = URL+notes /
> source-doc+notes → merged Markdown (frontmatter carries note metadata). SP-7 = watch the Obsidian Thino
> path, parse Thino blocks → call SP-6 → append organized result back. This is the path for "let the agent
> process the Obsidian vault." MainOrche fills this once SP-6/SP-7 land.

## 3. Pre-flight credential check (verify BEFORE any call)
1. **Cookie source (SP-1 CookieManager)** reachable — all cookie-needing tools **actively pull** the cookie at
   call time (JarvanKB never stores plaintext cookies). Verify `GET <base_url>/health` → `200`. Config needs
   `base_url` + box `uuid` + decryption `password` (skill: `config.yaml` `cookie:` block, `password_env`;
   watcher: `cookie_source:` block). **Zhihu cookie domain key = `.zhihu.com` (WITH leading dot)** — the
   undotted `zhihu.com` box is empty. (Bilibili = `bilibili.com`, no dot.)
2. **Fresh Zhihu `__zse_ck`** — Zhihu navigation pages (answers + 专栏 articles) need a **fresh** `__zse_ck`
   cookie; if stale/missing the page returns a 403 anti-bot challenge (NOT recoverable by retry — only fresh
   cookie helps). Keep the CookieCloud browser extension syncing. (Background: UN-032; `crawl-pipeline.md §知乎链路`.)
3. **LLM credentials** (only for the vague-path classification, not for plain fetch) — `jarvankb_common.LLMClient`
   reads `config/llm.yaml` + a key in `.env` (default provider `mimo-v2.5-pro`, OpenAI protocol). If absent,
   pass an explicit `.md` save path to skip classification entirely.
4. **Config-path env** — the skill resolves config relative to CWD unless you set `ZHIHU_CRAWL_CONFIG`
   (and `JARVANKB_LLM_CONFIG` for the LLM config) to absolute paths. Set these when invoking from another CWD.

## 4. Fallback policy (v2 — NOT Tingwu/Playwright)
- **`ZhihuFetchError` (exit 2)**: the engine tried all strategies (initialData → CSS-scrape → ANSWER-only
  `/api/v4` fallback). Most common real cause = **stale `__zse_ck`** (see §3.2) → refresh cookie and retry.
  **专栏 article body** is fetchable via the primary nav-GET with a fresh cookie; the `/api/v4/articles` API
  is **signature-gated (no fallback)** by design (D1 — no signer).
- **Rate limiting**: handled **inside** the engine (active min-interval + jitter + 403/429 backoff honoring
  `Retry-After`); a bulk caller benefits automatically, a single-URL call is near-instant. Do not add your own
  retry loop on top.
- **Vague-path classification fails** (LLM down): fall back to passing an explicit `.md` `--out` path.
- **Watcher**: failed items are not marked seen → retried next cycle (bounded by failure-backoff). No caller action.

## 5. Output format
- **Markdown** with YAML frontmatter (`title, author, url, type, vote_count, comment_count, created_at,
  updated_at, fetched_at, source: zhihu`) + body; remote image URLs preserved (not downloaded).
- **`SaveResult`** (skill, via `--json`): see §2.A — machine-parseable for an agent to learn where the file
  landed + whether/how it was classified.

## What lives here / does NOT
- HERE: how a caller agent uses JarvanKB (this letter + future `from-maintainer-<topic>.md` capability/breaking-change notes).
- NOT here: HarnessStack/RepoMem task coordination (`to<Role>/`); transient stop-and-ask (standard letter lifecycle); implementation details (`docs/RepoMem/persist/architecture/`).
- Lifecycle `persist` → not subject to default burn; any change flows through `RepoMem.merge` HITL.
