# ScoreExpert 部署经验 Wiki

这是一个使用 Markdown 与 `[[wikilinks]]` 维护的 ScoreExpert GPU 部署经验库。它把不可变原始来源、综合知识页和维护规则分开保存，可直接使用 Obsidian、VS Code 或普通文本编辑器阅读。

核心目标是把历史验证成本沉淀为可复用经验：新场景命中 `active` 经验及其适用边界时，直接推理部署策略，不要求为每次部署重新运行真实 Evaluation。Evaluation、仿真或人工审核主要用于经验准入、越界补库和冲突处理。

## 快速开始

- 从 [index.md](index.md) 查看当前经验目录；初始化状态下目录为空。
- 输入第一条经验前，阅读 [SCHEMA.md](SCHEMA.md) 中的页面、标签、来源和置信度规则。
- 使用 [`$maintain-scoreexpert-wiki`](.codex/skills/maintain-scoreexpert-wiki/SKILL.md) 导入新的来源和经验。

## 目录

```text
raw/          不可变来源快照
entities/     实体页
concepts/     按经验类别划分的经验页，以及根目录中的支撑知识
comparisons/  场景与策略对比
queries/      值得沉淀的查询结论
outputs/      暂不写入经验库的独立分析结果
index.md      全部知识页索引
log.md        追加式维护日志
SCHEMA.md     Wiki 结构与更新契约
```

## 健康检查

```bash
python3 scripts/lint_wiki.py
```

检查范围包括 frontmatter、标签、孤立页、断链、索引完整性、原始快照 SHA-256、上游来源漂移、页面大小和日志轮换。

## 当前经验格式

经验库采用“优化目标 × 异构范围”的二维结构：

1. 一级入口：**延迟优先型、稳定优先型**。
2. 二级场景：**同构基线、局部异构、分布式异构**。

完整字段与当前证据覆盖见 [ScoreExpert 部署经验总库](concepts/deployment-objective-knowledge-framework.md)。总库永久保留延迟优先和稳定优先的完整框架；当前稳定优先分支缺少直接 Evaluation，只保留结构、对照场景和验证缺口，不生成默认部署结论。

三类二级场景分别是：

1. **同构基线**：无已知异构设备时的正常部署对照。
2. **局部异构**：异常集中在单个局部区域时的污染限制与隔离。
3. **分布式异构**：异常跨节点、亲和组或副本分布时的均衡与对称映射。

局部异构和分布式异构知识统一按“场景定义 → 异构影响 → 并行策略 → 场景案例”组织；隔离、均衡与对称等对策直接融入 TP、TP/PP、DP、PP/MBN，不单列总体策略。

每张经验页都使用 `experience_category` 和对应标签声明唯一场景分类；延迟/稳定是查询、指标和验收入口，不要求复制经验页。当前采用“总经验库 → 优化目标总体经验 → 具体场景经验卡”的三层结构：总体经验只写跨实例规则，具体参数放入“场景案例”并链接唯一经验卡；不再保留重复的分类总览、独立 Score 决策链和通用验证计划。

每张具体场景经验卡的正文只保留“1. 场景描述”和“2. 具体的并行策略”两个一级章节；状态、优化目标、准入主体、准入日期、来源和置信度写入 frontmatter。适用范围写在场景描述，执行步骤并入部署策略，策略章只保留“部署策略、部署经验、失效条件与回退”。

```text
concepts/
├── deployment-objective-knowledge-framework.md  # 完整部署经验总库
├── latency-first-experience-summary.md           # 延迟优先总体经验
├── homogeneous-baseline/
│   └── homogeneous-32gpu-score-candidate.md
├── local-heterogeneity/
│   └── single-slow-gpu-isolation.md
├── distributed-heterogeneity/
│   ├── two-slow-gpu-distributed-balance.md
│   └── four-slow-gpu-symmetric-replicas.md
```

## 项目内 Codex Skill

打开本项目作为 Codex 工作目录后，可以使用 [`$maintain-scoreexpert-wiki`](.codex/skills/maintain-scoreexpert-wiki/SKILL.md) 导入来源、查询或更新经验、处理冲突、运行健康检查，以及在明确要求时维护 Git 提交。

## 维护流程

1. 在 `raw/` 新增带日期和 SHA-256 的来源快照，不修改旧快照。
2. 更新或新增知识页，补齐至少两个 Wiki 链接。
3. 同步更新 `index.md`，并向 `log.md` 追加操作记录。
4. 运行健康检查；确认无结构错误后提交 Git 变更。

## 经验库演化演示

四个场景的统一模板源文档，以及“正常卡 + 单慢卡 → 加入两慢卡 → 加入四慢卡”的筛选前后过程，保存在 [outputs/experience-evolution-demo/README.md](outputs/experience-evolution-demo/README.md)。这些文件是可审核的演示快照，不会自动升级为正式经验。
