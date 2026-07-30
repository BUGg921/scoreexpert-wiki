---
title: 延迟优先型部署经验总览
created: 2026-07-18
updated: 2026-07-30
type: summary
tags: [scoreexpert, deployment, decision-guide, gpu, topology, slow-gpu, pp, tp, dp, mbn, evidence]
sources: [raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md, raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md, raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md]
confidence: high
contested: false
contradictions: []
---

# 延迟优先型部署经验总览

在 [[scoreexpert]] 部署经验库中，延迟优先以端到端 latency 为主要优化目标，同时约束 throughput、显存、OOM 和运行波动；完整的延迟/稳定框架见 [[deployment-objective-knowledge-framework]]。

## 1. 同构基线知识

### (1) 场景定义

- 参与部署的 GPU 属于同一性能等级，没有已知慢卡、故障卡或持续性的设备性能差异。
- 节点和亲和组仍可存在通信层级，但不同 group、stage 或 replica 不因设备性能差异形成固定的快慢结构。
- 出现可重复识别的设备快慢差异时，不再属于同构场景。

### (2) 并行策略

1. **满卡方案**：在 `idle 的损失 > 通信优化收益` 时，使用全部可用卡；`PP` 取满足模型分层和显存约束的最小可行值，优先取 `PP=1`；在 `PP × TP × DP = active_gpu`、各并行组能够完整构造且不跨越不利通信边界的前提下，按 `TP:DP=2:1` 求解整数 `TP` 和 `DP`；`MBN` 取与所选 `PP` 匹配的最小可行值。每个 TP group 放在带宽最高的局部拓扑内，完整 TP group 组成 DP replica。

### (3) 原因

