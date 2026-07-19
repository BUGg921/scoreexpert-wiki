# 阶段 1：加入两张慢卡

## 输入

- 上一快照：`02-initial-library.md`
- 新场景：`01-source-cards/03-two-slow-gpus.md`

## 筛选前：新增候选

| ID | 候选摘要 | 与初始库关系 |
|---|---|---|
| T1 | 两慢卡跨亲和组时，从单慢卡隔离切换到无 PP、节点内 TP、节点间 DP | 新触发条件和新动作 |
| T2 | 任何两张慢卡都固定使用 `1/8/4/1` | 参数外推 |
| T3 | `PP=1`、`MBN=1` 是当前 score 的强偏好 | 补充 score 证据 |
| T4 | `TP=8,DP=4` 是稳定强规律 | 与 0.28 分差矛盾 |
| T5 | 用 replica skew 验证两个慢副本和两个快副本的等待 | 新验证命题 |

## 审查过程

| ID | 可追溯 | 条件具体 | 动作可执行 | 非 score 机制 | 可观测 | 有边界 | 判定 | 理由与去向 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| T1 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 不与正常卡经验合并：参数虽相同，慢卡触发、机制和验收不同 |
| T2 | 是 | 否 | 是 | 部分 | 是 | 否 | `REJECT` | 两卡同节点、不同速度或 `PP=1` OOM 时不适用 |
| T3 | 是 | 是 | 否 | 否 | 是 | 是 | `EVIDENCE_ONLY` | 解释公式排名，不算慢卡经验 |
| T4 | 是 | 否 | 否 | 否 | 是 | 否 | `REJECT` | `8/4` 只比 `1/32` 高 0.28，且受 GBS/候选空间影响 |
| T5 | 是 | 是 | 是 | 是 | 是 | 是 | `KEEP_FOR_VALIDATION` | 需要原始 replica time 和重复实验 |

## 筛选后：经验库快照

保留初始库：

- E-NORMAL-001：正常 32 卡基线选择，`unverified`。
- E-SINGLE-001：单慢卡局部隔离，`unverified`。

新增：

### E-TWO-001 两慢卡跨亲和组均衡

- 状态：`partially_supported`
- 触发：两张慢卡分别位于两个亲和组和两个节点；模型能在节点内 `TP=8` 下放入。
- 动作：设置 `PP=1,TP=8,DP=4,MBN=1`；每节点一个 TP group，记录两个慢 replica 与两个快 replica。
- 机制：取消深 PP，避免多个慢点串入流水线；节点内 TP 避免 TP 跨节点；DP 扩展仍会等待慢 replica。
- 观测：`max(replica_time)-avg(replica_time)` 或归一化 skew、快副本等待比例、TP group time、端到端 latency/throughput。
- 失效：两卡集中同节点、`PP=1` OOM、replica skew 过大、深 PP 对照更优。
- 证据状态：来源报告 Evaluation 胜者并给出 score 复算，但没有原始指标、卡号、倍率与重复波动。
- 正式页：`concepts/distributed-heterogeneity/two-slow-gpu-distributed-balance.md`

## 新增的证据与验证队列

- EV-MULTI-SCORE：强 bubble 惩罚和 `TP×MBN` 成本共同偏向 `PP=1,MBN=1`；`TP=8,DP=4` 仅为弱 score 命中。
- V-TWO-SKEW：固定参数，对比两张慢卡的不同节点/亲和组映射，观察 replica skew 和端到端指标。

## 本阶段真正新增了什么

```text
不是新增一个重复的 1/8/4/1 参数条目，
而是新增一条条件化切换规则：
局部单慢卡 → 隔离；跨亲和组两慢卡 → 取消深PP并检查副本失衡。
```

## 数量变化

```text
上一阶段经验：2
本阶段新增候选：5
新增经验：1
新增证据：1
新增待验证：1
拒绝：2
筛选后经验总数：3
```
