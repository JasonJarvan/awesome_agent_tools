> from: WatcherDeployImpler
> to: RootOrchestrator g5
> re: NEW FEATURE request (user-asked 2026-06-19/21) — watcher per-run result log ("可观测性")
> action: please handoff an impler session to build it (watcher-CODE change; out of my ops scope)
> created: 2026-06-21
> lifecycle: keep until root opens the task (UN-052) + dispatches an impler

# Feature request — Watcher run-result observability ("每次运行结果" log)

During v1.1 WatcherDeploy the user asked for an **observability feature** (explicitly: queue it as a toOrche
handoff at convergence, don't build it in this ops task). Verbatim intent:

> 我希望每次跑都能产出【结果】日志,然后 Service 会每次将日志 merge 到一个 md,我看 MD 就能知道
> 【每次运行结果】(如果运行没有改动就不合并)。

## What the user wants
A single, human-readable Markdown "run log" per watcher (in the vault, or a known path) that answers
**"what did this run change?"** at a glance, so the user never has to read `docker logs`:
- Each cycle that **made changes** appends a dated section: which collection/folder, which titles, the saved
  paths (zhihu: also the classified folder; bili: transcript source subtitle/asr).
- **No-op cycles do NOT append** (only merge when something changed) — keeps the log signal-dense.
- Reading that one md = the full history of "what got added, when."

## Why it's a separate task (not this deploy)
- It is a **watcher-CODE change in BOTH SP-5a + SP-5b** (a new run-result sink + merge-on-change writer),
  cross-module → **Lane: full** likely. My task was ops/deploy only (frozen watcher code).
- Today the same info is only in `docker logs` (e.g. this deploy already captured 2 real auto-saved zhihu items
  on 2026-06-20 — but the user had to ask me to dig them out of logs; that friction is exactly the motivation).

## Suggested scope for the impler (brainstorm to confirm with user)
- Sink: a structured per-cycle result already exists implicitly (watcher logs `collection/folder … N new`); add a
  result object {ts, target, added:[{title, path, extra}], failures:[…]} and a writer that **appends to a rolling
  md only when `added`+`failures` non-empty**.
- Location/format: one md per watcher (`<output_dir>/_<svc>-runlog.md`?) vs a central one — user to decide.
  Relate to the existing `_zhihu-watcher-attention.md` (failures/attention) — runlog = the positive/changes axis,
  attention = the needs-action axis; keep them distinct or unify (brainstorm).
- Idempotency/rotation, and whether bili includes transcript-source + whether classify items show the chosen folder.

## Ownership
watcher-ops/feature domain → **ReachOrche** (per the v1.1 forward-ownership). Root: please open **UN-052** and
hand off an impler (or route to ReachOrche). Dashboard UN-052 row added.
