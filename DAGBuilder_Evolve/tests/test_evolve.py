from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from dagbuilder_evolve.config import ScenarioConfig, load_scenario
from dagbuilder_evolve.engine import EvolutionEngine
from dagbuilder_evolve.evaluator import StrategyEvaluator, estimate_memory_gb
from dagbuilder_evolve.programs import SEED_SOURCES, score_program, validate_source
from dagbuilder_evolve.reporting import (
    _load_campaign_report_coverage,
    _load_wiki_experience_coverage,
    _validate_codex_experience_summary,
    write_codex_scenario_analysis,
)
from dagbuilder_evolve.strategy import communication_groups, enumerate_strategies, rank_mapping


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "configs" / "scenario_7b_32g.py"


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_scenario(SCENARIO)
        cls.catalog = enumerate_strategies(cls.config)

    def test_default_catalog_has_873_semantic_candidates(self) -> None:
        self.assertEqual(len(self.catalog), 873)
        self.assertEqual(len({item.signature for item in self.catalog}), 873)
        self.assertTrue(any(estimate_memory_gb(item, self.config)["oom"] for item in self.catalog))
        self.assertTrue(any(not estimate_memory_gb(item, self.config)["oom"] for item in self.catalog))

    def test_pp_major_mapping_and_domains(self) -> None:
        strategy = next(
            item for item in self.catalog
            if (item.pp, item.tp, item.dp, item.micro_batch_num) == (2, 4, 4, 1)
        )
        mapping = rank_mapping(strategy)
        self.assertEqual([item["global_rank"] for item in mapping], list(range(32)))
        groups = communication_groups(strategy)
        self.assertEqual(groups["tp"][0], [0, 1, 2, 3])
        self.assertEqual(groups["dp"][0], [0, 4, 8, 12])
        self.assertEqual(groups["pp"][0], [0, 16])

    def test_program_sandbox_and_full_catalog_scoring(self) -> None:
        feasible = [item for item in self.catalog if not estimate_memory_gb(item, self.config)["oom"]]
        ranking, complexity = score_program(
            SEED_SOURCES["balanced_generalist"], feasible, self.config, 5.0
        )
        self.assertEqual(len(ranking), len(feasible))
        self.assertGreater(complexity, 0)
        with self.assertRaises(ValueError):
            validate_source("import os\ndef score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):\n return 0")

    def test_wiki_experience_coverage_comes_from_summary_links(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            raw = root / "raw" / "articles"
            concepts.mkdir()
            raw.mkdir(parents=True)
            (raw / "two-slow-example.md").write_text(
                "两张慢卡分别位于两个亲和组，属于跨亲和组场景。\\n",
                encoding="utf-8",
            )
            summary = concepts / "latency-first-experience-summary.md"
            summary.write_text(
                "- **两慢卡经验**：[场景来源]"
                "(../raw/articles/two-slow-example.md)已形成成熟经验。\\n",
                encoding="utf-8",
            )
            coverage = _load_wiki_experience_coverage(summary)
            self.assertEqual(len(coverage), 1)
            self.assertEqual(coverage[0]["slow_count"], 2)
            self.assertEqual(coverage[0]["status"], "MATURE")
            self.assertEqual(
                coverage[0]["distribution_variant"], "cross_affinity"
            )

    def test_wiki_coverage_accepts_reviewed_link_and_ignores_future_suggestions(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            raw = root / "raw" / "articles"
            concepts.mkdir()
            raw.mkdir(parents=True)
            (raw / "five-slow-reviewed.md").write_text(
                "# 五慢卡 2/1/1/1\n"
                "## 实验场景\n共有5张慢卡，按节点2/1/1/1分布。\n"
                "## 最优解\n"
                "## 未仿真的场景\n建议继续仿真跨亲和组双慢卡。\n",
                encoding="utf-8",
            )
            summary = concepts / "latency-first-experience-summary.md"
            summary.write_text(
                "- **五慢卡 2/1/1/1 深 PP**：[审核后场景来源]"
                "(../raw/articles/five-slow-reviewed.md)已形成成熟经验。\n",
                encoding="utf-8",
            )
            coverage = _load_wiki_experience_coverage(summary)
            self.assertEqual(len(coverage), 1)
            self.assertEqual(coverage[0]["slow_count"], 5)
            self.assertEqual(coverage[0]["status"], "MATURE")
            self.assertIsNone(coverage[0]["distribution_variant"])

    def test_distribution_variant_recognizes_same_affinity_cross_node(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            concepts = root / "concepts"
            raw = root / "raw" / "articles"
            concepts.mkdir()
            raw.mkdir(parents=True)
            (raw / "two-slow-same-affinity.md").write_text(
                "共有2张慢卡。\n## 最优解\n",
                encoding="utf-8",
            )
            summary = concepts / "latency-first-experience-summary.md"
            summary.write_text(
                "- **同亲和组跨节点双慢卡**：[场景来源]"
                "(../raw/articles/two-slow-same-affinity.md)已形成成熟经验。\n",
                encoding="utf-8",
            )
            coverage = _load_wiki_experience_coverage(summary)
            self.assertEqual(
                coverage[0]["distribution_variant"],
                "same_affinity_different_nodes",
            )

    def test_campaign_coverage_comes_from_completed_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "round-2_scenario_analysis.md"
            report.write_text(
                "# 三慢卡场景\n## 实验场景\n共有3张慢卡，按节点2/1/0/0分布。\n"
                "## 最优解\n",
                encoding="utf-8",
            )
            value = self.config.to_dict()
            value["analysis"]["campaign"] = {
                "completed_report_paths": [str(report)]
            }
            config = ScenarioConfig.from_dict(value, source=SCENARIO)
            coverage = _load_campaign_report_coverage(config)
            self.assertEqual(len(coverage), 1)
            self.assertEqual(coverage[0]["slow_count"], 3)

    def test_scenario_json_roundtrip_normalizes_device_override_ranks(self) -> None:
        source = self.config.to_dict()
        source["topology"]["device_overrides"] = {
            7: {"compute_tflops": 156.0}
        }
        value = json.loads(json.dumps(source))
        self.assertTrue(all(isinstance(rank, str) for rank in value["topology"]["device_overrides"]))
        config = ScenarioConfig.from_dict(value, source=SCENARIO)
        self.assertTrue(all(isinstance(rank, int) for rank in config.topology["device_overrides"]))
        self.assertIn(7, config.topology["device_overrides"])

    def test_codex_experience_summary_enforces_evidence_boundaries(self) -> None:
        evidence = {
            "winner": {
                "strategy": {
                    "pp": 2,
                    "tp": 4,
                    "dp": 4,
                    "micro_batch_num": 16,
                },
                "latency_s": 4.2,
                "memory": {"estimated_total_gb": 12.0},
            },
            "placement": {
                "active_slow_ranks": [7],
                "affected_tp_group_count": 1,
                "total_tp_group_count": 8,
                "affected_pp_stage_count": 1,
                "total_pp_stage_count": 4,
                "affected_dp_replica_count": 1,
                "total_dp_replica_count": 2,
            },
            "one_dimension_neighbors": [{"latency_s": 4.3}],
            "search": {
                "evaluated_strategy_count": 70,
                "total_strategy_count": 873,
            },
            "real_training_evaluation": None,
        }
        valid = {
            "parallel_strategy": "根据当前映射，验证PP=2、TP=4、DP=4、MBN=16。",
            "reason_title": "场景专属推理",
            "reason_bullets": [
                "**场景**：慢卡影响1/8个TP group、1/4个PP stage和1/2个DP replica。",
                "**公式与仿真**：公式负责提名，仿真负责最终选择。",
                "**反例**：单变量邻居时延为4.300000，不能跳过对照。",
            ],
            "conclusion_boundaries": [
                "本轮评估70/873个候选，4.200000秒、12.000GB，只能称为当前已仿真候选最优。",
                "缺少真实训练Evaluation，不能视为生产验证。",
            ],
        }
        self.assertEqual(
            _validate_codex_experience_summary(valid, evidence), valid
        )
        invalid = copy.deepcopy(valid)
        invalid["parallel_strategy"] = "这是全局最优策略。"
        with self.assertRaises(ValueError):
            _validate_codex_experience_summary(invalid, evidence)
        invalid = copy.deepcopy(valid)
        invalid["parallel_strategy"] = "根据当前映射验证完整策略形状。"
        with self.assertRaises(ValueError):
            _validate_codex_experience_summary(invalid, evidence)
        invalid = copy.deepcopy(valid)
        invalid["conclusion_boundaries"][0] = (
            "本轮评估70/873个候选，只能称为当前已仿真候选最优。"
        )
        with self.assertRaises(ValueError):
            _validate_codex_experience_summary(invalid, evidence)

class IntegrationTests(unittest.TestCase):
    def test_single_strategy_numerical_evaluation_and_cache(self) -> None:
        config = load_scenario(SCENARIO)
        strategy = next(
            item for item in enumerate_strategies(config)
            if item.signature == "pp4_tp2_dp2_mb16_1f1b_rsag"
        )
        with tempfile.TemporaryDirectory() as directory:
            evaluator = StrategyEvaluator(config, Path(directory))
            first = evaluator.evaluate(strategy)
            second = evaluator.evaluate(strategy)
            self.assertEqual(first["status"], "pass")
            self.assertEqual(first, second)
            self.assertGreater(first["latency_s"], 0)
            artifact_dir = Path(first["artifact_dir"])
            dag = json.loads((artifact_dir / "dag.json").read_text(encoding="utf-8"))
            weighted = json.loads((artifact_dir / "weighted_dag.json").read_text(encoding="utf-8"))
            timings = json.loads((artifact_dir / "node_timings.json").read_text(encoding="utf-8"))
            self.assertEqual(len(dag["nodes"]), len(weighted["nodes"]))
            self.assertEqual(len(dag["edges"]), len(weighted["edges"]))
            self.assertTrue(
                any(
                    row["category"] == "compute"
                    and (
                        row["detail"].get("tp_duration_s", 0)
                        or row["detail"].get("tp_comm_non_overlapped_s", 0)
                    ) > 0
                    for row in timings
                )
            )
            self.assertTrue(
                any(
                    row["category"] == "dp"
                    and row["domain"] == "dp"
                    and len(row["rank_group"]) == strategy.dp
                    for row in timings
                )
            )

    def test_two_round_mock_evolution(self) -> None:
        base = load_scenario(SCENARIO)
        value = base.to_dict()
        value["search"]["nominations_per_program"] = 1
        value["evolution"]["migration_rounds"] = [2]
        with tempfile.TemporaryDirectory() as directory:
            value["output_root"] = directory
            config = ScenarioConfig.from_dict(value, source=SCENARIO)
            run_dir = Path(directory) / "mock"
            report = EvolutionEngine(config, run_dir, mock=True).run(2)
            self.assertEqual(report["total_strategy_count"], 873)
            self.assertGreaterEqual(report["evaluated_strategy_count"], 4)
            self.assertGreater(report["best"]["latency_s"], 0)
            self.assertTrue((run_dir / "checkpoint_latest.json").exists())
            self.assertTrue((run_dir / "deployment_experience.md").exists())
            self.assertTrue((run_dir / "best_score_program.py").exists())
            self.assertTrue((run_dir / "score_program_evidence.json").exists())
            self.assertFalse((run_dir / "scenario_analysis.md").exists())
            self.assertNotIn("codex_experience_summary", report)

            summary = {
                "parallel_strategy": (
                    "节点慢卡分布不对称时，当前候选为"
                    f"PP={report['best']['strategy']['pp']}、"
                    f"TP={report['best']['strategy']['tp']}、"
                    f"DP={report['best']['strategy']['dp']}、"
                    f"MBN={report['best']['strategy']['micro_batch_num']}；"
                    "应把完整并行策略与实际映射一起验证；"
                    "缺少单变量对照时，不把某一个并行维度单独推广为通用规则。"
                ),
                "reason_title": "不对称慢卡分布下的候选选择",
                "reason_bullets": [
                    (
                        "**数值**：胜者时延为"
                        f"{report['best']['latency_s']:.6f}，显存为"
                        f"{report['best']['memory']['estimated_total_gb']:.3f}GB。"
                    ),
                    "**公式与仿真**：公式负责提名候选，数值仿真按最长路径选择最终策略。",
                    (
                        "**单变量**："
                        + (
                            "邻居时延为"
                            f"{report['one_dimension_neighbors'][0]['latency_s']:.6f}。"
                            if report["one_dimension_neighbors"]
                            else "没有单变量邻居，只保留完整策略层面的证据。"
                        )
                    ),
                ],
                "conclusion_boundaries": [
                    (
                        f"本轮评估{report['evaluated_strategy_count']}/"
                        f"{report['total_strategy_count']}个候选，结论只是"
                        "当前已仿真候选最优。"
                    ),
                    "缺少真实训练Evaluation，不能视为生产验证。",
                ],
            }
            write_codex_scenario_analysis(config, run_dir, summary)
            report = json.loads(
                (run_dir / "final_report.json").read_text(encoding="utf-8")
            )
            self.assertTrue((run_dir / "scenario_analysis.md").exists())
            self.assertEqual(report["codex_experience_summary"], summary)

            formula = (run_dir / "best_score_program.py").read_text(encoding="utf-8")
            self.assertIn("def score_strategy", formula)
            evidence = json.loads(
                (run_dir / "score_program_evidence.json").read_text(encoding="utf-8")
            )
            experience = json.loads(
                (run_dir / "deployment_experience.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                experience["recommended_strategy"], report["best"]["strategy"]
            )
            self.assertEqual(experience["score_evidence"], evidence)
            self.assertIn("score_derived", experience["reasoning"])
            self.assertIn("simulation_derived", experience["reasoning"])
            self.assertIn(
                evidence["attribution"],
                {
                    "direct_evaluation_nomination",
                    "top8_ranked",
                    "fallback_best_program",
                },
            )

            analysis = (run_dir / "scenario_analysis.md").read_text(encoding="utf-8")
            headings = [line for line in analysis.splitlines() if line.startswith("## ")]
            self.assertEqual(
                headings,
                [
                    "## 实验场景",
                    "## 最优解",
                    "## 打分策略代码",
                    "## 经验总结",
                    "## 未仿真的场景",
                    "## 下一步仿真建议",
                ],
            )
            self.assertNotIn('## <span style="color:red;">任务</span>', analysis)
            self.assertIn(
                "### (1) 并行策略",
                analysis,
            )
            self.assertIn(
                "### (2) 原因",
                analysis,
            )
            self.assertIn(
                "### (3) 结论边界",
                analysis,
            )
            self.assertIn("节点慢卡分布", analysis)
            self.assertIn("公式与仿真", analysis)
            self.assertIn("当前已仿真候选最优", analysis)
            self.assertNotIn("当前实例得到", analysis)
            self.assertNotIn("具体Rank映射为", analysis)
            self.assertNotIn("formula candidate rank", analysis)
            self.assertIn("1. **", analysis)
            self.assertIn("双慢卡拓扑差集", analysis)
            self.assertIn("慢卡数量差集", analysis)
            self.assertRegex(
                analysis,
                r"P0—(?:补齐)?双慢卡拓扑对照",
            )
            self.assertTrue(
                "三类拓扑均已覆盖，无需重复仿真" in analysis
                or "优先仿真" in analysis
            )
            self.assertIn("从经验库目标总览读取", analysis)
            self.assertIn("不读取用户口头清单", analysis)
            self.assertIn("不在同一批同时改变慢卡速度", analysis)
            self.assertNotIn("优先仿真无", analysis)
            self.assertNotIn("补齐无张慢卡", analysis)
            self.assertIn("codex_experience_summary", report)
            self.assertTrue(
                (run_dir / "experience_reasoning_evidence.json").exists()
            )
            database = json.loads(
                (run_dir / "program_database.json").read_text(encoding="utf-8")
            )
            self.assertTrue(
                any(
                    record["evaluated_nominations"]
                    and record["evaluated_nomination_ranks"]
                    for record in database["records"].values()
                    if record["origin"] != "migration"
                )
            )
            self.assertTrue(
                all(
                    not record["evaluated_nominations"]
                    for record in database["records"].values()
                    if record["origin"] == "migration"
                )
            )


if __name__ == "__main__":
    unittest.main()
