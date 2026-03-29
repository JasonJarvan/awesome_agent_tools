import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import time
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, urlparse

import requests
import yaml


ROOT = Path(__file__).resolve().parents[1]
REFERENCES_DIR = ROOT / "references"
SOURCES_PATH = REFERENCES_DIR / "sources.yaml"
DEFAULT_OUTPUT_DIR = ROOT / "output"
USER_AGENT = "awesome-agent-tools/skill-orchestrator"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "for",
    "from",
    "help",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "reusable",
    "skill",
    "that",
    "the",
    "to",
    "tool",
    "use",
    "want",
    "with",
}
DOMAIN_HINTS = {
    "code_review": ["review", "reviewer", "reviewing", "critique", "audit", "pr"],
    "documentation": ["documentation", "docs", "spec", "proposal", "decision", "doc", "co-authoring"],
    "refactor": ["refactor", "refactoring", "cleanup", "migration", "modernization"],
    "debugging": ["debug", "debugging", "bug", "incident", "triage", "fix"],
    "testing": ["test", "testing", "qa", "verification", "validate"],
    "research": ["research", "investigate", "archaeology", "discovery", "explore"],
}
ECOSYSTEM_TERMS = {
    "codex": ["codex", "openai", "codex app"],
    "claude_code": ["claude code", "anthropic", "agent skills"],
    "openclaw": ["openclaw", "agentskills"],
}


@dataclass
class SearchSource:
    source_type: str
    level: str
    ecosystem: str
    name: str
    url: str
    description: str


@dataclass
class Candidate:
    name: str
    type: str
    source_type: str
    source_name: str
    ecosystem: str
    summary: str
    why_it_matches: str
    community_signals: str
    adaptation_need: str
    adoption_cost: str
    risks: str
    link: str
    score: int
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    source: SearchSource
    candidates: list[Candidate]
    notes: list[str]


@dataclass
class CreationBrief:
    reason_creation_is_justified: str
    target_ecosystem: str
    user_need: str
    expected_trigger_phrases: list[str]
    core_workflow: list[str]
    reusable_resources: dict[str, list[str]]
    cross_platform_concerns: list[str]
    open_questions_for_user: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search for reusable agent skills before deciding to create a new one."
    )
    parser.add_argument("request", help="Natural-language description of the skill you want.")
    parser.add_argument(
        "--ecosystem",
        choices=["auto", "codex", "claude_code", "openclaw"],
        default="auto",
        help="Target ecosystem. Defaults to auto.",
    )
    parser.add_argument(
        "--source-type",
        choices=["auto", "skill_market", "github", "other_market"],
        default="auto",
        help="Preferred starting source type. Defaults to auto.",
    )
    parser.add_argument(
        "--max-candidates",
        type=int,
        default=3,
        help="Target number of candidates to present. Defaults to 3.",
    )
    parser.add_argument(
        "--max-per-source",
        type=int,
        default=5,
        help="Maximum raw candidates gathered from any single source. Defaults to 5.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for JSON and Markdown summaries. Defaults to skill-orchestrator/output.",
    )
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print the final JSON result to stdout instead of a Markdown summary preview.",
    )
    return parser


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "search"


def keywordize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9][a-z0-9_-]{1,}", text.lower())
    ordered: list[str] = []
    for word in words:
        if word in STOPWORDS:
            continue
        if word not in ordered:
            ordered.append(word)
    return ordered[:10]


def fit_keywords(request_keywords: list[str], ecosystem: str) -> list[str]:
    ecosystem_words = set(" ".join(ECOSYSTEM_TERMS.get(ecosystem, [])).replace("-", " ").split())
    generic = {"skill", "skills", "agent", "agents", "tool", "tools", "code"}
    filtered = [
        keyword
        for keyword in request_keywords
        if keyword not in ecosystem_words and keyword not in generic
    ]
    return filtered or request_keywords


def extract_phrases(text: str) -> list[str]:
    lowered = re.sub(r"[^a-z0-9\s-]+", " ", text.lower())
    tokens = [token for token in lowered.split() if token and token not in STOPWORDS]
    phrases: list[str] = []
    for size in (3, 2):
        for index in range(len(tokens) - size + 1):
            phrase = " ".join(tokens[index : index + size]).strip()
            if len(phrase) >= 8 and phrase not in phrases:
                phrases.append(phrase)
    return phrases[:8]


def detect_domain_hints(request: str) -> list[str]:
    lowered = request.lower()
    matched: list[str] = []
    for label, hints in DOMAIN_HINTS.items():
        if any(hint in lowered for hint in hints):
            matched.append(label)
    return matched


def normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def contains_hint(candidate_text: str, hint: str) -> bool:
    normalized_candidate = normalized_text(candidate_text)
    normalized_hint = normalized_text(hint)
    if not normalized_hint:
        return False
    if " " in normalized_hint:
        return normalized_hint in normalized_candidate
    return bool(re.search(rf"\b{re.escape(normalized_hint)}\b", normalized_candidate))


