---
title: 延迟优先型部署经验总览
created: 2026-07-18
updated: 2026-07-20
type: summary
tags: [scoreexpert, deployment, decision-guide, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence]
sources: [raw/articles/scoring-strategy-analysis-2026-07-14.md, raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md, raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
confidence: high
contested: false
contradictions: []
---

# 延迟优先型部署经验总览

## 1. 延迟优先总体经验

延迟优先的目标是降低明确口径的端到端 latency，同时守住 throughput、显存、OOM 和运行波动等护栏。部署时先判断异构能否局部化，再决定使用同构基线、局部隔离还是分布式均衡；命中 `active` 经验及其边界时直接推理部署策略，真实 Evaluation 不再是每次部署的必经步骤。

总体经验可以概括为：

1. **资源规模先做反事实**：满卡和少卡都是候选。新增算力只有在收益大于通信、同步与异构成本时才值得保留；减卡后必须重建完整并行拓扑。
2. **并行策略按机制组合**：分别分析 TP 同步范围、PP stage 瓶颈、DP replica 等待和 PP/MBN bubble，不用一个参数元组代替经验。
3. **局部异常优先隔离**：异常能够限制在少量 group 或 stage 时，缩小污染范围并重平衡慢 stage，避免影响扩散。
4. **分布式异常优先均衡**：异常跨区域后，逐点隔离价值下降，应减少快组等待慢组，并同时检查绝对 latency 与 replica skew。
5. **实例只在案例中复用**：卡数、慢卡位置和 `PP/TP/DP/MBN` 必须绑定具体场景；总体经验只保存选择规则、机制和切换条件。
6. **验证成本在入库时支付**：来源、历史 Evaluation、仿真或人工审核负责把经验升级为 `active`；后续匹配场景直接复用，只有未命中、越界或冲突时才重新验证。

## 2. 同构基线知识

### (1) 场景定义

- 无已知慢卡、故障卡或显著设备异构。
- 目标是在当前模型、batch、网络和 rank mapping 约束下建立正常延迟对照。

### (2) 资源规模部署经验

- **满卡条件**：命中的正式经验明确覆盖当前资源和拓扑，并表明新增算力收益大于通信成本时，直接采用满卡方案；未命中正式经验时才保留满卡/少卡验证分支。
- **少卡对照**：至少测试一个满足显存、并行整除和拓扑约束的少卡候选，寻找通信收益超过算力损失的反转边界。
- **拓扑重建**：减卡不是随意删除 rank；需要重新形成完整 TP group、DP replica 或 PP stage，并重新搜索并行参数。

### (3) 并行策略

- **TP**：优先把高频 TP 通信限制在最快的拓扑域内；增大 TP 必须与同步和通信成本一起验证。
- **TP/DP**：在拓扑允许时比较接近平衡与偏 TP/偏 DP 的候选，不把某个比例跨资源规模直接复用。
- **PP**：显存允许时优先比较无流水线方案；OOM 时改用可行的最小 PP。
- **PP/MBN**：无流水线时从最小可行 MBN 起步；PP 增大后重新扫描 MBN。

### (4) 场景案例

- **案例：标准 32 卡同构基线**：[[homogeneous-32gpu-score-candidate]] 在 32 张正常卡、4 个 8 卡节点的约束下，以满卡、节点内 TP、无 PP 和低 MBN 构造第一轮基线；当前实例为 `PP=1,TP=8,DP=4,MBN=1`，同时对照少卡、浅 PP 和其他 TP/DP 组合。
- **准入状态**：`active`。知识库所有者于 2026-07-20 确认为成熟经验；来源附件未包含原始 latency、throughput、通信时间和显存结果。^[raw/articles/scoring-strategy-analysis-2026-07-14.md]

## 3. 局部异构处理知识

### (1) 场景定义

- 异常集中在一个可识别的局部区域，能够控制其所在的 TP group、PP stage 或计算映射。
- 局部性的判断依据是影响能否被限制，而不是机械地只看慢卡数量。

### (2) 并行策略

- **TP**：缩小 TP group 可以限制慢卡同步污染，但必须与更大 TP 的通信和流水线代价对照。
- **TP/PP**：降低 TP 往往需要更深 PP；只有同时减少慢卡 stage 的层数或计算量才构成有效隔离。
- **DP**：避免形成纯快 replica 等待含慢卡 replica；是否使用单 replica 由资源规模和异构分布共同决定。
- **PP/MBN**：PP 加深后扫描足够的 MBN 以降低 bubble，同时检查端到端时延、显存和调度开销。

### (3) 局部异构的影响

- `TP group`：慢 rank 会让组内快卡等待；TP group 越大，直接污染范围可能越大。
- `DP replica`：只有部分 replica 含慢卡时，快 replica 会等待慢 replica。
- `PP stage`：慢卡 stage 可能决定整条流水线周期；只增加 PP 而不重平衡层数，不能实现有效隔离。

### (4) 对策：隔离

1. 把异常限制在尽可能小且可执行的同步组或 stage 中。
2. 按预测 stage time 给慢卡 stage 少分层或少分计算。
3. 对照不隔离、浅 PP 和不同 MBN，检查隔离收益是否大于 bubble、激活传输和调度成本。

### (5) 场景案例

- **案例：单慢卡局部隔离**：[[single-slow-gpu-isolation]] 在 32 卡中存在一张约半速慢卡时，用小 TP、单 replica、深 PP 和 stage 重平衡限制局部污染；当前实例为 `PP=16,TP=2,DP=1,MBN=64`，其中 64 只是搜索上界候选。
- **准入状态**：`active`。知识库所有者于 2026-07-20 确认为成熟经验；来源附件未包含原始 latency、stage time、group time 和可执行 layer mapping。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md]

