---
title: 延迟优先型部署经验总览
created: 2026-07-18
updated: 2026-07-19
type: summary
tags: [scoreexpert, deployment, decision-guide, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence]
sources: [raw/articles/scoring-strategy-analysis-2026-07-14.md, raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md, raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: medium
contested: false
contradictions: []
---

# 延迟优先型部署经验总览

## 1. 当前经验范围

当前四张部署经验卡全部归入**延迟优先型**：目标是根据同构或慢卡分布选择第一轮并行策略，以减少流水线 bubble、同步等待、慢卡污染范围或 replica skew，并最终用端到端 latency 验证。它们不是稳定优先经验；现有来源没有重复运行方差、失败率、超时或恢复数据。

当前经验链为：

```text
同构 32 卡
→ 单张局部慢卡
→ 两张跨区域慢卡
→ 四张均匀分布慢卡
```

四张卡形成“同构基线 → 局部隔离 → 分布式均衡 → 分布式对称”的策略切换链。现有证据仍需区分：同构和单慢卡为 `unverified`，两慢卡和四慢卡为 `partially_supported`；当前没有 `active` 正式经验。

## 2. 同构基线知识

### (1) 场景定义

- 32 张正常 GPU，4 个节点，每节点 8 卡，每两个节点构成一个 16 卡亲和组。
- 无已知慢卡或设备异构，目标是建立延迟 Evaluation 的正常对照。

### (2) 卡的数量

- 当前候选使用全部 32 张卡。
- 满卡来自 score 的 idle penalty，不代表真实环境中少卡一定更慢；至少保留一个少卡候选检验通信收益是否使结论反转。

### (3) 并行策略

```text
第一基线：PP=1, TP=8, DP=4, MBN=1
```

- `PP=1`：避免当前 score 中的 pipeline bubble penalty。
- `TP=8,DP=4`：当前离散候选中 TP/DP 评分最高；`TP:DP=2:1` 是本场景实例，不是通用比例。
- `MBN=1`：当前二次 penalty 在 1 处最小；没有证明它在其他模型和 batch 条件下仍是延迟最优。

### (4) 场景案例

- [[homogeneous-32gpu-score-candidate]]：作为第一轮延迟验证基线，同时对照 `TP=4,DP=8`、浅 PP 和少卡候选。
- 状态：`unverified`。来源没有真实 latency、throughput、通信时间和显存结果。^[raw/articles/scoring-strategy-analysis-2026-07-14.md]

## 3. 局部异构处理知识

### (1) 场景定义

- 32 卡中只有一张约半速慢卡，异常仍能限制在一个局部区域。
- 能识别慢卡 rank，并控制它所在的 TP group 和 PP stage。

### (2) 并行策略

```text
隔离基线：PP=16, TP=2, DP=1, MBN=64
```

- 小 TP 缩小慢卡直接污染的同步组。
- `DP=1` 避免快 replica 等待含慢卡的 replica。
- 高 PP 使用全部 32 卡，并尝试把慢卡限制到少数 stage。
- `MBN=64` 是搜索上界候选，必须同时测试 16 和 32。

### (3) 局部异构的影响

- `TP group`：慢 rank 会让组内快卡等待；TP group 越大，直接污染范围可能越大。
- `DP replica`：只有部分 replica 含慢卡时，快 replica 会等待慢 replica。
- `PP stage`：慢卡 stage 可能决定整条流水线周期；只增加 PP 而不重平衡层数，不能实现有效隔离。

### (4) 对策：隔离

1. 将慢卡放入 2 卡 TP group。
2. 使用 `PP=16,DP=1` 限制同步污染和副本等待。
3. 按预测 stage time 给慢卡 stage 少分层或少分计算。
4. 对照无 PP、浅 PP 和不同 MBN，检查隔离收益是否大于 bubble、激活传输和调度成本。

### (5) 场景案例

- [[single-slow-gpu-isolation]]：以 `16/2/1/64` 构造局部慢卡隔离实验。
- 状态：`unverified`。两套 score 给出相同候选，但缺少 latency、stage time、group time 和可执行 layer mapping。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md]

