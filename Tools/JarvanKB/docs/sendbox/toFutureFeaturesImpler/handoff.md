> from: root orchestrator generation 4 (Claude Opus 4.8 1M, active 2026-06-07 →)
> recipient: FutureFeaturesImpler (a new Claude Code peer session you are about to become)
> mode: child-handoff (sendbox-protocol Mode A — root stays alive; you converge back to `toOrchestrator/`)
> purpose: requirements-clarify + research TWO future features (an auto-researcher scheduled agent; a repo-wide
>   agent-friendly index), produce a grounded DRAFT, and land it in the future version plan for LATER activation
> lifecycle: burn after root reads your `from-futurefeaturesimpler-done.md`
> date: 2026-06-11

# Handoff — FutureFeaturesImpler (draft two v2+ features into the version plan)

## 0. What you are

You are a **research + requirements-drafting** impler, a **direct child of root orche g4** (cross-cutting
future-platform features = root's domain, not a vertical's). Root stays alive; you converge back to
`toOrchestrator/`. Task identifier: **`future-features-auto-researcher-repo-index`**.

**This is NOT an implementation task.** You produce a *grounded draft* (requirements + research + open
questions) and write it into the future version plan, **explicitly marked "draft — not active, to be refined
& activated later."** No feature code. The user's words: *做个需求澄清和调研，产生 draft，然后写入 future
version plan，将来再激活和细化。*

## 1. The two features (capture the user's framing faithfully — it is the seed)

**Feature A — "auto researcher" scheduled agent (GENERAL).**
Make a scheduled/autonomous agent runtime — **like Hermes / OpenClaw** — into an **auto researcher**: it
accepts a **`/goal`** (a goal-driven directive analogous to codex's / claude-code's "goal" — **research how
those are actually implemented**), then **autonomously works to achieve that goal**. Its capabilities include
but are not limited to:
- **auto-reading the knowledge base**,
- **auto-using tools**, including but not limited to: tools/skills installed in **Hermes**; this repo's
  **Zhihu / Bilibili crawl skills** (SP-3 / SP-4b); the **MiroThinker research tool** (`MiroResearch`, §3);
  and other skills in the workspace.

**Feature B — repo-wide agent-friendly index (SPECIFIC).**
Generate an **agent-friendly index of the whole repository** — e.g. an **LLM wiki**, or a **memory system**
in the spirit of **Mem0 / MemOS / …**. The goal of B is to deliver a *general capability* (a reusable
indexing/memory layer over the repo).

