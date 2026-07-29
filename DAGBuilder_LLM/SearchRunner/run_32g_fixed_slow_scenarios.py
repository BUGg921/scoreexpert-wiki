from __future__ import annotations

import argparse
import copy
import json
import math
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"
DEFAULT_OUTPUT_ROOT = ROOT / "outputs"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "DagGenerator") not in sys.path:
    sys.path.insert(0, str(ROOT / "DagGenerator"))
if str(ROOT / "SearchRunner") not in sys.path:
    sys.path.insert(0, str(ROOT / "SearchRunner"))

from generate_dag import load_config  # noqa: E402
from run_two_stage_search import run_candidate, sanitize_name  # noqa: E402
from scoreexpert_search_runner import (  # noqa: E402
    cache_entry_from_result,
    score_program_full_space,
    strategy_key,
    strategy_output_name,
)
from ScoreExpert.island_store import ISLANDS  # noqa: E402
from ScoreExpert.strategy_space import (  # noqa: E402
    default_target_scenario,
    enumerate_strategies,
)


SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "id": "s0_homogeneous",
        "title": "32卡同构基线",
        "experience_category": "homogeneous-baseline",
        "slow_ranks": [],
    },
    {
        "id": "s1_single_slow",
        "title": "单张慢卡",
        "experience_category": "local-heterogeneity",
        "slow_ranks": [7],
    },
    {
        "id": "s3_two_same_node",
        "title": "两张慢卡同节点",
        "experience_category": "local-heterogeneity",
        "slow_ranks": [6, 7],
    },
    {
        "id": "s4_two_same_affinity",
        "title": "两张慢卡同亲和组跨节点",
        "experience_category": "local-heterogeneity",
        "slow_ranks": [7, 15],
    },
    {
        "id": "s5_two_cross_affinity",
        "title": "两张慢卡跨亲和组",
        "experience_category": "distributed-heterogeneity",
        "slow_ranks": [7, 23],
    },
    {
        "id": "s6_four_symmetric",
        "title": "四张慢卡四节点对称分布",
        "experience_category": "distributed-heterogeneity",
        "slow_ranks": [7, 15, 23, 31],
    },
    {
        "id": "s7_five_2111",
        "title": "五张慢卡按2-1-1-1分布",
        "experience_category": "distributed-heterogeneity",
        "slow_ranks": [6, 7, 15, 23, 31],
    },
)

