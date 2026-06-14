> from: BilibiliCrawl SubOrche (sub-orchestrator under root g4)
> recipient: WatcherDeployImpler (a Claude Code peer session, cwd = repo root)
> mode: child-handoff (sendbox-protocol Mode A — SubOrche stays alive; you converge back)
> purpose: bring up BOTH watcher services (SP-5a Zhihu + SP-5b Bilibili) as persistent daemons + verify live
> lifecycle: burn after you write `from-watcherdeployimpler-done.md` and SubOrche reads it

# Handoff — Watcher services bring-up + live verification (SP-5a + SP-5b)

## 0. What you are
An **ops / deployment impler**, child of BilibiliCrawl SubOrche. The two watchers are code-complete + merged +
unit-verified, but have only ever run `--once` — **neither is running as a persistent daemon**. Your job =
bring **both** up as resident services and verify a real first cycle + dedup. This is **ops + config + verify**,
**NOT** a code change. Use `superpowers:verify` discipline (run it, observe real behavior, evidence before claims).

## 1. Stage 0 — confirm config with the USER first (gate)
Before `up -d`, confirm with the user (write `from-watcherdeployimpler-blocker-config.md` to
`toBilibiliCrawlOrche/`, or ask in chat):
1. **Output (vault) root** — where each watcher writes Markdown. **Default proposal: `~/KB/zhihu/` and
   `~/KB/bilibili/`** (mirrors where SP-4b's live smoke already wrote: `~/KB/bilibili/music-videos/…`). The
   user MAY point these at their real Obsidian vault subdirs. **This is the one decision you must get from the user.**
2. **Which collections/folders** each watches:
   - SP-5a (Zhihu): the user's collection(s)/by-user target(s) (`targets` schema; v1.1).
   - SP-5b (Bilibili): design defaults = folders `AI生成` (2216104467) + `编程折腾` (1195057867); confirm or adjust.
3. **Poll intervals** (SP-5a default 30–60 min; SP-5b default ~20 min) — confirm or accept defaults.
4. **SP-1 cookie-manager connection** (box uuid/password/base_url) — the watchers pull cookies from it each cycle.

## 2. Bring-up + verify (definition of done)
For EACH watcher (`Service/crawl/zhihu-watcher/`, `Service/crawl/bilibili-watcher/`):
- Fill the real `config.yaml` from the example (output dir, targets, interval, SP-1 conn).
- `docker compose up -d` (both use `network_mode: host`; **no port mapping** — they're outbound pollers, the
  48xxx port rule does not bind them).
- **Verify live**: first cycle pulls cookie from SP-1 → lists favorites → fetches new items → saves Markdown
  to the vault dir; a **second cycle saves 0 new** (dedup/watermark works). Capture evidence (saved paths +
  log lines + watermark/seen state).
- **Bilibili watcher specifics**: it drives the engine → BN → bcut. (a) **unset `ALL_PROXY`/`HTTP(S)_PROXY`**
  in its runtime or it hits the `socksio` ImportError connecting to local BN (runbook gotcha). (b) BN must be
  up (`127.0.0.1:3015`) + have a **fresh SESSDATA** — the host cron `bn-cookie-sync.py` (`*/10`) keeps BN's
  downloader cookie current (UN-035 prevention); confirm it's installed/running, else transcription 412s.

## 3. Inputs (minimum)
| Resource | Role |
|---|---|
| `Service/crawl/zhihu-watcher/docs/{interface,runbook}.md` + `config.example.yaml` + compose | SP-5a deploy contract |
| `Service/crawl/bilibili-watcher/docs/{interface,runbook}.md` + `config.example.yaml` + compose | SP-5b deploy contract (runbook §5 = 412 SOP + ALL_PROXY) |
| `docs/RepoMem/persist/architecture/credentials.md` | SP-1 cookie pull (`bilibili.com` no-dot / `.zhihu.com` with-dot) |
| `Engine/bilibili/deploy/bilinote/` (README + `bn-cookie-sync.py`) | BN + the cookie-sync cron (UN-035) |
| live env | `jarvankb-bilinote`@`127.0.0.1:3015`, `cookie-manager`@`48088` (both up) |
| `~/.claude/skills/{superpowers/verify,sendbox-protocol,cc-dashboard,ops-doc-maintainer}` | your protocols |

## 4. Scope / boundaries
- **Ops only**: config + `compose up` + verify. Do NOT change watcher CODE (frozen contract). If a real code
  bug surfaces at bring-up, STOP + escalate to me (`from-watcherdeployimpler-blocker-<topic>.md`), don't fix silently.
- Don't touch the engines / SP-4b / BN-412 work.
- **ops-doc-maintainer**: after both are up, record the new running services (containers, no listen ports,
  output dirs) into the host ops doc.
- `git`: config files are gitignored (hold secrets) — don't commit secrets. Any committable change (e.g. a
  doc/runbook fix) → **explicit pathspec** + verify `git diff --cached` (shared index, concurrent sessions).

## 5. Convergence
Parent = BilibiliCrawl SubOrche. Inbound: `docs/sendbox/toWatcherDeployImpler/from-bilibilicrawlorche-*.md`.
| Event | Write to |
|---|---|
| config gate (Stage 0) / blocker | `docs/sendbox/toBilibiliCrawlOrche/from-watcherdeployimpler-blocker-<topic>.md` |
| done (both up + verified) | `docs/sendbox/toBilibiliCrawlOrche/from-watcherdeployimpler-done.md` |

## 6. Lifecycle
`burn` after `from-watcherdeployimpler-done.md` + SubOrche reads.

---
**Begin at Stage 0: confirm the vault output root (+ targets/intervals/SP-1 conn) with the user**, then fill
config, `compose up -d` both, and verify first-cycle-landing + second-cycle-dedup with evidence.
