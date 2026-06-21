> from: RootOrchestrator g5
> recipient: ReachOrche g1
> type: scope addition to UN-043 (MCP façade) — target the apodex platform
> date: 2026-06-21
> lifecycle: keep with the UN-043 task material

# UN-043 scope addition — switch the integration target to the apodex platform

User instruction (2026-06-21): the MCP-façade work (UN-043, **yours**) gains a **"Miro API modification" item —
switch the integration to the `apodex` platform.** The user states the **apodex platform's API format is COMPLETELY
IDENTICAL to MiroMind/Miro's** → this is a vendor/endpoint re-target, **not** a protocol change.

What this means for your UN-043 build:
- **Path A design carries over unchanged.** Same `mcp_servers` contract (Miro/apodex server calls our public MCP),
  same binding auth/security spec (`docs/superpowers/specs/2026-06-15-mcp-facade-auth-security-design.md`). Identical
  API format ⇒ the integration is a **base-URL / credential / model-id swap**, not new tool code.
- The hosted deepresearch models were already named **`apodex-1-0-deepresearch{-h,,-mini}`** (vs the older
  `mirothinker-1-7-*` docs) — consistent with "apodex is the platform." Path A = hosted **non-`-h`** apodex workflow
  + `mcp_servers`.
- **Confirm at build time** (don't assume): apodex platform's exact endpoint / base-URL, auth scheme, account &
  whitelist setup, and whether it replaces or fronts MiroMind. Fold these into the UN-042 "6 confirms" you carry.

Ownership: UN-043 dispatch stays yours; UN-042 (access-path/Path-A) stays root's, but the platform-name correction
(target = apodex) applies there too — note it when you next touch the MiroThinker integration. No new gate; same
dispatch conditions (apodex/Miro confirms + user go); coordinate the MCP tool-schema with root before dispatch.

— root orche g5 (2026-06-21)
