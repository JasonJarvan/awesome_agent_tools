# Engine

Pure per-platform libraries that turn a content reference (URL, video id) into structured
Markdown + metadata. An Engine has no scheduling loop, no agent packaging, and no LLM
orchestration of its own.

## Language

**Engine**:
A pure library that fetches and transforms content from one platform into structured output.
_Avoid_: crawler, scraper, spider

**FetchResult**:
The Zhihu Engine's structured output for one URL — Markdown body, title, author, metadata,
optionally comments; serializable to Markdown with YAML frontmatter.
_Avoid_: page result, article object

**EmbeddedAnswer**:
A full answer parsed out of a Zhihu question page's server-rendered data, obtained without an
extra request.
_Avoid_: inline answer

**api-fallback**:
The Zhihu Engine's rescue path when a content page's navigation GET is blocked: re-fetch via the
unsigned answers API. Exists for answers only — articles (专栏) have no unsigned equivalent.
_Avoid_: retry (it is a different route, not a repeat)

**Subtitle-first cascade**:
The Bilibili strategy: use the platform's existing subtitle when present (zero cost, zero error);
fall back to audio extraction + ASR only on miss.
_Avoid_: ASR-first, transcription pipeline

**BiliNote (BN)**:
The self-hosted note-generation backend the Bilibili Engine drives over HTTP. BN owns the
download → ASR → LLM-summary steps; the Engine orchestrates and assembles the result.
_Avoid_: bilibili engine (BN is a dependency of it, not it)

**bcut**:
Bilibili 必剪's free cloud ASR — BN's transcriber in v1. Requires no cookie.
_Avoid_: Tingwu/听悟, Paraformer (superseded pre-v1 designs)

**LLMClient**:
The shared in-process LLM access library (`jarvankb-common`), configured by a single repo-root
`config/llm.yaml`. The one way Python modules call an LLM.
_Avoid_: per-module LLM wrapper, direct litellm/openai calls

**Profile**:
A named provider+model entry in `config/llm.yaml`; the `active` list is the fallthrough order
of Profiles tried when the caller does not specify one.
_Avoid_: preset, model config
