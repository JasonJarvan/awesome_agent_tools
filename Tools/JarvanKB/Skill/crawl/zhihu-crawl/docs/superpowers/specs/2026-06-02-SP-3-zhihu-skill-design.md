# SP-3 Zhihu Skill — Design

> Status: design (brainstorming output). Authoritative scope for the SP-3 implementation plan.
> Audience: A2A (English per `docs/RepoMem/persist/config.md` Language Policy).
> Module: `Skill/crawl/zhihu-crawl/` (type=skill). Parent session: ZhihuCrawl SubOrche. Impler: SP3Impler.
> Locked cross-SP boundaries (from the SP-3 handoff §1) are restated, not re-litigated.

## 1. Purpose & scope

Given a Zhihu URL, fetch the content through the **frozen SP-2 engine** and save it as Markdown to a
user-chosen location. When the chosen path is vague, classify the content into a subfolder under a
configured output root. SP-3 is also the **first real consumer** of the shared `LLMClient`, so it lands
the real `litellm` body and freezes it for SP-6 reuse.

**In scope (v1):**
- URL → pull cookie from SP-1 (active pull) → call frozen SP-2 `fetch()` → `to_markdown()` → save.
- `save_path` rule-based vague detection; vague → LLM classification into a subfolder.
- Real `LLMClient` body (litellm) in `Engine/common`, made importable (see §7), frozen + documented.
- Importable Python API + thin CLI, plus a single agentskills.io-compliant `SKILL.md` (see §3).

**Out of scope (forbidden):** vault/Obsidian/GBrain/Thino semantics (SP-6/SP-7); favorites polling (SP-5a);
v1.1 comment full-tree; editing the SP-2 engine (`Engine/zhihu/`, frozen — pure consumer); SP-1 push
wiring (cancelled, pull-only); baking real LLM credentials into the repo; `git push` / merge-to-main /
rebase (local commits only on `feat/agentcrawl-bootstrap`).

**Locked cross-SP boundaries (honored, not re-decided):**
- Cookie = active **PULL**, never push (SP-1 push path permanently cancelled).
- Output = configurable **output root, vault-agnostic** (no GBrain frontmatter / Obsidian taxonomy / Thino).
- **Self-contained, parallel-independent** vs sibling SP-5a; minor cookie-fetch/save duplication accepted;
  the one shared piece SP-3 owns is `LLMClient`.

## 2. Decisions confirmed in brainstorming (2026-06-02)

| # | Decision | Choice |
|---|---|---|
| 1 | Packaging form | Python importable package + thin CLI (universal substrate) **+ one agentskills.io `SKILL.md`** (Claude Code = P0; same file reused by Codex / OpenClaw / Hermes) |
| 2 | vague_path taxonomy | **Infer from existing subfolders** under output root; propose a new subfolder name when none fit |
| 3 | save-path interaction | **`save_path` parameter + rule-based vagueness**; interactive asking is the caller agent's job, not the skill's |
| 4 | Cookie pull mechanism | **HTTP `GET /get/:uuid` + client-side decrypt** (pure Python, self-contained; supports `legacy` + `aes-128-cbc-fixed`) |
| 5 | LLMClient config path | **`<root>/config/llm.yaml`** (shared resource; `.example` already there) |
| 6 | Engine/common packaging | **Add `pyproject.toml`** so `LLMClient` is genuinely importable, consistent with the per-module pip-package convention (Engine/zhihu, Engine/bilibili) |

## 3. Multi-agent packaging surface

Per user research (2026-06-02): Claude Code / OpenAI Codex CLI / OpenClaw / Hermes Agent all implement the
**same open agentskills.io `SKILL.md` standard** — one compliant file is reusable across all four; format
forks are unnecessary. (Recorded in cross-session memory `agentskills-skill-md-standard`.)

| Layer | Artifact | Serves |
|---|---|---|
| Universal substrate | importable `zhihu_crawl` package + thin CLI `zhihu-crawl` with `--json` structured output | Hermes (pip-installed Python: `import` / `subprocess`), scripted clients, Codex, OpenClaw |
| Agent skill descriptor | **one** agentskills.io `SKILL.md` (frontmatter `name`/`description`/`version`/`license`/`tags`; body drives the CLI) | Claude Code (P0), Codex, OpenClaw, Hermes — same file |
| Discovery contract | SP-3 entry in `docs/sendbox/toAgent/handoff.md` (CLI/import I/O) — promoted via Step-8 HITL merge | any caller agent |

