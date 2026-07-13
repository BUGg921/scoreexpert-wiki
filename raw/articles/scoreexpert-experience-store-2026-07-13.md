---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/experiences.json
ingested: 2026-07-13
sha256: b10df6c1fb947af954790b50f4828f9962c3dd467eac923d3dd86d5f6c6c242e
original_sha256: 5b2d812e1f034b3344fd9fb0da887ecdd0dd4e4a1fc3e4de51f8d4425c28b505
---

# 原始来源：ScoreExpert 正式经验库

> 这是从 `/Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/experiences.json` 于 2026-07-13 导入的不可变快照。原文件 SHA-256：`5b2d812e1f034b3344fd9fb0da887ecdd0dd4e4a1fc3e4de51f8d4425c28b505`。

```json
{
  "schema_version": "2",
  "domain": "scoreexpert_deployment",
  "experiences": [
    {
      "id": "exp_normal_32g_homogeneous_baseline",
      "domain": "scoreexpert_deployment",
      "scenario": {
        "total_gpus": 32,
        "gpus_per_node": 8,
        "affinity_group_size": 16,
        "allow_cross_node_tp": false,
        "slow_gpus": {
          "count": 0,
          "ids": [],
          "speed_ratio": null,
          "distribution": "none"
        },
        "model": {
          "layers": null,
          "global_batch": null,
          "memory_pressure": "unknown"
        },
        "search_space": {
          "pp": [1, 2, 4, 8, 16],
          "tp": [1, 2, 4, 8],
          "dp": [1, 2, 4, 8],
          "mbn": [1, 2, 4, 8, 16, 32, 64]
        }
      },
      "recommendation": {
        "strategy": {
          "pp": 1,
          "tp": 8,
          "dp": 4,
          "mbn": 1
        },
        "rule": "32卡/8卡每节点/无慢卡且TP限制在节点内时，把PP=1,TP=8,DP=4,MBN=1作为第一候选；该候选消除无收益PP bubble，用节点内TP吃满单节点，并用DP补齐全机。"
      },
      "evidence": {
        "score_evidence": [
          "PP=1无pipeline bubble；当前score没有显式深PP补偿项。",
          "MBN=1没有二次MBN惩罚；PP=1后继续增大MBN不再降低bubble。",
          "满卡约束下TP*DP=32，且在TP<=8时，TP/DP耦合项偏向TP=8,DP=4；记录中的候选比较显示TP=8,DP=4优于TP=4,DP=8。"
        ],
        "topology_evidence": [
          "TP=8正好落在8卡单节点高速通信域内，不依赖跨节点TP。",
          "DP=4用于跨节点扩展吞吐并补齐32张卡。"
        ],
        "evaluation_evidence": [],
        "counterexamples": [
          {
            "strategy": {
              "pp": 1,
              "tp": 4,
              "dp": 8,
              "mbn": 1
            },
            "reason": "同样满卡，但TP/DP耦合项较弱，且DP更大可能提高同步成本。"
          },
          {
            "strategy": {
              "pp": 2,
              "tp": 4,
              "dp": 4,
              "mbn": 4
            },
            "reason": "引入PP bubble和更大MBN，需要显存或overlap收益才能抵消。"
          },
          {
            "strategy": {
              "pp": 16,
              "tp": 2,
              "dp": 1,
              "mbn": 64
            },
            "reason": "单慢卡隔离候选；无慢卡同构场景下不应直接替代基线。"
          }
        ]
      },
      "boundary": {
        "applies_when": [
          "32卡、每节点8卡、每16卡一个亲和组或相近拓扑。",
          "无慢卡，或当前score和输入没有建模慢卡异构。",
          "TP=8能稳定映射在单节点内。",
          "模型显存允许PP=1，MBN=1不违反batch或吞吐要求。"
        ],
        "fails_when": [
          "模型显存不足，必须引入PP或更高TP。",
          "DP=4跨节点all-reduce成为主瓶颈。",
          "慢卡、慢网络、层数不均衡或跨亲和组成本覆盖同构基线收益。",
          "搜索器允许TP>8但没有tp_cross硬过滤或惩罚。"
        ],
        "missing_evidence": [
          "真实micro定义和取值范围。",
          "显存可行性和DP all-reduce latency。",
          "跨亲和组带宽对DP同步的实际影响。",
          "加入慢卡、慢网络或更大模型后的策略翻转边界。"
        ]
      },
      "metadata": {
        "source": "manual_import_project_experience",
        "source_ids": [
          "src_scenario_example_001",
          "src_legacy_normal_32g_reports"
        ],
        "source_files": [
          "experience.md",
          "32卡基线_score_strategy_分析.md"
        ],
        "confidence": "medium",
        "update_type": "add",
        "notes": "Imported as a structured seed record; not automatically parsed from reports."
      },
      "lifecycle": {
        "status": "active",
        "version": 1,
        "supersedes": [],
        "superseded_by": null
      }
    },
    {
      "id": "exp_single_slow_gpu_local_isolation",
      "domain": "scoreexpert_deployment",
      "scenario": {
        "total_gpus": 32,
        "gpus_per_node": 8,
        "affinity_group_size": 16,
        "allow_cross_node_tp": false,
        "slow_gpus": {
          "count": 1,
          "ids": [7],
          "speed_ratio": 0.5,
          "distribution": "single_local"
        },
        "model": {
          "layers": null,
          "global_batch": null,
          "memory_pressure": "unknown"
        },
        "search_space": {
          "pp": [1, 2, 4, 8, 16],
          "tp": [1, 2, 4, 8],
          "dp": [1, 2, 4],
          "mbn": [1, 2, 4, 8, 16, 32, 64]
        }
      },
      "recommendation": {
        "strategy": {
          "pp": 16,
          "tp": 2,
          "dp": 1,
          "mbn": 64
        },
        "rule": "32卡/8卡每节点/1张半速慢卡为局部异常时，把PP=16,TP=2,DP=1,MBN=64作为隔离慢卡候选；用小TP限制慢卡同步污染范围，用低DP避免多副本straggler同步，用深PP吃满32卡，并用大MBN填充pipeline。"
      },
      "evidence": {
        "score_evidence": [
          "DP=1避免DP成本项或dp_overhead扩散，适合慢卡场景下的同步风险控制。",
          "在DP=1且偏好满32卡时，PP*TP=32；TP=2与PP=16形成低TP成本和不过深PP bubble之间的折中。",
          "MBN=64能稀释深PP bubble，但它位于搜索空间上界，必须标注为边界候选而非物理必然最优。"
        ],
        "topology_evidence": [
          "TP=2把慢卡影响限制在2卡TP group内，避免TP=8时拖慢整个节点内TP group。",
          "DP=1避免多个DP replica因为一个慢replica产生同步等待。",
          "PP=16把32卡切成16个pipeline stage，每个stage 2卡，使单个慢卡更可能表现为局部stage瓶颈。"
        ],
        "evaluation_evidence": [
          "已有单慢卡分析将PP=16,TP=2,DP=1,MBN=64作为关键最优/高优先候选；仍需要后续真实Evaluation字段结构化补齐。"
        ],
        "counterexamples": [
          {
            "strategy": {
              "pp": 1,
              "tp": 8,
              "dp": 4,
              "mbn": 1
            },
            "reason": "同构基线候选；如果慢卡不再是局部异常，或多慢卡分布式异构更适合均衡replica，该候选可能回到优先级最高。"
          },
          {
            "strategy": {
              "pp": 4,
              "tp": 8,
              "dp": 1,
              "mbn": 64
            },
            "reason": "高TP候选可能在部分scorer中靠前，但TP=8会扩大单慢卡同步污染范围，需要Evaluation比较。"
          },
          {
            "strategy": {
              "pp": 8,
              "tp": 2,
              "dp": 2,
              "mbn": 64
            },
            "reason": "保留小TP但引入DP同步，可能重新放大慢卡straggler风险。"
          }
        ]
      },
      "boundary": {
        "applies_when": [
          "32卡、每节点8卡、每16卡一个亲和组或相近拓扑。",
          "只有1张慢卡，且慢卡是局部单点异常，例如第7张卡半速。",
          "跨节点TP不允许或代价很高。",
          "候选空间允许PP=16、TP=2、DP=1、MBN=64。"
        ],
        "fails_when": [
          "慢卡扩展为2张或更多，并跨亲和组或跨节点分散。",
          "深PP形成多个慢stage，或stage time不均衡超过隔离收益。",
          "MBN上界降低，导致深PP bubble无法被足够稀释。",
          "模型层数不能支撑PP=16的均衡切分，或显存/batch约束不允许MBN=64。"
        ],
        "missing_evidence": [
          "真实stage time、TP group straggler、DP replica skew。",
          "MBN=32/64/128扫描以确认上界效应。",
          "慢速倍率从轻微慢到极慢时的策略翻转边界。",
          "单慢卡位置落入不同TP group或不同pipeline stage时的差异。"
        ]
      },
      "metadata": {
        "source": "manual_import_project_experience",
        "source_ids": [
          "src_scenario_single_slow_gpu_001",
          "src_legacy_single_slow_gpu_reports"
        ],
        "source_files": [
          "experience.md",
          "Scoring strategy analysis_快慢卡.md"
        ],
        "confidence": "medium",
        "update_type": "add",
        "notes": "Imported as a structured seed record; MBN=64 is explicitly marked as a search-boundary candidate."
      },
      "lifecycle": {
        "status": "active",
        "version": 1,
        "supersedes": [],
        "superseded_by": null
      }
    }
  ]
}
```