## 4. 分布式异构处理知识

### (1) 场景定义

- 慢卡跨节点、亲和组或 DP replica 分布，已经不能视为单个局部坏点。
- 当前有两种形态：两张慢卡造成副本不对称；四张慢卡一节点一张形成副本对称。

### (2) 并行策略

```text
均衡/对称基线：PP=1, TP=8, DP=4, MBN=1
```

- 每节点构造一个 `TP=8` group，避免 TP 跨节点。
- 四个节点组成 `DP=4`。
- 取消深 PP，避免多张慢卡形成多个慢 stage。
- `PP=1` 时从 `MBN=1` 起步，避免不必要的 microbatch 切分成本。

### (3) 分布式异构的影响

- 多个慢 stage 会削弱深 PP 对单个局部坏点的隔离价值。
- 两张慢卡分布在两个节点时，会形成两个慢 replica 和两个快 replica，快组等待慢组。
- 四张慢卡一节点一张时，所有 replica 都会变慢，但结构接近，可降低 replica skew。
- `replica 更均衡` 不等于绝对 latency 更低，两项必须同时验收。

### (4) 对策：均衡与对称

1. 两张慢卡时，优先比较无 PP、节点内 TP、节点间 DP，测量快慢 replica skew。
2. 四张慢卡且速度接近时，让每个 DP replica 都含一张慢卡，保持结构对称。
3. 慢卡速度不一致时按预测执行时间均衡，不能只按数量平均分配。
4. 同时报告端到端 latency、各 replica time、最大等待比例和 skew。

### (5) 场景案例

- [[two-slow-gpu-distributed-balance]]：两张慢卡跨亲和组，使用 `1/8/4/1` 从局部隔离切换为无流水线均衡。
- [[four-slow-gpu-symmetric-replicas]]：四张慢卡一节点一张，使用 `1/8/4/1` 构造四个慢卡结构一致的副本。
- 两页状态均为 `partially_supported`：来源报告当前候选为 Evaluation 最优，但缺少原始 latency、慢卡 ID/倍率、完整候选表和重复波动。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md] ^[raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]

## 5. 跨场景延迟决策规则

```text
无慢卡
→ 用 1/8/4/1 建立同构延迟基线

单张慢卡且能控制 rank/stage
→ 测试 16/2/1/64 的局部隔离

慢卡跨多个区域分散
→ 隔离收益下降，测试 1/8/4/1 的节点内 TP + 节点间 DP

慢卡均匀覆盖所有节点
→ 构造慢卡结构或预测耗时对称的 DP replica
```

切换依据是慢卡影响能否局部化，不是只按慢卡数量机械选择参数。模型显存、慢卡位置和倍率、rank mapping 或搜索空间改变时，应回到 [[deployment-objective-knowledge-framework]] 重新选择候选。

## 6. 延迟验收与共同失效边界

所有经验都必须在运行前定义 latency 口径和最小有效改善阈值 `δ`，至少同时报告：

- 端到端平均、P50、P95 或 P99 latency；选择其中一个作为主指标。
- throughput、peak memory、OOM 和稳定性护栏。
- TP group time、PP stage time 或 DP replica time 中与当前机制对应的指标。
- 重复运行波动，确认差异超过测量噪声。

共同失效条件：

- `PP=1` 或目标候选 OOM。
- 慢卡位置、速度倍率或拓扑不匹配。
- 反事实候选的真实 latency 更低。
- `MBN=64` 只表现为搜索边界解，并增加端到端时延或显存。
- 对称映射降低 skew，但绝对 latency 超过业务上限。

在原始指标和阈值补齐前，这四张卡必须继续按本节的延迟验收规则和各自经验页中的最小对照集合验证，不能作为无需对照的默认部署建议。整体知识格式见 [[deployment-objective-knowledge-framework]]。
