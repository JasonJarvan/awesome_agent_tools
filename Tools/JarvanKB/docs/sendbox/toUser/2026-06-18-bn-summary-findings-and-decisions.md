# BiliNote 总结:现状 / 可定制方法 / 本地 Agent 调研结论（2026-06-18）

> 给你的说明信。回应你问的三件事:BN 当前总结 prompt 是什么、有多少方法能改、能不能接本地 Agent。
> 决策已按你 2026-06-18 的回复落定。

## 1. BN 现在的总结怎么来的
B站视频 → BN 转录(ASR/字幕)→ 把转录发给一个 LLM(我们配的 `mimo-v2.5`)生成中文 markdown 笔记。
用的是 **BN 上游原版 prompt(未改)**:一句"你是一个专业的笔记助手,把视频转录整理成清晰、有条理、信息丰富的中文笔记…"
(完整 prompt 我上一条已逐字贴给你)。它**没有 system 消息**,就是单条中文 user 消息。

## 2. 一个发现:`style:"summary"` 是死配置
我们引擎发给 BN 的 `style:"summary"` 其实是**无效值**(`summary` 不是合法的 style,合法的是
minimal/detailed/学术/教程/小红书/会议纪要…),再加上没开任何 `format` →
**今天你拿到的是 BN 基础 prompt 的结构化笔记,并没有一个单独的"## AI 总结"小节。**(base 笔记本身已是完整结构化笔记,够用。)

- **v1.1 决定(你选的 = a)**:**先这样原样上线**,这个 style 修复 + 显式 AI 总结小节 **延后**。

## 3. 想改 BN 输出时,有哪些方法(将来用,从轻到重)
1. 修 `style` 用合法值 + 用 `format` 开 TOC / 显式"AI 总结"小节;
2. **`extras`**:往 prompt 末尾追加任意自定义指令 —— **最灵活、免改 BN**;
3. 在我们引擎里对返回的 markdown 做**后处理**(套模板 / 加 frontmatter / 插 KB 链接);
4. 换模型;5. 高级:bind-mount 自己的 `prompt.py` 完全改写;6. 最重:fork BN。
→ **将来主力推荐 = `extras` + 后处理**(零改 BN、全在我们这边可测)。**这些都延后**,归到一个 reach 域任务(见 §5)。

## 4. 本地 Agent 调研结论:**不做**(你的决定)
"把 BN 的 LLM 步骤接本机 `claude -p` 或 hermes agent"技术上**可行且干净**——BN 只发一个 OpenAI 请求,
把地址指向一个本地兼容 shim 即可,BN 完全无感、零改 BN/引擎。但:
- ⚠️ `claude -p` 自 **2026-06-15** 起**不再吃你的订阅、改成单独计费池**;
- 它**只在"深度笔记"**(Agent 用工具 / 翻你的 Obsidian 知识库 / 多步推理)才划算;平凡总结用它只是更慢更贵。
- **你的决定:不做。** 结论已存档(`persist/memory/bn-output-customization-and-local-agent-2026-06-18.md`),
  将来若想要"深度笔记"模式可重启(届时 fork `i-am-logger/claude-code-proxy` 当 shim,别自己写)。

## 5. 小结 / 接下来
- **v1.1**:用 BN 自带笔记**原样上线**(deployer 正在跑)。
- **BN 输出定制**(修 style 死配置 + extras + 后处理):**延后** = 一个 **reach 域任务(Dashboard UN-051)交给 ReachOrche**,将来非破坏式改进。
- **本地 Agent**:不做(已存档)。

— root orche g5
