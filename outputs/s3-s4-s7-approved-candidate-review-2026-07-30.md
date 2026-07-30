# S3、S4、S7 审核准入候选审查

## 筛选前

| Candidate ID | 审核后 raw 来源 | 场景与候选策略 | 初始角色 |
|---|---|---|---|
| `s3-same-node-20260730` | [S3 同节点双慢卡](../raw/articles/two-slow-gpu-same-node-evolve-analysis-2026-07-30.md) | 32 卡、两张 0.5× 慢卡同节点；`PP4/TP8/DP1/MBN8` | `KEEP_FOR_VALIDATION` |
| `s4-same-affinity-20260730` | [S4 同亲和组双慢卡](../raw/articles/two-slow-gpu-same-affinity-evolve-analysis-2026-07-30.md) | 32 卡、两张 0.5× 慢卡位于同亲和组不同节点；`PP16/TP1/DP2/MBN64` | `KEEP_FOR_VALIDATION` |
| `s7-five-slow-reviewed-20260730` | [S7 五慢卡审核后快照](../raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-reviewed-2026-07-30.md) | 32 卡、五张 0.5× 慢卡按 2/1/1/1 分布；`PP16/TP1/DP2/MBN64` | `KEEP_FOR_VALIDATION` |

## 审查

| ID | 可追溯 | 条件具体 | 动作可执行 | 非 score 机制 | 可观测 | 有边界 | 新增价值 | 判定 | 理由与去向 |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `s3-same-node-20260730` | 是 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 审核后 raw 给出同节点局部条件、`DP=1`、节点内 `TP=8`、反推 `PP=4` 和 `MBN=8`，并解释同步范围、气泡和固定映射观测；知识库所有者已审核通过。 |
| `s4-same-affinity-20260730` | 是 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 审核后 raw 给出跨节点但同亲和组的分布条件、`TP=1,DP=2`、反推 `PP=16` 和 `MBN=64`，并保留 replica skew 与覆盖率边界；知识库所有者已审核通过。 |
| `s7-five-slow-reviewed-20260730` | 是 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 当前审核后 raw 与旧快照不同，已重新计算来源和正文哈希；其参数求解规则与 S4 相同，因此合并到同一成熟策略，具体五慢卡场景仍独立链接。 |

## 筛选后

- **正式经验**：新增一个同节点多慢卡局部异构分支；新增一个由 S4、S7 共同支撑的 `TP=1,DP=2` 分布式异构分支。
- **合并规则**：S4 与 S7 使用相同的 PP/TP/DP/MBN 求解方式，只在场景条件和映射观测上不同，因此不重复创建两条参数策略。
- **证据边界**：三份来源均只代表当前已仿真候选最优，仍保留候选覆盖率、真实训练 Evaluation 缺口、等价最优和固定 Rank 映射边界。
- **正式库影响**：更新 [[latency-first-experience-summary]] 和 [[deployment-objective-knowledge-framework]]；命中对应审核后 raw 的全部硬条件时才允许直接召回。
