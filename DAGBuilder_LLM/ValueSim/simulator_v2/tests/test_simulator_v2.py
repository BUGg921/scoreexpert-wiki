from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from ValueSim.simulator_v2.config import load_config, validate_config
from ValueSim.simulator_v2.engine import SimulationEngine, load_json, run_simulation
from ValueSim.simulator_v2.simulators.compute import simulate_compute
from ValueSim.simulator_v2.simulators.dp import simulate_dp
from ValueSim.simulator_v2.simulators.ep import simulate_ep
from ValueSim.simulator_v2.simulators.pp import simulate_pp
from ValueSim.simulator_v2.topology import LinkUnavailableError, Topology


ROOT = Path(__file__).resolve().parents[3]
CONFIG_30B = ROOT / "ValueSim" / "simulator_v2" / "config" / "config_30b.py"
DAG_30B = ROOT / "outputs" / "dag_30b_coarse_20260710_112015" / "dag.json"


def small_topology_config() -> tuple[dict, dict]:
    topology = {
        "total_devices": 8,
        "devices_per_server": 2,
        "servers_per_affinity_group": 2,
        "default_compute_tflops": 300.0,
        "device_compute_tflops": {1: 100.0},
        "domains": {
            "tp": {"size": 2, "stride": 1},
            "ep": {"size": 4, "stride": 2},
        },
    }
    network = {
        "bandwidth_unit_bits": 1e9,
        "hccs_intra_server": {"bandwidth_gbps": 400.0, "efficiency": 1.0, "latency_s": 1e-6},
        "hccs_inter_server": {"bandwidth_gbps": 200.0, "efficiency": 1.0, "latency_s": 2e-6},
        "roce": {"bandwidth_gbps": 100.0, "efficiency": 1.0, "latency_s": 3e-6},
        "hbm": {"bandwidth_gbps": 800.0, "efficiency": 1.0, "latency_s": 0.0},
    }
    return topology, network


