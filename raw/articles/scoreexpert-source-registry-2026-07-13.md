---
source_url:
source_path: /Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/sources.json
ingested: 2026-07-13
sha256: c4550da9eae3d91201967df653249f2c7bb746d98dbe374c44c07ee5afb14245
original_sha256: 170f8dc37d032d6b280a4af0fee4b41fa19acaece3a22d714021c84f510ab7d1
---

# 原始来源：ScoreExpert 来源登记表

> 这是从 `/Users/cookie/Documents/clc/DAG_build/scoreexpert_kb/data/sources.json` 于 2026-07-13 导入的不可变快照。原文件 SHA-256：`170f8dc37d032d6b280a4af0fee4b41fa19acaece3a22d714021c84f510ab7d1`。

```json
{
  "schema_version": "1",
  "sources": [
    {
      "id": "src_legacy_normal_32g_reports",
      "kind": "report",
      "title": "同构 32 卡种子经验历史报告",
      "locator": [
        "experience.md",
        "32卡基线_score_strategy_分析.md"
      ],
      "sha256": null,
      "captured_at": null,
      "verification_status": "unverified_legacy",
      "immutable": false,
      "notes": "历史人工导入来源尚未在本知识库内保存不可变快照。"
    },
    {
      "id": "src_legacy_single_slow_gpu_reports",
      "kind": "report",
      "title": "单慢卡种子经验历史报告",
      "locator": [
        "experience.md",
        "Scoring strategy analysis_快慢卡.md"
      ],
      "sha256": null,
      "captured_at": null,
      "verification_status": "unverified_legacy",
      "immutable": false,
      "notes": "历史人工导入来源尚未在本知识库内保存不可变快照。"
    },
    {
      "id": "src_report_two_slow_cross_affinity_analysis_20260709",
      "kind": "report",
      "title": "两张慢卡跨亲和组分析报告",
      "path": "data/updates/two_slow_cross_affinity_analysis_rerun_20260709_233028.md",
      "sha256": "9fbf1c2789ff43ba108929fab9828a73537031d618be812f6d360665af353d39",
      "captured_at": "2026-07-13T10:27:33+08:00",
      "verification_status": "hash_verified",
      "immutable": true,
      "notes": "作为冲突原因假设和仿真计划的来源，不等同于 Evaluation 证据。"
    },
    {
      "id": "src_scenario_example_001",
      "kind": "scenario",
      "title": "同构 32 卡示例场景",
      "path": "data/scenarios/example_scenario.json",
      "sha256": "50fa29b4a36180b9289f7e2a4e3565446e5363a34e6b89d4d808cf0bc03c91c1",
      "captured_at": "2026-07-12T00:00:00+08:00",
      "verification_status": "hash_verified",
      "immutable": true,
      "notes": "用于定位同构基线经验的结构化场景输入。"
    },
    {
      "id": "src_scenario_four_slow_one_per_node_20260713",
      "kind": "scenario",
      "title": "32卡四节点各一张慢卡场景",
      "path": "data/scenarios/four_slow_one_per_node_scenario_20260713_105112.json",
      "sha256": "58adbb34fa031214ae7d845442a88f879276237968db6e07d26f42acc92f0a09",
      "captured_at": "2026-07-13T10:51:45+08:00",
      "verification_status": "hash_verified",
      "immutable": true,
      "notes": ""
    },
    {
      "id": "src_scenario_single_slow_gpu_001",
      "kind": "scenario",
      "title": "单张半速慢卡场景",
      "path": "data/scenarios/single_slow_gpu_scenario.json",
      "sha256": "3b41226c4640bb737c6f8fe0ec1c8558cec2740a51330f15056ff312003ca656",
      "captured_at": "2026-07-12T00:00:00+08:00",
      "verification_status": "hash_verified",
      "immutable": true,
      "notes": "用于定位单慢卡隔离经验的结构化场景输入。"
    },
    {
      "id": "src_scenario_two_slow_cross_affinity_001",
      "kind": "scenario",
      "title": "两张慢卡跨亲和组场景",
      "path": "data/scenarios/two_slow_cross_affinity_scenario.json",
      "sha256": "460fd2fb0b24016a68ebc6ea7508c7d510ff38c50ba8f2c74e6126f724a4417a",
      "captured_at": "2026-07-13T10:27:33+08:00",
      "verification_status": "hash_verified",
      "immutable": true,
      "notes": "慢卡位置、速度倍率和 rank mapping 仍然缺失，不能当作完整 Evaluation 场景。"
    }
  ]
}
```
