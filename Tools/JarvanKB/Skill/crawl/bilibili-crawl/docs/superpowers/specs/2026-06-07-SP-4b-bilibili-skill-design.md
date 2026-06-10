# SP-4b Bilibili Skill — Design

> Status: design (brainstorming output, 2026-06-07). Authoritative scope for the SP-4b implementation plan.
> Audience: A2A (English per `docs/RepoMem/persist/config.md` Language Policy).
> Module: `Skill/crawl/bilibili-crawl/` (type=skill). Parent session: BilibiliCrawl SubOrche. Impler: SP4bImpler.
> Locked cross-SP boundaries (from the SP-4b handoff §1) are restated, not re-litigated.
> **Structural mirror = SP-3 (Zhihu Skill, ⚫ done + merged 2026-06-07).** Reuse, don't reinvent.

## 1. Purpose & scope

Given a Bilibili video reference, transcribe it through the **frozen SP-4a engine** and save it as Markdown
to a user-chosen location. When the chosen path is vague, classify the content into a subfolder under a
configured output root. SP-4b is a **pure consumer** of the frozen SP-4a engine (`Engine/bilibili`) and the
shared `jarvankb_common.LLMClient` (landed + frozen by SP-3) — it edits neither, and holds no LLM-connection
config of its own.

**In scope (v1):**
- Video ref (BV id / `bilibili.com` URL / av id) → pull cookie from SP-1 (active pull) → build a
  `BilibiliCredential` → call the frozen SP-4a engine `transcribe(ref, credential=cred) -> BilibiliResult`,
  then `result.render(RenderOptions(...))` → save `rendered.main_markdown` (and the split transcript file
  when `split_transcript` is enabled).
- `save_path` rule-based vague detection; vague → LLM classification into a subfolder under `output_root`.
- Importable Python API + thin CLI, plus a single agentskills.io-compliant `SKILL.md` (see §3).

**Out of scope (forbidden):** favorites polling / any watcher behavior (SP-5b); editing the SP-4a engine
(`Engine/bilibili/`, frozen — pure consumer); reimplementing `Engine/common` LLMClient (SP-3 landed it,
reuse `jarvankb-common`); vault/Obsidian/GBrain/Thino semantics (SP-6/SP-7); SP-1 push wiring (cancelled,
pull-only); baking real LLM credentials into the repo; the Zhihu vertical or any non-Bilibili SP; `git push`
/ merge-to-main / rebase (local commits only on `feat/agentcrawl-bootstrap`).

**Locked cross-SP boundaries (honored, not re-decided):**
- Cookie = active **PULL**, never push (SP-1 push path permanently cancelled). Decrypt transiently in memory,
  never persist plaintext.
- **Cookie domain = `bilibili.com` (NO leading dot)** — verified 2026-06-02 (`credentials.md §Bilibili`). The
  box holds `SESSDATA` + `bili_jct` (no `buvid3`). `.bilibili.com` returns nothing. (Engine `interface.md §5`
  still says `.bilibili.com` — that line is **stale**; `credentials.md` is authoritative.)
- Engine is **cookie-less-capable** on public videos (metadata + bcut ASR work without SESSDATA); SESSDATA
  only engages the subtitle-first path. A missing/expired cookie degrades **gracefully**, not fatally.
- Output = configurable **output root, vault-agnostic** (no GBrain frontmatter / Obsidian taxonomy / Thino).
- **Self-contained, parallel-independent** vs sibling SP-5b; minor cookie-fetch/save duplication accepted; the
  one shared piece (LLMClient) already exists and is consumed, not rebuilt.

## 2. Decisions confirmed in brainstorming (2026-06-07)

