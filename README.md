# ScoreExpert 部署经验 Wiki

这是一个使用 Markdown 与 `[[wikilinks]]` 维护的 ScoreExpert GPU 部署经验库。它把不可变原始来源、综合知识页和维护规则分开保存，可直接使用 Obsidian、VS Code 或普通文本编辑器阅读。

## 快速开始

- 从 [index.md](index.md) 浏览经验目录。
- 从 [新场景部署策略选择](queries/deployment-strategy-selection.md) 开始分析新场景。
- 更新前阅读 [SCHEMA.md](SCHEMA.md) 中的页面、标签、来源和置信度规则。

## 目录

```text
raw/          不可变来源快照
entities/     实体页
concepts/     经验、参数和治理概念
comparisons/  场景与策略对比
queries/      值得沉淀的查询结论
index.md      全部知识页索引
log.md        追加式维护日志
SCHEMA.md     Wiki 结构与更新契约
```

## 健康检查

```bash
python3 scripts/lint_wiki.py
```

检查范围包括 frontmatter、标签、孤立页、断链、索引完整性、原始快照 SHA-256、上游来源漂移、页面大小和日志轮换。

## 项目内 Codex Skill

打开本项目作为 Codex 工作目录后，可以使用 [`$maintain-scoreexpert-wiki`](.codex/skills/maintain-scoreexpert-wiki/SKILL.md) 导入来源、查询或更新经验、处理冲突、运行健康检查，以及在明确要求时维护 Git 提交。

## 维护流程

1. 在 `raw/` 新增带日期和 SHA-256 的来源快照，不修改旧快照。
2. 更新或新增知识页，补齐至少两个 Wiki 链接。
3. 同步更新 `index.md`，并向 `log.md` 追加操作记录。
4. 运行健康检查；确认无结构错误后提交 Git 变更。
