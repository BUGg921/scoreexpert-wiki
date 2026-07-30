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
from dagbuilder_evolve.reporting import _load_wiki_experience_coverage
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
            self.assertTrue((run_dir / "scenario_analysis.md").exists())

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
                '### <span style="color:blue;">(1) 并行策略</span>',
                analysis,
            )
            self.assertIn(
                '### <span style="color:blue;">(2) 原因</span>',
                analysis,
            )
            self.assertIn(
                '### <span style="color:blue;">(3) 结论边界</span>',
                analysis,
            )
            self.assertIn("参数按以下规则求解", analysis)
            self.assertIn("PP=active_gpu/(TP×DP)", analysis)
            self.assertIn("1. **", analysis)
            self.assertIn("双慢卡拓扑差集", analysis)
            self.assertIn("慢卡数量差集", analysis)
            self.assertIn("P0—补齐双慢卡拓扑对照", analysis)
            self.assertIn("从经验库目标总览读取", analysis)
            self.assertIn("不读取用户口头清单", analysis)
            self.assertIn("不在同一批同时改变慢卡速度", analysis)
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
