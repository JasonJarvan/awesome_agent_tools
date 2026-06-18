---
language: en
audience: A2A
status: rejected-alternative record (local-GPU ASR) — keep cloud bcut
created: 2026-06-19
---

# Local-GPU ASR Enablement — Feasibility Assessment (REJECTED, keep cloud bcut)

> Read-only assessment (subagent, 2026-06-19) of making this host's GPU usable for in-container `faster-whisper`,
> so BiliNote could switch from cloud bcut to local GPU ASR. **Outcome: NOT worth it — keep bcut.** User-facing:
> `toUser/2026-06-19-bn-transcription-cloud-vs-local-and-gpu.md`. Supersedes the looser note in
> `crawl-pipeline.md` ("GPU 驱动不匹配 → 本地 ASR 不可用") with the exact why.

## Verdict (gating question = "fully automatic, no human, no machine reboot?")
**NO — not fully automatic.** Hard blocker: **no passwordless sudo** (`sudo -n true` → exit 1, "需要密码"); every
required step (driver realign, toolkit install, dockerd restart) needs root → a human must supply the password.
**Reboot is NOT required** (modules reloadable — evidence below), so reboot is not the blocker; **privilege is.**
Deeper: even with a human, the prebuilt CT2 CUDA wheels don't run on this card → a from-source CT2 build is needed.

## Two corrected facts (override earlier hypotheses)
1. **Maxwell IS supported on driver 580.** 580 is the *last/frozen legacy branch* that keeps Maxwell/Pascal/Volta
   (the 590/595 branch dropped them). So the GTX 860M (GM107, CC 5.0) works on 580 — the fix is **realign the same
   580 branch, NOT downgrade to 470/535.** (Earlier "downgrade = reboot-class" hypothesis was wrong.)
2. **The mismatch is a stale-module skew, fixable without reboot.** Loaded kernel module `580.126.09` (the on-disk
   `nvidia.ko` for the *running* kernel `6.17.0-20-generic`) vs userspace NVML `580.159.03` (whose module is only
   installed for the *not-booted* `6.17.0-35-generic`). Fix without reboot: reinstall/DKMS-rebuild the .159 module
   for the running kernel + reload, OR revert userspace to .126, OR boot 6.17.0-35. Reboot-free is genuinely
   possible because: display is on the **Intel iGPU** (`i915`, `boot_vga=1` on 00:02.0; NVIDIA is a "3D controller",
   Optimus `on-demand`); session is `XDG_SESSION_TYPE=tty`; nvidia module use-counts 0; `fuser /dev/nvidia*` empty →
   modules unpinned.

## Three required steps (all necessary; none optional)
| Step | Cost | root? | non-interactive? | reboot? |
|---|---|---|---|---|
| 1. Driver realign (reinstall .159 module for running kernel + reload) | minutes | yes | yes *if root pre-granted* | no |
| 2. `nvidia-container-toolkit` install + `nvidia-ctk runtime configure` (runtime is plain `runc`, no `nvidia`) | minutes | yes | yes | no |
| 3a. dockerd restart | seconds | yes | yes | no (≠ machine reboot; `live-restore` OFF → bounces `jarvankb-bilinote`, which `restart: unless-stopped` auto-returns) |
| 3b. CUDA-enabled BN image (current `ghcr.io/jefferyhcool/bilinote:latest` is CPU-only, no torch/CUDA) + `--gpus`/device reservation + `TRANSCRIBER_TYPE=fast-whisper` | several GB pull/build; **`/` only 12 GB free of 39 GB** → tight | yes | yes | no |
| 0. **From-source CT2 build w/ CC 5.0** (likely dominates) | hours | build-time | fiddly | no |

## Worth-it: marginal-to-negative
Prebuilt `ctranslate2 ≥4.5` (host has 4.6.0) needs CUDA ≥12.3 and its wheels throw
`cudaErrorNoKernelImageForDevice` on CC 5.0 Maxwell (CT2 #1765, faster-whisper #1086) → needs from-source CT2 with
CC 5.0 re-enabled. Even then 2 GB VRAM caps to tiny/base/small-int8, no FP16 (CC < 7.0) → little gain over CPU, and
**negative vs free/zero-maintenance cloud bcut** (which only runs for subtitle-less videos). **Keep bcut.**

## Re-trigger conditions
Revisit only if (a) the user swaps the GPU, or (b) the user needs fully-local/offline transcription (audio must not
leave the host). Then: user grants sudo → fix module skew (no reboot) → toolkit → from-source CT2 → CUDA image.

Sources: Phoronix (580 = last branch for Maxwell/Pascal/Volta); CTranslate2 #1765 (CC 5.0); faster-whisper #1086;
CTranslate2 hardware-support page.