COUNTERFACTUAL_KEYS = ("pp1_mbn1_tp8_dp4",)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def make_run_root(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_root = output_root / f"scoreexpert_32g_7scenes_v2_{timestamp}"
    suffix = 1
    while run_root.exists():
        suffix += 1
        run_root = output_root / f"scoreexpert_32g_7scenes_v2_{timestamp}_{suffix}"
    run_root.mkdir(parents=True)
    return run_root


def configure_base(base_config: dict[str, Any]) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    config["model_name"] = "scoreexpert_32g_reference_model"
    config["domains"]["num_gpus"] = 32
    config["network_config"]["die_num_per_node"] = 8

    search = config["search_config"]
    search["allow_idle_gpus"] = False
    search["allowed_active_gpu_counts"] = [32]
    search["allowed_tp_sizes"] = [1, 2, 4, 8]
    search["cluster_scenarios"] = [
        {
            "name": "target_32g_2affinity_4servers",
            "num_gpus": 32,
            "affinity_groups": 2,
            "nodes_per_affinity_group": 2,
            "gpus_per_node": 8,
            "weight": 1.0,
            "rank_mapping_mode": "pp_major_huawei",
        }
    ]
    search["initial_nomination_top_n"] = 10_000
    search["program_nomination_top_n"] = 10_000
    search.setdefault("evolution", {})["enabled"] = False
    search.setdefault("deepseek", {})["enabled"] = False
    search.setdefault("funsearch", {})["enabled"] = False

    value_sim = config["value_sim_config"]
    value_sim["ranks_per_node"] = 8
    value_sim["affinity_group_size"] = 16
    value_sim["num_affinity_groups"] = 2
    value_sim["rank_to_affinity_group"] = [0] * 16 + [1] * 16
    value_sim["tp_size_limit"] = 8
    value_sim["device_overrides"] = {}
    return config


def config_for_scenario(
    base_config: dict[str, Any],
    scenario: dict[str, Any],
) -> dict[str, Any]:
    config = copy.deepcopy(base_config)
    normal_tflops = float(config["value_sim_config"]["device_peak_flops"]) / 1e12
    slow_tflops = normal_tflops * 0.5
    config["dag_id"] = f"{scenario['id']}_32g_fixed_half_speed"
    config["value_sim_config"]["device_overrides"] = {
        int(rank): {
            "compute_tflops": slow_tflops,
            "status": "slow",
            "note": f"{scenario['id']}: fixed 0.5x compute rate",
        }
        for rank in scenario["slow_ranks"]
    }
    config["scenario_metadata"] = {
        **copy.deepcopy(scenario),
        "total_gpus": 32,
        "servers": 4,
        "gpus_per_server": 8,
        "affinity_groups": 2,
        "servers_per_affinity_group": 2,
        "normal_compute_tflops": normal_tflops,
        "slow_compute_tflops": slow_tflops,
        "slow_ratio": 0.5,
        "ep_enabled": False,
    }
    return config


def build_candidate_pool(
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]], int]:
    strategies = enumerate_strategies(config, default_target_scenario(config))
    candidates: dict[str, dict[str, Any]] = {}
    island_scores: dict[str, dict[str, float]] = {}
    source_islands: dict[str, list[str]] = {}

    for island in ISLANDS:
        for row in score_program_full_space(config, island, strategies):
            key = strategy_key(row)
            candidates.setdefault(key, copy.deepcopy(row))
            island_scores.setdefault(key, {})[island] = float(row["island_score"])
            source_islands.setdefault(key, []).append(island)

    for key, candidate in candidates.items():
        candidate["source_islands"] = source_islands[key]
        candidate["island_scores"] = island_scores[key]
    ordered = [
        candidates[key]
        for key in sorted(candidates, key=strategy_tuple)
    ]
    return ordered, island_scores, len(strategies)


def strategy_tuple(key: str) -> tuple[int, int, int, int]:
    values: dict[str, int] = {}
    for token in key.split("_"):
        if token.startswith("pp"):
            values["pp"] = int(token[2:])
        elif token.startswith("mbn"):
            values["mbn"] = int(token[3:])
        elif token.startswith("tp"):
            values["tp"] = int(token[2:])
        elif token.startswith("dp"):
            values["dp"] = int(token[2:])
    return values["pp"], values["mbn"], values["tp"], values["dp"]


def failed_score_rule_entry(candidate: dict[str, Any]) -> dict[str, Any]:
    key = strategy_key(candidate)
    rule = candidate.get("rule_check") or {}
    return {
        "strategy_key": key,
        "evaluation_status": "fail",
        "total_latency_s": None,
        "rulecheck_status": "not_run",
        "valuesim_status": "not_run",
        "failure_reason": ",".join(str(item) for item in rule.get("violations", []))
        or "score_hard_constraint_failed",
        "hard_oom": "memory_hard_overflow" in set(rule.get("violations", [])),
        "timeout": False,
        "candidate_dir": "",
    }


def evaluate_candidate(
    config: dict[str, Any],
    rules_path: Path,
    eval_dir: Path,
    candidate: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    key = strategy_key(candidate)
    output_name = sanitize_name(strategy_output_name(candidate))
    try:
        result = run_candidate(
            base_config=config,
            candidate=copy.deepcopy(candidate),
            candidate_dir=eval_dir / output_name,
            rules_path=rules_path,
            enable_overlap=False,
        )
        return key, cache_entry_from_result(key, result)
    except Exception as exc:  # noqa: BLE001
        message = str(exc)
        return key, {
            "strategy_key": key,
            "evaluation_status": "fail",
            "total_latency_s": None,
            "rulecheck_status": "unknown",
            "valuesim_status": "unknown",
            "failure_reason": message,
            "hard_oom": "oom" in message.lower(),
            "timeout": "timeout" in message.lower(),
            "candidate_dir": str((eval_dir / output_name).as_posix()),
        }


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "pp_size": int(candidate["pp_size"]),
        "tp_size": int(candidate["tp_size"]),
        "dp_size": int(candidate["dp_size"]),
        "micro_batch_num": int(candidate["micro_batch_num"]),
        "active_gpus": int(candidate["active_gpus"]),
        "idle_gpus": int(candidate["idle_gpus"]),
        "island_scores": copy.deepcopy(candidate.get("island_scores", {})),
        "rule_check": copy.deepcopy(candidate.get("rule_check", {})),
    }


