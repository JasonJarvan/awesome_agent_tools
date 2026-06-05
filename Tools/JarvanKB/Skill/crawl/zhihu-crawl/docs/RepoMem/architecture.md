# zhihu-crawl — Module Internal Architecture

> A2A internal memory (English per Language Policy). External summary: `docs/architecture.md`.
> Version: v1 (frozen, SP-3, 2026-06-05).

## File responsibilities

| File | Responsibility |
|---|---|
| `src/zhihu_crawl/api.py` | `save_zhihu()` orchestration: config load → cookie pull → engine fetch → vagueness check → classify (if vague) → path resolve → write. Imports `LLMClient`, `fetch` at module level so tests can monkeypatch. |
| `src/zhihu_crawl/cli.py` | argparse thin shell over `save_zhihu`; `--json` dumps `dataclasses.asdict(result)`; exit-code map: 0=ok, 1=generic, 2=ZhihuFetchError. |
| `src/zhihu_crawl/cookie.py` | Active pull from SP-1 (`GET {base_url}/get/{uuid}`) + client-side decrypt. Supports two `crypto_type` values (see §Cookie decrypt below). Plaintext never written to disk. |
| `src/zhihu_crawl/classify.py` | `is_vague(save_path, output_root)` rule + `classify(result, output_root, client)` LLM classification. Prompt feeds existing subdirs + title + type + 500-char snippet. JSON extraction handles fenced-code-block wrapping. |
| `src/zhihu_crawl/config.py` | Loads `config.yaml` (YAML). Fields: `output_root`, `cookie.{base_url,uuid,password_env}`, `llm.profile`. Password resolved from env by `password_env`; `~` expanded on all paths. Default path: `ZHIHU_CRAWL_CONFIG` env → `config.yaml` in cwd. |
| `src/zhihu_crawl/saver.py` | `slugify(title)` (CJK-safe, lowercased, hyphenated), `is_vague()` rule, `resolve_target()` with numeric-suffix dedup, `write()` (creates parents). |
| `src/zhihu_crawl/__init__.py` | Re-exports `save_zhihu`, `SaveResult` only (public surface). |

## Cookie decrypt (both crypto_types)

Key derivation (shared): `the_key = md5(f"{uuid}-{password}").hexdigest()[:16]` (16-char hex string).

**`legacy`** (default; CryptoJS OpenSSL-envelope):
1. Base64-decode the ciphertext; expect `b"Salted__"` prefix (8 bytes).
2. Extract 8-byte salt from bytes 8–15.
3. Derive AES-256 key (32 B) + IV (16 B) via `EVP_BytesToKey` (iterated MD5: `md5(prev + passphrase + salt)`, where passphrase = `the_key.encode()`).
4. AES-256-CBC decrypt + PKCS7 unpad.

**`aes-128-cbc-fixed`**:
1. Raw base64-decode (no `Salted__` header).
2. `key = the_key.encode()[:16]`, IV = 16 zero bytes.
3. AES-128-CBC decrypt + PKCS7 unpad.

Outer JSON: `{cookie_data, local_storage_data, update_time}`. Take `cookie_data[".zhihu.com"]` (list of `{name, value}` objects) → `{name: value}` dict. Keys of interest: `z_c0`, `d_c0`, `__zse_ck`.

## vague_path classification flow

1. `is_vague(save_path, output_root)`: returns True iff `save_path` is None/empty, or equals `output_root`, or has no `.md` suffix.
2. `existing_subfolders(output_root)`: sorted immediate subdirs (skip hidden).
3. Prompt: existing folders + item title + type + content[:500] → `LLMClient.complete()` → JSON `{category, is_new}`.
4. JSON extraction: try fenced-code-block regex first, fallback to bare `{...}` regex.
5. `is_new` is authoritative from the filesystem: `name not in existing_subfolders` overrides the model's flag.
6. Category name is slugified before use.

## Path resolution + filename rules

- Explicit: `save_path` ends in `.md` → use verbatim (no classify, no dedup).
- Vague: `<output_root>/<category>/<slugify(title)>.md`. If that file exists, append `-2`, `-3`, … until free.
- `slugify`: strips non-word non-CJK chars, hyphenates runs, lowercases, returns `"untitled"` on empty.

## Cross-SP promotion candidates (D-SP3-3)

These patterns are cross-SP-reusable and are promoted to global `persist/` at Step-8 HITL merge:

1. **SP-1 cookie active-pull + client-side decrypt** (`legacy` CryptoJS Salted__/EVP + `aes-128-cbc-fixed`):
   SP-5a / SP-4b will need the same pull-and-decrypt; the *lesson* (not the code) belongs in global memory.
2. **`LLMClient` real litellm body** (landed in `Engine/common`, made importable via new `pyproject.toml`):
   SP-6 reuses as-is; the packaging pattern (add `pyproject.toml` + src-layout to `Engine/common`) is global.
3. **agentskills.io single-SKILL.md-across-four-runtimes packaging**:
   SP-4b will need the same pattern; already in cross-session memory.

Module-local (stay here, not promoted): vague_path classification mechanism, path-resolution rules, slug rules.

## D-SP3-4: LLMClient library vs service (v1/v2 note)

v1: `LLMClient` is an **in-process library** (`jarvankb_common.LLMClient` + single `config/llm.yaml`).
v2 plan (deferred, new platform SP): promote to a standalone `Service/.../llm-service` (HTTP, OpenAI-compatible)
for centralized config / metering / rate-limit / cache. The `complete`/`stream` interface is frozen — the
v2 swap is a non-breaking substitution at the `LLMClient` constructor level; SP-3/6/7 call sites do not change.

## Test boundary summary

Every module file is tested in isolation with mocks:
- `cookie`: decrypt round-trips (both crypto_types), pull with FakeClient.
- `classify`: existing-subfolders listing, pick-existing, propose-new, is_new override from filesystem.
- `saver`: `is_vague` rule matrix, `slugify`, `resolve_target` (explicit + vague + dedup), `write`.
- `config`: password-from-env, llm_profile default.
- `api`: explicit-path write (no classify called), vague-path write (classify + save), `SaveResult` fields.
- `cli`: `--json` output shape, flag passthrough, `ZhihuFetchError` exit code 2.

No live credentials or network calls in the unit suite.
