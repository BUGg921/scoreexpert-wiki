# 阶段 0：初始经验库（正常卡 + 单张慢卡）

## 输入

- `01-source-cards/01-homogeneous-32gpu.md`
- `01-source-cards/02-single-slow-gpu.md`

初始库只看这两个场景，不提前使用两张或四张慢卡结论。

## 筛选前：全部候选

| ID | 候选摘要 | 来源类型 |
|---|---|---|
| N1 | 匹配正常 32 卡场景时，以 `1/8/4/1` 作为第一轮 Evaluation 基线 | 来源结论 + score |
| N2 | 正常场景永远满卡 | 过度概括 |
| N3 | `TP:DP=2:1` 是跨场景通用最优比例 | 来源实例被外推 |
| N4 | 当前 score 的 bubble、idle、TP/DP、MBN 项解释参数排名 | score 推导 |
| S1 | 一张局部半速慢卡时，用小 TP、高 PP 和 stage rebalance 做隔离型 Evaluation | 来源结论 + 拓扑推理 |
| S2 | 所有单慢卡场景都固定使用 `16/2/1/64` | 参数外推 |
| S3 | MBN 越大越好 | score 边界解 |
| S4 | 两套 score 通过 TP/DP 成本、bubble 与 MBN 奖励形成当前排名 | score 推导 |
| S5 | 慢卡 stage 少分层可缓解瓶颈 | 可证伪拓扑命题 |

## 审查过程

| ID | 可追溯 | 条件具体 | 动作可执行 | 非 score 机制 | 可观测 | 有边界 | 判定 | 理由与去向 |
|---|---:|---:|---:|---:|---:|---:|---|---|
| N1 | 是 | 是 | 是 | 部分 | 是 | 是 | `ACCEPT_EXPERIENCE` | 进入初始库；无 Evaluation，状态为 `unverified` |
| N2 | 是 | 否 | 否 | 否 | 否 | 否 | `REJECT` | “永远”越过来源边界；只在源文档保留 |
| N3 | 是 | 否 | 否 | 否 | 否 | 否 | `EVIDENCE_ONLY` | 保留当前约束下 `8:4` 实例；删除“通用”外推 |
| N4 | 是 | 是 | 否 | 否 | 是 | 是 | `EVIDENCE_ONLY` | 能解释 score，但不能单独指导部署 |
| S1 | 是 | 是 | 是 | 是 | 是 | 是 | `ACCEPT_EXPERIENCE` | 进入初始库；缺少真实指标和映射，状态为 `unverified` |
| S2 | 是 | 否 | 是 | 部分 | 是 | 否 | `REJECT` | 忽略模型层数、显存、慢卡位置和速度倍率 |
| S3 | 是 | 否 | 否 | 否 | 否 | 否 | `REJECT` | `64` 是上界；不能把 score 单调性写成物理经验 |
| S4 | 是 | 是 | 否 | 否 | 是 | 是 | `EVIDENCE_ONLY` | 进入 score 证据层 |
| S5 | 是 | 是 | 部分 | 是 | 是 | 是 | `KEEP_FOR_VALIDATION` | 需要 stage profile 和 layer mapping 后再决定是否并入经验 |

## 筛选后：初始经验库快照

### E-NORMAL-001 正常 32 卡基线选择

- 状态：`unverified`
- 触发：32 张正常卡、4×8 卡节点、来源 v10 score、`TP≤8`、允许 `PP=1`。
- 动作：先测 `PP=1,TP=8,DP=4,MBN=1`，同时测 `1/4/8/1`、浅 PP 与少卡候选。
- 机制：当前动作由 score 的 idle、bubble、TP/DP 和 MBN 项形成；硬件性能机制尚未证实。
- 观测：score 排名、latency、throughput、TP/DP 通信、peak memory。
- 失效：出现慢卡、`PP=1` OOM、score/搜索空间改变、反事实候选更优。
- 正式页：`concepts/homogeneous-baseline/homogeneous-32gpu-score-candidate.md`

### E-SINGLE-001 单慢卡局部隔离

- 状态：`unverified`
- 触发：32 卡中只有一张约半速慢卡，位置局部化，模型允许 16 stage 且能重平衡层。
- 动作：以 `PP=16,TP=2,DP=1,MBN=64` 为隔离基线；把慢卡放入 2 卡 TP group，减少慢 stage 负载，并扫描 `MBN∈{16,32,64}`。
- 机制：小 TP 缩小同步污染范围；高 PP 尝试把局部异常限制在少数 stage；DP=1 避免副本同步等待。
- 观测：TP group time、slowest-stage ratio、bubble、latency、throughput、显存。
- 失效：出现第二张跨区域慢卡、深 PP 不可行、慢 stage 仍控制吞吐、较小 MBN 或无 PP 更优。
- 正式页：`concepts/local-heterogeneity/single-slow-gpu-isolation.md`

## 筛选后附属内容

### Score 证据层

- EV-NORMAL-SCORE：当前 v10 score 为什么偏向满卡、`PP=1`、当前候选中的 `8/4` 和 `MBN=1`。
- EV-SINGLE-SCORE：两套单慢卡 score 为什么在当前搜索边界给出 `16/2/1/64`。

### 验证队列

- V-SINGLE-STAGE：比较均匀层分配与慢 stage 少分层；观察 slowest-stage ratio 和端到端指标。

## 数量变化

```text
筛选前候选：9
经验：2
证据：3（N3、N4、S4，其中 N3 只保留受限实例）
待验证：1
拒绝：3
```
