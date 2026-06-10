# bilibili-crawl — architecture (external summary)

Pure consumer skill: `ref → cookie pull (SP-1, domain=bilibili.com) → BilibiliCredential → frozen SP-4a
engine transcribe → render → save Markdown`. Vague save paths are classified by `jarvankb_common.LLMClient`
into a subfolder under `output_root`. Cookie failure degrades to the public-video ASR path (non-fatal).

Modules: `cookie` (pull+decrypt+credential), `config` (load), `classify` (vague + LLM categorize),
`saver` (path + write, single/split), `api` (orchestrate `save_bilibili`), `cli` (thin adapter). Frozen
upstreams (`bilibili` engine, `jarvankb_common.LLMClient`) are consumed verbatim. Internal detail:
`docs/RepoMem/architecture.md`. Frozen contract: `docs/interface.md`.
