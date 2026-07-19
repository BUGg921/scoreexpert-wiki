# 阶段 2：加入四张慢卡

## 输入

- 上一快照：`03-after-two-slow-gpus.md`
- 新场景：`01-source-cards/04-four-slow-gpus.md`

## 筛选前：新增候选

| ID | 候选摘要 | 与已有库关系 |
|---|---|---|
| F1 | 一节点一张且速度相近时，使每个 DP replica 含相同慢卡结构 | 新触发条件和新机制 |
| F2 | 只要有四张慢卡就固定使用 `1/8/4/1` | 参数外推 |
| F3 | 四慢卡与两慢卡的 score 完全相同 | 新的 score 能力边界 |
| F4 | 四个副本一样慢就一定更快 | 混淆均衡与绝对性能 |
| F5 | 比较均匀与非均匀映射的 replica skew | 新验证命题 |

## 审查过程

| ID | 可追溯 | 条件具体 | 动作可执行 | 非 score 机制 | 可观测 | 有边界 | 判定 | 理由与去向 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| F1 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 不与两慢卡经验合并：共同参数背后的部署目标不同 |
| F2 | 是 | 否 | 是 | 部分 | 是 | 否 | `REJECT` | 非均匀位置或速度差异会破坏对称机制 |
| F3 | 是 | 是 | 否 | 否 | 是 | 是 | `EVIDENCE_ONLY` | 证明 score 不具备区分慢卡数量/位置的能力 |
| F4 | 是 | 否 | 否 | 部分 | 否 | 否 | `REJECT` | skew 下降不等于绝对 latency 改善 |
| F5 | 是 | 是 | 是 | 是 | 是 | 是 | `KEEP_FOR_VALIDATION` | 需要相同参数下的位置扰动实验 |

## 筛选后：经验库快照

保留已有三条经验：

- E-NORMAL-001：正常 32 卡基线选择，`unverified`。
- E-SINGLE-001：单慢卡局部隔离，`unverified`。
- E-TWO-001：两慢卡跨亲和组均衡，`partially_supported`。

新增：

### E-FOUR-001 四慢卡对称副本

- 状态：`partially_supported`
- 触发：四节点各一张慢卡，慢卡速度接近，模型能在节点内 `TP=8` 下放入。
- 动作：设置 `PP=1,TP=8,DP=4,MBN=1`；每节点构造一个含一张慢卡的 TP group，使四个 DP replica 结构一致。
- 机制：不尝试把四个慢点串进多个 PP stage；通过对称映射减少 replica 间的额外 straggler skew，但不消除单副本绝对变慢。
- 观测：各 replica time、归一化 skew、TP group time、端到端 latency/throughput；同时报告均值和方差。
- 失效：慢卡不是一节点一张、速度差异明显、`PP=1` OOM、非均匀映射在可接受 skew 下更快。
- 证据状态：来源报告 Evaluation 胜者并给出拓扑解释，但无原始指标、卡号、倍率与位置扰动。
- 正式页：`concepts/distributed-heterogeneity/four-slow-gpu-symmetric-replicas.md`

## 新增的证据与验证队列

- EV-SCORE-BLIND-SPOT：当前 score 对两张和四张慢卡给出完全相同的分数，说明慢卡经验来自拓扑 + Evaluation，不是公式已学到设备异构。
- V-FOUR-MAPPING：固定 `1/8/4/1`，比较“一节点一张”与非均匀映射；同时看绝对 latency 和 replica skew。

## 本阶段真正新增了什么

```text
不是再次保存相同的 1/8/4/1，
而是新增“副本结构对称”的条件化经验：
每个副本慢卡数量和速度分布尽量一致，
并明确区分“更均衡”与“绝对更快”。
```

## 数量变化

```text
上一阶段经验：3
本阶段新增候选：5
新增经验：1
新增证据：1
新增待验证：1
拒绝：2
筛选后经验总数：4
```
