# ScoreExpert Wiki 工作流

## 目录

- 导入来源
- 查询与沉淀
- Lint 与审核
- 冲突与状态迁移
- 归档
- Git 维护

## 导入来源

1. 判断来源类型：网页或文本放入 `raw/articles/`，论文或 PDF 放入 `raw/papers/`，会议或访谈放入 `raw/transcripts/`，图片放入 `raw/assets/`。
2. 保存完整来源内容并加入 raw frontmatter。URL 记录 `source_url`；本地文件记录 `source_path` 和原文件 SHA-256。
3. 计算第二个 `---` 之后正文的 SHA-256，写入 `sha256`。可用：

   ```bash
   awk 'BEGIN { n=0 } /^---$/ { n++; next } n >= 2 { print }' raw/articles/<file>.md | shasum -a 256
   ```

4. 重复导入同一路径或 URL 时先比较哈希。内容不变则跳过；内容变化则新增带日期或时间戳的快照，不覆盖旧文件。
5. 搜索 `index.md` 和所有知识页，识别需要更新的实体、概念、对比或查询页。
6. 仅在主题出现于两个以上来源，或是单一来源核心主题时创建新页。顺带提及不建页。
7. 使用 `SCHEMA.md` 规定的 frontmatter 和标签；单一来源或变化较快的结论使用 `confidence: medium` 或 `low`。
8. 对三种证据分栏：`score` 推导、拓扑推理、真实 Evaluation。没有 Evaluation 时保留证据缺口。
9. 至少添加两个出站 wikilink，并检查相关旧页是否需要回链。
10. 按字母或领域顺序更新 `index.md` 的摘要、总页数和日期。
11. 向 `log.md` 追加 `ingest` 或 `update` 记录，列出所有创建和更新的文件。

批量导入时先读完全部来源，再统一识别主题、搜索现有页面、写页面、更新一次索引和一次日志。若会修改 10 个及以上已有页面，先确认范围。

## 查询与沉淀

1. 先从 `index.md` 选择相关页面；页面超过 100 个时用 `rg -n '<关键词>' . -g '*.md'` 补充搜索。
2. 读取正式经验、比较页、假设页和治理页，区分 active 结论与未验证内容。
3. 回答时引用 Wiki 页面，例如“基于 [[homogeneous-32gpu-baseline]] 和 [[single-slow-gpu-isolation]]”。
4. 只把难以重新推导的对比、深度分析或新综合写入 `queries/` 或 `comparisons/`；简单查找不落盘。
5. 落盘时使用模板、补双向链接、更新 `index.md` 和 `log.md`。

新场景至少回答：场景设置、第一候选、score/拓扑/Evaluation 证据、适用边界、失效条件、证据缺口和下一步单变量仿真。

## Lint 与审核

运行：

```bash
python3 scripts/lint_wiki.py
```

按优先级处理：

1. 结构错误：断链、孤立页、缺失索引、frontmatter 缺失、未知标签、raw SHA 不匹配。
2. 来源漂移：上游文件变化时新增快照，不修订旧 raw 文件。
3. 审核项：`confidence: low`、`contested: true`、超过 200 行页面和日志轮换。
4. 人工语义审核：相同场景是否出现不兼容策略、是否把假设写成了结论、是否混淆 score 与 Evaluation。

修复后再次运行 lint，并向 `log.md` 追加 `lint` 记录。结构错误必须为 0；审核项可以保留，但要记录原因。

## 冲突与状态迁移

1. 比较来源日期、哈希验证状态、场景条件和 Evaluation 直接性。
2. 条件不同但结论不同不一定是冲突；优先拆成明确场景分支。
3. 真正冲突时保留双方陈述，设置 `contested: true`，并填写 `contradictions` slug。
4. 不静默覆盖旧结论。active 经验被替代时保留生命周期和历史页面。
5. 未验证原因先写成可证伪假设，列出替代解释、指标、最小效应阈值和仿真计划。
6. supported 假设只能生成正式更新提案；等待审核门禁完成后再更新 active 页面。

## 归档

1. 仅在内容完全被替代时创建 `_archive/` 并按原相对路径移动页面。
2. 从 `index.md` 删除该页。
3. 把所有旧 wikilink 改为新页面链接，或改成“普通文本（已归档）”。
4. 向 `log.md` 追加 `archive` 记录，写清替代页面和原因。
5. 运行 lint，确认没有断链和孤立页。

## Git 维护

只在用户明确要求 Git 写操作时提交、建分支或推送。

1. 运行 `git status --short --branch` 和 `git diff`，识别并保护用户已有改动。
2. 运行 Wiki lint 与 `git diff --check`。
3. 只暂存本次任务范围内文件；核对 `git diff --cached --stat` 和必要内容。
4. 使用描述知识变化的提交信息，例如 `docs: add two-slow-gpu deployment hypothesis`。
5. 提交后确认工作区状态和提交哈希。只有用户明确要求并且远端已配置时才推送。
