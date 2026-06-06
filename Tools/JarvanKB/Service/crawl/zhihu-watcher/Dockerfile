FROM python:3.12-slim

WORKDIR /app

# The frozen SP-2 engine is a sibling package in the monorepo; copy + install both.
COPY Engine/zhihu /app/engine-zhihu
COPY Service/crawl/zhihu-watcher /app/zhihu-watcher

RUN pip install --no-cache-dir /app/engine-zhihu \
    && pip install --no-cache-dir /app/zhihu-watcher

# config + data are mounted at runtime (see docker-compose.yml)
ENTRYPOINT ["python", "-m", "zhihu_watcher", "--config", "/config/zhihu-watcher.yaml"]