**The relationship (a key design thesis — preserve it):**
A is the **general** feature; B is the **specific** one (B's aim is a general capability). **A can GROW OUT OF
B's practice** — e.g. via self-evolving / self-learning: *first research, then summarize, and in doing so
complete B's process itself.* I.e. building B (the repo index) is a concrete instance of the auto-researcher
loop A describes; doing B well teaches how to generalize into A. Explore + sharpen this thesis with the user.

## 2. Method (the user specified this)

- **`superpowers:brainstorming`** — run requirements clarification **WITH THE USER** first. The two features
  are deliberately open; pin scope, success criteria, boundaries, and the A↔B relationship before drafting.
- **`grill-with-docs`** — stress-test your draft against RepoMem + current-code ground truth.
  ⚠️ This skill is **mid-replacement** (UN-034) — its semantics may be shifting between "design-review gate"
  and "CONTEXT.md producer." Check `docs/Dashboard/index.md` UN-034 state; use whatever grill capability is
  available, or fall back to a manual adversarial design review if it's unstable. Don't block on it.
- Then **research** (web + local) → draft → write into the version plan.
- **Lane: full** (net-new, cross-cutting, produces a `persist/` asset). Declare it in your plan-doc frontmatter.

## 3. Research scope (what to investigate — cite findings)

1. **`/goal` mechanism.** How do codex and claude-code implement goal-driven autonomous loops? (Codex stores
   goals in `~/.codex/goals_1.sqlite`; investigate the actual pattern — plan/step loop, tool selection,
   stop conditions.) This grounds Feature A's `/goal` contract.
2. **Hermes & OpenClaw.** Their autonomous/scheduled-agent model: how tools & skills are installed and
   invoked, scheduling, memory, and what "auto researcher" would require of them. (Note: `cc-switch` manages
   skills for both — `--app hermes` / `--app open-claw` — so the repo's skills can be synced to them; relevant
   to A's "auto-use tools" capability.)
3. **MiroThinker / `MiroResearch`.** ⚠️ It is **newly added and NOT in the local working tree** — first
   **`git pull` / sync the parent repo `awesome_agent_tools`**, then examine **`awesome_agent_tools/Skills/
   MiroResearch`** (capital-S `Skills/` at the *parent-repo root* — distinct from JarvanKB's `Tools/JarvanKB/
   Skill/`). Understand what research capability it provides and how A would orchestrate it.
4. **Memory / index systems for Feature B.** Survey **Mem0, MemOS, "LLM wiki"** patterns (and peers) — their
   data model, update/retrieval, and applicability to indexing THIS repo for agent consumption. Relate to the
   project's existing **RepoMem** layer (persist/architecture/memory + temp) — B is plausibly an evolution /
   superset of RepoMem; say how.
5. **The repo's own tools as A's toolbox.** SP-3/SP-4b crawl skills, `awesome_agent_tools/Skills/`
   (web-search, skill-orchestrator, ProductMngr, …), and the `jarvankb_common` LLMClient — inventory what an
   auto-researcher could already call.
6. **Situate vs existing roadmap.** Reconcile with what's already in `version-plan.md`: the **LLMService v2**
   roadmap (§Shared LLM layer) and **SP-8 Web Search Router**. Do A/B subsume, depend on, or sit beside them?

## 4. Inputs (minimum — re-fetch as needed)

| Need | Path |
|---|---|
| Where the draft lands | `docs/RepoMem/persist/version-plan.md` — add a new section, e.g. `## Future feature drafts (v2+)`, clearly marked draft/not-active. Keep `### v1.0 OSS release plan` + existing sections intact. |
| Existing roadmap to reconcile | same file: `§v1.0 OSS release plan`, `§Shared LLM layer / LLMService v2 roadmap` |
| The repo's memory layer (B's relative) | `docs/RepoMem/persist/` + `docs/RepoMem/README.md` + the `repo-mem` skill |
| SP map (where A/B would slot) | `docs/superpowers/specs/2026-05-31-SP-0-jarvankb-skeleton-design.md` §7 (SP-8 + v1+ candidates) |
| Crawl tools A would use | `Skill/crawl/{zhihu-crawl,bilibili-crawl}/docs/interface.md` |
| Parent-repo skills + MiroResearch | `awesome_agent_tools/Skills/` (sync first — §3.3) |
| Cross-runtime skill mgmt (Hermes/OpenClaw/Codex) | `cc-switch skills --help` (`--app` ∈ claude/codex/gemini/open-code/hermes/open-claw) |

## 5. Deliverable + convergence

- **Draft content** (in `version-plan.md`, marked draft-for-later-activation): for EACH feature — problem &
  goal, scope + explicit non-goals, the `/goal` contract sketch (A) / index data-model sketch (B), the tools/
  runtimes involved, research findings with citations, the **A-grows-from-B self-evolving thesis**, open
  questions, and a rough sequencing/dependency note vs LLMService-v2 / SP-8. **It is a draft** — completeness
  of *thinking* and clarity of *open questions* matter more than final answers.
- **Discipline:** Lane: full; brainstorm-with-user → research → draft → grill/adversarial review → land. No
  feature code. Your **Step-8 RepoMem.merge IS the act of writing the draft into `version-plan.md`** (HITL,
  user-approved); keep it non-duplicative with existing roadmap sections; prune any temp.
- **Done →** `docs/sendbox/toOrchestrator/from-futurefeaturesimpler-done.md` (what landed: the version-plan
  section + a 1-paragraph summary per feature + the key open questions deferred to activation-time + commit).
- **Blocked →** `docs/sendbox/toOrchestrator/from-futurefeaturesimpler-blocker-<topic>.md` (options + your pick).
- **Parent cwd (absolute):** `/home/shenzhou/Codes/awesome_agent_tools/Tools/JarvanKB/`.

## 6. Worktree / commit / out-of-scope

- Worktree off **local** `feat/agentcrawl-bootstrap` (NOT origin/main). Push enabled for that branch; **no
  merge to main / rebase / gstack** without user say-so. Scope commits with pathspec; shared tree → re-read on
  conflict. Don't touch other sessions' in-flight files, `.claire/`, or `.mcp.json` (gitignored key; **repo
  is PUBLIC** — don't paste secrets into the draft).
- **Out of scope:** implementing A or B; activating the features; editing CLAUDE.md/longterm governance;
  reintroducing OpenSpec. If syncing the parent repo surfaces conflicts/uncommitted work, **don't force it —
  surface to the user** (the parent repo is shared; `gstack` shows `M` and is off-limits).

## 7. Day-1 checklist

1. `RepoMem.read` (global persist) + read `version-plan.md` (roadmap to reconcile) + SP-0 §7.
2. `superpowers:brainstorming` **with the user** — pin scope + success criteria + the A↔B thesis (§1).
3. Sync parent repo → examine `Skills/MiroResearch`; research §3 items (web + local), citing.
4. Draft both features → grill / adversarial review → land in `version-plan.md §Future feature drafts (v2+)`,
   marked draft.
5. Verification (grounded + cited + internally consistent + captures user's full thesis & open questions) →
   Step-8 (the write-in) HITL → report `from-futurefeaturesimpler-done.md`.

— root orche g4 (2026-06-11)