**SKILL.md conventions for cross-runtime reuse:**
- `description` uses **"Use when …"** style (best auto-trigger match across runtimes).
- `tags` lowercase-hyphenated (e.g. `zhihu`, `crawl`, `markdown`, `knowledge-base`).
- Runtime-private fields go in `metadata.<runtime>` namespaces (others ignore them):
  - `metadata.hermes.required_environment_variables`: `ANTHROPIC_API_KEY` / `DASHSCOPE_API_KEY` (LLM) + cookie-manager connection vars.
  - `metadata.openclaw.requires.bins` / `install`: declare the `zhihu-crawl` console script / pip install.
- Runtime hooks/plugins (Claude Code `plugin.json`, settings) are NOT part of SKILL.md — out of scope here.

**Deployment is a sync concern, not a format concern.** A thin `scripts/sync-skill.sh` (or `make
install-skill`) symlinks/copies the one `SKILL.md` directory to `~/.claude/skills/`, `~/.codex/skills/`,
`~/.openclaw/skills/`, `~/.hermes/skills/` — one source, many deploy targets. v1 ships the script;
running it is the user's choice.

## 4. Module structure

```
Skill/crawl/zhihu-crawl/
├── SKILL.md                      # single agentskills.io descriptor (drives the CLI)
├── pyproject.toml                # dist=zhihu-crawl; script: zhihu-crawl = zhihu_crawl.cli:main
├── config.example.yaml           # output_root / cookie source / llm profile ref (real → config/, gitignored)
├── scripts/sync-skill.sh         # deploy SKILL.md to the four runtime skill dirs
├── src/zhihu_crawl/
│   ├── __init__.py               # public API exports: save_zhihu, SaveResult
│   ├── api.py                    # save_zhihu(...) -> SaveResult  (the importable core)
│   ├── cli.py                    # argparse thin shell → api; --out/--json/--comments/--profile
│   ├── cookie.py                 # SP-1 pull: GET /get/:uuid + decrypt (legacy + aes-128-cbc-fixed); in-memory only
│   ├── classify.py               # vague detection + LLM classify into subfolder (infer-existing + propose-new)
│   ├── config.py                 # load module config (output_root, cookie source, llm profile)
│   └── saver.py                  # resolve path + write Markdown
├── docs/                         # interface.md (frozen here), architecture.md, RepoMem/, superpowers/
└── tests/                        # unit tests with mocked engine / LLMClient / cookie service
```

## 5. Data flow

```
save_zhihu(url, save_path=None, *, with_comments=False, comment_limit=None, profile="default")
  │
  ├─ load config (output_root, cookie source, llm profile)
  ├─ cookie.pull()  ── GET {base_url}/get/{uuid} → {encrypted, crypto_type} → decrypt → cookie_data[".zhihu.com"]
  │                     → {name: value} dict   (plaintext cookies live in memory only, never written to disk)
  ├─ fetch(url, cookies=cookie_dict, with_comments=..., comment_limit=...)   [FROZEN SP-2 engine]
  │     → FetchResult           (raises ZhihuFetchError on total failure → surfaced to caller)
  ├─ md = result.to_markdown()  (engine already emits YAML frontmatter incl. source: zhihu)
  ├─ resolve target path:
  │     save_path points to a .md file (or existing file)  → explicit write, verbatim
  │     save_path is a dir / == output_root / None/empty    → VAGUE:
  │         classify.classify(result, output_root) →
  │             list existing subdirs under output_root + (title, type, snippet) → LLMClient.complete(...)
  │             → pick an existing subfolder OR propose a new subfolder name (slugged)
  │         target = <output_root>/<category>/<slug(title)>.md
  └─ saver.write(target, md) → SaveResult{path, category, was_vague, title, type, url}
```

## 6. Components

### 6.1 `api.save_zhihu` (importable core)
```python
@dataclass
class SaveResult:
    path: str            # absolute path written
    title: str
    type: str            # answer | article | question
    url: str
    category: str | None # subfolder chosen by classification; None for explicit-path writes
    was_vague: bool       # True if vague-path classification ran
    proposed_new: bool    # True if classification proposed a brand-new subfolder

def save_zhihu(url: str, save_path: str | None = None, *,
               with_comments: bool = False, comment_limit: int | None = None,
               profile: str = "default", config_path: str | None = None) -> SaveResult: ...
```
Orchestrates config → cookie pull → engine fetch → markdown → path resolve → write. Propagates
`ZhihuFetchError` (no sentinels). Pure consumer of the engine; never edits it.

