# ScoreExpert 部署经验 Wiki

> 面向 GPU 部署选型的互链知识目录。
> Last updated: 2026-07-19 | Total pages: 7

## 当前状态

已导入 3 份原始分析来源，形成 4 张决策经验卡，当前全部属于**延迟优先型**；稳定优先型目前没有经验卡。延迟优先入口下再按 **同构基线、局部异构、分布式异构** 选择场景知识。标准卡与单慢卡为 `unverified`；两张、四张慢卡为 `partially_supported`。当前没有 `active` 正式经验。

四场景统一源文档、初始库和两次增量更新的筛选前后过程见 [经验库增量演示](outputs/experience-evolution-demo/README.md)。演示快照位于 `outputs/`，不计入正式知识页总数。

## Entities

- [[scoreexpert]] — ScoreExpert 部署经验的领域入口和当前知识状态。

## 部署经验

- [[deployment-objective-knowledge-framework]] — 定义“优化目标 × 异构范围”二维格式，给出延迟/稳定两个入口下三类知识的固定字段、当前案例和证据缺口。
- [[latency-first-experience-summary]] — 汇总当前全部延迟优先型经验：同构基线、单慢卡局部隔离、两慢卡均衡和四慢卡对称副本，以及跨场景切换与延迟验收规则。

### 同构基线

- [[homogeneous-32gpu-score-candidate]] — 标准 32 卡：严格匹配 v10 score 时以 `PP=1,TP=8,DP=4,MBN=1` 开始验证，不把 `2:1` 外推为通用规律。

### 局部异构

- [[single-slow-gpu-isolation]] — 单慢卡：以 `PP=16,TP=2,DP=1,MBN=64` 测试局部隔离；64 是搜索上界候选。

### 分布式异构

- [[two-slow-gpu-distributed-balance]] — 两张慢卡跨亲和组：以无 PP、节点内 `TP=8`、节点间 `DP=4` 测试从隔离到均衡的切换。
- [[four-slow-gpu-symmetric-replicas]] — 四张慢卡一节点一张：构造四个慢卡结构一致的 DP replica，优先降低 replica skew。

## Comparisons

_暂无页面。_
