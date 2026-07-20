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

- 参与部署的 GPU 属于同一性能等级，没有已知慢卡、故障卡或持续性的设备性能差异。
- 节点和亲和组仍可存在通信层级，但不同 group、stage 或 replica 不因设备性能差异形成固定的快慢结构。
- 出现可重复识别的设备快慢差异时，不再属于同构场景。

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

- **案例：标准 32 卡同构基线**：[[homogeneous-32gpu-score-candidate]] 在 32 张正常卡、4 个 8 卡节点的约束下，以满卡、节点内 TP、无 PP 和低 MBN 构造第一轮基线；当前实例为 `PP=1,TP=8,DP=4,MBN=1`，同时对照少卡、浅 PP 和其他 TP/DP 组合。^[raw/articles/scoring-strategy-analysis-2026-07-14.md]

## 3. 局部异构处理知识

### (1) 场景定义

- 异常集中在一个可识别、可控制的局部拓扑范围内，例如一个 TP group、PP stage、节点或 DP replica。
- 能够识别异常 rank，并通过 group、stage、layer 或计算映射把主要影响限制在这个局部范围内。
- 局部性的判断依据是异构影响能否被限制，而不是机械地只看慢卡数量；异常跨越多个独立区域且无法收敛到一个局部范围时，属于分布式异构。

### (2) 局部异构的影响

- `TP group`：慢 rank 会让组内快卡等待；TP group 越大，直接污染范围可能越大。
- `DP replica`：只有部分 replica 含慢卡时，快 replica 会等待慢 replica。
- `PP stage`：慢卡 stage 可能决定整条流水线周期；只增加 PP 而不重平衡层数，不能实现有效隔离。

### (3) 并行策略

- **TP**：使用较小的 TP group，把慢卡造成的同步等待限制在较小范围内，避免影响扩散到更多正常卡。
- **TP/PP**：降低 TP 后使用更深的 PP 承接剩余并行度，并把慢卡限制在少数 stage；同时减少慢卡 stage 的层数或计算量，使各 stage 的预计执行时间接近。
- **DP**：避免形成纯快 replica 等待含慢卡 replica；异构无法在多个 replica 间均衡时，优先减少 DP 数量或使用单 replica。
- **PP/MBN**：PP 加深后增大 MBN，降低 pipeline bubble；MBN 的选择同时受显存和调度开销约束。

### (4) 场景案例

- **案例：单慢卡局部隔离**：[[single-slow-gpu-isolation]] 在 32 卡中存在一张约半速慢卡时，用小 TP、单 replica、深 PP 和 stage 重平衡限制局部污染；当前实例为 `PP=16,TP=2,DP=1,MBN=64`，其中 64 只是搜索上界候选。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md]

## 4. 分布式异构处理知识

### (1) 场景定义

- 异常卡跨多个独立节点、亲和组、TP group 或 DP replica 分布，无法作为一个局部坏点处理。
- 分布式异构包含两种基本形态：各 replica 的异常结构或预测耗时不同的“不对称分布”，以及各 replica 的异常结构和预测耗时接近的“近似对称分布”。
- 分布范围按异常是否跨越多个独立拓扑区域判断，不以慢卡数量直接划分。

### (2) 分布式异构的影响

- 多个慢 stage 会削弱深 PP 对单个局部坏点的隔离价值。
- 不对称分布会形成慢 replica 和快 replica，快组等待慢组。
- 近似对称分布会让所有 replica 一起变慢，但结构接近时可降低 replica skew。
- `replica 更均衡` 不等于绝对 latency 更低，两项必须同时验收。

### (3) 并行策略

- **TP**：将 TP group 限制在节点内或高速拓扑域内，避免高频 TP 通信跨越较慢链路；每个 TP group 的慢卡结构应尽可能可控。
- **TP/PP**：慢卡跨多个区域分布时，深 PP 容易形成多个慢 stage，因此优先使用浅 PP 或无 PP；因显存必须增加 PP 时，按各 stage 的预计执行时间重新分配计算量。
- **DP**：对于不对称分布，按预计执行时间重新映射慢卡，减少快 replica 等待慢 replica；对于近似对称分布，保持各 replica 的慢卡数量、速度和位置尽可能一致。慢卡速度不同时按预计执行时间均衡，不能只按数量平均分配。
- **PP/MBN**：无 PP 时使用较小 MBN；因显存约束增加 PP 后，再根据流水线深度增大 MBN，减少 pipeline bubble。

### (4) 场景案例

- **案例一：两慢卡非对称均衡**：[[two-slow-gpu-distributed-balance]] 在两张慢卡跨亲和组时，从逐点 PP 隔离切换到节点内 TP、节点间 DP，并测量快慢 replica skew；当前实例为 `PP=1,TP=8,DP=4,MBN=1`。^[raw/articles/scoring-strategy-analysis-slow-gpu-2026-07-15.md] ^[raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]
- **案例二：四慢卡对称副本**：[[four-slow-gpu-symmetric-replicas]] 在四张速度接近的慢卡一节点一张时，让每个 DP replica 具有相同慢卡结构；当前实例同为 `PP=1,TP=8,DP=4,MBN=1`，但机制和触发条件不同。^[raw/articles/multi-slow-gpu-deployment-analysis-2026-07-15.md]

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