### 6.2 `cli` (thin CLI)
```
zhihu-crawl <url> [--out PATH] [--comments] [--comment-limit N]
                  [--json] [--profile NAME] [--config PATH]
```
- `--out` → `save_path`; omitted → vague (classify under output_root).
- `--json` → print `SaveResult` as JSON (machine-readable for any agent); else human summary.
- Exit code 0 on success; non-zero + stderr message on `ZhihuFetchError` / config / cookie errors.
- `console_scripts` entry `zhihu-crawl = zhihu_crawl.cli:main` (mirrors `zhihu` engine CLI).

### 6.3 `cookie` (SP-1 active pull + decrypt)
- `pull(source) -> dict[str, str]`: `GET {base_url}/get/{uuid}` → `{encrypted, crypto_type}`.
- Decrypt by `crypto_type` (honor whatever the store returns):
  - key derivation (both modes): `the_key = md5(f"{uuid}-{password}").hexdigest()[:16]`.
  - `legacy` (default): CryptoJS passphrase envelope — base64 → `b"Salted__" + 8-byte salt + ct`;
    derive key(32)+iv(16) via OpenSSL **EVP_BytesToKey** (iterated MD5) with `the_key` as passphrase;
    AES-256-CBC + PKCS7 unpad.
  - `aes-128-cbc-fixed`: key = first 16 UTF-8 bytes of `the_key`, IV = 16 zero bytes, AES-128-CBC + PKCS7,
    raw base64 (no `Salted__`).
- Inner plaintext JSON `{cookie_data, local_storage_data, update_time}`; take `cookie_data[".zhihu.com"]`
  (array of cookie objects) → `{name: value}`. Keys of interest: `z_c0`, `d_c0`, `__zse_ck`.
- **Plaintext cookies exist only transiently in memory; never persisted to disk.**
- Crypto via a pure-Python AES lib (`pycryptodome`); `EVP_BytesToKey` implemented locally (small MD5 loop).
- Module-local (not in `Engine/common`); minor duplication vs SP-5a accepted (handoff §1). The decrypt
  routine is a **cross-SP-reusable pattern** → Step-8 merge promotes the *lesson* (not the code) to global.

### 6.4 `classify` (vague_path)
- `is_vague(save_path, output_root) -> bool`: vague iff `save_path` is None/empty, OR equals `output_root`,
  OR is a directory / has no `.md` filename component. Explicit iff it names a `.md` file.
- `classify(result, output_root, client) -> Category`: list immediate subdirs of `output_root`; prompt
  `LLMClient.complete(...)` with the existing subfolder names + `result.title` + `result.type` +
  a content snippet; instruct it to return one existing subfolder OR propose a new lowercase-hyphenated
  subfolder name. Returns `{name, is_new}`. New subfolder is created on write.
- Filename = slugified `result.title` (+ `.md`); collision → numeric suffix.
- LLM prompt + parsing live here so unit tests can inject a mocked `LLMClient`.

### 6.5 `config` (module config loader)
- Loads `config.yaml` (default; overridable via `--config` / `config_path`); schema in `config.example.yaml`:
  - `output_root`: base dir for vague-path writes.
  - `cookie`: `{base_url, uuid, password_env}` — password read from env (`.env`), never in repo.
  - `llm`: `{profile}` — which `config/llm.yaml` profile to use (default `default`).
- Resolves `~` and relative paths against a documented base.
- **Profile precedence:** the `--profile` flag / `save_zhihu(profile=...)` arg, when explicitly given,
  overrides `config.llm.profile`; otherwise `config.llm.profile` (else `"default"`) applies.

## 7. LLMClient real body (Engine/common — landed + frozen by SP-3)