1. **`PP` 取最小值**：减少流水线 stage 和 pipeline bubble；模型显存允许时优先不切 PP。
   - **`TP:DP=2:1`**：在当前成熟经验支持的比例上，让 TP 承担更多模型内并行，同时由 DP 扩展完整 replica；具体整数值由可用卡数和完整拓扑共同求解。
   - **TP group 映射**：把高频 TP 通信限制在带宽最高的局部拓扑内，避免为了满足比例而跨越不利通信边界。
   - **`MBN` 取最小值**：最小 PP 不需要额外微批填充深流水线。^[raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **标准 32 卡同构基线**：[场景来源](../raw/articles/homogeneous-32gpu-deployment-analysis-2026-07-22.md)在 32 张正常卡、4 个 8 卡节点的场景中使用 `PP=1, TP=8, DP=4, MBN=1`。

## 2. 局部异构处理知识

### (1) 场景定义

- 部署中存在可重复识别的设备性能差异，例如部分 GPU 的计算速度持续低于其余 GPU；异常 rank、相对速度和所在拓扑位置能够被识别，偶发抖动或暂时性通信拥塞不直接判为局部异构。
- 异常设备集中在一个可控制的局部拓扑范围内，或者能够通过 rank/group/stage 映射收敛到一个范围内，例如一个 TP group、一个 PP stage、一个节点或一个 DP replica。
- 局部范围之外的大部分 group、stage 和 replica 不形成持续性的快慢结构；异常造成的同步等待、stage 变慢或负载失衡能够主要限制在少量固定设备和一个局部执行单元内，不会同时污染多个独立拓扑区域。
- 模型和部署系统能够识别异常设备并调整 rank、group、stage、layer 或计算量映射；慢卡所在 stage 可以减层或减计算，使其预计执行时间接近其他 stage。无法进行这种局部重映射或负载调整时，即使只有一张慢卡，也不能直接套用局部隔离经验。
- 局部性由“影响是否能够收敛到一个可控范围”决定，而不是由慢卡数量决定：多张异常卡若能被同一局部单元统一承载，仍可属于局部异构；异常卡跨多个独立节点、亲和组、TP group、PP stage 或 DP replica，且无法通过一次局部映射完成隔离时，属于分布式异构；没有持续设备性能差异时属于同构场景。

### (2) 并行策略

1. 当异构影响能够限制在一个局部 group/stage，且 `保留异构设备并进行局部隔离的算力收益 > 深 PP 引入的流水线与调度成本` 时，使用全部可用卡；`DP` 取避免快慢 replica 等待的最小可行值，优先取 `DP=1`；按 `TP:DP=2:1` 求解 `TP`，再由 `PP × TP × DP = active_gpu` 求得整数 `PP`，使 `PP` 取能够形成局部隔离的最大可行值；`MBN` 取显存、延迟和调度边界内能够充分填充深流水线的最大可行值。构造完整 TP group 和 PP stage，将异常卡限制在一个 TP group/stage，并减少异常卡所在 stage 的层数或计算量。

### (3) 原因

1. **`DP` 取最小值**：避免形成纯快 replica 等待含慢卡 replica 的跨副本同步；优先 `DP=1` 时，`TP:DP=2:1` 对应 `TP=2`。
   - **`TP:DP=2:1`**：较小的 TP group 把慢卡引起的同步等待限制在局部范围内，避免污染更多正常卡。
   - **`PP` 取最大可行值**：在使用全部可用卡、`DP` 和 `TP` 已确定后，通过增加 PP 构造更多局部 stage；慢卡 stage 同时减层或减计算，使其预计执行时间接近其他 stage。
   - **`MBN` 取最大可行值**：深 PP 需要更多微批降低 pipeline bubble，但上限必须由显存、端到端延迟和调度开销约束；32 卡案例中的 `MBN=64` 是搜索上界，不是所有资源规模的固定值。^[raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **单慢卡局部隔离**：[场景来源](../raw/articles/single-slow-gpu-deployment-analysis-2026-07-22.md)在 32 卡中存在一张约半速慢卡时，使用 `PP=16, TP=2, DP=1, MBN=64` 隔离慢卡并重平衡慢卡 stage。

## 3. 分布式异构处理知识

### (1) 场景定义

- 异常卡跨多个独立节点、亲和组、TP group 或 DP replica 分布，无法作为一个局部坏点处理。
- 分布式异构包含两种基本形态：各 replica 的异常结构或预测耗时不同的“不对称分布”，以及各 replica 的异常结构和预测耗时接近的“近似对称分布”。
- 分布范围按异常是否跨越多个独立拓扑区域判断，不以慢卡数量直接划分。

### (2) 并行策略

1. 当异常设备跨多个独立拓扑区域分布，且 `局部 PP 隔离收益 < 多个慢 stage 与流水线开销`、`满卡算力收益 > replica 等待与通信成本` 时，使用全部可用卡；`PP` 取满足模型约束的最小可行值，优先取 `PP=1`；在 `PP × TP × DP = active_gpu` 和完整拓扑约束下，按 `TP:DP=2:1` 求解整数 `TP` 和 `DP`，`MBN` 取与最小 PP 匹配的最小可行值；每个 TP group 放在带宽最高的局部拓扑内。异常卡映射再按 replica 分布选择：
   - **replica 不对称**：各 replica 的异常设备结构或预测耗时不一致时，按预测执行时间调整异常卡映射，减少快 replica 等待慢 replica。
   - **replica 可对称**：异常设备能够按数量、速度和位置对称分配，且 `副本对称收益 > 多个 PP stage 的隔离收益` 时，使各 DP replica 中的异常设备数量、速度和相对位置保持一致。

### (3) 原因

1. **共同参数**：慢卡跨多个区域时，深 PP 容易形成多个慢 stage，因此 `PP` 取最小值以避免多个 stage 瓶颈和 pipeline bubble；`TP:DP=2:1` 保留成熟经验中的并行比例，再根据可用卡数求解完整 TP group 和 DP replica；最小 PP 不需要更多微批填充深流水线，因此 `MBN` 也取最小可行值。
   - **replica 不对称**：各 replica 的异常结构或预计耗时不一致时，固定位置映射会产生快慢 replica 等待；按预测执行时间调整异常卡位置可以缩小 replica step-time 差异。
   - **replica 可对称**：异常卡能够按数量、速度和位置对称分配时，使各 replica 的异常结构一致，可以让慢卡影响在副本间近似同步，减少由结构差异造成的等待。高频 TP 通信仍留在带宽最高的局部拓扑内。^[raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md] ^[raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md]

### (4) 场景案例

- **两慢卡非对称均衡**：[场景来源](../raw/articles/two-slow-gpu-deployment-analysis-2026-07-22.md)在两张慢卡跨亲和组时，使用 `PP=1, TP=8, DP=4, MBN=1`，重点处理快慢 replica 等待。
- **四慢卡对称副本**：[场景来源](../raw/articles/four-slow-gpu-deployment-analysis-2026-07-22.md)在四张速度接近的慢卡一节点一张时，使用相同参数构造慢卡结构对称的 DP replica。
- **五慢卡 2/1/1/1 待验证证据**：[场景来源](../raw/articles/five-slow-gpu-2-1-1-1-evolve-analysis-2026-07-30.md)的当前已仿真候选最优为 `PP=16, TP=1, DP=2, MBN=64`，但只覆盖 `65/873` 个候选，且两个 replica 的慢卡数为 1/4、不满足现有对称映射分支；知识库所有者已撤回正式准入，因此恢复为 `KEEP_FOR_VALIDATION`，不改变上面的成熟并行策略。
