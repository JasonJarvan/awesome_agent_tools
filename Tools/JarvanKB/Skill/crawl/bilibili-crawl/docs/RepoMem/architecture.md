# Module internal architecture

Layering (leaf → orchestration): `cookie` / `config` / `saver` / `classify` are independent leaves;
`api.save_bilibili` orchestrates them + the frozen engine; `cli` is a thin argparse adapter over `api`.

Key paths:
- Cookie: `cookie.pull(source, domain="bilibili.com")` reuses SP-3's verified decrypt (legacy +
  aes-128-cbc-fixed); `build_credential` maps `SESSDATA`(+`bili_jct`,`buvid3`) → `BilibiliCredential`, or
  `None` when SESSDATA absent. In-memory only.
- Render: options come from `config.render`; `api` passes `slug=target.stem` so a split transcript file
  (`<stem>.transcript.md`) matches the engine's in-document link.
- Classify input: `metadata.title` + a markdown-stripped lead of `summary_markdown` (fallback
  `transcript.full_text`), capped at `classify_snippet_chars`.
- Graceful degrade: cookie pull/decrypt failure is caught in `api` → `credential=None` + warning.

Test seams: `api.transcribe` / `api.LLMClient` / `api.cookie.*` / `api.cfgmod.load_config` are
module-level so unit tests monkeypatch them — no live engine / LLM / cookie service needed.