class TopologyTests(unittest.TestCase):
    def test_30b_physical_and_strided_domains(self) -> None:
        config = load_config(CONFIG_30B)
        topology = Topology(config["topology"], config["network"])
        self.assertEqual(topology.server_count, 8)
        self.assertEqual(topology.device(0).affinity_group_id, 0)
        self.assertEqual(topology.device(31).affinity_group_id, 0)
        self.assertEqual(topology.device(32).affinity_group_id, 1)
        self.assertEqual(topology.group("dp_cp", 0), tuple(range(0, 128, 4)))
        self.assertEqual(topology.group("dp_ep", 0), (0, 32, 64, 96))
        self.assertEqual(topology.link_kind(0, 4), "hccs_intra_server")
        self.assertEqual(topology.link_kind(0, 16), "hccs_inter_server")
        self.assertEqual(topology.link_kind(0, 32), "roce")
        resolved = topology.to_dict()
        self.assertEqual(
            resolved["summary"],
            {
                "total_devices": 128,
                "server_count": 8,
                "affinity_group_count": 4,
                "devices_per_server": 16,
                "servers_per_affinity_group": 2,
                "devices_per_affinity_group": 32,
            },
        )
        self.assertEqual(resolved["affinity_groups"][0]["servers"][0]["ranks"], list(range(16)))

    def test_explicit_groups_and_invalid_partitions(self) -> None:
        topology_config, network = small_topology_config()
        topology_config["domains"]["explicit"] = {
            "size": 2,
            "groups": [[0, 2], [1, 3], [4, 6], [5, 7]],
        }
        topology = Topology(topology_config, network)
        self.assertEqual(topology.group("explicit", 2), (4, 6))
        invalid = copy.deepcopy(topology_config)
        invalid["domains"]["explicit"]["groups"][3] = [5, 6]
        with self.assertRaisesRegex(ValueError, "cover every rank exactly once"):
            Topology(invalid, network)
        invalid_stride = copy.deepcopy(topology_config)
        invalid_stride["domains"]["bad"] = {"size": 4, "stride": 3}
        with self.assertRaisesRegex(ValueError, "cannot fully partition"):
            Topology(invalid_stride, network)

    def test_device_and_link_overrides_and_precedence(self) -> None:
        topology_config, network = small_topology_config()
        topology_config["device_overrides"] = {
            3: {"compute_tflops": 75.0, "status": "slow", "note": "slow test card"}
        }
        topology_config["link_overrides"] = [
            {
                "scope": "server",
                "endpoints": [0, 0],
                "status": "slow",
                "bandwidth_gbps": 100.0,
            },
            {
                "scope": "device",
                "endpoints": [0, 1],
                "status": "slow",
                "bandwidth_gbps": 50.0,
                "latency_s": 9e-6,
                "note": "specific slow edge",
            },
            {
                "scope": "server",
                "endpoints": [0, 1],
                "status": "down",
                "note": "server link fault",
            },
        ]
        topology = Topology(topology_config, network)
        self.assertEqual(topology.device(3).compute_tflops, 75.0)
        self.assertEqual(topology.device(3).status, "slow")
        exact = topology.link(0, 1)
        self.assertEqual(exact.override_scope, "device")
        self.assertEqual(exact.bandwidth_bytes_s, 50e9 / 8)
        self.assertEqual(exact.latency_s, 9e-6)
        server_wide = topology.link(1, 0)
        self.assertEqual(server_wide.override_scope, "device")
        with self.assertRaisesRegex(LinkUnavailableError, "0->2.*server link fault"):
            topology.link(0, 2)

        invalid = copy.deepcopy(topology_config)
        invalid["link_overrides"][0].pop("bandwidth_gbps")
        with self.assertRaisesRegex(ValueError, "must provide"):
            Topology(invalid, network)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config_30b = load_config(CONFIG_30B)
        cls.topology_30b = Topology(cls.config_30b["topology"], cls.config_30b["network"])
        cls.dag_30b = load_json(DAG_30B)

    def test_30b_dp_regression_and_payloads(self) -> None:
        actual_us = {
            "dp_scalar_allreduce_loss_token_count": 55_851.276,
            "zero3_grad_rs_dp_cp_attention": 115_450.627,
            "zero3_grad_rs_dp_ep_moe": 141_612.269,
            "dp_cp_expert_load_allreduce": 600.392,
            "zero3_muon_grad_ag_dp_cp": 28_469.969,
            "zero3_next_step_param_prefetch_dp_cp": 38_217.364,
            "zero3_muon_grad_ag_dp_ep": 70_908.257,
            "zero3_next_step_param_prefetch_dp_ep": 70_903.097,
        }
        nodes = {node["node_id"]: node for node in self.dag_30b["nodes"]}
        for node_id, actual in actual_us.items():
            result = simulate_dp(nodes[node_id], self.config_30b, self.topology_30b)
            self.assertAlmostEqual(result.local_payload_bytes, float(nodes[node_id]["payload_bytes"]), delta=1e-6)
            error = (result.duration_s * 1e6 - actual) / actual
            if node_id != "dp_scalar_allreduce_loss_token_count":
                self.assertLessEqual(abs(error), 0.05, node_id)
        cp_rs = simulate_dp(nodes["zero3_grad_rs_dp_cp_attention"], self.config_30b, self.topology_30b)
        self.assertEqual(cp_rs.logical_steps, 114)
        self.assertAlmostEqual(cp_rs.wire_bytes_per_rank, 3_629_380_800.0, delta=1e-5)
        self.assertAlmostEqual(cp_rs.detail["local_copy_bytes_per_rank"], 3_746_457_600.0, delta=1e-5)
        self.assertAlmostEqual(cp_rs.detail["reduction_memory_bytes_per_rank"], 14_517_523_200.0, delta=1e-4)

    def test_pp_link_selection(self) -> None:
        topology_config, network = small_topology_config()
        topology = Topology(topology_config, network)
        config = {
            "parallel": {"tp_size": 1, "pp_size": 2},
            "algorithms": {
                "operations": {},
                "task_kinds": {
                    "pp_forward_send": {"payload_scope": "per_rank_send", "algorithm": "p2p"}
                },
            },
        }
        base = {"task_kind": "pp_forward_send", "payload_bytes": 1000, "payload_scope": "per_rank_send"}
        same_server = simulate_pp({**base, "node_id": "a", "src_ranks": [0], "dst_ranks": [1]}, config, topology)
        same_affinity = simulate_pp({**base, "node_id": "b", "src_ranks": [0], "dst_ranks": [2]}, config, topology)
        cross_affinity = simulate_pp({**base, "node_id": "c", "src_ranks": [0], "dst_ranks": [4]}, config, topology)
        self.assertEqual(same_server.detail["critical_lane"]["link_kind"], "hccs_intra_server")
        self.assertEqual(same_affinity.detail["critical_lane"]["link_kind"], "hccs_inter_server")
        self.assertEqual(cross_affinity.detail["critical_lane"]["link_kind"], "roce")
        self.assertLess(same_server.duration_s, same_affinity.duration_s)
        self.assertLess(same_affinity.duration_s, cross_affinity.duration_s)

    def test_slow_and_failed_links_affect_only_used_paths(self) -> None:
        topology_config, network = small_topology_config()
        config = {
            "parallel": {"tp_size": 1, "pp_size": 2},
            "algorithms": {
                "operations": {},
                "task_kinds": {
                    "pp_forward_send": {"payload_scope": "per_rank_send", "algorithm": "p2p"}
                },
            },
        }
        node = {
            "node_id": "pp",
            "task_kind": "pp_forward_send",
            "payload_bytes": 1_000_000,
            "payload_scope": "per_rank_send",
            "src_ranks": [0],
            "dst_ranks": [1],
        }
        baseline = simulate_pp(node, config, Topology(topology_config, network))
        slow_config = copy.deepcopy(topology_config)
        slow_config["link_overrides"] = [
            {
                "scope": "device",
                "endpoints": [0, 1],
                "status": "slow",
                "bandwidth_gbps": 20.0,
                "latency_s": 20e-6,
            }
        ]
        slow = simulate_pp(node, config, Topology(slow_config, network))
        self.assertGreater(slow.duration_s, baseline.duration_s)
        self.assertEqual(slow.detail["critical_lane"]["link_status"], "slow")

        failed_config = copy.deepcopy(topology_config)
        failed_config["link_overrides"] = [
            {
                "scope": "device",
                "endpoints": [0, 1],
                "status": "down",
                "note": "injected PP failure",
            }
        ]
        with self.assertRaisesRegex(LinkUnavailableError, "injected PP failure"):
            simulate_pp(node, config, Topology(failed_config, network))

        unrelated_config = copy.deepcopy(topology_config)
        unrelated_config["link_overrides"] = [
            {
                "scope": "device",
                "endpoints": [0, 1],
                "status": "down",
                "note": "not in EP domain",
            }
        ]
        ep_config = {
            "algorithms": {
                "operations": {
                    "ep_ag": {
                        "domain": "ep",
                        "collective": "all_gather",
                        "algorithm": "nhr",
                        "payload_scope": "full_tensor",
                        "payload_bytes": 64.0,
                    }
                },
                "task_kinds": {},
            }
        }
        result = simulate_ep(
            {"node_id": "ep_ag", "task_kind": "ep_allgather"},
            ep_config,
            Topology(unrelated_config, network),
        )
        self.assertGreater(result.duration_s, 0.0)

        dp_config = {
            "algorithms": {
                "operations": {
                    "dp_ag": {
                        "domain": "ep",
                        "collective": "all_gather",
                        "algorithm": "nhr",
                        "link_kind": "roce",
                        "payload_scope": "full_tensor",
                        "payload_bytes": 64_000_000.0,
                    }
                },
                "task_kinds": {},
            }
        }
        dp_node = {"node_id": "dp_ag", "task_kind": "dp"}
        base_dp = simulate_dp(dp_node, dp_config, Topology(topology_config, network))
        slow_dp_config = copy.deepcopy(topology_config)
        slow_dp_config["link_overrides"] = [
            {
                "scope": "device",
                "endpoints": [0, 2],
                "status": "slow",
                "bandwidth_gbps": 10.0,
            }
        ]
        slow_dp = simulate_dp(dp_node, dp_config, Topology(slow_dp_config, network))
        self.assertGreater(slow_dp.duration_s, base_dp.duration_s)
        self.assertIn(
            "slow",
            {item["status"] for item in slow_dp.detail["round_links"]},
        )

    def test_ep_alltoall_conservation(self) -> None:
        topology_config, network = small_topology_config()
        topology = Topology(topology_config, network)
        config = {
            "algorithms": {
                "operations": {
                    "ep_a2a": {
                        "domain": "ep",
                        "collective": "all_to_all",
                        "algorithm": "hierarchical_pairwise",
                        "payload_scope": "per_rank_send",
                    }
                },
                "task_kinds": {},
            }
        }
        node = {"node_id": "ep_a2a", "task_kind": "ep_alltoall_dispatch", "payload_bytes": 400.0}
        result = simulate_ep(node, config, topology)
        self.assertEqual(result.rank_group, (0, 2, 4, 6))
        self.assertEqual(result.logical_steps, 3)
        self.assertAlmostEqual(result.local_payload_bytes, 400.0)
        self.assertAlmostEqual(result.wire_bytes_per_rank, 300.0)
        self.assertIn("roce", {step["link_kind"] for step in result.detail["critical_steps"]})

        variable = {
            **node,
            "node_id": "ep_a2a_v",
            "peer_payload_matrix": [
                [100.0, 100.0, 100.0, 100.0],
                [50.0, 150.0, 100.0, 100.0],
                [100.0, 100.0, 150.0, 50.0],
                [150.0, 50.0, 100.0, 100.0],
            ],
        }
        variable_config = copy.deepcopy(config)
        variable_config["algorithms"]["operations"]["ep_a2a_v"] = {
            **variable_config["algorithms"]["operations"]["ep_a2a"],
            "collective": "all_to_all_v",
        }
        variable_result = simulate_ep(variable, variable_config, topology)
        self.assertTrue(variable_result.detail["variable_payload_matrix"])
        self.assertEqual(variable_result.logical_steps, 3)

    def test_ep_collective_payload_and_step_conservation(self) -> None:
        topology_config, network = small_topology_config()
        topology = Topology(topology_config, network)
        base_spec = {
            "domain": "ep",
            "algorithm": "nhr",
            "link_kind": "roce",
            "payload_scope": "full_tensor",
            "payload_bytes": 64.0,
        }
        config = {
            "algorithms": {
                "operations": {
                    "ep_ag": {**base_spec, "collective": "all_gather"},
                    "ep_rs": {**base_spec, "collective": "reduce_scatter"},
                    "ep_ar": {**base_spec, "collective": "all_reduce", "payload_scope": "replicated"},
                },
                "task_kinds": {},
            }
        }
        ag = simulate_ep({"node_id": "ep_ag", "task_kind": "ep_allgather"}, config, topology)
        rs = simulate_ep({"node_id": "ep_rs", "task_kind": "ep_reducescatter"}, config, topology)
        ar = simulate_ep({"node_id": "ep_ar", "task_kind": "ep_allreduce"}, config, topology)
        self.assertEqual((ag.logical_steps, rs.logical_steps, ar.logical_steps), (2, 2, 4))
        self.assertEqual((ag.wire_bytes_per_rank, rs.wire_bytes_per_rank, ar.wire_bytes_per_rank), (48.0, 48.0, 96.0))
        explicit_config = copy.deepcopy(config)
        explicit_config["algorithms"]["operations"]["ep_ag"]["bucket_sizes_bytes"] = [16.0, 48.0]
        explicit = simulate_ep({"node_id": "ep_ag", "task_kind": "ep_allgather"}, explicit_config, topology)
        self.assertEqual(explicit.bucket_count, 2)
        self.assertEqual(explicit.logical_steps, 4)
        self.assertEqual(explicit.wire_bytes_per_rank, 48.0)
        self.assertEqual(explicit.detail["bucket_sizes_bytes"], [16.0, 48.0])

    def test_slow_card_only_changes_numerical_compute(self) -> None:
        topology_config, network = small_topology_config()
        topology = Topology(topology_config, network)
        config = {
            "model": {
                "hidden_size": 16,
                "ffn_hidden_size": 32,
                "microbatch_size": 1,
                "sequence_length": 8,
                "num_layers": 1,
            },
            "parallel": {"tp_size": 2, "pp_size": 1},
            "algorithms": {"compute": {"efficiency": 1.0, "flops_scope": "global", "operation_flops": {}}},
        }
        node = {"node_id": "compute", "task_kind": "compute", "flops": 600e12, "ranks": [0, 1]}
        result = simulate_compute(node, config, topology)
        self.assertEqual(result.detail["critical_rank"], 1)
        self.assertAlmostEqual(result.duration_s, 3.0)