def best_candidate_detail(
    entry: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_dir = Path(entry["candidate_dir"])
    timing_path = candidate_dir / "node_timing_table.json"
    weighted_path = candidate_dir / "weighted_dag.json"
    timing_rows = json.loads(timing_path.read_text(encoding="utf-8"))
    weighted = json.loads(weighted_path.read_text(encoding="utf-8"))

    category_duration_s: dict[str, float] = {}
    critical_slow_ranks: set[int] = set()
    for row in timing_rows:
        category = str(row["category"])
        category_duration_s[category] = category_duration_s.get(category, 0.0) + float(
            row["duration_s"]
        )
        if category == "compute":
            critical_rank = row.get("detail", {}).get("critical_rank")
            if critical_rank is not None:
                critical_slow_ranks.add(int(critical_rank))
    return {
        "strategy": compact_candidate(candidate),
        "total_latency_s": float(entry["total_latency_s"]),
        "candidate_dir": entry["candidate_dir"],
        "dag_id": weighted.get("dag_id"),
        "dag_node_count": len(weighted.get("nodes", [])),
        "dag_edge_count": len(weighted.get("edges", [])),
        "sum_node_duration_by_category_s": category_duration_s,
        "compute_critical_ranks_seen": sorted(critical_slow_ranks),
        "weighted_dag": str(weighted_path.as_posix()),
        "node_timing_table": str(timing_path.as_posix()),
    }


def prune_evaluation_artifacts(
    eval_dir: Path,
    evaluation_cache: dict[str, dict[str, Any]],
    retained_candidate_dirs: set[Path],
) -> dict[str, Any]:
    resolved_eval_dir = eval_dir.resolve()
    retained = {path.resolve() for path in retained_candidate_dirs}
    pruned: list[str] = []
    for child in eval_dir.iterdir():
        resolved_child = child.resolve()
        if resolved_child.parent != resolved_eval_dir:
            raise RuntimeError(f"Refusing to prune unexpected candidate path: {child}")
        if resolved_child in retained:
            continue
        if not child.is_dir():
            raise RuntimeError(f"Refusing to prune non-directory candidate artifact: {child}")
        shutil.rmtree(child)
        pruned.append(child.name)
    for entry in evaluation_cache.values():
        raw_path = str(entry.get("candidate_dir") or "")
        if not raw_path:
            entry["artifacts_retained"] = False
            continue
        entry["artifacts_retained"] = Path(raw_path).resolve() in retained
    return {
        "policy": "retain_ranked_top_10_and_counterfactuals",
        "retained_ranked_candidate_count": len(retained),
        "pruned_ranked_candidate_count": len(pruned),
        "pruned_candidate_names": sorted(pruned),
        "recoverability": "rerun this scenario with the same script and config",
    }


def slow_tp_group_analysis(
    strategy: dict[str, Any],
    slow_ranks: list[int],
) -> dict[str, Any]:
    tp_size = int(strategy["tp_size"])
    groups: dict[int, list[int]] = {}
    for rank in slow_ranks:
        group_index = int(rank) // tp_size
        groups.setdefault(group_index, []).append(int(rank))
    return {
        "tp_size": tp_size,
        "affected_tp_group_count": len(groups),
        "affected_tp_groups": [
            {
                "group_index": group_index,
                "group_ranks": list(
                    range(group_index * tp_size, (group_index + 1) * tp_size)
                ),
                "slow_ranks": ranks,
            }
            for group_index, ranks in sorted(groups.items())
        ],
        "model_semantics": (
            "A compute supernode is bounded by the slowest rank in its TP group; "
            "equal-speed slow ranks in the same group do not multiply its duration."
        ),
    }


def render_scenario_markdown(result: dict[str, Any]) -> str:
    scene = result["scenario"]
    best = result.get("best")
    slow_text = ", ".join(str(rank) for rank in scene["slow_ranks"]) or "无"
    lines = [
        f"# {scene['id']}：{scene['title']}",
        "",
        "- 经验候选判定：`KEEP_FOR_VALIDATION`",
        "- 优化目标：`latency-first`",
        f"- 场景分类：`{scene['experience_category']}`",
        "- 仿真链：`ScoreExpert 全空间枚举/打分 → DagGenerator → RuleCheck → ValueSim simulator_v2 → Evaluation 最长路径`",
        "- OverlapOPT：禁用；按未重叠的 baseline latency 排名",
        "- EP：禁用",
        f"- 完整候选产物保留：Top {result['artifact_retention']['retained_ranked_candidate_count']}；其余 {result['artifact_retention']['pruned_ranked_candidate_count']} 个候选仅保留 evaluation cache，可按相同配置重跑恢复",
        "",
        "## 场景设置",
        "",
        "- 资源：32 卡，4 个服务器 × 8 卡；2 个亲和组，每组 2 个服务器",
        f"- 慢卡 Rank：`{slow_text}`",
        f"- 正常/慢卡算力：`{scene['normal_compute_tflops']:.3f}` / `{scene['slow_compute_tflops']:.3f}` TFLOPS，固定倍率 `0.5×`",
        f"- 模型：{result['model']['num_layers']} 层，hidden={result['model']['hidden_size']}，FFN={result['model']['ffn_hidden_size']}，seq={result['workload']['seq_len']}，global batch={result['workload']['global_batch_size']}",
        "- 搜索约束：`PP×TP×DP=32`，`TP∈{1,2,4,8}`，不允许 idle GPU，`MBN∈{1,2,4,8,16,32,64}`",
        "- Rank mapping：`pp_major_huawei`；PP stage 均匀分层",
        "",
        "## 搜索与评估结果",
        "",
        f"- 枚举策略：{result['counts']['enumerated']}",
        f"- ScoreExpert 四岛均可评分：{result['counts']['scoreable']}",
        f"- Score 硬约束通过并进入完整 DAG 评估：{result['counts']['fully_evaluated']}",
        f"- 完整链通过：{result['counts']['passed']}",
        f"- 失败/跳过：{result['counts']['failed']}",
        "",
    ]
    if best is None:
        lines.extend(
            [
                "没有候选完成完整链评估，不能生成并行策略候选。",
                "",
            ]
        )
    else:
        strategy = best["strategy"]
        lines.extend(
            [
                "## 当前最优候选",
                "",
                f"- `PP={strategy['pp_size']}, TP={strategy['tp_size']}, DP={strategy['dp_size']}, MBN={strategy['micro_batch_num']}`",
                f"- Evaluation 最长路径 latency：`{best['total_latency_s']:.9f} s`",
                f"- DAG：{best['dag_node_count']} 个节点，{best['dag_edge_count']} 条边",
                f"- 完整候选目录：`{best['candidate_dir']}`",
                f"- 受慢卡影响的 TP group：{best['slow_tp_group_analysis']['affected_tp_group_count']} 个",
                "",
                "## Top 10",
                "",
                "| 排名 | PP | TP | DP | MBN | latency (s) | RuleCheck | simulator_v2 |",
                "|---:|---:|---:|---:|---:|---:|---|---|",
            ]
        )
        for rank, item in enumerate(result["top_candidates"], start=1):
            strategy = item["strategy"]
            lines.append(
                f"| {rank} | {strategy['pp_size']} | {strategy['tp_size']} | "
                f"{strategy['dp_size']} | {strategy['micro_batch_num']} | "
                f"{item['total_latency_s']:.9f} | `{item['rulecheck_status']}` | "
                f"`{item['valuesim_status']}` |"
            )
        lines.append("")
    counterfactuals = result.get("counterfactuals", [])
    if counterfactuals:
        lines.extend(
            [
                "## 硬约束外反事实",
                "",
                "下列策略可以完成 DAG 数值仿真，但被 ScoreExpert 硬约束排除，不参与最优排名。",
                "",
                "| 策略 | simulator_v2 + Evaluation | latency (s) | 排除原因 |",
                "|---|---|---:|---|",
            ]
        )
        for item in counterfactuals:
            strategy = item["strategy"]
            lines.append(
                f"| `PP={strategy['pp_size']}, TP={strategy['tp_size']}, "
                f"DP={strategy['dp_size']}, MBN={strategy['micro_batch_num']}` | "
                f"`{item['evaluation_status']}` | "
                + (
                    f"{float(item['total_latency_s']):.9f}"
                    if item.get("total_latency_s") is not None
                    else ""
                )
                + f" | `{item['ranking_exclusion_reason']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## 证据边界",
            "",
            "- 本结果是完整软件仿真链产生的候选，不是真实 32 卡集群 Evaluation；因此暂不写入正式 active 经验。",
            "- ScoreExpert 分数只用于保留打分证据；本次对所有 Score 硬约束通过的策略都运行完整 DAG 评估，最终按 Evaluation latency 排名。",
            "- 当前搜索只支持均匀 PP 分层和固定 rank-major 映射，尚不能针对慢卡自动减层或交换 rank；这会限制单慢卡深 PP 策略的可发现范围。",
            "- 慢卡仅改变计算吞吐，未模拟慢卡通信链路、抖动、故障、显存差异或不同慢速倍率。",
            "- `MBN=64` 若成为最优，只能解释为当前搜索上界候选，不能解释为物理必然最优。",
            "",
        ]
    )
    return "\n".join(lines)


