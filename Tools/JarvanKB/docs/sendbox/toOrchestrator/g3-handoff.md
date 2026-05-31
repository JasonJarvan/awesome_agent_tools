> from: orchestrator generation 2 (Claude Opus 4.7, active 2026-05-30 → 2026-05-31)
> recipient: orchestrator generation 3 (next Claude Code session inheriting)
> mode: inheritance-handoff (cc-sendbox §Handoff modes §Mode B)
> purpose: hand over full JarvanKB orchestration responsibility; no convergence back
> lifecycle: burn after g3 logs first orche-attributable commit (decision letter to any impler / Dashboard archive / new SP brainstorming kickoff)

# JarvanKB Orchestrator — g2 → g3 Inheritance Handoff

## 1. Identity statement

You are the JarvanKB orchestrator **generation 3** (`g3`). You inherit full orchestration responsibility from g2 (which is gone after this letter is written). Scope: deliver the 10-sub-project v1 family (SP-1 through SP-7) + v1.0 OSS Organization split. HarnessStack recipe v2 is active. The user (JasonJarvan) is the sole human stakeholder.

This is a **role transfer**, not a subtask. There is no g2 to converge back to.

## 2. Status snapshot

| Layer | Status | Evidence |
|---|---|---|
| HarnessStack recipe | v2 `superpowers-repomem-sendbox-dashboard` active | `CLAUDE.md` + `longterm.md` |
| Repo identity | `JarvanKB` (renamed from `AgentCrawl` 2026-05-31) | commits `bd74f70` + `4fc38a5` |
| Working dir | `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB` | `pwd` |
| Branch | `feat/agentcrawl-bootstrap` (parent repo `awesome_agent_tools`) | `git branch` |
| Tags | `sp0-complete` (commit `5c28447`) | `git tag` |
| **SP-0** | ⚫ done | tag `sp0-complete`; 14 commits `8b91d9c..5c28447` |
| **SP-1** | 🟡 wip (Stage 1 brainstorming/design) | `sp1impler` peer CC session active; latest commit `dc5c114` SP-1 design.zh.md added |
| SP-2..7 | ⚪ queued | Dashboard `§SP Status Board` |
| SP-8 (v1+) | ⚪ queued placeholder | `Skill/router/README.md` |
| Git tree | clean except gstack submodule `M` (pre-existing, **never touch**) | `git status` |
| Dashboard `§Active` | 3 rows: UN-006, UN-008, UN-011 (all user-side or you-spawning) | `docs/Dashboard/index.md` |
| Upstream | CodeTeam#1 (mailbox naming) + CodeTeam#2 (HarnessStack v2 consolidated proposal) filed; awaiting user review | `gh issue list -R JasonJarvan/CodeTeam` |

## 3. Must-read list (priority order)

