"""Live LLM smoke for SP-4b vague_path classification — exercises the REAL `jarvankb_common.LLMClient`.

This hits the one path the offline tests mock: the real `LLMClient` calling the live provider to classify a
sample Bilibili video into a subfolder. It does NOT touch BiliNote / the engine / cookies — just the LLM
provider that `bilibili_crawl.classify` consumes. (Mirrors `Skill/crawl/zhihu-crawl/scripts/live_smoke.py`.)

Credentials: per the shared-layer manual (`docs/RepoMem/persist/memory/llm-shared-layer.md` + `config/llm.yaml`),
keys live in the repo-root `.env` (gitignored, NEVER committed). This script auto-loads that `.env` into the
environment (existing env vars win), so a bare `python scripts/live_smoke.py` works once `.env` has the key
for your chosen profile (e.g. `MIMO_API_KEY` for the `mimo` profile = `openai/mimo-v2.5-pro`).

Run (from anywhere):
    python Skill/crawl/bilibili-crawl/scripts/live_smoke.py            # uses 'mimo' profile
    python Skill/crawl/bilibili-crawl/scripts/live_smoke.py default    # force another config/llm.yaml profile

Pass criterion: prints a real category the model picked from the sample subfolders (or a sensible new one)
and "LIVE SMOKE OK". Missing creds -> LLMClient raises a clear RuntimeError naming the env var to set.

(The full transcribe->save pipeline live test additionally needs BiliNote up + `config/bilibili-engine.yaml`
resolvable; run that via the CLI `bilibili-crawl <BV> --out <path>` when BN is up — it is a separate
engine-side gate, intentionally out of this LLM-provider smoke.)
"""
import os
import sys
import tempfile
import types
from pathlib import Path

# JarvanKB root = .../Tools/JarvanKB (scripts -> bilibili-crawl -> crawl -> Skill -> JarvanKB)
JARVANKB_ROOT = Path(__file__).resolve().parents[4]


def _load_dotenv(path: Path) -> None:
    """Minimal stdlib .env loader (no python-dotenv dep). Existing env vars take precedence."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip())


def main() -> int:
    profile = sys.argv[1] if len(sys.argv) > 1 else "mimo"
    _load_dotenv(JARVANKB_ROOT / ".env")

    from jarvankb_common import LLMClient        # the shared LLM layer (Engine/common)
    from bilibili_crawl import classify          # SP-4b vague_path classifier — consumes LLMClient

    item = types.SimpleNamespace(
        metadata=types.SimpleNamespace(
            title="【硬核】从零实现一个 Transformer:注意力机制逐行讲解"),
        summary_markdown=("本视频深入讲解 Transformer 的自注意力与多头注意力机制,逐行实现 "
                          "scaled dot-product attention,并讨论位置编码与训练技巧。"),
        transcript=types.SimpleNamespace(full_text="大家好，今天我们从零实现 transformer ……"),
    )
    root = Path(tempfile.mkdtemp())
    for name in ("机器学习", "历史", "生活随笔", "投资理财"):
        (root / name).mkdir()

    client = LLMClient(profile=profile, config_path=str(JARVANKB_ROOT / "config" / "llm.yaml"))
    cat = classify.classify(item, root, client)    # REAL LLM call via the configured provider

    print(f"profile            : {profile}")
    print(f"provider model     : {client._candidates[0].model}")
    print(f"existing subfolders: {sorted(p.name for p in root.iterdir())}")
    print(f"LIVE classify      -> category={cat.name!r}  is_new={cat.is_new}")
    print("LIVE SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
