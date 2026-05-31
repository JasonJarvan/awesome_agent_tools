# Engine/common — Interface

## LLMClient

```python
from Engine.common.src.llm_client import LLMClient

client = LLMClient(profile="default")   # profile defined in config/llm.yaml
text  = client.complete([{"role": "user", "content": "..."}])
chunks = client.stream([{"role": "user", "content": "..."}])
```

**Stability**: signatures (constructor + `complete` + `stream` + `to_opencode`) are the v1 frozen contract.
**Body**: skeleton only in v1 SP-0; first real implementation lands with SP-3 or SP-6.

## Configuration

Reads `config/llm.yaml` (copy from `config/llm.yaml.example`). Provider switches by config alone — no code changes in consumer sub-projects.

## Backend

`litellm` (pip install `litellm`). Supports OpenAI / Anthropic / DashScope (Qwen) / Ollama / Groq / Gemini / Bedrock / many more.
