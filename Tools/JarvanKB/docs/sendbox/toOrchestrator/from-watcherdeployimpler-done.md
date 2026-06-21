> from: WatcherDeployImpler
> to: RootOrchestrator g5
> re: UN-047 v1.1 WatcherDeploy — both watchers up + live-verified
> created: 2026-06-19
> lifecycle: burn after root reads + reflects into Dashboard/version-plan

# DONE — SP-5a + SP-5b watchers deployed as daemons + verified (v1.1)

Both watchers are running as resident Docker daemons, first-cycle verified live, **from-now** policy applied
(user-decided: no history backfill). toUser ops manual delivered. **Lane: fast** (ops/deploy; no watcher-code change).

## Running services (both `Up`, 30-min poll, NO listening port — outbound pollers)
| Service | container | output (bind-mounted) | state |
|---|---|---|---|
| SP-5a zhihu | `jarvankb-zhihu-watcher` | `…/ResourceBase资源库/Zhihu知乎` | `./data/state` (from-now baselines persisting) |
| SP-5b bili | `jarvankb-bilibili-watcher` | `…/ResourceBase资源库/BiliB站` | `./data/state` (22 folder watermarks seeded = now) |

## Stage-0 (resolved live, not re-asked)
- Cookie box = `jasonjarvan` (only account in gitignored `cookie-manager.yaml`; `/get/:uuid` returns 200 **without**
  the auth_token → zhihu's tokenless provider works). Reused on-disk creds.
- Zhihu: `type:user me` → 33 non-empty named collections (`产品思维` empty-skipped) + default-collection
  `我的收藏 721323262` classify:true. Bili: all **22** fav folders (two named `效率工具` merge into one subdir).
- Model `mimo-v2.5` (flat, UN-050 deferred). Verified resolves: HTTP 200 + 4 live litellm calls in classify smoke.

## Verification evidence (`verify` discipline — observed, not assumed)
- **Land + dedup invariant** (scoped `--once` ×2, isolated dirs, NOT the vault):
  - zhihu: run-1 saved `量化/普通人能做量化吗….md`; run-2 saved **0**, file count 1→1 (no dup). zhuanlan article 403 = documented best-effort.
  - bili: run-1 (健康) saved `健康/菠萝….md` (subtitled → BN used AI subtitle, no bcut); run-2 early-stopped → **0 new**, 1→1.
- **Classify** (default-collection, only_after=2026-06-12 → 1 answer): fetched → 4× `mimo-v2.5` → landed in **existing** folder `赚钱-投资分析/`. ledger recorded.
- **Production first cycle**: zhihu resolved 34 collections → 0 new (from-now); bili 22 folders early-stop → 0 new; both schedulers started; no crash.
- **No creds in tracked files**: `git grep` of box-password / auth_token / mimo-key across all tracked files = **0 hits**. All live yamls + `config/llm.yaml` + `cookie-manager.yaml` gitignored.

## Deploy-artifact fixes I had to make (ops, NOT watcher-code contract)
1. **zhihu Dockerfile**: also `COPY Engine/common` + install — `watcher.py` imports `jarvankb_common` at module top (and `LLMClient` for classify); image previously installed only Engine/zhihu+watcher → would crash on import.
2. **zhihu compose**: `network_mode: host` (bridge cannot reach `127.0.0.1:48088` cookie-manager — was the root of a `Connection refused`), bind-mount vault, mount `config/llm.yaml`→`/llm.yaml` + `JARVANKB_LLM_CONFIG`, `env_file ../../../.env` (MIMO_API_KEY).
3. **bili compose**: bind-mount vault; defensive proxy-clear env (runbook §5 socksio).
4. `config/llm.yaml` (gitignored): `mimo` profile `openai/mimo-v2.5-pro` → `openai/mimo-v2.5`.
5. both `.gitignore`: add `data/`.

## ⚠️ Things you (root) should know / forward to ReachOrche
- **BN MiMo provider key was expired (401 Invalid API Key)** — blocked all bili transcription. **User approved** refreshing it from repo `.env` via BN `/api/update_provider` (id `cf11f2fc-…`); done, 401 cleared. This key has NO auto-refresh (unlike the SESSDATA cron) → a recurring B站链路 ops gotcha (documented in the ops manual + proposed for crawl-pipeline §B站链路).
- **bcut ASR fails for some subtitle-less videos** (`上传提交失败: 第三方服务异常`; reproduced on one 购物 video). Subtitled videos bypass bcut and succeed. This is BN/bcut-side (SP-4a engine domain, out of my scope) — watcher handles it gracefully (no seen, retries). Relates to UN-051 (BN output).
- **bn-cookie-sync cron runs `*/30`, not `*/10`** as the handoff stated (still active; SESSDATA fresh).

## Deliverables
- toUser ops manual (中文): `docs/sendbox/toUser/2026-06-19-watcher-ops-manual.md`.
- Host ops doc updated (ops-doc-maintainer): both containers recorded, "no published ports".
- Plan: `docs/superpowers/plans/2026-06-19-v1.1-watcher-deploy-plan.md`.

## Milestone
**v1.1 capability (auto-watch zhihu/bili favorites → Obsidian) is DELIVERED** (from-now; new favorites flow on the
next cycle). I've updated Dashboard §里程碑 v1.1 → done. (B站 transcription depends on BN key freshness + bcut per-video.)

## Open / pending
- **Tracked-file commit is ask-first** — 5 tracked files (2 compose, 1 Dockerfile, 2 .gitignore) + plan + manual + RepoMem promotions await user go (shared index → explicit pathspec). `config/llm.yaml` stays gitignored/uncommitted.
- **Step-8 RepoMem.merge** (I own closure): promote BN-key-drift + bcut-per-video to crawl-pipeline §B站链路 (global); zhihu host-net + Engine/common-in-image + bili watermark-seed to module decisions. Runs with the commit above.
- watcher-ops domain → **ReachOrche** forward.