def run_scenario(
    base_config: dict[str, Any],
    scenario: dict[str, Any],
    run_root: Path,
    rules_path: Path,
    workers: int,
) -> dict[str, Any]:
    scene_dir = run_root / str(scenario["id"])
    scene_dir.mkdir(parents=True)
    config = config_for_scenario(base_config, scenario)
    dump_json(scene_dir / "scenario_config.json", config)

    candidates, _island_scores, enumerated_count = build_candidate_pool(config)
    candidate_by_key = {strategy_key(candidate): candidate for candidate in candidates}
    evaluation_cache: dict[str, dict[str, Any]] = {}
    ready: list[dict[str, Any]] = []
    for candidate in candidates:
        key = strategy_key(candidate)
        if (candidate.get("rule_check") or {}).get("status") == "pass":
            ready.append(candidate)
        else:
            evaluation_cache[key] = failed_score_rule_entry(candidate)

    print(
        f"[{scenario['id']}] enumerated={enumerated_count}, "
        f"scoreable={len(candidates)}, full_eval={len(ready)}",
        flush=True,
    )
    eval_dir = scene_dir / "evaluations"
    completed = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(
                evaluate_candidate,
                config,
                rules_path,
                eval_dir,
                candidate,
            ): candidate
            for candidate in ready
        }
        for future in as_completed(futures):
            key, entry = future.result()
            evaluation_cache[key] = entry
            completed += 1
            if completed % 5 == 0 or completed == len(ready):
                passed_so_far = sum(
                    item.get("evaluation_status") == "pass"
                    for item in evaluation_cache.values()
                )
                print(
                    f"[{scenario['id']}] progress={completed}/{len(ready)}, "
                    f"passed={passed_so_far}",
                    flush=True,
                )
                dump_json(scene_dir / "evaluation_cache.partial.json", evaluation_cache)

    dump_json(scene_dir / "evaluation_cache.json", evaluation_cache)
    partial_path = scene_dir / "evaluation_cache.partial.json"
    if partial_path.exists():
        partial_path.unlink()

    passed = [
        entry
        for entry in evaluation_cache.values()
        if entry.get("evaluation_status") == "pass"
        and isinstance(entry.get("total_latency_s"), (int, float))
        and math.isfinite(float(entry["total_latency_s"]))
    ]
    passed.sort(key=lambda item: float(item["total_latency_s"]))
    top_candidates = [
        {
            "strategy_key": entry["strategy_key"],
            "strategy": compact_candidate(candidate_by_key[entry["strategy_key"]]),
            "total_latency_s": float(entry["total_latency_s"]),
            "rulecheck_status": entry["rulecheck_status"],
            "valuesim_status": entry["valuesim_status"],
            "candidate_dir": entry["candidate_dir"],
        }
        for entry in passed[:10]
    ]
    artifact_retention = prune_evaluation_artifacts(
        eval_dir,
        evaluation_cache,
        {Path(item["candidate_dir"]) for item in top_candidates},
    )
    dump_json(scene_dir / "evaluation_cache.json", evaluation_cache)
    best = (
        best_candidate_detail(passed[0], candidate_by_key[passed[0]["strategy_key"]])
        if passed
        else None
    )
    if best is not None:
        best["slow_tp_group_analysis"] = slow_tp_group_analysis(
            best["strategy"],
            list(scenario["slow_ranks"]),
        )

    counterfactuals: list[dict[str, Any]] = []
    counterfactual_dir = scene_dir / "counterfactuals"
    for key in COUNTERFACTUAL_KEYS:
        candidate = candidate_by_key.get(key)
        ranked_entry = evaluation_cache.get(key)
        if candidate is None or ranked_entry is None:
            continue
        if ranked_entry.get("evaluation_status") == "pass":
            continue
        _key, entry = evaluate_candidate(
            config,
            rules_path,
            counterfactual_dir,
            candidate,
        )
        counterfactuals.append(
            {
                "strategy_key": key,
                "strategy": compact_candidate(candidate),
                "evaluation_status": entry["evaluation_status"],
                "total_latency_s": entry["total_latency_s"],
                "rulecheck_status": entry["rulecheck_status"],
                "valuesim_status": entry["valuesim_status"],
                "candidate_dir": entry["candidate_dir"],
                "ranking_eligible": False,
                "ranking_exclusion_reason": ranked_entry["failure_reason"],
            }
        )
    metadata = config["scenario_metadata"]
    result = {
        "status": "pass" if best is not None else "fail",
        "experience_candidate_status": "KEEP_FOR_VALIDATION",
        "scenario": metadata,
        "model": {
            "name": config["model_name"],
            "num_layers": int(config["model_para"]["num_layers"]),
            "hidden_size": int(config["model_para"]["hidden_size"]),
            "ffn_hidden_size": int(config["model_para"]["ffn_hidden_size"]),
        },
        "workload": {
            "seq_len": int(config["parallelism_config"]["seq_len"]),
            "global_batch_size": float(
                config["parallelism_config"]["global_batch_size"]
            ),
        },
        "search_space": {
            "active_gpus": [32],
            "allowed_tp_sizes": [1, 2, 4, 8],
            "micro_batch_candidates": list(
                config["search_config"]["micro_batch_candidates"]
            ),
            "allow_idle_gpus": False,
            "rank_mapping_mode": "pp_major_huawei",
        },
        "counts": {
            "enumerated": enumerated_count,
            "scoreable": len(candidates),
            "fully_evaluated": len(ready),
            "passed": len(passed),
            "failed": len(evaluation_cache) - len(passed),
        },
        "best": best,
        "top_candidates": top_candidates,
        "counterfactuals": counterfactuals,
        "artifact_retention": artifact_retention,
        "evaluation_cache": str((scene_dir / "evaluation_cache.json").as_posix()),
        "scenario_config": str((scene_dir / "scenario_config.json").as_posix()),
    }
    json_path = scene_dir / f"{scenario['id']}.json"
    markdown_path = scene_dir / f"{scenario['id']}.md"
    dump_json(json_path, result)
    markdown_path.write_text(render_scenario_markdown(result), encoding="utf-8")
    result["result_json"] = str(json_path.as_posix())
    result["result_markdown"] = str(markdown_path.as_posix())
    print(
        f"[{scenario['id']}] done: best="
        + (
            f"PP{best['strategy']['pp_size']}/TP{best['strategy']['tp_size']}/"
            f"DP{best['strategy']['dp_size']}/MBN{best['strategy']['micro_batch_num']} "
            f"{best['total_latency_s']:.9f}s"
            if best
            else "none"
        ),
        flush=True,
    )
    return result


