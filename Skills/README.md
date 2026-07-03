# Skills

可被 agent 调用的 skill 集合。每个 skill = 一个目录 + 标准 `SKILL.md`(frontmatter: `name` / `description`;正文薄,细节下沉到 `references/`、`scripts/`)。

## 分类(按用途)

| 分类 | 说明 |
|---|---|
| [maintain/](maintain/) | 维护/运维类:cc-relocate-project · skill-orchestrator · ops-doc-maintainer |
| [knowledge/](knowledge/) | 信息获取类:MiroResearch · web-search |
| [product/](product/) | 业务/评估决策类:idea-evaluator · interviewer-designer |

## 生命周期目录

| 目录 | 说明 |
|---|---|
| [in-progress/](in-progress/) | 开发中/未稳定,不进插件、不参与分类导航 |
| [deprecated/](deprecated/) | 已弃用,保留参考,勿在新工作中调用 |

## 新增 skill

在对应分类下建子目录,写标准 `SKILL.md`;未稳定先放 `in-progress/`。分类粒度随 skill 数量增长再细分,当前保持三类。