## 4. 分布式异构处理知识

### (1) 场景定义

- 慢卡跨节点、亲和组或 DP replica 分布，已经不能视为单个局部坏点。
- 需要继续区分副本结构不对称和结构近似对称两种形态。

### (2) 并行策略

- **TP**：把 TP group 限制在快速拓扑域内，同时测量含慢卡 group 的实际时间。
- **TP/PP**：慢卡跨区域后，比较浅 PP/无 PP 与深 PP 隔离，避免多个慢 stage 串联放大瓶颈。
- **DP**：不对称分布重点测快慢 replica skew；近似对称分布重点保持各 replica 的结构或预测耗时接近。
- **PP/MBN**：无流水线时从最小可行 MBN 起步；因显存增加 PP 后重新扫描 MBN。

### (3) 分布式异构的影响

- 多个慢 stage 会削弱深 PP 对单个局部坏点的隔离价值。
- 不对称分布会形成慢 replica 和快 replica，快组等待慢组。
- 近似对称分布会让所有 replica 一起变慢，但结构接近时可降低 replica skew。
- `replica 更均衡` 不等于绝对 latency 更低，两项必须同时验收。

### (4) 对策：均衡与对称

1. 不对称分布按预测执行时间重新映射，减少快 replica 等待慢 replica。
2. 近似对称分布保持各 replica 的慢卡结构和预计耗时接近。
3. 慢卡速度不一致时按预测执行时间均衡，不能只按数量平均分配。
4. 同时报告端到端 latency、各 replica time、最大等待比例和 skew。

### (5) 场景案例

- **案例一：两慢卡非对称均衡**：[[two-slow-gpu-distributed-balance]] 在两张慢卡跨亲和组时，从逐点 PP 隔离切换到节点内 TP、节点间 DP，并测量快慢 replica skew；当前实例为 `PP=1,TP=8,DP=4,MBN=1`。
- **案例二：四慢卡对称副本**：[[four-slow-gpu-symmetric-replicas]] 在四张速度接近的慢卡一节点一张时，让每个 DP replica 具有相同慢卡结构；当前实例同为 `PP=1,TP=8,DP=4,MBN=1`，但机制和触发条件不同。
- **准入状态**：两页均为 `active`，知识库所有者于 2026-07-20 确认为成熟经验；来源报告当前策略最优，但附件未包含原始 latency、慢卡 ID/倍率、完整候选表和重复波动。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md] ^[raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]

## 5. 跨场景延迟决策规则

```text
无慢卡
→ 建立同构资源规模与并行策略基线

异常能够限制在局部 group/stage
→ 缩小污染范围并重平衡慢 stage

慢卡跨多个区域分散
→ 隔离收益下降，转向按预测耗时均衡 replica

慢卡均匀覆盖所有节点
→ 构造慢卡结构或预测耗时对称的 DP replica
```

切换依据是慢卡影响能否局部化，不是只按慢卡数量机械选择参数。模型显存、慢卡位置和倍率、rank mapping 或搜索空间改变时，应回到 [[deployment-objective-knowledge-framework]] 重新选择候选。

## 6. 经验准入、直接推理与回退

### 经验准入

经验进入 `active` 前必须定义 latency 口径和最小有效改善阈值 `δ`，并通过可追溯来源、历史 Evaluation、仿真或人工审核补齐：

- 端到端平均、P50、P95 或 P99 latency；选择其中一个作为主指标。
- throughput、peak memory、OOM 和稳定性护栏。
- TP group time、PP stage time 或 DP replica time 中与当前机制对应的指标。
- 重复运行波动，确认差异超过测量噪声。

### 在线直接推理

新场景的优化目标、资源拓扑、异构分布、模型约束、映射能力和经验量化边界全部匹配 `active` 卡时，直接返回：

- 主部署策略及 `PP/TP/DP/MBN`。
- rank/group/stage 映射和资源使用方式。
- 命中的经验、置信度、适用边界与回退策略。

这一路径不要求重新运行真实 Evaluation。

### 回退与补库条件

- `PP=1` 或目标候选 OOM。
- 慢卡位置、速度倍率或拓扑不匹配。
- 反事实候选的真实 latency 更低。
- MBN 只表现为搜索边界解，并增加端到端时延或显存。
- 对称映射降低 skew，但绝对 latency 超过业务上限。
- 没有命中 `active` 经验、关键场景字段缺失、经验相互冲突或参数推导超出已登记量化范围。

触发回退时才生成仿真、Evaluation 或人工审核任务，并把结果用于补库。当前四张场景卡均已由知识库所有者审核为 `active`；新场景命中任一卡的硬条件和量化边界时，直接输出其部署策略，不再重复支付 Evaluation 成本。完整经验库框架见 [[deployment-objective-knowledge-framework]]，领域状态与召回入口见 [[scoreexpert]]。
