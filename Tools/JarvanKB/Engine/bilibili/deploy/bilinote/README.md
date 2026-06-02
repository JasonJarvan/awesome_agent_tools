# SP-4a 的 BiliNote 部署

SP-4a 引擎是自托管 **BiliNote（BN）** 实例的 *客户端*：BN 负责音频提取 + bcut ASR + LLM 总结，引擎
提交任务并解析结果。上游：<https://github.com/JefferyHcool/BiliNote>。

## 起 BN（用户操作 — Dashboard UN-018）

1. `cp .env.example .env`（如 3015 端口被占用，改 `APP_PORT`）。
2. 在本目录执行 `docker compose up -d`。
3. 打开 `http://localhost:<APP_PORT>` → **模型供应商** → 添加你的 LLM 供应商（API key 存进 BN 的
   SQLite，不入 git）。记下该供应商的 `provider_id`。
4. 复制 `config/bilibili-engine.example.yaml` 为 `config/bilibili-engine.yaml`，填：
   - `base_url: http://127.0.0.1:<APP_PORT>`
   - `provider_id: <上一步的 id>`
   - `model_name: <你的模型名>`
5. 告诉引擎会话「BN 端点已就绪」，即可跑 Stage-3 手动冒烟。

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
