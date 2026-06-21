FROM python:3.12-slim

WORKDIR /app

# The frozen SP-2 engine + the shared jarvankb_common layer are sibling packages in the monorepo.
# jarvankb_common is imported at module top-level in watcher.py (and supplies LLMClient for the
# classify path), so it MUST be installed or the container crashes on import.
COPY Engine/zhihu /app/engine-zhihu
COPY Engine/common /app/engine-common
COPY Service/crawl/zhihu-watcher /app/zhihu-watcher

RUN pip install --no-cache-dir /app/engine-zhihu \
    && pip install --no-cache-dir /app/engine-common \
    && pip install --no-cache-dir /app/zhihu-watcher

# config + data are mounted at runtime (see docker-compose.yml)
ENTRYPOINT ["python", "-m", "zhihu_watcher", "--config", "/config/zhihu-watcher.yaml"]
