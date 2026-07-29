from __future__ import annotations

import unittest
import copy
from pathlib import Path

from DagGenerator.generate_dag import build_dag, load_config
from ValueSim.simulator_v2.adapter import _prepare_dag, config_from_dagbuilder, simulate_dag


ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "config" / "config.py"


class DagBuilderAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = load_config(CONFIG)
        cls.dag = build_dag(
            cls.config,
            CONFIG,
            ROOT / "outputs" / "_adapter_test.html",
            ROOT / "outputs" / "_adapter_test.json",
        )

    def test_runtime_config_is_translated_to_v2(self) -> None:
        translated = config_from_dagbuilder(self.config)
        self.assertEqual(translated["parallel"], {"tp_size": 4, "pp_size": 2, "dp_size": 4, "ep_size": 1, "cp_size": 1})
        self.assertFalse(translated["profiling"]["enabled"])
        self.assertEqual(translated["topology"]["total_devices"], 32)
        self.assertEqual(translated["simulation_flags"]["ep"], 0)
        self.assertTrue(translated["algorithms"]["compute"]["tp_communication"]["enabled"])

    def test_slow_rank_override_reaches_v2_topology(self) -> None:
        config = copy.deepcopy(self.config)
        config["value_sim_config"]["device_overrides"] = {
            3: {
                "compute_tflops": 156.0,
                "status": "slow",
                "note": "fixed 0.5x",
            }
        }
        translated = config_from_dagbuilder(config)
        self.assertEqual(
            translated["topology"]["device_overrides"][3],
            {
                "compute_tflops": 156.0,
                "status": "slow",
                "note": "fixed 0.5x",
            },
        )

    def test_pp_payload_is_already_per_tp_lane(self) -> None:
        prepared = _prepare_dag(self.dag, self.config)
        pp_nodes = [
            node
            for node in prepared["nodes"]
            if node["task_kind"] in {"pp_forward_send", "pp_backward_send"}
        ]
        self.assertTrue(pp_nodes)
        self.assertEqual({node["payload_scope"] for node in pp_nodes}, {"per_rank_send"})

    def test_generated_dag_runs_with_v2_and_keeps_topology(self) -> None:
        weighted, rows = simulate_dag(self.dag, self.config)
        self.assertEqual(len(weighted["nodes"]), len(self.dag["nodes"]))
        self.assertEqual(len(weighted["edges"]), len(self.dag["edges"]))
        self.assertTrue(weighted["value_sim_v2"]["topology_unchanged"])
        self.assertEqual(len(rows), len(self.dag["nodes"]))
        self.assertEqual(
            {row["duration_source"] for row in rows},
            {"zero_control", "numerical"},
        )
        compute_rows = [row for row in rows if row["category"] == "compute"]
        self.assertTrue(compute_rows)
        self.assertTrue(all(row["detail"]["tp_comm_s"] > 0 for row in compute_rows))

    def test_slow_rank_increases_affected_compute_nodes(self) -> None:
        slow_config = copy.deepcopy(self.config)
        slow_config["value_sim_config"]["device_overrides"] = {
            0: {"compute_tflops": 156.0, "status": "slow"}
        }
        _baseline_weighted, baseline_rows = simulate_dag(self.dag, self.config)
        _slow_weighted, slow_rows = simulate_dag(self.dag, slow_config)
        baseline_by_id = {row["node_id"]: row for row in baseline_rows}
        affected = [
            row
            for row in slow_rows
            if row["category"] == "compute" and 0 in row["rank_group"]
        ]
        self.assertTrue(affected)
        self.assertTrue(
            all(
                row["duration_s"] > baseline_by_id[row["node_id"]]["duration_s"]
                for row in affected
            )
        )


if __name__ == "__main__":
    unittest.main()