**Packaging (decision #6):** add `Engine/common/pyproject.toml` (dist `jarvankb-common`), `src`-layout
package `jarvankb_common`, so `from jarvankb_common.llm_client import LLMClient` works after
`pip install -e Engine/common`. The current loose `Engine/common/src/{__init__,llm_client}.py` reorganize
under `src/jarvankb_common/`. Update `Engine/common/docs/interface.md` import line + mark
**"real impl landed in SP-3"** so SP-6 inherits a working import and does not redo it. Exact dist/import
name confirmed at writing-plans (proposal: `jarvankb-common` / `jarvankb_common`).

**Config loader** (`jarvankb_common/config.py`): read `<root>/config/llm.yaml`
(`profiles{model, api_key_env, api_base_env?}` + `active: [...]`). A profile is *available* iff its
`api_key_env` is empty (no key needed, e.g. ollama) OR `os.environ[api_key_env]` is non-empty.

**Body** (signatures frozen, unchanged):
- `__init__(profile="default")`: resolve the requested profile; if unavailable, fall through the `active`
  order to the first available profile.
- `complete(messages, **kwargs) -> str`: `litellm.completion(model, messages, api_key, api_base?, **kwargs)`
  → `.choices[0].message.content`. On provider error, fall to the next available `active` profile; raise if
  all exhausted.
- `stream(messages, **kwargs) -> Iterator[str]`: `litellm.completion(..., stream=True)`; yield
  `chunk.choices[0].delta.content` (skip empty).
- `to_opencode()`: stays `NotImplementedError("opencode integration planned for v1.x")`.

`litellm` is a dependency of `jarvankb-common` (not SP-3 directly). No real credentials in the repo;
`config/llm.yaml.example` (already present, default `claude-opus-4-7`, fallback `dashscope/qwen-max`) is the
template; real keys go in `.env`.

## 8. Interface contract (frozen into `docs/interface.md`)

```python
from zhihu_crawl import save_zhihu, SaveResult
r = save_zhihu("https://www.zhihu.com/question/1/answer/2", save_path="~/KB")  # vague → classify
r = save_zhihu(url, save_path="~/KB/tech/note.md")                            # explicit → verbatim
```
```
zhihu-crawl <url> [--out PATH] [--comments] [--comment-limit N] [--json] [--profile NAME] [--config PATH]
```
`SaveResult` fields per §6.1. Engine contract consumed verbatim from `Engine/zhihu/docs/interface.md`.

## 9. Error handling

| Condition | Behavior |
|---|---|
| Engine total failure | `ZhihuFetchError` (url/attempts/status) propagates; CLI prints diagnostics, non-zero exit |
| Cookie service unreachable / decrypt fail | explicit error; offer anonymous fetch fallback only if caller opts in (default: fail loud) |
| LLM unavailable on vague path | classification error surfaced; non-vague (explicit) path unaffected (see §11 creds gate) |
| Path collision | numeric suffix on filename |
| Vague but `output_root` unset | config error before any network call |

## 10. Testing strategy (TDD, subagent-driven)

Unit tests mock the engine, `LLMClient`, and the cookie HTTP service — **no live credentials needed**:
- `is_vague` rule matrix (file vs dir vs root vs None vs non-.md).
- `classify` — pick-existing and propose-new, with a mocked `LLMClient`.
- `cookie` decrypt — both `crypto_type`s against known vectors (a fixture encrypted with a known
  uuid/password round-trips to a known cookie dict).
- path resolution + filename slug + collision suffix.
- `cli --json` shape; exit codes on error.
- `LLMClient` — profile resolution / availability / active-order fallthrough (litellm mocked).

## 11. Verification & the LLM-creds gate (handoff §3.E)

- `verification-before-completion`: full unit suite + lint/typecheck + **offline smoke**
  (explicit path: a Zhihu URL → engine → save; engine runs against a recorded fixture or a live URL) +
  the mocked-LLM vague path.
- **Live vague_path classification** needs real LLM creds → emit a **Dashboard Type-F row**
  ("填 `config/llm.yaml` LLM 凭据 → 解锁 SP-3 vague_path live smoke") + a
  `from-sp3impler-blocker-llm-creds.md` note to `toZhihuCrawlOrche/`. Only this one path is gated; the
  fetch→save path is verified offline.

## 12. Self-isolation / unit boundaries

Each module file has one purpose, a typed interface, and is testable in isolation: `cookie` (pull+decrypt),
`classify` (vague + LLM categorize), `saver` (path + write), `config` (load), `api` (orchestrate), `cli`
(adapt). `LLMClient` is the only shared/frozen piece, owned in `Engine/common`. No file reaches into
another's internals.
