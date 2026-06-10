FROM python:3.12-slim

WORKDIR /app

# The frozen SP-4a engine is a sibling package in the monorepo; copy + install both.
COPY Engine/bilibili /app/engine-bilibili
COPY Service/crawl/bilibili-watcher /app/bilibili-watcher

RUN pip install --no-cache-dir /app/engine-bilibili \
    && pip install --no-cache-dir /app/bilibili-watcher

# config + data are mounted at runtime (see docker-compose.yml)
ENTRYPOINT ["python", "-m", "bilibili_watcher", "--config", "/config/bilibili-watcher.yaml"]
