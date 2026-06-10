"""Manual live smoke: real Bilibili video -> engine transcribe -> save, both explicit and vague paths.

Requires (the live-smoke GATE — see docs/superpowers/plans/2026-06-07-SP-4b-bilibili-skill-plan.md Task 10):
- BiliNote up (container jarvankb-bilinote @ 127.0.0.1:3015).
- `config/bilibili-engine.yaml` resolvable from the CWD (the real one lives at
  `Engine/bilibili/config/bilibili-engine.yaml`; run from there, or copy/symlink it under the CWD's `config/`).
- repo-root `config/llm.yaml` `mimo` profile + `MIMO_API_KEY` set (for the vague-path classification half).
- a `bilibili-crawl` `config.yaml` (copy `config.example.yaml`; set `output_root` + cookie connection).
  Cookie is optional — a missing/expired cookie degrades to the public-video ASR path (non-fatal).

NOT part of the unit suite (needs live services). Run manually:
    python scripts/live_smoke.py "BV1xx..." [output_dir]
"""
import sys

from bilibili_crawl import save_bilibili


def main() -> int:
    ref = sys.argv[1] if len(sys.argv) > 1 else "BV1GJ411x7h7"  # replace with a known-public ref
    out_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print("== explicit-path save (no LLM) ==")
    r1 = save_bilibili(ref, save_path=f"{out_dir or '.'}/_smoke_explicit.md")
    print(f"  path={r1.path} source={r1.transcript_source} title={r1.title!r}")

    print("== vague-path save (LLM classify via mimo) ==")
    r2 = save_bilibili(ref, save_path=out_dir)  # None -> classify under config output_root
    print(f"  path={r2.path} category={r2.category} new={r2.proposed_new} was_vague={r2.was_vague}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
