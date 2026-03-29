# Search Playbook

Use this playbook to keep search behavior fast, parallel where useful, and easy for the user to trust.

## 1. Start Narrow

Start with the most likely source type and the highest-priority registered sources.

Prefer:

- official or primary skill collections
- strong community repositories
- ecosystem-specific sources that are already registered in `sources.yaml`

Avoid broad web search as the first move unless the request is highly niche or the ecosystem lacks good registries.

## 2. Parallelize Independent Searches

When the runtime supports it, search independent sources in parallel.

Good candidates for parallel search:

- all `tier_1` markets for one ecosystem
- multiple GitHub queries that test different phrasings
- a market search plus a GitHub search when the request is ambiguous

Do not parallelize work that depends on the previous result.

## 3. Prefer Evidence Over Hype

Trust signals matter more than marketing language.

Prefer candidates that show:

- clear packaging
- recent maintenance
- community validation
- concrete examples
- understandable installation or usage steps

Be cautious with:

- abandoned repositories
- unclear ownership
- vague claims without examples
- high-risk scripts with weak explanation

For GitHub discovery, use `100+ stars` as the default first-pass trust heuristic for mainstream workflows, but treat it as one signal among several rather than a hard gate.

## 4. Escalate Search Breadth Deliberately

Broaden the search only when:

- high-priority sources fail
- returned candidates are too weak
- or the user explicitly asks for a broader search

When broadening, tell the user what changed:

- "No strong match in tier 1 sources; expanding to tier 2."
- "Curated markets were weak; searching GitHub next."

## 5. Keep The User In The Loop

At each decision boundary, return a short explanation:

- what was searched
- whether strong candidates were found
- why the current candidates are or are not convincing

This is especially important before:

- adaptation
- creation
- exhaustive fallback search

## 6. Creation Is A Deliberate Outcome

Creating a new skill is justified when:

- no good reusable candidate exists
- adaptation cost is too high
- or the user explicitly prefers ownership and control

When creation is recommended, explain why reuse failed in concrete terms rather than abstract preference.
