---
slug: sp4a-bilibili-engine
status: done
domains: [bilibili-engine]
updated_at: 2026-06-02
---

# SP-4a manual smoke evidence (Stage-3, against live BiliNote + real bilibili)

BiliNote: `ghcr.io/jefferyhcool/bilinote:latest`, host `127.0.0.1:3015` → backend `:8483`
(nginx bypassed — image's nginx broken). `TRANSCRIBER_TYPE=bcut`. LLM provider = xiaomi mimo
(`mimo-v2.5-pro`, OpenAI-compatible). Credential pulled from SP-1 cookie-manager (`domain=bilibili.com`).

## ✅ ASR path — `BV1GJ411x7h7` (no credential → subtitle skipped → bcut), 28s
- `transcript_source = asr`; 61 segments from bcut; full_text = the song's lyrics (bcut transcribed singing).
- `summary_markdown` present (mimo, ~1.2k chars, structured zh note).
- Render: frontmatter (bvid/title/up/url/duration/pubdate=2019-12-31/transcript_source) + summary + prose transcript.

## ✅ Subtitle path — `BV1BXQABNE4y` (with SESSDATA → AI subtitle → prefetched to BN), 84s
- `transcript_source = subtitle`; 456 segments; `language = ai-zh`; engine fetched the AI subtitle via
  bilibili-api-python and fed it to BN as `prefetched_transcript` (BN skipped audio+ASR, ran summary only).
- `summary_markdown` present (mimo-v2.5-pro, ~2.6k chars — richer than ASR run).
- Render frontmatter `transcript_source: subtitle`, pubdate 2026-04-11.

## ✅ Prose-merge (user's key requirement: readable text, not line-per-segment)
- 456 subtitle segments → ~27 flowing paragraphs (longest line 626 chars), CJK joined without spaces.
  `include_timestamps=False` default. Confirmed on real data for both runs.

## ✅ split mode
- Covered by unit tests (`test_split_emits_two_documents_and_link`); render is pure, not re-run against BN.

## Defects found + fixed during smoke (both committed)
1. `bilibili-api-python.get_subtitle` RAISES `CredentialNoSessdataException` without SESSDATA (not empty).
   `fetch_subtitle` now returns None on missing-cred / any subtitle-fetch error → cascade falls to ASR;
   engine now runs on public videos with NO credential. (+4 tests)
2. `latest` BiliNote image's nginx is broken (`/`→nonexistent :8080; Debian default site shadows `/api/`);
   deploy compose now maps host port straight to backend `:8483`. `TRANSCRIBER_TYPE` must be set via
   `POST /api/transcriber_config` (env doesn't pass through supervisord in that image).
3. ASR branch now raises `TranscriptionFailed` if BN returns SUCCESS with no transcript (final-review minor).

## Cross-SP gotcha for Step 8 promotion
- Bilibili cookies are stored in SP-1 cookie-manager under domain **`bilibili.com`** (no leading dot),
  NOT `.bilibili.com` as `credentials.md` / design assumed. SP-4b / SP-5b must query `domain=bilibili.com`.
- BiliNote `latest` image nginx breakage + the `/api` direct-to-backend workaround + bcut-needs-no-cookie
  + env-not-passing-through-supervisord: reusable BN-client operational knowledge.
