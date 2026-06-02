# SP-4a 的 BiliNote 部署

SP-4a 引擎是自托管 **BiliNote（BN）** 实例的 *客户端*：BN 负责音频提取 + bcut ASR + LLM 总结，引擎
提交任务并解析结果。上游：<https://github.com/JefferyHcool/BiliNote>。

## 起 BN（用户操作 — Dashboard UN-018）

1. `cp .env.example .env`（如 3015 端口被占用，改 `APP_PORT`）。
2. 在本目录执行 `docker compose up -d`。
3. 添加一个 LLM 供应商（BN 的后端是 **OpenAI-compatible**，所以任何 OpenAI 兼容端点都行：OpenAI /
   DashScope-compat / DeepSeek / Moonshot / OpenRouter / 本地 Ollama 等）。**两种方式任选**：
   - **(A) 无浏览器 / headless（SSH 在主机上推荐）** —— curl BN 的 API：
     ```bash
     PORT=${APP_PORT:-3015}
     curl -s -X POST http://127.0.0.1:$PORT/api/add_provider \
       -H 'Content-Type: application/json' \
       -d '{"name":"my-llm","api_key":"sk-...","base_url":"https://api.openai.com/v1","type":"custom"}'
     # 读回 provider_id：
     curl -s http://127.0.0.1:$PORT/api/get_all_providers
     ```
     `data[].id`（一个 uuid）就是 `provider_id`。（API 创建的供应商 `type` 会被强制为 `custom`；`name` 须唯一。）
   - **(B) 浏览器 UI** —— 见下「远程访问」用 SSH tunnel 后开 `http://localhost:<APP_PORT>` → **模型供应商**。
4. 复制 `../../config/bilibili-engine.example.yaml` 为 `../../config/bilibili-engine.yaml`（即
   `Engine/bilibili/config/bilibili-engine.yaml`），填：
   - `base_url: http://127.0.0.1:<APP_PORT>`
   - `provider_id: <上一步的 uuid>`
   - `model_name: <你的模型名，如 gpt-4o-mini / deepseek-chat>`
5. 告诉引擎会话「BN 端点已就绪」，即可跑 Stage-3 手动冒烟。

## 可达性 / 安全

容器端口**只绑 `127.0.0.1`**（见 `docker-compose.yml`），**不对外暴露**——因为 BN **无鉴权**，公网暴露
等于把你的 LLM api_key + 任务执行能力开放给任何人。对齐 SP-1 cookie-manager 的 localhost 约定。

- 你 SSH 在主机上 → 直接 `curl http://127.0.0.1:<APP_PORT>/...`，**无需 tunnel**。
- 想在**笔记本浏览器**里用 BN 的 Web UI → 在笔记本上开 SSH 隧道，把本地端口转发到主机的 localhost：
  ```bash
  ssh -L 3015:127.0.0.1:3015 shenzhou-linux-cloud
  ```
  保持该 SSH 连接，然后笔记本浏览器开 `http://localhost:3015`。

## 为什么用 bcut

`TRANSCRIBER_TYPE=bcut` 用 B站必剪的免费云端 ASR——无需本地 Whisper 模型下载、无需 GPU、无需额外
API key。字幕优先级联意味着 ASR 只在「无字幕」的视频上触发；有字幕的视频零 ASR 成本。可在 BN web UI
（**音频转写配置 → 必剪**）确认/切换。

## 回退（若 `ghcr.io/jefferyhcool/bilinote:latest` 镜像不可用）

部分环境只能从源码构建。改为：
```bash
git clone https://github.com/JefferyHcool/BiliNote && cd BiliNote
cp .env.example .env          # 把 TRANSCRIBER_TYPE 设为 bcut
docker-compose up -d
```
然后照上面第 3–5 步配置引擎。
