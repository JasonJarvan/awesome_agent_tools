# Result Schema

When presenting results to the user, return information that helps them make a decision quickly.

Each candidate should include these fields:

- `name`
  Candidate name or repository name.

- `type`
  Usually `skill`, but may also be `skill-repo`, `template`, or `workflow package` if the source is not packaged as a formal skill.

- `source_type`
  `skill_market`, `github`, or `other_market`.

- `source_name`
  The specific market, registry, or repository source.

- `ecosystem`
  `codex`, `claude_code`, `openclaw`, or `portable`.

- `summary`
  One short paragraph explaining what it does.

- `why_it_matches`
  One or two sentences connecting the candidate to the user's request.

- `community_signals`
  The few trust signals that matter most, such as stars, recency, or reference quality.

- `adaptation_need`
  `none`, `light`, `moderate`, or `heavy`.

- `adoption_cost`
  A short note on setup or integration effort.

- `risks`
  The most important risk or caution. If no major risk is visible, say so plainly.

- `link`
  Direct source link.

## Recommended Presentation Format

Use this order:

1. one-sentence recommendation summary
2. candidate list
3. short explanation of tradeoffs
4. direct question asking whether to adopt, adapt, continue searching, or create

## Example Summary Style

Use compact language that supports a decision:

- "Best fit if you want the most mature Claude-native option."
- "Best fit if you want portability and are comfortable with light adaptation."
- "Lower setup cost, but weaker community validation."

## What To Avoid

- Do not dump raw search snippets.
- Do not show every repository that matched a query.
- Do not hide adaptation cost.
- Do not force the user to infer trust signals from a bare link list.