def render_summary(results: list[dict[str, Any]], run_root: Path) -> str:
    lines = [
        "# 32卡固定半速慢卡七场景完整仿真",
        "",
        f"- 运行目录：`{run_root}`",
        "- 结果身份：`KEEP_FOR_VALIDATION`，未写入正式经验库",
        "- 每个场景均使用完整链：ScoreExpert → DagGenerator → RuleCheck → simulator_v2 → Evaluation",
        "- 拓扑：4 个 8 卡服务器，2 个亲和组，每组 2 个服务器",
        "- EP：禁用",
        "- 产物策略：每场景保留 Top 10 完整 DAG 目录及旧经验反事实；其余候选保留 evaluation cache，可按同一脚本恢复",
        "",
        "| 场景 | 慢卡 Rank | PP | TP | DP | MBN | latency (s) | 场景文件 |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for result in results:
        scene = result["scenario"]
        best = result.get("best")
        ranks = ",".join(str(rank) for rank in scene["slow_ranks"]) or "无"
        if best:
            strategy = best["strategy"]
            lines.append(
                f"| `{scene['id']}` | `{ranks}` | {strategy['pp_size']} | "
                f"{strategy['tp_size']} | {strategy['dp_size']} | "
                f"{strategy['micro_batch_num']} | {best['total_latency_s']:.9f} | "
                f"[报告]({scene['id']}/{scene['id']}.md) |"
            )
        else:
            lines.append(
                f"| `{scene['id']}` | `{ranks}` |  |  |  |  |  | "
                f"[报告]({scene['id']}/{scene['id']}.md) |"
            )
    lines.extend(
        [
            "",
            "旧经验元组 `PP1/TP8/DP4/MBN1` 另做硬约束外反事实仿真；若 ScoreExpert 判定 `memory_hard_overflow`，其 latency 仅用于分析，不参与最优排名。",
            "",
            "旧的 `simulator_v2/experiments/run_32g_scenarios.py` 简化结果不参与本次排名；本目录结果应作为新的仿真候选来源。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run seven fixed-half-speed 32-GPU scenarios through the complete DAGBuilder chain."
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--scenes",
        nargs="*",
        choices=[str(item["id"]) for item in SCENARIOS],
        help="Optional subset of scene IDs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_root = make_run_root(args.output_root)
    base_config = configure_base(load_config(args.config))
    selected = [
        scenario
        for scenario in SCENARIOS
        if not args.scenes or scenario["id"] in set(args.scenes)
    ]
    dump_json(
        run_root / "manifest.json",
        {
            "status": "running",
            "started_at": datetime.now().isoformat(timespec="seconds"),
            "config_source": str(args.config.resolve()),
            "rules_source": str(args.rules.resolve()),
            "workers": max(1, args.workers),
            "scenarios": list(selected),
        },
    )
    results: list[dict[str, Any]] = []
    for scenario in selected:
        results.append(
            run_scenario(
                base_config,
                scenario,
                run_root,
                args.rules,
                max(1, args.workers),
            )
        )
    dump_json(
        run_root / "results.json",
        {
            "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
            "experience_candidate_status": "KEEP_FOR_VALIDATION",
            "run_root": str(run_root.as_posix()),
            "results": results,
        },
    )
    (run_root / "summary.md").write_text(
        render_summary(results, run_root),
        encoding="utf-8",
    )
    dump_json(
        run_root / "manifest.json",
        {
            "status": "pass" if all(item["status"] == "pass" for item in results) else "fail",
            "started_at": json.loads(
                (run_root / "manifest.json").read_text(encoding="utf-8")
            )["started_at"],
            "finished_at": datetime.now().isoformat(timespec="seconds"),
            "config_source": str(args.config.resolve()),
            "rules_source": str(args.rules.resolve()),
            "workers": max(1, args.workers),
            "scenarios": list(selected),
            "summary": str((run_root / "summary.md").as_posix()),
            "results": str((run_root / "results.json").as_posix()),
        },
    )
    print(f"RUN_ROOT={run_root}", flush=True)
    return 0 if all(item["status"] == "pass" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
