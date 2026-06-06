"""Live LLM smoke for SP-3 vague_path classification — requires REAL LLM credentials.

This exercises the one path the offline tests mock: the real `LLMClient` calling a live provider
to classify a sample item into a subfolder. It does NOT touch the network for cookies/Zhihu.

Setup (one-time):
  1) cp <repo-root>/config/llm.yaml.example <repo-root>/config/llm.yaml   # already has default+fallback
  2) export the key for your chosen profile:
       default  profile -> ANTHROPIC_API_KEY   (model claude-opus-4-7)
       fallback profile -> DASHSCOPE_API_KEY    (model dashscope/qwen-max)
     (put it in <repo-root>/.env or just `export` it in your shell — NEVER commit it)

Run (from the repo root, or set JARVANKB_LLM_CONFIG to the absolute config path):
    python Skill/crawl/zhihu-crawl/scripts/live_smoke.py            # uses 'default' profile
    python Skill/crawl/zhihu-crawl/scripts/live_smoke.py fallback   # force a profile

Pass criterion: it prints a real category the model picked from the sample subfolders (or a sensible
new one) and "LIVE SMOKE OK". If credentials are missing, LLMClient raises a clear RuntimeError naming
the env var to set.
"""
import sys
import tempfile
import types
from pathlib import Path

from jarvankb_common import LLMClient
from zhihu_crawl import classify


def main() -> int:
    profile = sys.argv[1] if len(sys.argv) > 1 else "default"

    item = types.SimpleNamespace(
        title="Transformer 自注意力机制详解",
        type="answer",
        content_markdown="本文从 Q/K/V 出发讲解自注意力、多头注意力与位置编码,并对比 RNN 的长程依赖问题……",
    )
    root = Path(tempfile.mkdtemp())
    for name in ("机器学习", "历史", "生活随笔", "编程工具"):
        (root / name).mkdir()

    client = LLMClient(profile=profile)            # raises a clear error if no creds available
    cat = classify.classify(item, root, client)    # REAL LLM call

    print(f"profile           : {profile}")
    print(f"existing subfolders: {sorted(p.name for p in root.iterdir())}")
    print(f"LIVE classify     -> category={cat.name!r}  is_new={cat.is_new}")
    print("LIVE SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
