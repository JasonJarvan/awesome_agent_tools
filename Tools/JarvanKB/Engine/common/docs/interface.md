# Engine/common — Interface

## LLMClient

```python
from jarvankb_common import LLMClient          # pkg: jarvankb-common (pip install -e Engine/common)

client = LLMClient(profile="default")           # profile defined in config/llm.yaml
text   = client.complete([{"role": "user", "content": "..."}])
chunks = client.stream([{"role": "user", "content": "..."}])
```

**Stability**: signatures (`__init__` + `complete` + `stream` + `to_opencode`) are the v1 frozen contract.
`__init__` accepts an optional `config_path` kwarg (defaults to `config/llm.yaml` / `$JARVANKB_LLM_CONFIG`).
**Body**: **real impl landed in SP-3** (litellm backend, active-order fallthrough). SP-6 reuses as-is.

## Configuration

Reads `config/llm.yaml` (copy from `config/llm.yaml.example`). Provider switches by config alone — no code changes in consumer sub-projects.

## Backend

`litellm` (pip install `litellm`). Supports OpenAI / Anthropic / DashScope (Qwen) / Ollama / Groq / Gemini / Bedrock / many more.
