---
name: maintain-scoreexpert-wiki
description: 维护项目内 ScoreExpert GPU 部署经验 Wiki。用于导入本地文件、URL、报告、场景或 Evaluation 来源，创建或更新部署经验页面，回答并沉淀部署查询，处理冲突和经验替代关系，审计 frontmatter、标签、wikilinks、索引、日志与来源哈希，归档过期页面，或在用户明确要求时用 Git 提交已经验证的 Wiki 变更。
---

# 维护 ScoreExpert 部署经验 Wiki

## 目标

维护一个持续积累、来源可追溯、结论有边界的 ScoreExpert 部署经验 Wiki。把原始来源、综合知识和结构规则分层保存；不要每次从原始材料重新推导全部知识。

从包含 `SCHEMA.md`、`index.md` 和 `log.md` 的项目根目录执行命令。若当前目录不确定，先运行 `git rev-parse --show-toplevel` 并切换到返回目录。

## 每次任务先定向

在读取、查询或修改页面前，按顺序执行：

1. 读取 `SCHEMA.md`，确认领域、frontmatter、标签和状态规则。
2. 读取 `index.md`，确认已有页面及其摘要。
3. 读取 `log.md` 最近 20–30 条记录，了解近期操作。
4. 运行 `git status --short --branch`，识别用户已有改动并保护它们。
5. 用 `rg` 搜索当前主题；页面超过 100 个时必须同时按文件名和正文搜索。

不要跳过定向步骤。不要创建已有主题的近义重复页。

## 选择操作

- 导入文件、URL、场景、报告或 Evaluation：读取 [工作流](references/workflows.md) 的“导入来源”，创建文件时同时读取 [模板](references/templates.md)。
- 回答部署问题或沉淀新分析：读取 [工作流](references/workflows.md) 的“查询与沉淀”。
- 检查 Wiki 健康状态：读取 [工作流](references/workflows.md) 的“Lint 与审核”。
- 处理冲突、经验覆盖或合并：读取 [工作流](references/workflows.md) 的“冲突与状态迁移”。
- 归档完全被替代的页面：读取 [工作流](references/workflows.md) 的“归档”。
- 用户明确要求提交、建分支或推送时：读取 [工作流](references/workflows.md) 的“Git 维护”。

## 不可违反的知识边界

- 把 `raw/` 视为不可变来源层。来源变化时新增带日期的快照，不修改旧快照。
- 只把 active 正式经验写成部署第一候选；不要默认召回 superseded 经验。
- 把 `unverified`、`partially_supported`、`mixed` 等假设留在验证层，不要改写成正式经验。
- 即使假设达到 `supported`，也只允许生成更新提案；仍需人工审核、dry-run 和显式写入。
- 分开陈述 score 证据、拓扑推理和真实 Evaluation 证据。缺少 Evaluation 时直接写明，不要补造。
- 把参数组合绑定到总卡数、每节点卡数、亲和组、慢卡数量/位置/速度倍率、rank mapping、模型约束和搜索空间。
- 把 `MBN=64` 等搜索空间边界值写成边界候选，不要写成物理必然最优。
- 每个知识页至少保留两个出站 `[[wikilinks]]`，并检查相关旧页面是否需要反向链接。
- 只使用 `SCHEMA.md` 已登记标签。需要新标签时先更新 schema。
- 每次新增或更新知识页时同步维护 `index.md`，并向 `log.md` 追加记录。
- 若一次导入将修改 10 个及以上已有页面，先向用户确认范围。

## 使用项目能力

把这些文件视为当前权威接口：

- `SCHEMA.md`：页面、标签、来源和状态契约。
- `index.md`：页面目录与查询入口。
- `log.md`：追加式操作历史。
- `raw/`：不可变来源快照。
- `scripts/lint_wiki.py`：零第三方依赖的结构与来源健康检查。

不要在 skill 内复制 `scripts/lint_wiki.py`；直接使用项目版本，保证检查规则只有一个来源。

## 验证与交付

完成任何写操作后运行：

```bash
python3 scripts/lint_wiki.py
git diff --check
git status --short --branch
```

把结构错误修到 0。逐项解释 review item；低置信度假设可以保留，但必须是有意且与页面状态一致。

最终说明：创建或更新了哪些文件、来源与置信度如何变化、lint 结果、仍待验证的内容。不要因为修改完成就自动提交或推送；只在用户明确要求 Git 写操作时执行。
