# Codex 会话历史导出（barksy_pipeline）

## 用途

将 **Codex** 的会话历史从 JSONL 格式导出为 Markdown 文件，便于在项目目录下归档或查看当前项目的 Agent 对话记录。仅导出「当前工作目录」匹配的会话，并自动跳过已导出过的 Session ID。

## 适用场景与输入输出

- **输入**
  - Codex 会话目录（默认 `~/.codex/sessions`）下的 `*.jsonl` 会话文件
  - 可选：指定要匹配的 `cwd`、会话目录、输出目录
- **输出**
  - 在指定输出目录（默认 `./codexhistory`）下生成与会话对应的 `.md` 文件
  - 每个 Markdown 包含：元数据（Session ID、时间、CWD、CLI 版本）与完整 Transcript（用户/助手消息、工具调用与输出）

## 依赖

- **运行环境**：Python 3，仅使用标准库（`argparse`、`json`、`re`、`pathlib`），无第三方依赖
- **数据来源**：本机 Codex 会话目录（默认 `~/.codex/sessions`），不依赖外部服务或环境变量（路径均可通过命令行参数覆盖）

## 使用方式

在项目根目录下执行（导出「当前目录」对应的会话到默认 `codexhistory/`）：

```bash
# 从本仓库根目录运行（输出到当前目录下的 codexhistory/）
python skills/barksy_pipeline/codexhistory_export.py

# 或进入 skill 目录后运行（输出到执行时的当前目录下的 codexhistory/）
cd skills/barksy_pipeline
python codexhistory_export.py
```

### 可选参数

```bash
python skills/barksy_pipeline/codexhistory_export.py \
  --cwd /path/to/project \
  --sessions-dir /path/to/.codex/sessions \
  --output-dir /path/to/project/codexhistory
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--cwd` | 只导出会话中记录的 cwd 与此路径匹配的会话 | 当前工作目录 |
| `--sessions-dir` | Codex 会话 JSONL 所在目录 | `~/.codex/sessions` |
| `--output-dir` | 导出 Markdown 的写入目录 | `codexhistory` |

行为说明：

- 仅处理首行类型为 `session_meta` 的 JSONL 文件，且 `payload.cwd` 与 `--cwd` 一致；
- 若某 Session ID 已在输出目录下任意 `.md` 中出现过，则该会话会被跳过，不重复写入。
