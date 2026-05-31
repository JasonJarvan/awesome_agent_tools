# cookie-manager — 架构概览（对外）

> 对外架构摘要。内部设计细节见 `docs/RepoMem/architecture.md` 与权威设计
> `docs/superpowers/specs/2026-05-31-SP-1-cookie-manager-design.md`。

## 数据流

```
官方 CookieCloud 扩展(不改) ──加密──▶ POST /update {uuid,encrypted,crypto_type?}
                                       │
        server.ts  校验→ store.save(原样存密文) → 立即回 {action:'done'}
                                       │ (异步, 不阻塞扩展)
                              emit 'cookie-update'
                                       ▼
        hooks/engine.ts  取 account password → crypto 解密 → 算 domains
                          → matchHook 过滤 → runExec(A1) / runWriteFile(A3)
                                       ▲
        node-cron (T2 定时) ───────────┘   （对 store 内全部账号跑，无叠加）

        cli.ts  list / show domain= / dump  ← store.load + crypto 解密
```

## 模块（单一职责，接口为值/事件）

| 模块 | 职责 |
|---|---|
| `crypto.ts` | CookieCloud 加解密（legacy + aes-128-cbc-fixed）；纯函数；正确性命脉 |
| `store.ts` | 文件存储 `data/<basename(uuid)>.json`；唯一文件系统拥有者；防路径穿越 |
| `config.ts` | zod 校验的 YAML 配置（server / accounts / hooks） |
| `server.ts` | Express：`/update`、`/get/:uuid`、`/health`；发 `cookie-update` 事件 |
| `hooks/{template,actions,triggers,engine}.ts` | 模板插值 + match / exec + write_file / T1 事件 + T2 cron / 编排 |
| `cli.ts` | `list` / `show` / `dump` |
| `index.ts` | bootstrap 装配 + 优雅退出 |

## 关键设计点

- **不 fork CookieCloud**（GPLv3）；自写服务复刻协议，license MIT。
- **复用 `crypto-js`** 保证与扩展字节级兼容（含独立 `node:crypto` oracle 测试交叉验证）。
- **异步 hook**：先回扩展，再跑 hook，避免上传超时。
- **解密失败不崩**：记日志跳过该 hook / CLI 报错退出。

## 技术栈

Node.js + TypeScript + Express 4 + crypto-js + zod + js-yaml + node-cron；测试 vitest + supertest；Docker compose 部署。