1. **`CLAUDE.md`** — always-loaded contract (recipe v2, 8-step pipeline, hard invariants, Where-to-Look). Already auto-loaded; just internalize §4 Hard Invariants
2. **`docs/HarnessStack/longterm.md`** §Recipe v1→v2 Migration + §Pipeline v2 + §Local sendbox conventions + §Hard Invariants
3. **`docs/Dashboard/index.md`** §Active + §SP Status Board — your current to-do projection
4. **`docs/RepoMem/persist/version-plan.md`** — recipe + generation history, project rename, v1.0 OSS plan
5. **`docs/RepoMem/persist/config.md`** §Language Policy — A2A/H2A rules (formalized + narrowed; existing 中文 RepoMem persist files grandfathered)
6. **`docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md`** §7 SP分解最终表 + §4 分层契约 + §6 recipe v2 — full SP map with paths and dependencies
7. **`docs/sendbox/toSP1Impler/handoff.md`** — what SP1Impler is currently doing (so you don't duplicate)
8. **`docs/sendbox/toAllActiveSessions/from-orche-jarvankb-rename.md`** — broadcast about UN-005 rename; reminds you the AgentCrawl strings in historical-narrative files are intentional, not residue

**Skip**: SP-0 plan.md beyond §Self-Review (executed); R1–R9 subagent transcripts in `/tmp/` (gone with g2 session; conclusions captured in design/plan/persist/commit-messages); the bootstrap inheritance handoff (burned in SP-0 closure).

## 4. Pending decisions / open items

You will encounter these; here's how to handle them:

| Item | How to handle |
|---|---|
| **UN-006**: v1.0 GitHub Org name | Defer until v1 completion nears; not blocking. When time comes, surface options to user |
| **UN-008**: user review of CodeTeam#1 + #2 | User-side only; no orche action. Watch for user response (chat or possibly upstream PR by maintainer) |
| **SP1Impler `plan-ready.md` letter** | When it lands in `toOrchestrator/`, read + review against SP-0 design §7 SP-1 entry; greenlight via `toSP1Impler/from-orche-sp1-greenlight.md` |
| **SP1Impler `blocker-*.md` letter** | A-12 stop-and-ask; respond with `decisions` letter per cc-sendbox §A-12 |
| **SP1Impler `sp1-done.md` letter** | Archive Dashboard SP-1 → ⚫ done; RepoMem.merge HITL for `temp/sp1-cookie-manager/` (promote module decisions to global persist if warranted); spawn SP-2 brainstorming |
| **SP-2 brainstorming kickoff** | Knowledge engine work; user already done R1-R8 research; clarifying intent is `clear`; auto-judge skip brainstorming likely, jump to writing-plans or direct execute. Spawn `toSP2Impler/` handoff (fat-impler pattern like SP-1 if Stage 1+2+3 needed; thin-impler if plan settled) |
| **`docs/sendbox/toAllActiveSessions/from-orche-jarvankb-rename.md`** | Per its frontmatter: archive when SP1Impler logs next stage-transition commit (it has implicitly accepted by then) OR 7 days idle |
| **`docs/sendbox/toOrchestrator/from-sp0impler-sp0-done.md`** | Per its lifecycle "persist until next milestone": archive when SP-1 done lands |

## 5. Active relationships

- **SP1Impler peer Claude Code session** (cwd = `Tools/JarvanKB/`, separate terminal): in flight at Stage 1; communicates via sendbox (`toSP1Impler/` inbound, `toOrchestrator/` outbound) + direct chat with user. DO NOT spawn redundant SP-1 work; let it converge through its own pipeline.
- **User (JasonJarvan)**: project owner, sole human reader. H2A surface = Dashboard + sendbox. See `docs/HarnessStack/hooks/cc-dashboard.md §H2A Coupling`. User's working language = 中文 (per `config.md`); your reply language follows that for H2A docs, English for A2A.
- **CodeTeam upstream** (`JasonJarvan/CodeTeam`): two open issues filed by g2:
  - `#1` — mailbox naming for parallel implementers (with SubOrche generalization comment)
  - `#2` — HarnessStack v2 consolidated proposal (4 proposals: `to{Prefix}{Role}`, H2A Coupling, SP Status Board, Language Policy)
- **Hermes Agent v0.14.0** (`~/.hermes/hermes-agent/`): downstream caller-agent that will eventually consume JarvanKB tools via `docs/sendbox/toAgent/handoff.md` (placeholder; SP-3 / SP-4b will fill it with real I/O contracts)
- **gstack submodule** (parent repo `awesome_agent_tools`): shows `M` in `git status`; pre-existing, unrelated, **never touch**

## 6. Env / tool state

- Working dir: `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`
- Latest commit: `dc5c114` (`docs(SP-1): add Chinese translation design.zh.md (H2A) + cross-link`) — by SP1Impler
- Tag list: `sp0-complete` at `5c28447`
- npm global `@fission-ai/openspec` v1.3.1 still installed (orche kept; user can uninstall anytime; not blocking — v2 recipe doesn't use it)
- Docker not used by orche directly; SP-4a will require Docker for BiliNote deploy when it starts
- `.env` not yet populated (SP-1 / SP-3 / SP-6 / SP-7 will need credentials at their respective stages; not g3's concern until then)

## 7. Orche-internal patterns g2 evolved (not in any single doc — internalize)

These are the soft-knowledge governance refinements g2 landed; they're scattered across `CLAUDE.md`, `longterm.md`, `config.md`, `hooks/cc-dashboard.md`. Read those for full text. Quick mental model:

| Pattern | One-line summary |
|---|---|
| **Per-task mailbox** | `to{Prefix}{Role}/`; root orche = `toOrchestrator/` (no prefix); see CodeTeam#1 |
| **H2A Coupling** | User only reads sendbox + Dashboard; agent-internal docs reached via Dashboard `§Where else to look`; link not copy |
| **A2A / H2A Language Policy** | A2A=English, H2A=user_lang; narrow H2A scope; per-file frontmatter override; existing 中文 RepoMem persist grandfathered (don't churn) |
| **SP kanban location** | Dashboard `§SP Status Board` (NOT in version-plan); single H2A surface for status |
| **Eager-materialization** | When plan heredoc target is H2A and user needs it pre-impler, write to target eagerly so impler's write becomes idempotent overwrite |
| **Generations decoupled from recipe versions** | recipe v=v2, orche gen=g3; tracked in version-plan §Orchestrator generations |
| **Mixed-content split** | If a file accidentally bundles A2A + H2A (e.g. version-plan had kanban), refactor by moving H2A content out, not by adapting language |
| **Forward-edit over revert** | When refining a decision committed earlier, forward-edit with commit message citing supersession; linear history clearer than revert noise |

## 8. Things NOT to do

- Don't replay R1–R9 调研; conclusions are in commit messages + design.md + plan.md + RepoMem persist + this letter
- Don't reintroduce OpenSpec (Full Rewrite required per `longterm.md §Full Rewrite Conditions`)
- Don't move SP kanban out of Dashboard (violates single H2A surface)
- Don't translate grandfathered 中文 RepoMem persist files (churn cost > marginal benefit)
- Don't touch `docs/RepoMem/temp/sp1-cookie-manager/` (SP1Impler-owned, in-flight)
- Don't touch `gstack` submodule (parent-repo concern, never)
- Don't `git push` / `git merge to main` — local commits only on `feat/agentcrawl-bootstrap`
- Don't burn the SP-0 done letter or the rename broadcast prematurely — they have specific lifecycle conditions (§4)
- Don't spawn a new SP-1 anything; SP1Impler owns it end-to-end including reaching Stage 3 after auto-gate

## 9. First-actions checklist (when g3 boots)

In order:
1. `pwd` — confirm `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB`
2. `git log --oneline -10` — see recent commits including any SP1Impler progress past `dc5c114`
3. `ls docs/sendbox/toOrchestrator/` — see if any new `from-sp1impler-*.md` letters arrived
4. Read §3 Must-read list (top 4 minimum)
5. Reply to user in chat: "g3 inherited; ready"

After that, sit in receive mode. Your turn-action is triggered by:
- New letter in `docs/sendbox/toOrchestrator/`
- User chat
- Dashboard row state changes you notice

## 10. Lifecycle of this letter

**Burn condition**: your first orche-attributable commit lands. That commit could be:
- A decision/greenlight letter to any impler (`from-orche-<role>-<topic>.md` to `to<Prefix>Role/`)
- A Dashboard row archive (e.g. you archive UN-011 because "g3 spawned" is done)
- A new SP brainstorming kickoff (e.g. `toSP2Impler/handoff.md`)

When that lands, in the same commit or the next: `git rm docs/sendbox/toOrchestrator/g3-handoff.md`. Update `version-plan.md §Orchestrator generations` g3 row with EOL=ongoing or similar marker the moment you write your own g4-handoff (eventually).

g2 will tag `orche-g2-handoff` at the commit that publishes this letter, so the inheritance point is bisectable.

---

Welcome, g3. The project is in good shape: SP-0 cleanly done, SP-1 self-pacing, all governance patches landed and documented. Two open user-side items in Dashboard, one in-flight peer session. Your first major decision will likely be reviewing SP1Impler's plan-ready letter when it arrives.

— g2, signing off (2026-05-31)