class EngineTests(unittest.TestCase):
    def test_source_flags_profile_coverage_and_full_output(self) -> None:
        config = load_config(CONFIG_30B)
        engine = SimulationEngine(config, config_path=CONFIG_30B)
        dag = load_json(DAG_30B)
        weighted, rows, critical = engine.simulate(dag)
        self.assertEqual(len(weighted["nodes"]), 23)
        self.assertEqual(len(weighted["edges"]), 22)
        self.assertAlmostEqual(critical["duration_s"], 3.756507228568254)
        sources = {row["duration_source"] for row in rows}
        self.assertEqual(sources, {"zero_control", "profiling", "numerical"})

        missing = copy.deepcopy(dag)
        target = next(node for node in missing["nodes"] if node["node_id"] == "compute0")
        target["profile_key"] = "not-present"
        target["node_id"] = "not-present"
        target["op_name"] = "not-present"
        target["label"] = "not-present"
        with self.assertRaisesRegex(ValueError, "Missing exact profiling entries"):
            engine.simulate(missing)

        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_simulation(
                DAG_30B,
                CONFIG_30B,
                run_name="integration",
                output_root=Path(temp_dir),
            )
            expected = {
                "weighted_dag.json",
                "node_timings.json",
                "topology.json",
                "resolved_config.json",
                "run_manifest.json",
                "summary.json",
                "summary.md",
            }
            self.assertEqual({path.name for path in result["output_dir"].iterdir()}, expected)
            output_dag = json.loads((result["output_dir"] / "weighted_dag.json").read_text(encoding="utf-8"))
            self.assertEqual((len(output_dag["nodes"]), len(output_dag["edges"])), (23, 22))

    def test_config_validation_rejects_non_binary_flag(self) -> None:
        config = load_config(CONFIG_30B)
        config["simulation_flags"]["dp"] = 2
        with self.assertRaisesRegex(ValueError, "0 or 1"):
            validate_config(config)


if __name__ == "__main__":
    unittest.main()
