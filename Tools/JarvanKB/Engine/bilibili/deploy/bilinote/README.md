# SP-4a 的 BiliNote 部署

SP-4a 引擎是自托管 **BiliNote（BN）** 实例的 *客户端*：BN 负责音频提取 + bcut ASR + LLM 总结，引擎
提交任务并解析结果。上游：<https://github.com/JefferyHcool/BiliNote>。

## ⚠️ 已知问题（`ghcr.io/jefferyhcool/bilinote:latest` 全合一镜像）

实测该镜像内置的 nginx 路由是坏的：`location /` 代理到一个不存在的 `:8080`，且残留的 Debian 默认站点
（`sites-enabled/default`，`default_server`）遮蔽了 `/api/` 代理 —— 结果经 nginx（:80）访问 `/api/*`
一律 **404**，而后端（FastAPI，容器内 `:8483`）其实完全正常。

**本 `docker-compose.yml` 因此把宿主端口直接映射到后端 `:8483`，绕开 nginx**。引擎只用 `/api/*` JSON
接口，不需要 web UI，所以这样最稳、且与镜像 nginx 解耦。代价：该镜像的 web UI 本就不可用（无所谓）。

另外 `TRANSCRIBER_TYPE` 环境变量在该镜像里**不能可靠透传**给后端（supervisord env 坑 + BN 会把转写器
配置 seed 进持久化的 SQLite），所以下面用 API **显式**设 bcut，而不是只靠 `.env`。

## 起 BN（用户操作 — Dashboard UN-018）

1. `cp .env.example .env`（如 3015 端口被占用，改 `APP_PORT`）。
2. 在本目录执行 `docker compose up -d`；等几秒，确认后端活着：
   ```bash
   curl -s http://127.0.0.1:3015/api/sys_check     # 应回 {"code":0,"msg":"success","data":null}
   ```
3. **显式设转写器为 bcut**（环境变量在此镜像不可靠）：
   ```bash
   curl -s -X POST http://127.0.0.1:3015/api/transcriber_config \
     -H 'Content-Type: application/json' -d '{"transcriber_type":"bcut"}'
   ```
4. 注册一个 LLM 供应商（BN 后端是 **OpenAI-compatible**，任何 OpenAI 兼容端点都行：OpenAI / DeepSeek /
   DashScope-compat / Moonshot / OpenRouter / 本地 Ollama / 小米 mimo 等）：
   ```bash
   curl -s -X POST http://127.0.0.1:3015/api/add_provider \
     -H 'Content-Type: application/json' \
     -d '{"name":"my-llm","api_key":"sk-...","base_url":"https://api.openai.com/v1","type":"custom"}'
   curl -s http://127.0.0.1:3015/api/get_all_providers      # data[].id（uuid）即 provider_id
   ```
   （API 创建的供应商 `type` 会被强制为 `custom`；`name` 须唯一。模型名可 `curl <base_url>/models` 查。）
5. 复制 `../../config/bilibili-engine.example.yaml` 为 `../../config/bilibili-engine.yaml`
   （即 `Engine/bilibili/config/bilibili-engine.yaml`，**gitignored，不含密钥**），填：
   - `base_url: http://127.0.0.1:3015`（现在直连后端）
   - `provider_id: <上一步的 uuid>`
   - `model_name: <该供应商的模型名>`
6. 告诉引擎会话「BN 端点已就绪」，即可跑 Stage-3 手动冒烟。

## 可达性 / 安全

容器端口**只绑 `127.0.0.1`**（见 `docker-compose.yml`），**不对外暴露**——因为 BN **无鉴权**，公网暴露
等于把你的 LLM api_key + 任务执行能力开放给任何人。对齐 SP-1 cookie-manager 的 localhost 约定。

- 你 SSH 在主机上 → 直接 `curl http://127.0.0.1:3015/api/...`，**无需 tunnel**。
- 想从**笔记本**直接 curl 这个后端 API → 在笔记本上开 SSH 隧道转发后端端口：
  ```bash
  ssh -L 3015:127.0.0.1:3015 shenzhou-linux-cloud
  ```
  （注意：由于上面的 nginx 问题，:3015 是后端 JSON API，不是网页；浏览器打开只会看到 API 响应。）

## 为什么用 bcut

`TRANSCRIBER_TYPE=bcut` 用 B站必剪的免费云端 ASR——无需本地 Whisper 模型下载、无需 GPU、无需额外
API key。字幕优先级联意味着 ASR 只在「无字幕」的视频上触发；有字幕的视频零 ASR 成本。

## 回退（若 `latest` 镜像不可用 / 想要可用的 web UI）

从源码构建分离式部署（backend + frontend + nginx 三容器，nginx 路由正确）：
```bash
git clone https://github.com/JefferyHcool/BiliNote && cd BiliNote
cp .env.example .env          # 把 TRANSCRIBER_TYPE 设为 bcut
docker-compose up -d
```
那套的 `/api/` 经 nginx 正常；engine 的 `base_url` 填它暴露的 `APP_PORT`（默认 3015，经 nginx）。