| # | Decision | Choice |
|---|---|---|
| 1 | Packaging form | Python importable package (`bilibili_crawl.save_bilibili` + `SaveResult`) + thin CLI `bilibili-crawl` with `--json` **+ one agentskills.io `SKILL.md`** (Claude Code = P0; same file reused by Codex / OpenClaw / Hermes). Mirrors SP-3. |
| 2 | Cookie pull mechanism | **HTTP `GET /get/:uuid` + client-side decrypt** in pure Python — reuse SP-3's verified `cookie.py` routine (`legacy` + `aes-128-cbc-fixed`), parametrized with `domain="bilibili.com"`. Map the cookie dict → `BilibiliCredential`. |
| 3 | vague_path taxonomy + save-path | Mirror SP-3: **`save_path` parameter + rule-based vagueness** (`.md` = explicit; dir / `output_root` / None/empty = vague). vague → **infer an existing subfolder, else propose a new one**. Interactive asking is the caller agent's job, not the skill's. |
| 4 | Classification input (video) | **`metadata.title` + a lead of `summary_markdown`** (BN's AI note = densest, lowest-noise topic signal). `summary_markdown` is best-effort and may be `None` → **fall back to a lead of `transcript.full_text`**. Lead capped by `classify_snippet_chars` (default 240), reusing SP-3's markdown-noise stripper. |
| 5 | RenderOptions defaults (saved note shape) | **Single file**: `include_transcript=True, include_timestamps=False, split_transcript=False` → frontmatter + AI summary + readable (merged, no-timestamp) transcript inline. **Config-overridable** in `config.yaml` (`render:` block); flipping `split_transcript: true` yields the two-file progressive-disclosure form, surfaced via `SaveResult.transcript_path`. |

## 3. Multi-agent packaging surface (mirror SP-3 §3)

Claude Code / OpenAI Codex CLI / OpenClaw / Hermes Agent all implement the same open agentskills.io
`SKILL.md` standard — one compliant file is reusable across all four (cross-session memory
`agentskills-skill-md-standard`). No per-runtime format fork.

| Layer | Artifact | Serves |
|---|---|---|
| Universal substrate | importable `bilibili_crawl` package + thin CLI `bilibili-crawl` with `--json` structured output | Hermes (`import` / `subprocess`), scripted clients, Codex, OpenClaw |
| Agent skill descriptor | **one** agentskills.io `SKILL.md` (frontmatter `name`/`description`/`version`/`license`/`tags`; body drives the CLI) | Claude Code (P0), Codex, OpenClaw, Hermes — same file |
| Discovery contract | SP-4b entry in `docs/sendbox/toAgent/handoff.md` (CLI/import I/O) — promoted via Step-8 HITL merge | any caller agent |

**SKILL.md conventions for cross-runtime reuse:**
- `description` uses **"Use when …"** style (best auto-trigger match across runtimes); explicitly *not* for
  non-Bilibili URLs or for article/text crawling (steer agents away from the Zhihu skill's turf).
- `tags` lowercase-hyphenated (e.g. `bilibili`, `video`, `transcription`, `markdown`, `knowledge-base`).
- Runtime-private fields go in `metadata.<runtime>` namespaces (others ignore them):
  - `metadata.hermes.required_environment_variables`: LLM `api_key_env` (for vague-path classification) +
    the cookie-manager decrypt password var.
  - `metadata.openclaw.requires.bins` / `install`: declare the `bilibili-crawl` console script / pip install.

**Deployment is a sync concern, not a format concern.** A thin `scripts/sync-skill.sh` symlinks/copies the one
`SKILL.md` directory to `~/.claude/skills/`, `~/.codex/skills/`, `~/.openclaw/skills/`, `~/.hermes/skills/` —
one source, many deploy targets. v1 ships the script; running it is the user's choice. (Mirror SP-3's script.)

## 4. Module structure

```
Skill/crawl/bilibili-crawl/
├── SKILL.md                      # single agentskills.io descriptor (drives the CLI)
├── pyproject.toml                # dist=bilibili-crawl; script: bilibili-crawl = bilibili_crawl.cli:main
├── config.example.yaml           # output_root / cookie source / llm profile / render defaults / snippet cap
├── scripts/sync-skill.sh         # deploy SKILL.md to the four runtime skill dirs (mirror SP-3)
├── src/bilibili_crawl/
│   ├── __init__.py               # public API exports: save_bilibili, SaveResult
│   ├── api.py                    # save_bilibili(...) -> SaveResult  (the importable core)
│   ├── cli.py                    # argparse thin shell → api; --out/--json/--profile/--config
│   ├── cookie.py                 # SP-1 pull (domain=bilibili.com) + decrypt + build BilibiliCredential; in-memory only
│   ├── classify.py               # vague detection + LLM classify into subfolder (title + summary/transcript lead)
│   ├── config.py                 # load module config (output_root, cookie source, llm profile, render, snippet cap)
│   └── saver.py                  # resolve path + write main (+ transcript) Markdown
├── docs/                         # interface.md (frozen here), architecture.md, RepoMem/, superpowers/
└── tests/                        # unit tests with mocked engine / LLMClient / cookie service
```

## 5. Data flow

```
save_bilibili(ref, save_path=None, *, profile=None, config_path=None)
  │
  ├─ load config (output_root, cookie source, llm profile, render defaults, classify_snippet_chars)
  ├─ cred = cookie.build_credential(cookie.pull(cfg.cookie, domain="bilibili.com"))
  │       pull: GET {base_url}/get/{uuid} → {encrypted, crypto_type} → decrypt → cookie_data["bilibili.com"]
  │       build_credential: SESSDATA present → BilibiliCredential(sessdata, bili_jct?, buvid3?); else None
  │       cookie failure (unreachable / decrypt / no SESSDATA) is NON-FATAL → warn, cred=None  [graceful degrade]
  ├─ result = transcribe(ref, credential=cred)            [FROZEN SP-4a engine]
  │       → BilibiliResult (raises BilibiliEngineError subclasses on failure → surfaced to caller)
  ├─ resolve target path:
  │     save_path points to a .md file        → explicit write, verbatim
  │     save_path is a dir / == output_root / None/empty → VAGUE:
  │         classify.classify(result, output_root, client, snippet_chars) →
  │             list existing subdirs + (title, summary|transcript lead) → LLMClient.complete(...)
  │             → pick an existing subfolder OR propose a new lowercase-hyphenated subfolder name
  │         target = <output_root>/<category>/<slug(title)>.md
  ├─ rendered = result.render(RenderOptions(include_transcript, include_timestamps, split_transcript, slug))
  ├─ saver.write(target, rendered.main_markdown)
  │       split_transcript=True → also write <target without .md>.transcript.md = rendered.transcript_markdown
  └─ SaveResult{path, transcript_path, title, ref, transcript_source, category, was_vague, proposed_new}
```

## 6. Components

### 6.1 `api.save_bilibili` (importable core)
```python
@dataclass
class SaveResult:
    path: str                  # absolute path of the main file written
    transcript_path: str | None # absolute path of the split transcript file; None unless split_transcript
    title: str
    ref: str                   # original request ref (BV / URL / av)
    transcript_source: str     # "subtitle" | "asr"
    category: str | None       # subfolder chosen by classification; None for explicit-path writes
    was_vague: bool            # True if vague-path classification ran
    proposed_new: bool         # True if classification proposed a brand-new subfolder

def save_bilibili(ref: str, save_path: str | None = None, *,
                  profile: str | None = None, config_path: str | None = None) -> SaveResult: ...
```
Orchestrates config → cookie pull + credential build → engine transcribe → render → path resolve → write.
Propagates `BilibiliEngineError` subclasses (no sentinels). Pure consumer of the engine; never edits it.
Render options come from config (decision #5) — no per-call render knobs in v1 (YAGNI).

### 6.2 `cli` (thin CLI)
```
bilibili-crawl <ref> [--out PATH] [--json] [--profile NAME] [--config PATH]
```
- `--out` → `save_path`; omitted → vague (classify under `output_root`).
- `--json` → print `SaveResult` as JSON (machine-readable for any agent); else human summary.
- `console_scripts` entry `bilibili-crawl = bilibili_crawl.cli:main` (mirrors the `bilibili` engine CLI).

### 6.3 `cookie` (SP-1 active pull + decrypt + credential build)
- `pull(source, domain="bilibili.com") -> dict[str, str]`: `GET {base_url}/get/{uuid}` → `{encrypted,
  crypto_type}` → decrypt → `cookie_data["bilibili.com"]` → `{name: value}`. **Verbatim reuse of the SP-3
  routine** (`the_key = md5(f"{uuid}-{password}").hexdigest()[:16]`; `legacy` = OpenSSL `Salted__` +
  EVP_BytesToKey(MD5) → AES-256-CBC; `aes-128-cbc-fixed` = 16-byte key + zero IV); only the default `domain`
  differs. Plaintext cookies live **only in memory**, never persisted.
- `build_credential(cookies) -> BilibiliCredential | None`: `SESSDATA` present →
  `BilibiliCredential(sessdata=cookies["SESSDATA"], bili_jct=cookies.get("bili_jct"),
  buvid3=cookies.get("buvid3"))`; absent → `None` (anonymous / public-video path).
- Module-local (not in `Engine/common`); minor duplication vs SP-5b accepted (handoff §1). The decrypt
  routine is a **cross-SP-reusable pattern** already promoted globally by SP-3 (`credentials.md`); SP-4b's
  only new lesson is the `domain=bilibili.com` + SESSDATA→credential mapping.

### 6.4 `classify` (vague_path)
- `is_vague(save_path, output_root) -> bool`: vague iff `save_path` is None/empty, OR equals `output_root`,
  OR is a directory / has no `.md` filename component. Explicit iff it names a `.md` file. (SP-3 logic verbatim.)
- `classify(result, output_root, client, *, snippet_chars=240) -> Category`: list immediate subdirs of
  `output_root`; build the classification lead from **`result.summary_markdown` (fallback
  `result.transcript.full_text`)** via the SP-3 markdown-noise stripper capped at `snippet_chars`; prompt
  `LLMClient.complete(...)` with existing subfolder names + `result.metadata.title` + the lead; instruct it
  to return one existing subfolder OR propose a new lowercase-hyphenated name. Returns `{name, is_new}`
  (`is_new` authoritative from the filesystem, not the model's flag). New subfolder created on write.
- Filename = slugified `result.metadata.title` (+ `.md`); collision → numeric suffix.
- LLM prompt + parsing live here so unit tests can inject a mocked `LLMClient`. Reuses SP-3's `_lead_text`,
  `existing_subfolders`, `_parse`, `Category`, `slugify` shapes.

### 6.5 `config` (module config loader)
- Loads `config.yaml` (default; overridable via `--config` / `config_path`); schema in `config.example.yaml`:
  - `output_root`: base dir for vague-path writes.
  - `cookie`: `{base_url, uuid, password_env}` — password read from env (`.env`), never in repo.
  - `llm`: `{profile}` — which `config/llm.yaml` profile to use (default `mimo-v2.5-pro`, already configured).
  - `render`: `{include_transcript, include_timestamps, split_transcript}` — note-shape defaults (decision #5).
  - `classify_snippet_chars`: int (default 240).
- Resolves `~` and relative paths against a documented base.
- **Profile precedence:** the `--profile` flag / `save_bilibili(profile=...)` arg, when explicitly given,
  overrides `config.llm.profile`; otherwise `config.llm.profile` (else `"default"`) applies.
- **Engine config is NOT here:** the SP-4a engine reads its own `config/bilibili-engine.yaml` via
  `transcribe()` / `BilibiliEngine.from_config()`. SP-4b depends on that being set up (BN reachable) but does
  not duplicate engine params.

### 6.6 `saver` (path resolve + write)
- `is_vague` (shared with classify), `slugify`, `resolve_target(save_path, output_root, category, title)`,
  `write(target, markdown) -> Path`. For `split_transcript`: also write
  `<target stem>.transcript.md` from `rendered.transcript_markdown`, returning both paths. Collision →
  numeric suffix on the main filename (transcript file follows the same stem).

## 7. Interface contract (frozen into `docs/interface.md`)

```python
from bilibili_crawl import save_bilibili, SaveResult
r = save_bilibili("BV1xx...", save_path="~/KB/bilibili")          # vague → classify
r = save_bilibili("https://www.bilibili.com/video/BV1xx...",
                  save_path="~/KB/tech/note.md")                  # explicit → verbatim
```
```
bilibili-crawl <ref> [--out PATH] [--json] [--profile NAME] [--config PATH]
```
`SaveResult` fields per §6.1. Engine contract consumed verbatim from `Engine/bilibili/docs/interface.md` §3–§5.
Supported refs follow the engine: BV id / `bilibili.com` URL / av id.

## 8. Error handling

| Condition | Behavior |
|---|---|
| Engine total failure | `BilibiliEngineError` subclass (`InvalidVideoRef` / `TranscriptionFailed` / `TranscriptionTimeout`) propagates; CLI prints diagnostics, non-zero exit |
| **BiliNote unreachable** | `BiliNoteUnavailable` propagates (Stage-3 / live-smoke gate); CLI distinct exit code |
| Cookie service unreachable / decrypt fail / no SESSDATA | **NON-FATAL** — warn, proceed with `credential=None` (engine handles public videos cookie-less). Never crashes the save. |
| LLM unavailable on vague path | classification error surfaced; explicit (non-vague) path unaffected. **No creds gate** — `mimo-v2.5-pro` already configured. |
| Path collision | numeric suffix on the main filename (transcript file follows the same stem) |
| Vague but `output_root` unset | config error before any network call |

## 9. Testing strategy (TDD, subagent-driven)

Unit tests mock the engine (`transcribe`), `LLMClient`, and the cookie HTTP service — **no live credentials
needed**:
- `is_vague` rule matrix (file vs dir vs root vs None vs non-.md).
- `classify` — pick-existing and propose-new with a mocked `LLMClient`; **summary-present path AND
  summary-None fallback to transcript lead**.
- `cookie` decrypt — both `crypto_type`s against known vectors (reuse SP-3's fixture round-trip);
  `build_credential` mapping (SESSDATA present → credential; bili_jct present, buvid3 absent; SESSDATA absent
  → None).
- path resolution + filename slug + collision suffix; **single-file vs `split_transcript` two-file write**.
- render integration: a mocked `BilibiliResult` → `render()` → save (single + split).
- `cli --json` shape; exit codes on engine / BN-unavailable / config errors.
- **graceful degradation**: cookie pull raises → `credential=None`, engine still called once.

## 10. Verification (handoff §3.D) — no LLM-creds gate; BN-up gate only

- `verification-before-completion`: full unit suite + lint/typecheck + **offline smoke** (explicit path: a
  ref → mocked-or-real engine seam → save) + the mocked-LLM vague path.
- **Live smoke**: a real Bilibili video → engine `transcribe` → save (explicit path) **and** the vague_path
  classification via the real `mimo-v2.5-pro` profile. Requires BN up — container `jarvankb-bilinote` at
  `127.0.0.1:3015` (`TRANSCRIBER_TYPE=bcut`, provider `mimo-v2.5-pro`). If BN is down at smoke time → a
  **gate** (Dashboard row + `from-sp4bimpler-blocker-bn-down.md` to `toBilibiliCrawlOrche/`), not a design
  blocker. **No LLM-creds gate** (mimo already configured — reuse it).

## 11. Self-isolation / unit boundaries

Each module file has one purpose, a typed interface, and is testable in isolation: `cookie` (pull + decrypt +
credential build), `classify` (vague + LLM categorize), `saver` (path + write, single/split), `config`
(load), `api` (orchestrate), `cli` (adapt). `LLMClient` and the SP-4a engine are the frozen upstream pieces,
consumed verbatim. No file reaches into another's internals.