def hint_overlap_score(request_hints: list[str], candidate_text: str) -> int:
    if not request_hints:
        return 0
    score = 0
    for label in request_hints:
        hints = DOMAIN_HINTS[label]
        hits = sum(1 for hint in hints if contains_hint(candidate_text, hint))
        if hits >= 2:
            score += 8
        elif hits == 1:
            score += 4
    return min(20, score)


def phrase_overlap_count(phrases: list[str], candidate_text: str) -> int:
    lowered = candidate_text.lower()
    return sum(1 for phrase in phrases if phrase in lowered)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def get_session() -> requests.Session:
    session = requests.Session()
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    session.headers.update(headers)
    return session


def load_sources(path: Path = SOURCES_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def detect_ecosystem(request: str) -> str:
    lowered = request.lower()
    for ecosystem, terms in ECOSYSTEM_TERMS.items():
        if any(term in lowered for term in terms):
            return ecosystem
    return "claude_code" if "anthropic" in lowered else "codex"


def choose_source_order(request: str, source_type: str) -> list[str]:
    if source_type != "auto":
        return [source_type]
    lowered = request.lower()
    if any(term in lowered for term in ["niche", "experimental", "github", "repo", "repository"]):
        return ["github", "skill_market", "other_market"]
    if "cross-platform" in lowered or "portable" in lowered:
        return ["skill_market", "github", "other_market"]
    return ["skill_market", "github", "other_market"]


def build_web_queries(
    source: SearchSource,
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    target_ecosystem: str,
) -> list[str]:
    parsed = urlparse(source.url)
    domain = parsed.netloc or source.url
    ecosystem_terms = ECOSYSTEM_TERMS.get(target_ecosystem, [])
    short_keywords = " ".join(request_keywords[:3]).strip()
    short_phrase = request_phrases[0] if request_phrases else ""
    queries: list[str] = []

    def add(query: str) -> None:
        query = query.strip()
        if query and query not in queries:
            queries.append(query)

    add(f'site:{domain} "{request}" skill')
    if short_phrase:
        add(f'site:{domain} "{short_phrase}" skill')
        add(f'site:{domain} "{short_phrase}" {" ".join(ecosystem_terms[:2])}'.strip())
    if short_keywords:
        add(f"site:{domain} {short_keywords} skill")
        add(f"site:{domain} {short_keywords} {' '.join(ecosystem_terms[:2])}".strip())
    if source.name:
        add(f'site:{domain} {source.name.replace("-", " ")} {short_keywords or request_keywords[0]}')
    if source.description:
        add(f"site:{domain} {short_keywords} {target_ecosystem.replace('_', ' ')}")

    return queries[:2]


def build_market_sources(config: dict[str, Any], ecosystem: str, level: str) -> list[SearchSource]:
    agent = config.get("agents", {}).get(ecosystem, {})
    items = agent.get("markets", {}).get(level, [])
    return [
        SearchSource(
            source_type="skill_market",
            level=level,
            ecosystem=ecosystem,
            name=item["name"],
            url=item["url"],
            description=item.get("description", ""),
        )
        for item in items
    ]


def build_global_sources(config: dict[str, Any], source_type: str) -> list[SearchSource]:
    items = config.get("global_sources", {}).get(source_type, [])
    return [
        SearchSource(
            source_type=source_type,
            level="global",
            ecosystem="portable",
            name=item["name"],
            url=item["url"],
            description=item.get("description", ""),
        )
        for item in items
    ]


def github_repo_from_url(url: str) -> tuple[str, str] | None:
    parsed = urlparse(url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    return parts[0], parts[1]


def fetch_json(session: requests.Session, url: str, params: dict[str, Any] | None = None) -> Any:
    response = session.get(url, params=params, timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_text(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def get_with_retries(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 4,
    attempts: int = 1,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = session.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < attempts - 1:
                time.sleep(0.2 * (attempt + 1))
    assert last_error is not None
    raise last_error


def parse_frontmatter(markdown_text: str) -> dict[str, str]:
    if not markdown_text.startswith("---"):
        return {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", markdown_text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}
    return {str(key): str(value) for key, value in data.items()}


def summarize_markdown(markdown_text: str) -> str:
    text = re.sub(r"^---.*?---\s*", "", markdown_text, flags=re.DOTALL)
    text = re.sub(r"`+", "", text)
    text = re.sub(r"#+\s*", "", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "No summary available."
    return " ".join(lines[:3])[:280]


def days_since(timestamp: str | None) -> int | None:
    if not timestamp:
        return None
    try:
        value = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (dt.datetime.now(dt.timezone.utc) - value).days


def score_candidate(
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    request_hints: list[str],
    target_ecosystem: str,
    candidate_text: str,
    stars: int | None,
    updated_at: str | None,
    source_type: str,
    same_ecosystem: bool,
    has_license: bool,
    archived: bool = False,
) -> tuple[int, dict[str, Any]]:
    lowered = candidate_text.lower()
    matched_keywords = sum(1 for keyword in request_keywords if keyword in lowered)
    matched_phrases = phrase_overlap_count(request_phrases, candidate_text)
    hint_score = hint_overlap_score(request_hints, candidate_text)
    need_fit = min(30, matched_keywords * 5 + matched_phrases * 7 + hint_score)
    platform_fit = 20 if same_ecosystem else 12 if "portable" in lowered or "cross-platform" in lowered else 6

    community_trust = 0
    if stars is not None:
        if stars >= 500:
            community_trust = 20
        elif stars >= 100:
            community_trust = 17
        elif stars >= 30:
            community_trust = 12
        elif stars >= 5:
            community_trust = 7
        else:
            community_trust = 3
    elif source_type == "skill_market":
        community_trust = 8

    maintenance_health = 0
    age_days = days_since(updated_at)
    if age_days is None:
        maintenance_health = 6
    elif age_days <= 60:
        maintenance_health = 15
    elif age_days <= 180:
        maintenance_health = 12
    elif age_days <= 365:
        maintenance_health = 8
    else:
        maintenance_health = 4

    clarity_and_packaging = 8 if "skill" in lowered else 5
    if "scripts/" in lowered or "references/" in lowered or "assets/" in lowered:
        clarity_and_packaging = min(10, clarity_and_packaging + 2)

    risk_penalty = 0
    if archived:
        risk_penalty += 8
    if not has_license:
        risk_penalty += 3
    if "deprecated" in lowered or "experimental" in lowered:
        risk_penalty += 2
    if request_hints and hint_score == 0:
        risk_penalty += 8

    total = max(
        0,
        min(
            100,
            need_fit
            + platform_fit
            + community_trust
            + maintenance_health
            + clarity_and_packaging
            - risk_penalty,
        ),
    )
    evidence = {
        "need_fit": need_fit,
        "platform_fit": platform_fit,
        "community_trust": community_trust,
        "maintenance_health": maintenance_health,
        "clarity_and_packaging": clarity_and_packaging,
        "risk_penalty": risk_penalty,
        "matched_keywords": matched_keywords,
        "matched_phrases": matched_phrases,
        "hint_score": hint_score,
        "stars": stars,
        "updated_at": updated_at,
    }
    return total, evidence


def adaptation_need(candidate_ecosystem: str, target_ecosystem: str) -> str:
    if candidate_ecosystem in {"portable", target_ecosystem}:
        return "none"
    if {candidate_ecosystem, target_ecosystem} <= {"codex", "claude_code", "openclaw"}:
        return "light"
    return "moderate"


def community_signal_text(stars: int | None, updated_at: str | None, extra: str | None = None) -> str:
    parts: list[str] = []
    if stars is not None:
        parts.append(f"{stars} GitHub stars")
    age_days = days_since(updated_at)
    if age_days is not None:
        parts.append(f"updated {age_days} day(s) ago")
    if extra:
        parts.append(extra)
    return ", ".join(parts) if parts else "Limited public trust signals available."


def rank_and_dedupe(candidates: Iterable[Candidate]) -> list[Candidate]:
    best_by_link: dict[str, Candidate] = {}
    for candidate in candidates:
        current = best_by_link.get(candidate.link)
        if current is None or candidate.score > current.score:
            best_by_link[candidate.link] = candidate
    ranked = sorted(best_by_link.values(), key=lambda item: (-item.score, item.name.lower()))
    return ranked


def candidate_limit(candidates: list[Candidate], target_count: int) -> int:
    strong = [candidate for candidate in candidates if candidate.score >= 85]
    usable = [candidate for candidate in candidates if candidate.score >= 70]
    if not usable:
        return 0
    if len(candidates) == 1:
        return 1
    if strong and len(candidates) > 1 and candidates[0].score - candidates[1].score >= 10:
        return min(2, len(candidates))
    return min(max(2, target_count), min(5, len(usable) if len(usable) >= 2 else len(candidates)))


def should_stop(candidates: list[Candidate]) -> bool:
    strong = [candidate for candidate in candidates if candidate.score >= 85]
    usable = [candidate for candidate in candidates if candidate.score >= 70]
    return bool(strong) or len(usable) >= 3


def infer_workflow_steps(request_hints: list[str]) -> list[str]:
    steps = [
        "Clarify the exact user outcome, target runtime, and what should be reusable.",
        "Define the workflow steps, decision points, and expected output shape.",
    ]
    if "code_review" in request_hints:
        steps.extend(
            [
                "Define the review rubric, severity model, and summary format.",
                "Bundle reusable review heuristics, examples, and templates.",
            ]
        )
    elif "documentation" in request_hints:
        steps.extend(
            [
                "Define the document workflow, structure, and iteration checkpoints.",
                "Bundle reusable writing guidance, templates, and examples.",
            ]
        )
    elif "debugging" in request_hints:
        steps.extend(
            [
                "Define the debugging flow, evidence-gathering order, and triage format.",
                "Bundle reusable commands, log-check patterns, and incident summary templates.",
            ]
        )
    else:
        steps.extend(
            [
                "Bundle the parts that are repeated often enough to justify a skill.",
                "Keep the core instructions portable and push runtime-specific details into adapters or metadata.",
            ]
        )
    return steps


def infer_resources(request_hints: list[str]) -> dict[str, list[str]]:
    scripts = ["validation or helper scripts for repeated deterministic steps"]
    references = ["decision rules, domain notes, and examples"]
    assets = ["summary templates and creation brief templates"]
    if "code_review" in request_hints:
        references.append("review heuristics and severity guidance")
        assets.append("review comment templates")
    if "documentation" in request_hints:
        references.append("writing workflow and quality checklist")
        assets.append("document outline templates")
    if "debugging" in request_hints:
        scripts.append("environment inspection or log collection helpers")
        references.append("triage checklist and debugging playbook")
    return {"scripts": scripts, "references": references, "assets": assets}


def infer_cross_platform_concerns(ecosystem: str) -> list[str]:
    concerns = [
        "Keep SKILL.md body portable so the workflow can move across runtimes.",
        "Separate runtime-specific metadata, permission settings, and UI integration.",
    ]
    if ecosystem == "codex":
        concerns.append("Add Codex-specific UI metadata only if needed, such as agents/openai.yaml.")
    elif ecosystem == "claude_code":
        concerns.append("Review Claude Code frontmatter and tool-constraint expectations before packaging.")
    elif ecosystem == "openclaw":
        concerns.append("Review OpenClaw runtime fields and command-dispatch expectations before packaging.")
    return concerns


def build_creation_brief(
    request: str,
    ecosystem: str,
    request_keywords: list[str],
    request_hints: list[str],
    candidates: list[Candidate],
) -> CreationBrief:
    if not candidates:
        reason = "Registered search sources were exhausted without finding a candidate that cleared the minimum quality threshold."
    else:
        top = candidates[0]
        reason = (
            f"The best current candidate is `{top.name}`, but creation may still be preferable if you want tighter fit, "
            "better portability, or full ownership of the workflow."
        )
    triggers = extract_phrases(request)[:5] or request_keywords[:5] or [request]
    open_questions = [
        "Should the first version target one runtime only, or be portable from day one?",
        "What should the success output look like for the user?",
        "Which repeated steps deserve scripts instead of remaining in prose?",
    ]
    return CreationBrief(
        reason_creation_is_justified=reason,
        target_ecosystem=ecosystem,
        user_need=request,
        expected_trigger_phrases=triggers,
        core_workflow=infer_workflow_steps(request_hints),
        reusable_resources=infer_resources(request_hints),
        cross_platform_concerns=infer_cross_platform_concerns(ecosystem),
        open_questions_for_user=open_questions,
    )


def search_duckduckgo(
    session: requests.Session,
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    response = get_with_retries(
        session,
        "https://html.duckduckgo.com/html/",
        params={"q": query},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=8,
    )
    response.raise_for_status()
    html = response.text
    pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        flags=re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>|<div[^>]*class="result__snippet"[^>]*>(?P<snippet2>.*?)</div>',
        flags=re.DOTALL,
    )
    snippets = [
        re.sub(r"<.*?>", "", match.group("snippet") or match.group("snippet2") or "").strip()
        for match in snippet_pattern.finditer(html)
    ]
    results: list[dict[str, str]] = []
    for index, match in enumerate(pattern.finditer(html)):
        title = re.sub(r"<.*?>", "", match.group("title")).strip()
        href = match.group("href")
        if href.startswith("//"):
            href = "https:" + href
        snippet = snippets[index] if index < len(snippets) else ""
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def search_duckduckgo_lite(
    session: requests.Session,
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    response = get_with_retries(
        session,
        "https://lite.duckduckgo.com/lite/",
        params={"q": query},
        timeout=8,
    )
    html = response.text
    pattern = re.compile(
        r'<a[^>]*href="(?P<href>[^"]+)"[^>]*class="result-link"[^>]*>(?P<title>.*?)</a>',
        flags=re.DOTALL,
    )
    results: list[dict[str, str]] = []
    for match in pattern.finditer(html):
        title = re.sub(r"<.*?>", "", match.group("title")).strip()
        href = match.group("href")
        if href.startswith("//"):
            href = "https:" + href
        results.append({"title": title, "url": href, "snippet": ""})
        if len(results) >= max_results:
            break
    return results


def search_bing(
    session: requests.Session,
    query: str,
    max_results: int,
) -> list[dict[str, str]]:
    response = get_with_retries(
        session,
        "https://www.bing.com/search",
        params={"q": query},
        timeout=8,
    )
    html = response.text
    block_pattern = re.compile(r'<li class="b_algo".*?</li>', flags=re.DOTALL)
    link_pattern = re.compile(r'<a href="(?P<href>https?://[^"]+)"[^>]*>(?P<title>.*?)</a>', flags=re.DOTALL)
    snippet_pattern = re.compile(r'<p>(?P<snippet>.*?)</p>', flags=re.DOTALL)
    results: list[dict[str, str]] = []
    for block in block_pattern.findall(html):
        link_match = link_pattern.search(block)
        if not link_match:
            continue
        title = re.sub(r"<.*?>", "", link_match.group("title")).strip()
        href = link_match.group("href")
        snippet_match = snippet_pattern.search(block)
        snippet = re.sub(r"<.*?>", "", snippet_match.group("snippet")).strip() if snippet_match else ""
        results.append({"title": title, "url": href, "snippet": snippet})
        if len(results) >= max_results:
            break
    return results


def search_web(
    session: requests.Session,
    query: str,
    max_results: int,
) -> tuple[list[dict[str, str]], str]:
    providers = [
        ("duckduckgo-html", search_duckduckgo),
        ("duckduckgo-lite", search_duckduckgo_lite),
        ("bing", search_bing),
    ]
    errors: list[str] = []
    for provider_name, provider in providers:
        try:
            results = provider(session, query, max_results)
        except requests.RequestException as exc:
            errors.append(f"{provider_name}: {exc}")
            continue
        if results:
            return results, provider_name
        errors.append(f"{provider_name}: no results")
    raise requests.RequestException("All web search providers failed: " + " | ".join(errors))


def search_github_repository_collection(
    session: requests.Session,
    source: SearchSource,
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    request_hints: list[str],
    target_ecosystem: str,
    max_per_source: int,
) -> SearchResult:
    repo = github_repo_from_url(source.url)
    if not repo:
        return SearchResult(source=source, candidates=[], notes=["Source URL is not a GitHub repository."])
    owner, repo_name = repo
    repo_meta = fetch_json(session, f"https://api.github.com/repos/{owner}/{repo_name}")
    default_branch = repo_meta.get("default_branch", "main")
    tree = fetch_json(
        session,
        f"https://api.github.com/repos/{owner}/{repo_name}/git/trees/{default_branch}",
        params={"recursive": "1"},
    )
    skill_paths = [item["path"] for item in tree.get("tree", []) if item.get("path", "").endswith("SKILL.md")]
    candidates: list[Candidate] = []
    for skill_path in skill_paths[: max_per_source * 2]:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{default_branch}/{skill_path}"
        try:
            content = fetch_text(session, raw_url)
        except requests.RequestException:
            continue
        frontmatter = parse_frontmatter(content)
        name = frontmatter.get("name") or Path(skill_path).parent.name
        description = frontmatter.get("description") or summarize_markdown(content)
        summary_preview = summarize_markdown(content)
        candidate_text = f"{name} {description} {summary_preview}"
        score, evidence = score_candidate(
            request=request,
            request_keywords=request_keywords,
            request_phrases=request_phrases,
            request_hints=request_hints,
            target_ecosystem=target_ecosystem,
            candidate_text=candidate_text,
            stars=repo_meta.get("stargazers_count"),
            updated_at=repo_meta.get("updated_at"),
            source_type=source.source_type,
            same_ecosystem=source.ecosystem == target_ecosystem,
            has_license=bool(repo_meta.get("license")),
            archived=bool(repo_meta.get("archived")),
        )
        evidence["community_trust"] = min(evidence["community_trust"], 12)
        score = max(0, min(100, score - max(0, evidence["community_trust"] - 12)))
        if evidence["matched_keywords"] == 0 and evidence["matched_phrases"] == 0 and evidence["hint_score"] < 4:
            continue
        if evidence["need_fit"] < 12:
            continue
        why = description if len(description) < 180 else description[:177] + "..."
        candidates.append(
            Candidate(
                name=name,
                type="skill",
                source_type=source.source_type,
                source_name=source.name,
                ecosystem=source.ecosystem,
                summary=description,
                why_it_matches=why,
                community_signals=community_signal_text(
                    repo_meta.get("stargazers_count"),
                    repo_meta.get("updated_at"),
                    f"from collection {owner}/{repo_name}",
                ),
                adaptation_need=adaptation_need(source.ecosystem, target_ecosystem),
                adoption_cost="Inspect the skill folder and copy or adapt it into your target runtime.",
                risks="Review packaging details because collection entries may need ecosystem-specific adaptation.",
                link=f"https://github.com/{owner}/{repo_name}/blob/{default_branch}/{skill_path}",
                score=score,
                evidence=evidence | {"collection_repo": f"{owner}/{repo_name}", "skill_path": skill_path},
            )
        )
    notes = [f"Enumerated {len(skill_paths)} skill file(s) in {owner}/{repo_name}."]
    return SearchResult(source=source, candidates=rank_and_dedupe(candidates)[:max_per_source], notes=notes)


def search_github_repositories(
    session: requests.Session,
    source: SearchSource,
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    request_hints: list[str],
    target_ecosystem: str,
    max_per_source: int,
) -> SearchResult:
    ecosystem_terms = " ".join(ECOSYSTEM_TERMS.get(target_ecosystem, []))
    query = f'{request} {ecosystem_terms} "SKILL.md"'
    items = fetch_json(
        session,
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "order": "desc", "per_page": max_per_source},
    ).get("items", [])

    candidates: list[Candidate] = []
    for item in items:
        full_text = " ".join(
            [
                item.get("full_name", ""),
                item.get("description") or "",
                " ".join(item.get("topics") or []),
            ]
        )
        same_ecosystem = target_ecosystem.replace("_", " ") in full_text.lower()
        score, evidence = score_candidate(
            request=request,
            request_keywords=request_keywords,
            request_phrases=request_phrases,
            request_hints=request_hints,
            target_ecosystem=target_ecosystem,
            candidate_text=full_text,
            stars=item.get("stargazers_count"),
            updated_at=item.get("updated_at"),
            source_type=source.source_type,
            same_ecosystem=same_ecosystem,
            has_license=bool(item.get("license")),
            archived=bool(item.get("archived")),
        )
        if (
            evidence["matched_keywords"] == 0
            and evidence["matched_phrases"] == 0
            and evidence["hint_score"] < 4
            and (item.get("stargazers_count") or 0) < 100
        ):
            continue
        if evidence["need_fit"] < 10:
            continue
        ecosystem = target_ecosystem if same_ecosystem else "portable"
        candidates.append(
            Candidate(
                name=item.get("full_name", "unknown"),
                type="skill-repo",
                source_type=source.source_type,
                source_name=source.name,
                ecosystem=ecosystem,
                summary=item.get("description") or "No repository description provided.",
                why_it_matches="Repository metadata overlaps strongly with the requested workflow."
                if evidence["matched_keywords"] >= 2
                else "Repository surfaced in the highest-signal GitHub search for this request.",
                community_signals=community_signal_text(
                    item.get("stargazers_count"),
                    item.get("updated_at"),
                    "repository search result",
                ),
                adaptation_need=adaptation_need(ecosystem, target_ecosystem),
                adoption_cost="Inspect repository packaging and confirm it contains a reusable skill or near-skill workflow.",
                risks="May be a broader repository rather than a clean drop-in skill package.",
                link=item.get("html_url", ""),
                score=score,
                evidence=evidence | {"repo_full_name": item.get("full_name", "")},
            )
        )
    notes = [f"GitHub repository query: {query}"]
    return SearchResult(source=source, candidates=rank_and_dedupe(candidates), notes=notes)


def search_generic_source(
    session: requests.Session,
    source: SearchSource,
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    request_hints: list[str],
    target_ecosystem: str,
    max_per_source: int,
) -> SearchResult:
    search_queries = build_web_queries(
        source=source,
        request=request,
        request_keywords=request_keywords,
        request_phrases=request_phrases,
        target_ecosystem=target_ecosystem,
    )
    raw_results: list[dict[str, str]] = []
    provider_notes: list[str] = []
    errors: list[str] = []
    for search_query in search_queries:
        try:
            query_results, provider_name = search_web(session, search_query, max_per_source)
        except requests.RequestException as exc:
            errors.append(f"{search_query} -> {exc}")
            continue
        provider_notes.append(f"{provider_name}: {search_query}")
        raw_results.extend(query_results)
        if len(raw_results) >= max_per_source * 2:
            break

    if not raw_results:
        if errors:
            message = f"All expanded web queries failed or returned no results. Tried {len(search_queries)} variant(s). First failure: {errors[0]}"
        else:
            message = "All expanded web queries returned no results."
        raise requests.RequestException(message)

    candidates: list[Candidate] = []
    seen_links: set[str] = set()
    for result in raw_results:
        if result["url"] in seen_links:
            continue
        seen_links.add(result["url"])
        text = " ".join([result["title"], result["snippet"]])
        same_ecosystem = source.ecosystem in {target_ecosystem, "portable"}
        score, evidence = score_candidate(
            request=request,
            request_keywords=request_keywords,
            request_phrases=request_phrases,
            request_hints=request_hints,
            target_ecosystem=target_ecosystem,
            candidate_text=text,
            stars=None,
            updated_at=None,
            source_type=source.source_type,
            same_ecosystem=same_ecosystem,
            has_license=True,
        )
        if evidence["need_fit"] < 10:
            continue
        candidates.append(
            Candidate(
                name=result["title"] or source.name,
                type="external-page",
                source_type=source.source_type,
                source_name=source.name,
                ecosystem=source.ecosystem,
                summary=result["snippet"] or source.description,
                why_it_matches="Search result from a registered source that matches the request terms.",
                community_signals="Source came from a registered market or directory.",
                adaptation_need=adaptation_need(source.ecosystem, target_ecosystem),
                adoption_cost="Manual inspection required before adoption.",
                risks="This is a search lead, not necessarily a ready-to-install skill.",
                link=result["url"],
                score=score,
                evidence=evidence,
            )
        )
    notes = [f"Web search query variants tried: {len(search_queries)}"]
    notes.extend([f"Web search hit: {item}" for item in provider_notes[:3]])
    if errors:
        notes.append(f"Web search fallback notes: {len(errors)} query variant(s) returned no results or failed.")
    return SearchResult(source=source, candidates=rank_and_dedupe(candidates), notes=notes)


def execute_source_search(
    session: requests.Session,
    source: SearchSource,
    request: str,
    request_keywords: list[str],
    request_phrases: list[str],
    request_hints: list[str],
    target_ecosystem: str,
    max_per_source: int,
) -> SearchResult:
    repo = github_repo_from_url(source.url)
    if source.source_type == "github":
        return search_github_repositories(
            session,
            source,
            request,
            request_keywords,
            request_phrases,
            request_hints,
            target_ecosystem,
            max_per_source,
        )
    if source.source_type == "skill_market" and repo is not None:
        return search_github_repository_collection(
            session,
            source,
            request,
            request_keywords,
            request_phrases,
            request_hints,
            target_ecosystem,
            max_per_source,
        )
    return search_generic_source(
        session,
        source,
        request,
        request_keywords,
        request_phrases,
        request_hints,
        target_ecosystem,
        max_per_source,
    )


def render_markdown_summary(
    request: str,
    ecosystem: str,
    source_order: list[str],
    searched_sources: list[dict[str, Any]],
    candidates: list[Candidate],
    creation_brief: CreationBrief,
) -> str:
    lines = [
        f"# Skill Search Summary",
        "",
        f"- Request: {request}",
        f"- Target ecosystem: {ecosystem}",
        f"- Source order: {', '.join(source_order)}",
        f"- Generated at: {now_utc()}",
        "",
    ]
    if candidates:
        lines.extend(["## Recommendation", "", best_recommendation(candidates), ""])
        lines.extend(["## Candidates", ""])
        for index, candidate in enumerate(candidates, start=1):
            lines.extend(
                [
                    f"### {index}. {candidate.name}",
                    "",
                    f"- Score: {candidate.score}",
                    f"- Type: {candidate.type}",
                    f"- Ecosystem: {candidate.ecosystem}",
                    f"- Source: {candidate.source_type} / {candidate.source_name}",
                    f"- Summary: {candidate.summary}",
                    f"- Why it matches: {candidate.why_it_matches}",
                    f"- Community signals: {candidate.community_signals}",
                    f"- Adaptation need: {candidate.adaptation_need}",
                    f"- Adoption cost: {candidate.adoption_cost}",
                    f"- Risks: {candidate.risks}",
                    f"- Link: {candidate.link}",
                    "",
                ]
            )
    else:
        lines.extend(["## Recommendation", "", "No candidate cleared the minimum quality threshold.", ""])

    lines.extend(["## Sources Searched", ""])
    for result in searched_sources:
        source = result["source"]
        lines.append(f"### {source['name']} ({source['source_type']}, {source['level']})")
        lines.append("")
        for note in result["notes"]:
            lines.append(f"- {note}")
        if not result["notes"]:
            lines.append("- No notes recorded.")
        lines.append(f"- Candidates found: {result['candidate_count']}")
        lines.append("")

    lines.extend(
        [
            "## Next Step",
            "",
            next_step_prompt(candidates),
            "",
        ]
    )
    lines.extend(render_creation_brief(creation_brief))
    return "\n".join(lines).rstrip() + "\n"


def best_recommendation(candidates: list[Candidate]) -> str:
    if not candidates:
        return "Continue searching or prepare to create a new skill."
    top = candidates[0]
    if len(candidates) > 1 and top.score - candidates[1].score >= 10:
        return f"`{top.name}` is the clearest lead. It stands noticeably above the backup option and is the best first candidate to inspect."
    return "The candidates below form the best current decision set. Choose one to adopt, adapt, or use as the basis for creation."


def next_step_prompt(candidates: list[Candidate]) -> str:
    if not candidates:
        return "Would you like to continue searching broader sources, or create a new skill now?"
    return "Would you like to adopt one of these, adapt a cross-platform option, continue searching, or create a new skill?"


def render_creation_brief(brief: CreationBrief) -> list[str]:
    lines = [
        "## Creation Brief",
        "",
        f"- Reason creation is justified: {brief.reason_creation_is_justified}",
        f"- Target ecosystem: {brief.target_ecosystem}",
        f"- User need: {brief.user_need}",
        "",
        "### Expected Trigger Phrases",
        "",
    ]
    lines.extend([f"- {item}" for item in brief.expected_trigger_phrases])
    lines.extend(["", "### Core Workflow", ""])
    for index, step in enumerate(brief.core_workflow, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(["", "### Reusable Resources", ""])
    for key, values in brief.reusable_resources.items():
        lines.append(f"- {key}: {', '.join(values)}")
    lines.extend(["", "### Cross-Platform Concerns", ""])
    lines.extend([f"- {item}" for item in brief.cross_platform_concerns])
    lines.extend(["", "### Open Questions For The User", ""])
    lines.extend([f"- {item}" for item in brief.open_questions_for_user])
    lines.append("")
    return lines


def run_search(args: argparse.Namespace) -> dict[str, Any]:
    request = args.request.strip()
    config = load_sources()
    ecosystem = detect_ecosystem(request) if args.ecosystem == "auto" else args.ecosystem
    request_keywords = fit_keywords(keywordize(request), ecosystem)
    request_phrases = extract_phrases(request)
    request_hints = detect_domain_hints(request)
    source_order = choose_source_order(request, args.source_type)
    session = get_session()

    searched_results: list[SearchResult] = []
    candidate_pool: list[Candidate] = []

    for source_type in source_order:
        if source_type == "skill_market":
            grouped_sources = [
                build_market_sources(config, ecosystem, "tier_1"),
                build_market_sources(config, ecosystem, "tier_2"),
            ]
        else:
            grouped_sources = [build_global_sources(config, source_type)]

        for source_group in grouped_sources:
            if not source_group:
                continue
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(source_group))) as executor:
                futures = {
                    executor.submit(
                        execute_source_search,
                        session,
                        source,
                        request,
                        request_keywords,
                        request_phrases,
                        request_hints,
                        ecosystem,
                        args.max_per_source,
                    ): source
                    for source in source_group
                }
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                    except Exception as exc:  # noqa: BLE001
                        source = futures.get(future)
                        fallback_source = source.name if source else "unknown"
                        searched_results.append(
                            SearchResult(
                                source=source or SearchSource(source_type, "unknown", ecosystem, fallback_source, "", ""),
                                candidates=[],
                                notes=[f"Search failed: {exc}"],
                            )
                        )
                        continue
                    searched_results.append(result)
                    candidate_pool.extend(result.candidates)

            ranked = rank_and_dedupe(candidate_pool)
            if should_stop(ranked):
                break
        ranked = rank_and_dedupe(candidate_pool)
        if should_stop(ranked):
            break

    ranked = rank_and_dedupe(candidate_pool)
    limit = candidate_limit(ranked, args.max_candidates)
    presented = ranked[:limit]
    creation_brief = build_creation_brief(
        request=request,
        ecosystem=ecosystem,
        request_keywords=request_keywords,
        request_hints=request_hints,
        candidates=presented,
    )

    output = {
        "request": request,
        "ecosystem": ecosystem,
        "source_order": source_order,
        "generated_at": now_utc(),
        "searched_sources": [
            {
                "source": asdict(result.source),
                "notes": result.notes,
                "candidate_count": len(result.candidates),
            }
            for result in searched_results
        ],
        "candidates": [asdict(candidate) for candidate in presented],
        "all_ranked_candidates": [asdict(candidate) for candidate in ranked[:20]],
        "creation_brief": asdict(creation_brief),
    }
    return output


def write_outputs(output: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = f"{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(output['request'])}"
    json_path = output_dir / f"{base}.json"
    md_path = output_dir / f"{base}.md"
    json_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    candidates = [Candidate(**item) for item in output["candidates"]]
    creation_brief = CreationBrief(**output["creation_brief"])
    markdown = render_markdown_summary(
        request=output["request"],
        ecosystem=output["ecosystem"],
        source_order=output["source_order"],
        searched_sources=output["searched_sources"],
        candidates=candidates,
        creation_brief=creation_brief,
    )
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    output = run_search(args)
    json_path, md_path = write_outputs(output, Path(args.output_dir))
    if args.json_only:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(md_path.read_text(encoding="utf-8"))
        print(f"JSON output: {json_path}")
        print(f"Markdown output: {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
