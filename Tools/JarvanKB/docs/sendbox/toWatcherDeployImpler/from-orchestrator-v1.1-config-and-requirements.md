> from: RootOrchestrator g5
> recipient: WatcherDeployImpler ("the deployer")
> type: v1.1 deploy config + requirements (supplements the existing handoff.md)
> lifecycle: keep until v1.1 deployed + verified + toUser ops manual delivered
> created: 2026-06-18

# v1.1 WatcherDeploy — locked config + requirements

User greenlit the deploy (2026-06-18). This supplements `handoff.md` with the now-locked Stage-0 config and two
explicit user requirements (ops manual + port-rule awareness). v1.1 capability = auto-watch zhihu/bili favorites
→ Obsidian vault. **Lane: fast** (ops/deploy, no code change). **Root finishes this deploy; the watcher-ops
domain goes to ReachOrche forward** (you converge to root at `toOrchestrator/`).

## 1. Locked config (user-decided 2026-06-18)

**Both watchers:**
- `poll_interval_minutes: 30`.
- `cookie_source`: base_url `http://127.0.0.1:48088` (SP-1 cookie-manager) + **uuid + password = USER-PROVIDED** →
  collect from the user in your Stage-0 and write ONLY into the gitignored live yaml. **NEVER commit creds; never
  echo them.** (Live yamls are gitignored: `zhihu-watcher.yaml` already; `bilibili-watcher.yaml` fixed in commit
  `3f3f1e9` — re-verify with `git check-ignore` before writing.)
- Model = **mimo-v2.5** for v1.1 (flat — the heavy/medium/light tier router is deferred, UN-050). zhihu classify
  uses the `mimo` profile (`config/llm.yaml`; set `model: openai/mimo-v2.5` if not already); bili uses the
  BN-registered mimo-v2.5. **Verify `mimo-v2.5` resolves at the MiMo provider in your live smoke** (only
  `mimo-v2.5-pro` was tested before); if it 404s, escalate to root.

**Zhihu (`zhihu-watcher.yaml`):**
- `output_dir: /home/shenzhou/Documents/Obsidian/JasonJarvan/ResourceBase资源库/Zhihu知乎` (already the example value).
- `targets` = **ALL collections + default-collection classify**:
  - `{ type: user, url_token: me, skip_empty: true, include_default: false }` — auto-discover all named collections.
  - `{ type: collection, id: <我的收藏 default-collection id — resolve in Stage-0>, classify: true }`.
- `classify`: `llm_profile: mimo`, `allow_new_folders: false` (unattended → pick from the existing ~33 folders only).

**Bilibili (`bilibili-watcher.yaml`):**
- `output_dir`: change the `/data/output` placeholder → bind-mount target
  `/home/shenzhou/Documents/Obsidian/JasonJarvan/ResourceBase资源库/BiliB站`.
- `folders` = **ALL fav folders**: the config takes an explicit list → **confirm whether the watcher supports
  auto-discover-all; if not, enumerate the user's fav folders and list them all** (don't silently watch a subset —
  `log()` what you watch).
- `engine`: `bn_base_url http://127.0.0.1:3015`; `provider_id`/`model_name` → fetch from BN
  `GET /api/get_all_providers`, pick the mimo-v2.5 provider.
- BN summary = **stock built-in (route A, user-decided)**. NOTE the known quirk: our engine sends `style:"summary"`
  which is a **no-op** (`summary` is a `format` value, not a `style`) + `format:[]` → notes are the bare
  `BASE_PROMPT` structured notes (good enough per user). **Do NOT "fix" this in v1.1** — a separate reach-domain
  task (UN-051) may revisit BN output. Just deploy as-is.
- Docker: bind-mount both host vault dirs into the containers; persist `state_dir` via a volume.

## 2. REQUIRED deliverable — a toUser ops manual (user explicitly asked)

Produce `docs/sendbox/toUser/<name>-watcher-ops-manual.md` (**中文 — H2A**) so the user can run/maintain the
watchers themselves. MUST cover, in plain terms:
- **start / stop / restart / status** — exact `docker compose` commands + the working directory.
- **logs + "is it working?"** — where logs are; first-run landing count; the second-run `0 new` dedup invariant.
- **dependencies that must be UP**: cookie-manager (`:48088`, fresh cookies — host cron keeps SESSDATA fresh;
  zhihu `__zse_ck` may need periodic browser re-sync, UN-032) and BN (`:3015`, for B站 transcription).
- **add/remove a watched collection/folder + change interval** — which fields, then restart.
- **failure behavior** — FailureStore backoff (cooldown after N consecutive failures; circuit-break + attention-list).
- **cookie-refresh + BN-cookie-restart gotchas** — point to `crawl-pipeline.md §B站链路` / the runbook.
- a one-line **"who owns this going forward"** = watcher-ops domain → ReachOrche.

## 3. Port rule (follow it; root already knows it — no need to ask the user)

Host listening-services use the **48xxx convention** (48000–48999, sub-allocated; ratified UN-044; see
`credentials.md §Host service-port convention`). Existing: cookie-manager `:48088` (frp public `:48098`).
**The watchers do NOT listen on any port** — they poll outbound (cookie-manager `:48088`, BN `:3015`) and write
files → **no new port allocation needed for v1.1.** If you ever add a listening surface it must fall in 48xxx.
Document the depended-on ports (48088, 3015) in the manual. (BN at `:3015` predates the convention; left as-is.)

## 4. Acceptance
- Both watchers `compose up -d`; first cycle lands files into the two vault dirs; second cycle `0 new` (dedup
  invariant) — show evidence.
- `mimo-v2.5` resolves live; zhihu classify lands default-collection items into existing subfolders.
- **No creds in any tracked file** (assert `git check-ignore` + grep the tree before any commit).
- **toUser ops manual delivered** + a `from-watcherdeployimpler-done.md` convergence letter to `toOrchestrator/`.
- **You own Step-8 RepoMem.merge closure** (promote deploy-ops gotchas; the watcher modules' domain → ReachOrche).

— root orche g5 (2026-06-18)
