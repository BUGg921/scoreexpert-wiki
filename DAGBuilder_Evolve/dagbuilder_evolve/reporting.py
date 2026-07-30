from __future__ import annotations

import json
import shutil
import hashlib
import re
from pathlib import Path
from typing import Any

from .config import ScenarioConfig
from .database import ProgramDatabase
from .programs import ProgramRecord, score_program
from .strategy import Strategy


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _strategy_label(strategy: dict[str, Any]) -> str:
    schedule = str(strategy["schedule"]).upper()
    communication = (
        "RS+AG" if strategy["dp_communication"] == "rs_ag" else "AllReduce"
    )
    return (
        f"PP{strategy['pp']}/TP{strategy['tp']}/DP{strategy['dp']}/"
        f"MBN{strategy['micro_batch_num']}/{schedule}/{communication}"
    )


def _slow_count_from_source(path: Path, text: str) -> int | None:
    filename_counts = {
        "homogeneous": 0,
        "single-slow": 1,
        "two-slow": 2,
        "three-slow": 3,
        "four-slow": 4,
        "five-slow": 5,
        "six-slow": 6,
        "seven-slow": 7,
        "eight-slow": 8,
    }
    for marker, count in filename_counts.items():
        if marker in path.name:
            return count
    if "无慢卡" in text:
        return 0
    match = re.search(r"(?:共有|存在)\s*(\d+)\s*张慢卡", text)
    return int(match.group(1)) if match else None


def _distribution_variant(text: str) -> str | None:
    if "跨亲和组" in text or "分别位于两个亲和组" in text:
        return "cross_affinity"
    if "同亲和组" in text and "不同节点" in text:
        return "same_affinity_different_nodes"
    if "同一节点" in text or "同节点" in text:
        return "same_node"
    return None


def _load_wiki_experience_coverage(summary_path: Path) -> list[dict[str, Any]]:
    if not summary_path.is_file():
        return []
    summary = summary_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^- \*\*(?P<label>[^*]+)\*\*："
        r"\[场景来源\]\((?P<href>[^)]+)\)(?P<tail>.*)$",
        flags=re.MULTILINE,
    )
    coverage: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for match in pattern.finditer(summary):
        source = (summary_path.parent / match.group("href")).resolve()
        if source in seen or not source.is_file():
            continue
        seen.add(source)
        source_text = source.read_text(encoding="utf-8")
        slow_count = _slow_count_from_source(source, source_text)
        if slow_count is None:
            continue
        tail = match.group("tail")
        coverage.append(
            {
                "label": match.group("label"),
                "slow_count": slow_count,
                "status": (
                    "KEEP_FOR_VALIDATION"
                    if "KEEP_FOR_VALIDATION" in tail
                    else "MATURE"
                ),
                "distribution_variant": (
                    _distribution_variant(source_text) if slow_count >= 2 else None
                ),
                "source": str(source),
            }
        )
    return coverage


def _slow_mapping_evidence(
    config: ScenarioConfig,
    best: dict[str, Any],
) -> dict[str, Any]:
    overrides = {
        int(rank): value
        for rank, value in config.topology.get("device_overrides", {}).items()
    }
    rank_locations: dict[int, dict[str, int]] = {}
    for affinity in config.topology["affinity_groups"]:
        for server in affinity["servers"]:
            for rank in server["ranks"]:
                rank_locations[int(rank)] = {
                    "server_id": int(server["server_id"]),
                    "affinity_group_id": int(affinity["affinity_group_id"]),
                }
    mapping = {
        int(item["global_rank"]): item for item in best.get("rank_mapping", [])
    }
    active_slow = sorted(rank for rank in overrides if rank in mapping)
    idle_slow = sorted(rank for rank in overrides if rank not in mapping)
    rows = []
    tp_groups: set[tuple[int, int]] = set()
    pp_stages: set[int] = set()
    dp_replicas: set[int] = set()
    replica_slow_counts: dict[int, int] = {}
    for rank in active_slow:
        item = mapping[rank]
        pp_stage = int(item["pp_stage"])
        dp_rank = int(item["dp_rank"])
        tp_rank = int(item["tp_rank"])
        location = rank_locations.get(rank, {})
        rows.append(
            {
                "global_rank": rank,
                "pp_stage": pp_stage,
                "dp_rank": dp_rank,
                "tp_rank": tp_rank,
                "server_id": location.get("server_id"),
                "affinity_group_id": location.get("affinity_group_id"),
                "compute_tflops": overrides[rank].get("compute_tflops"),
            }
        )
        tp_groups.add((pp_stage, dp_rank))
        pp_stages.add(pp_stage)
        dp_replicas.add(dp_rank)
        replica_slow_counts[dp_rank] = replica_slow_counts.get(dp_rank, 0) + 1
    strategy = best["strategy"]
    return {
        "active_slow_ranks": active_slow,
        "idle_slow_ranks": idle_slow,
        "slow_rank_mapping": rows,
        "affected_tp_group_count": len(tp_groups),
        "total_tp_group_count": int(strategy["pp"]) * int(strategy["dp"]),
        "affected_pp_stage_count": len(pp_stages),
        "total_pp_stage_count": int(strategy["pp"]),
        "affected_dp_replica_count": len(dp_replicas),
        "total_dp_replica_count": int(strategy["dp"]),
        "replica_slow_counts": {
            str(key): value for key, value in sorted(replica_slow_counts.items())
        },
    }


def _program_fitness(record: ProgramRecord) -> tuple[float, float, int, int]:
    return (
        float("inf") if record.best_latency_s is None else record.best_latency_s,
        float("inf") if record.top3_mean_latency_s is None else record.top3_mean_latency_s,
        record.failures,
        len(record.source),
    )


def _visible_formula_inputs(source: str) -> dict[str, list[str]]:
    fields = {
        "strategy": (
            "pp", "tp", "dp", "micro_batch_num", "schedule",
            "dp_communication", "active_gpus", "signature",
        ),
        "model": (
            "name", "num_layers", "hidden_size", "ffn_hidden_size",
            "parameter_count", "dtype_bytes", "gradient_dtype_bytes",
        ),
        "topology": ("total_devices", "cards_per_server", "affinity_group_count"),
        "workload": (
            "global_batch_size", "sequence_length", "compute_efficiency",
            "backward_flop_multiplier", "activation_multiplier",
            "optimizer_state_multiplier",
        ),
    }
    return {
        group: [
            field
            for field in values
            if f'"{field}"' in source or f"'{field}'" in source
        ]
        for group, values in fields.items()
    }


def _score_program_evidence(
    config: ScenarioConfig,
    run_dir: Path,
    database: ProgramDatabase,
    best_strategy: Strategy,
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    signature = best_strategy.signature
    matches: list[tuple[int, int, tuple[float, float, int, int], ProgramRecord, str]] = []
    records = list(database.records.values())
    known_ids = {record.program_id for record in records}
    for path in sorted((run_dir / "rounds").glob("round_*/programs.json")):
        for value in json.loads(path.read_text(encoding="utf-8")):
            if value["program_id"] not in known_ids:
                records.append(ProgramRecord(**value))
                known_ids.add(value["program_id"])
    for record in records:
        if signature in record.evaluated_nominations:
            rank = int(record.evaluated_nomination_ranks.get(signature, 10**9))
            matches.append(
                (0, rank, _program_fitness(record), record, "direct_evaluation_nomination")
            )
        elif signature in record.nominated:
            default_rank = record.nominated.index(signature) + 1
            rank = int(record.nominated_ranks.get(signature, default_rank))
            matches.append((1, rank, _program_fitness(record), record, "top8_ranked"))
    if matches:
        matches.sort(key=lambda item: (item[0], item[1], item[2], -item[3].generation))
        _, rank, _, selected, attribution = matches[0]
        alternative_ids = [item[3].program_id for item in matches[1:6]]
    else:
        selected = database.best()
        if selected is None:
            raise RuntimeError("No score program is available for deployment attribution")
        rank = 0
        attribution = "fallback_best_program"
        alternative_ids = []
    score = selected.evaluated_nomination_scores.get(signature)
    if score is None:
        score = selected.nominated_scores.get(signature)
    if score is None:
        try:
            ranking, _ = score_program(
                selected.source,
                [best_strategy],
                config,
                float(config.evolution["program_timeout_s"]),
            )
            score = float(ranking[0][1])
        except Exception:
            score = None
    global_batch_size = float(config.workload["global_batch_size"])
    dp = int(best_strategy.dp)
    micro_batch_num = int(best_strategy.micro_batch_num)
    pp = int(best_strategy.pp)
    active = int(best_strategy.active_gpus)
    total = int(config.topology["total_devices"])
    cards_per_server = max(
        len(server["ranks"])
        for affinity in config.topology["affinity_groups"]
        for server in affinity["servers"]
    )
    ranked_candidate_evidence = []
    for nominated_signature in selected.nominated:
        result = results.get(nominated_signature)
        ranked_candidate_evidence.append(
            {
                "signature": nominated_signature,
                "candidate_rank": selected.nominated_ranks.get(
                    nominated_signature,
                    selected.nominated.index(nominated_signature) + 1,
                ),
                "candidate_score": selected.nominated_scores.get(
                    nominated_signature
                ),
                "simulation_status": None if result is None else result.get("status"),
                "simulation_latency_s": (
                    None if result is None else result.get("latency_s")
                ),
                "strategy": None if result is None else result.get("strategy"),
            }
        )
    return {
        "program_id": selected.program_id,
        "island": selected.island,
        "generation": selected.generation,
        "origin": selected.origin,
        "attribution": attribution,
        "candidate_rank": None if rank == 0 or rank >= 10**9 else rank,
        "candidate_score": score,
        "formula_source": selected.source,
        "visible_inputs": _visible_formula_inputs(selected.source),
        "derived_candidate_metrics": {
            "active_gpus": active,
            "idle_gpus": total - active,
            "pipeline_bubble_ratio": float(pp - 1) / max(
                1.0, float(micro_batch_num + pp - 1)
            ),
            "derived_microbatch_size": global_batch_size / max(
                1.0, float(dp * micro_batch_num)
            ),
            "tp_size": int(best_strategy.tp),
            "cards_per_server": cards_per_server,
            "tp_size_within_one_server": int(best_strategy.tp) <= cards_per_server,
            "tp_tiles_server": cards_per_server % max(1, int(best_strategy.tp)) == 0,
        },
        "alternative_attribution_program_ids": alternative_ids,
        "ranked_candidate_evidence": ranked_candidate_evidence,
        "boundaries": [
            "该公式负责候选排序，最终部署仍按数值仿真的最长路径选择。",
            "score输入不包含逐Rank慢卡状态、固定Rank映射后的通信路径或最终仿真时延。",
            "不同评分程序的原始分数尺度可能不同，不能跨程序直接相加或比较。",
        ],
    }


def _automatic_reasoning(
    best: dict[str, Any],
    score_evidence: dict[str, Any],
) -> dict[str, list[str]]:
    strategy = best["strategy"]
    metrics = score_evidence["derived_candidate_metrics"]
    score_text = (
        "未记录"
        if score_evidence["candidate_score"] is None
        else f"{score_evidence['candidate_score']:.6f}"
    )
    rank_text = (
        "未记录"
        if score_evidence["candidate_rank"] is None
        else str(score_evidence["candidate_rank"])
    )
    critical = best.get("critical_path_category_s", {})
    bottleneck = max(critical, key=critical.get) if critical else "unknown"
    visible = score_evidence["visible_inputs"]
    visible_text = "；".join(
        f"{group}={','.join(fields)}"
        for group, fields in visible.items()
        if fields
    ) or "未识别到配置字段"
    formula_interpretations = [
        f"公式实际读取字段为：{visible_text}。",
    ]
    strategy_fields = set(visible["strategy"])
    workload_fields = set(visible["workload"])
    topology_fields = set(visible["topology"])
    if {"pp", "micro_batch_num"} <= strategy_fields:
        formula_interpretations.append(
            f"公式同时读取PP和micro_batch_num；推荐候选的气泡近似为"
            f"{metrics['pipeline_bubble_ratio']:.2%}，这是解释其流水线项的候选特征。"
        )
    if "active_gpus" in strategy_fields:
        formula_interpretations.append(
            f"公式显式读取active_gpus；推荐候选使用{metrics['active_gpus']}卡、"
            f"空闲{metrics['idle_gpus']}卡。"
        )
    if "tp" in strategy_fields and topology_fields:
        formula_interpretations.append(
            f"公式同时读取TP和拓扑；该候选TP={metrics['tp_size']}，"
            f"单节点{metrics['cards_per_server']}卡，"
            f"TP是否限制在单节点={metrics['tp_size_within_one_server']}。"
        )
    if (
        {"dp", "micro_batch_num"} <= strategy_fields
        and "global_batch_size" in workload_fields
    ):
        formula_interpretations.append(
            f"公式可由GBS、DP和micro_batch_num判断批次切分；该候选派生"
            f"micro-batch size={metrics['derived_microbatch_size']:.3f}。"
        )
    return {
        "score_derived": [
            (
                f"关联评分程序来自{score_evidence['island']}岛第"
                f"{score_evidence['generation']}代，归因方式为"
                f"{score_evidence['attribution']}。"
            ),
            f"该公式对推荐候选的分数为{score_text}，完整候选排序名次为{rank_text}。",
            *formula_interpretations,
        ],
        "simulation_derived": [
            (
                f"候选通过DAG生成和RuleCheck，数值仿真最长路径为"
                f"{best['latency_s']:.6f} s。"
            ),
            f"关键路径主导类别为{bottleneck}，该结论来自仿真而不是启发式分数。",
            (
                f"推荐策略{_strategy_label(strategy)}是已仿真候选中的最低时延项，"
                "不代表未仿真候选中的全局最优。"
            ),
        ],
    }


def _write_scenario_analysis(
    config: ScenarioConfig,
    run_dir: Path,
    report: dict[str, Any],
    experience: dict[str, Any],
) -> None:
    best = report["best"]
    strategy = best["strategy"]
    score = experience["score_evidence"]
    metrics = score["derived_candidate_metrics"]
    slow = config.topology.get("device_overrides", {})
    slow_text = "无" if not slow else "、".join(str(rank) for rank in sorted(slow))
    server_count = sum(
        len(affinity["servers"]) for affinity in config.topology["affinity_groups"]
    )
    cards_per_server = metrics["cards_per_server"]
    top_rows = []
    for index, item in enumerate(report["top10"][:5], start=1):
        top_rows.append(
            f"| {index} | {_strategy_label(item['strategy'])} | "
            f"{item['latency_s']:.6f} | {item['memory']['estimated_total_gb']:.3f} |"
        )
    equivalent = report["equivalent_best"]
    equivalent_signatures = {
        item["strategy"]["signature"] for item in equivalent
    }
    counterexample = next(
        (
            item
            for item in report["top10"][1:]
            if item["strategy"]["signature"] not in equivalent_signatures
        ),
        None,
    )
    counterexample_text = (
        "本轮只有一个候选通过，尚无已仿真的次优反例。"
        if counterexample is None
        else (
            f"关键反例是`{_strategy_label(counterexample['strategy'])}`，最长路径"
            f"`{counterexample['latency_s']:.6f} s`；它比推荐候选慢"
            f"`{(counterexample['latency_s'] / best['latency_s'] - 1.0):.2%}`，"
            "差异由数值仿真确认。"
        )
    )
    score_value = (
        "未记录"
        if score["candidate_score"] is None
        else f"{score['candidate_score']:.6f}"
    )
    score_rank = "未记录" if score["candidate_rank"] is None else str(score["candidate_rank"])
    score_counterexample = next(
        (
            item
            for item in score.get("ranked_candidate_evidence", [])
            if item["candidate_rank"] < (score["candidate_rank"] or 10**9)
            and item["simulation_status"] == "pass"
            and item["simulation_latency_s"] > best["latency_s"]
            and item["strategy"] is not None
        ),
        None,
    )
    score_counterexample_text = (
        "没有找到“score排名更高但仿真更慢”的已评估候选。"
        if score_counterexample is None
        else (
            f"评分反例：公式把`{_strategy_label(score_counterexample['strategy'])}`排在"
            f"第{score_counterexample['candidate_rank']}，高于最终候选的第"
            f"{score_rank}；但它的仿真时延为"
            f"`{score_counterexample['simulation_latency_s']:.6f} s`，比最终候选慢"
            f"`{(score_counterexample['simulation_latency_s'] / best['latency_s'] - 1):.2%}`。"
        )
    )
    critical_text = "、".join(
        f"{key}={value:.6f}s"
        for key, value in sorted(
            best.get("critical_path_category_s", {}).items(),
            key=lambda item: item[1],
            reverse=True,
        )
    )
    critical_total = sum(best.get("critical_path_category_s", {}).values())
    critical_percent_text = "、".join(
        f"{key}={value / critical_total:.1%}"
        for key, value in sorted(
            best.get("critical_path_category_s", {}).items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if critical_total > 0 and value > 0
    )
    memory_headroom = (
        float(best["memory"]["capacity_gb"])
        - float(best["memory"]["estimated_total_gb"])
    )
    equivalent_text = "、".join(
        f"`{_strategy_label(item['strategy'])}`" for item in equivalent
    )
    placement = experience["placement_evidence"]
    if placement["active_slow_ranks"]:
        placement_rows = "；".join(
            (
                f"Rank {item['global_rank']}→节点{item['server_id']}/"
                f"亲和组{item['affinity_group_id']}/stage{item['pp_stage']}/"
                f"DP副本{item['dp_rank']}/TP lane{item['tp_rank']}"
            )
            for item in placement["slow_rank_mapping"]
        )
        placement_experience_lines = [
            (
                f"- **慢卡映射证据：** {placement_rows}；共影响"
                f"{placement['affected_tp_group_count']}/"
                f"{placement['total_tp_group_count']}个TP group、"
                f"{placement['affected_pp_stage_count']}/"
                f"{placement['total_pp_stage_count']}个PP stage和"
                f"{placement['affected_dp_replica_count']}/"
                f"{placement['total_dp_replica_count']}个DP replica。"
            ),
            (
                "- **异构经验推理：** 打分公式不读取慢卡Rank和速度；慢卡部署结论"
                "只能由上述Rank映射、关键路径和候选对照推出，不能归因给score。"
            ),
        ]
        if int(strategy["dp"]) == 1:
            placement_experience_lines.append(
                "- **DP异构含义：** DP=1避免形成纯快副本等待含慢卡副本；"
                "该动作适用于慢卡影响无法在多个副本间做对称复制的场景。"
            )
        elif (
            placement["affected_dp_replica_count"]
            == placement["total_dp_replica_count"]
            and len(set(placement["replica_slow_counts"].values())) == 1
        ):
            placement_experience_lines.append(
                "- **DP异构含义：** 每个DP replica包含相同数量的慢卡，"
                "形成数量对称的副本结构；仍需检查慢卡速度和组内位置是否对称。"
            )
        else:
            placement_experience_lines.append(
                "- **DP异构含义：** 只有部分DP replica包含慢卡，存在快副本等待"
                "慢副本的风险；部署前应比较replica关键路径并准备降低DP或重映射。"
            )
    else:
        placement_experience_lines = [
            "- **拓扑映射证据：** 当前没有活跃慢卡，部署经验属于同构基线；"
            "不从该结果外推慢卡隔离或副本均衡规则。"
        ]
    condition_text = (
        f"{config.topology['total_devices']}卡全部正常、"
        f"{server_count}节点×{cards_per_server}卡、"
        f"{len(config.topology['affinity_groups'])}个亲和组"
        if not slow
        else f"{config.topology['total_devices']}卡且慢卡Rank为{slow_text}"
    )
    source = score["formula_source"].rstrip()
    lines = [
        f"# {config.name}仿真与部署经验报告",
        "",
        "## 1. 场景设置",
        "",
        (
            f"- 物理环境：{config.topology['total_devices']}卡，{server_count}节点×"
            f"{cards_per_server}卡，{len(config.topology['affinity_groups'])}个亲和组。"
        ),
        f"- 慢卡Rank：{slow_text}。",
        (
            f"- 模型与负载：{config.model['name']}、{config.model['num_layers']}层、"
            f"GBS={config.workload['global_batch_size']}、"
            f"Seq={config.workload['sequence_length']}、"
            f"{config.memory['device_capacity_gb']} GB显存/卡。"
        ),
        (
            f"- 搜索覆盖：结构候选{report['total_strategy_count']}个，实际评估"
            f"{report['evaluated_strategy_count']}个，通过{report['passed_strategy_count']}个，"
            f"覆盖率{report['coverage']:.2%}。"
        ),
        (
            f"- 关联评分程序：{score['island']}岛，第{score['generation']}代，"
            f"`{score['program_id']}`；归因方式为`{score['attribution']}`。"
        ),
        "- score不可见逐Rank慢卡状态、具体Rank通信路径和最终仿真时延。",
        "",
        "## 2. 为什么能得到最优解",
        "",
        (
            f"源程序推荐`{_strategy_label(strategy)}`，最长路径"
            f"`{best['latency_s']:.9f} s`。这里的最优仅指已实际仿真的候选。"
        ),
        "",
        (
            f"- 合法性：`{strategy['pp']}×{strategy['tp']}×{strategy['dp']}="
            f"{strategy['active_gpus']}`，空闲{metrics['idle_gpus']}卡；"
            f"派生micro-batch size={metrics['derived_microbatch_size']:.3f}；"
            f"显存估算{best['memory']['estimated_total_gb']:.3f} GB/卡。"
        ),
        (
            f"- score证据：候选在关联公式中的分数为`{score_value}`，"
            f"排名为`{score_rank}`；公式只能解释为何候选被提名。"
        ),
        (
            f"- 仿真证据：关键路径拆解为{critical_text or '未提供'}；"
            "最终排序按最长路径，不按启发式分数。"
        ),
        (
            f"- 等价最优：在相对误差`1e-6`内共有{len(equivalent)}个策略，"
            f"分别是{equivalent_text}。这些差异不能作为通信或调度方式优劣证据。"
        ),
        "",
        "```python",
        source,
        "```",
        "",
        "| 排名 | 已仿真策略 | 时延 (s) | 显存估算 (GB/卡) |",
        "| ---: | --- | ---: | ---: |",
        *top_rows,
        "",
        counterexample_text,
        "",
        score_counterexample_text,
        "",
        "## 3. 经验总结",
        "",
        "- **经验状态：** `KEEP_FOR_VALIDATION`，尚缺真实训练Evaluation。",
        f"- **场景条件：** {condition_text}，模型和负载保持本报告配置。",
        (
            f"- **推荐部署形状：** `PP{strategy['pp']}/TP{strategy['tp']}/"
            f"DP{strategy['dp']}/MBN{strategy['micro_batch_num']}`，使用"
            f"{strategy['active_gpus']}卡，派生micro-batch size="
            f"{metrics['derived_microbatch_size']:.3f}。"
        ),
        (
            f"- **部署动作：** 优先验证最优策略族{equivalent_text}；当前仿真不能"
            "区分其中的调度和DP通信变体，应通过真实训练再选择具体变体。"
        ),
        (
            f"- **打分策略推理：** 关联公式来自{score['island']}岛，"
            f"候选score={score_value}、rank={score_rank}；公式实际读取"
            f"`{score['visible_inputs']}`。"
        ),
        (
            f"- **公式排序校正：** {score_counterexample_text}"
            "这说明公式适合产生候选，但不能直接充当部署结论。"
        ),
        (
            f"- **仿真结果推理：** DAG和RuleCheck通过，最长路径"
            f"`{best['latency_s']:.6f} s`；关键路径占比为"
            f"{critical_percent_text or '缺少分类拆解'}；显存余量"
            f"`{memory_headroom:.3f} GB/卡`。"
        ),
        *placement_experience_lines,
        (
            f"- **具体部署经验：** 在上述场景中，优先验证"
            f"`PP{strategy['pp']}/TP{strategy['tp']}/DP{strategy['dp']}`形状，"
            f"使用{strategy['active_gpus']}/{config.topology['total_devices']}卡；"
            f"TP={strategy['tp']}不跨越单节点{metrics['cards_per_server']}卡边界；"
            f"MBN={strategy['micro_batch_num']}在当前显存约束下取得最低已仿真时延。"
        ),
        (
            "- **证据边界：** score只解释候选排序和提名；策略是否采用由RuleCheck、"
            "显存与DAG最长路径决定。等价最优之间的具体选择仍需真实训练Evaluation。"
        ),
        (
            "- **源程序证据：** 推荐策略、Rank映射和量化结果来自"
            "[deployment_experience.json](deployment_experience.json)，"
            "对应公式来自[best_score_program.py](best_score_program.py)。"
        ),
        "",
        "## 4. 未验证的经验",
        "",
        "以下条目指尚未通过独立仿真得到部署经验的新场景，不是本场景结论的重复。",
        "",
        (
            f"1. **显存容量变化场景：** 当前容量为"
            f"{config.memory['device_capacity_gb']} GB/卡。尚未得到更大或更小显存下，"
            f"最优MBN是否仍为{strategy['micro_batch_num']}的部署经验。"
        ),
        (
            f"2. **批次规模变化场景：** 当前GBS={config.workload['global_batch_size']}、"
            f"Seq={config.workload['sequence_length']}。尚未得到GBS或序列长度变化后，"
            f"DP={strategy['dp']}与MBN={strategy['micro_batch_num']}是否仍最优的经验。"
        ),
        (
            f"3. **节点形态变化场景：** 当前为{server_count}节点×"
            f"{cards_per_server}卡。尚未得到保持总卡数不变但改成其他节点粒度后，"
            f"TP={strategy['tp']}是否仍应限制在单节点内的经验。"
        ),
        (
            "4. **跨节点带宽变化场景：** 尚未得到RoCE或跨节点HCCS带宽降低后，"
            "是否需要降低DP/TP通信规模或提高PP的经验。"
        ),
        (
            f"5. **模型规模变化场景：** 当前模型为{config.model['name']}。尚未得到"
            "参数量和层数变化后，显存压力是否会推动PP、TP或MBN切换的经验。"
        ),
        "",
        "## 5. 下一步仿真场景建议（为了验证第 4 部分）",
        "",
        (
            f"- **对应未验证场景1：显存容量对照。** 固定当前拓扑、模型和负载，"
            f"分别使用低于、等于和高于{config.memory['device_capacity_gb']} GB/卡的"
            "容量重跑完整搜索；比较最优MBN、OOM边界、时延和显存余量。"
        ),
        (
            f"- **对应未验证场景2：批次对照。** 固定拓扑与模型，以当前"
            f"GBS={config.workload['global_batch_size']}为中心设置更小和更大GBS，"
            "分别搜索PP/TP/DP/MBN；以最优形状是否切换作为判断标准。"
        ),
        (
            f"- **对应未验证场景3：节点形态对照。** 保持"
            f"{config.topology['total_devices']}卡总量和网络参数不变，比较不同"
            "“节点数×每节点卡数”；观察TP组是否跨节点以及TP最优值是否变化。"
        ),
        (
            "- **对应未验证场景4：带宽对照。** 固定模型、负载和卡数，分别按"
            "当前值、0.5×和0.25×设置跨节点带宽；比较通信占比和PP/TP/DP切换点。"
        ),
        (
            f"- **对应未验证场景5：模型规模对照。** 保持拓扑不变，以"
            f"{config.model['name']}为基线增加模型层数或参数量；比较显存可行域、"
            "最优PP/TP/MBN和最长路径。"
        ),
    ]
    (run_dir / "scenario_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    _write_raw_article_style_analysis(config, run_dir, report, experience)


def _write_raw_article_style_analysis(
    config: ScenarioConfig,
    run_dir: Path,
    report: dict[str, Any],
    experience: dict[str, Any],
) -> None:
    """Write the simulation report in the same shape as Wiki raw articles."""
    best = report["best"]
    strategy = best["strategy"]
    score = experience["score_evidence"]
    metrics = score["derived_candidate_metrics"]
    placement = experience["placement_evidence"]
    server_count = sum(
        len(affinity["servers"]) for affinity in config.topology["affinity_groups"]
    )
    cards_per_server = int(metrics["cards_per_server"])
    slow_overrides = config.topology.get("device_overrides", {})
    slow_ranks = sorted(int(rank) for rank in slow_overrides)
    normal_tflops = float(config.topology["default_compute_tflops"])
    slow_descriptions = []
    for rank in slow_ranks:
        value = slow_overrides[rank]
        compute = float(value["compute_tflops"])
        slow_descriptions.append(
            f"Rank {rank}={compute:g} TFLOPS（{compute / normal_tflops:.2f}×）"
        )
    score_value = (
        "未记录"
        if score["candidate_score"] is None
        else f"{score['candidate_score']:.6f}"
    )
    score_rank = (
        "未记录"
        if score["candidate_rank"] is None
        else str(score["candidate_rank"])
    )
    top_rows = [
        (
            f"| {index} | `{_strategy_label(item['strategy'])}` | "
            f"{item['latency_s']:.6f} | "
            f"{item['memory']['estimated_total_gb']:.3f} |"
        )
        for index, item in enumerate(report["top10"][:5], start=1)
    ]
    equivalent = report["equivalent_best"]
    equivalent_text = "、".join(
        f"`{_strategy_label(item['strategy'])}`" for item in equivalent
    )
    critical = best.get("critical_path_category_s", {})
    critical_total = sum(critical.values())
    critical_text = "、".join(
        f"{key}={value / critical_total:.1%}"
        for key, value in sorted(
            critical.items(), key=lambda item: item[1], reverse=True
        )
        if critical_total > 0 and value > 0
    )
    score_counterexample = next(
        (
            item
            for item in score.get("ranked_candidate_evidence", [])
            if item["candidate_rank"] < (score["candidate_rank"] or 10**9)
            and item["simulation_status"] == "pass"
            and item["simulation_latency_s"] > best["latency_s"]
            and item["strategy"] is not None
        ),
        None,
    )
    if score_counterexample is None:
        counterexample_text = (
            "当前没有“公式排名更高但仿真更慢”的已评估反例；"
            "公式只用于提名，最终仍以数值仿真排序。"
        )
    else:
        slower = (
            float(score_counterexample["simulation_latency_s"])
            / float(best["latency_s"])
            - 1.0
        )
        counterexample_text = (
            f"公式把`{_strategy_label(score_counterexample['strategy'])}`排在第"
            f"{score_counterexample['candidate_rank']}，高于最终候选的第"
            f"{score_rank}；但其仿真时延为"
            f"`{score_counterexample['simulation_latency_s']:.6f} s`，"
            f"比最终候选慢`{slower:.2%}`。因此公式负责提名，"
            "不能直接替代数值仿真结论。"
        )
    replica_counts = placement.get("replica_slow_counts", {})
    replica_text = "、".join(
        f"副本{key}含{value}张慢卡"
        for key, value in sorted(replica_counts.items())
    )
    schedule_reason = (
        f"相对误差`1e-6`内存在{len(equivalent)}个等价最优："
        f"{equivalent_text}。当前数值模型不能据此区分调度和DP通信实现，"
        "真实部署需用训练Evaluation选择。"
    )
    if slow_ranks:
        tp_reason = (
            f"`TP={strategy['tp']}`把TP同步范围限制在"
            f"{'单卡、消除TP集合通信' if int(strategy['tp']) == 1 else f'单节点{cards_per_server}卡边界内'}；"
            "慢卡不会通过跨节点TP集合通信进一步放大等待。"
        )
    else:
        tp_reason = (
            f"`TP={strategy['tp']}`不跨单节点{cards_per_server}卡边界，"
            "保持高频TP通信局部化。"
        )
    dp_reason = (
        f"`DP={strategy['dp']}`与PP、TP共同使用"
        f"{strategy['active_gpus']}/{config.topology['total_devices']}张卡。"
    )
    if replica_text:
        dp_reason += (
            f"当前映射中{replica_text}；该不对称结构需要以副本关键路径"
            "和真实训练尾延迟为护栏，必要时优先重映射慢卡。"
        )
    affected_affinities = {
        int(item["affinity_group_id"])
        for item in placement.get("slow_rank_mapping", [])
    }
    affected_servers = {
        int(item["server_id"])
        for item in placement.get("slow_rank_mapping", [])
    }
    if not slow_ranks:
        reusable_condition = (
            "没有稳定设备快慢差异，且`空闲卡损失 > 增加通信或减少并行规模的收益`"
        )
        experience_category = "同构基线"
    elif len(affected_affinities) == 1 and len(affected_servers) == 1:
        reusable_condition = (
            "异常设备能够收敛到一个局部执行单元，且"
            "`保留异常卡并局部隔离的算力收益 > 深流水线与重映射成本`"
        )
        experience_category = "局部异构"
    else:
        reusable_condition = (
            "异常设备跨多个节点或亲和组、无法通过一个局部执行单元完成隔离，且"
            "`保留满卡与数据并行的收益 > replica等待和DP通信成本`"
        )
        experience_category = "分布式异构"
    parameter_rule = (
        f"先取能够限制异常同步扩散的最小已验证`TP={strategy['tp']}`；"
        f"再保留本轮仿真有收益的`DP={strategy['dp']}`；"
        f"在满卡约束下由`PP=active_gpu/(TP×DP)="
        f"{strategy['active_gpus']}/({strategy['tp']}×{strategy['dp']})="
        f"{strategy['pp']}`反推PP；最后取显存、气泡和调度边界内"
        f"已验证的`MBN={strategy['micro_batch_num']}`"
    )
    formula_source = score["formula_source"].rstrip()
    default_summary = (
        Path(__file__).resolve().parents[2]
        / "concepts"
        / "latency-first-experience-summary.md"
    )
    summary_path = Path(
        config.analysis.get("experience_summary_path", default_summary)
    ).resolve()
    experience_coverage = _load_wiki_experience_coverage(summary_path)
    current_slow_count = len(slow_ranks)
    per_server_slow: dict[int, int] = {}
    for rank in slow_ranks:
        location = next(
            (
                server
                for affinity in config.topology["affinity_groups"]
                for server in affinity["servers"]
                if rank in server["ranks"]
            ),
            None,
        )
        if location is not None:
            server_id = int(location["server_id"])
            per_server_slow[server_id] = per_server_slow.get(server_id, 0) + 1
    current_distribution = (
        "正常卡"
        if not slow_ranks
        else (
            f"{current_slow_count}张慢卡，按节点"
            + "/".join(str(per_server_slow.get(server_id, 0)) for server_id in range(server_count))
            + "分布"
        )
    )
    experience_descriptions = [
        (
            f"{item['label']}（"
            f"{'KEEP_FOR_VALIDATION' if item['status'] == 'KEEP_FOR_VALIDATION' else '成熟经验'}）"
        )
        for item in experience_coverage
    ]
    covered_counts = {
        int(item["slow_count"]) for item in experience_coverage
    } | {current_slow_count}
    count_targets = [3, 4, 6, 7, 8]
    missing_counts = [value for value in count_targets if value not in covered_counts]
    missing_count_text = "、".join(str(value) for value in missing_counts) or "无"
    count_explanations = {
        3: "3张观察奇数慢卡造成的副本不对称",
        4: "4张构造每节点1张的对称对照",
        6: "6张观察2/2/1/1过渡分布",
        7: "7张观察2/2/2/1近对称边界",
        8: "8张构造每节点2张的高密度对称对照",
    }
    missing_count_reason = "，".join(
        count_explanations[value] for value in missing_counts
    ) or "当前数量梯度没有上述缺口"
    low_density_missing = [value for value in (3, 4) if value in missing_counts]
    low_density_text = "和".join(str(value) for value in low_density_missing) or "无"
    high_density_missing = [value for value in (6, 8) if value in missing_counts]
    high_density_text = "和".join(str(value) for value in high_density_missing) or "无"
    dual_variants = {
        str(item["distribution_variant"])
        for item in experience_coverage
        if int(item["slow_count"]) == 2 and item["distribution_variant"]
    }
    if current_slow_count == 2:
        current_variant = (
            "same_node"
            if len(affected_servers) == 1
            else (
                "same_affinity_different_nodes"
                if len(affected_affinities) == 1
                else "cross_affinity"
            )
        )
        dual_variants.add(current_variant)
    dual_variant_labels = {
        "same_node": "同一节点",
        "same_affinity_different_nodes": "同亲和组不同节点",
        "cross_affinity": "跨亲和组",
    }
    missing_dual_variants = [
        label
        for key, label in dual_variant_labels.items()
        if key not in dual_variants
    ]
    missing_dual_text = "、".join(missing_dual_variants) or "无"
    fixed_dimensions = [
        str(item) for item in config.analysis.get("fixed_dimensions", [])
    ]
    fixed_text = "；".join(fixed_dimensions) or "除慢卡数量和位置外，其余条件保持不变"
    lines = [
        f"# {config.name}仿真与部署策略分析",
        "",
        "## 实验场景",
        "",
        (
            f"共 {config.topology['total_devices']} 张 GPU：{server_count}个节点，"
            f"每节点{cards_per_server}卡，每两个节点组成一个"
            f"{sum(len(server['ranks']) for server in config.topology['affinity_groups'][0]['servers'])}卡亲和组。"
        ),
        (
            "无慢卡。"
            if not slow_ranks
            else (
                f"共有{len(slow_ranks)}张慢卡，具体为"
                + "、".join(slow_descriptions)
                + "。"
            )
        ),
        "",
        "### 模型配置与复算条件",
        "",
        "```text",
        f"model = {config.model['name']}",
        f"num_layers = {config.model['num_layers']}",
        f"global_batch_size = {config.workload['global_batch_size']}",
        f"sequence_length = {config.workload['sequence_length']}",
        f"device_memory = {config.memory['device_capacity_gb']} GB",
        f"total_devices = {config.topology['total_devices']}",
        "PP × TP × DP ≤ total_devices",
        (
            f"search_coverage = {report['evaluated_strategy_count']}/"
            f"{report['total_strategy_count']} ({report['coverage']:.2%})"
        ),
        "```",
        "",
        "## 最优解",
        "",
        "```text",
        f"PP = {strategy['pp']}",
        f"TP = {strategy['tp']}",
        f"DP = {strategy['dp']}",
        f"micro-batch number = {strategy['micro_batch_num']}",
        f"schedule = {strategy['schedule']}",
        f"DP communication = {strategy['dp_communication']}",
        f"active GPUs = {strategy['active_gpus']}",
        f"simulated critical-path latency = {best['latency_s']:.6f} s",
        f"formula candidate score = {score_value}",
        f"formula candidate rank = {score_rank}",
        "```",
        "",
        "",
        "| 排名 | 已仿真策略 | 时延 (s) | 显存估算 (GB/卡) |",
        "| ---: | --- | ---: | ---: |",
        *top_rows,
        "",
        "## 打分策略代码",
        "",
        (
            f"该代码来自`{score['island']}`岛第{score['generation']}代程序"
            f"`{score['program_id']}`，归因方式为"
            f"`{score['attribution']}`。"
        ),
        "",
        "```python",
        formula_source,
        "```",
        "",
        "## 经验总结",
        "",
        '### <span style="color:blue;">(1) 并行策略</span>',
        "",
        (
            f"1. 当{reusable_condition}时，优先采用满卡方案。参数按以下规则求解："
            f"{parameter_rule}。"
        ),
        "",
        '### <span style="color:blue;">(2) 原因</span>',
        "",
        (
            f"1. **{experience_category}参数求解与映射原因**："
        ),
        (
            f"   - **TP**：{tp_reason}"
        ),
        (
            f"   - **DP**：{dp_reason}"
        ),
        (
            f"   - **PP/MBN**：32层模型可被{strategy['pp']}个stage整除；"
            f"当前气泡近似为`{metrics['pipeline_bubble_ratio']:.2%}`，"
            f"派生micro-batch size为`{metrics['derived_microbatch_size']:.3f}`。"
            f"`MBN={strategy['micro_batch_num']}`只是在当前显存、气泡和搜索边界内"
            "与该PP深度配套的已验证值。"
        ),
        (
            f"   - **仿真观测**：关键路径中"
            f"{critical_text or '缺少分类拆解'}；慢卡影响"
            f"{placement['affected_tp_group_count']}/{placement['total_tp_group_count']}个TP group、"
            f"{placement['affected_pp_stage_count']}/{placement['total_pp_stage_count']}个PP stage和"
            f"{placement['affected_dp_replica_count']}/{placement['total_dp_replica_count']}个DP replica。"
            if slow_ranks
            else (
                f"   - **仿真观测**：关键路径中"
                f"{critical_text or '缺少分类拆解'}；当前没有慢卡，"
                "本结果只形成同构基线。"
            )
        ),
        f"   - **公式与仿真分工**：{counterexample_text}",
        f"   - **等价最优**：{schedule_reason}",
        "",
        '### <span style="color:blue;">(3) 结论边界</span>',
        "",
        (
            f"该经验仅适用于本报告的{config.topology['total_devices']}卡拓扑、"
            f"{config.model['name']}、GBS={config.workload['global_batch_size']}、"
            f"Seq={config.workload['sequence_length']}、"
            f"{config.memory['device_capacity_gb']}GB/卡和当前慢卡Rank/速度。"
        ),
        "",
        (
            f"本轮只实际评估{report['evaluated_strategy_count']}/"
            f"{report['total_strategy_count']}个候选；结论是当前已仿真候选最优。"
            "缺少真实训练P50/P99、吞吐、显存峰值和运行方差，"
            "因此经验状态保持`KEEP_FOR_VALIDATION`。"
        ),
        "",
        (
            f"{schedule_reason}若慢卡Rank、速度、模型、batch、显存、网络或"
            "Rank映射变化，应作为新场景重新仿真。"
        ),
        "",
        "## 未仿真的场景",
        "",
        (
            "从经验库目标总览读取的已总结场景为："
            + ("、".join(experience_descriptions) if experience_descriptions else "未读取到场景经验")
            + f"。本轮另有待人工审核的{current_distribution}。"
            "缺口计算以经验库已总结场景和本轮结果为准，不读取用户口头清单，"
            "也不把仅存在的配置文件算作已仿真。"
        ),
        "",
        "尚未形成完整对照的场景包括：",
        "",
        (
            f"1. **双慢卡拓扑差集**：经验库当前仍缺少{missing_dual_text}场景。"
            "同一节点还应继续区分同TP group与不同TP group；"
            "已由经验库覆盖的分支不重复建议。"
        ),
        (
            f"2. **慢卡数量差集**：建议补充{missing_count_text}张慢卡。"
            f"其中{missing_count_reason}。"
        ),
        (
            "3. **同数量不同分布**：对3张及以上慢卡分别比较集中、同亲和组分散、"
            "跨亲和组不对称和跨节点近似对称映射，避免把慢卡数量本身误当成部署经验。"
        ),
        "",
        "## 下一步仿真建议",
        "",
        (
            f"1. **P0—补齐双慢卡拓扑对照**：优先仿真{missing_dual_text}；"
            "保持慢卡数量不变，可以直接识别节点边界、亲和边界和replica映射"
            "对策略的影响。"
        ),
        (
            f"2. **P1—补齐{low_density_text}张慢卡**："
            + (
                "3张采用1/1/1/0或2/1/0/0分布，观察奇数不对称场景。"
                if low_density_missing == [3]
                else (
                    "4张采用1/1/1/1分布，构造偶数对称场景。"
                    if low_density_missing == [4]
                    else (
                        "3张采用1/1/1/0或2/1/0/0分布，4张采用1/1/1/1分布，"
                        "用奇数不对称与偶数对称场景判断策略切换点。"
                        if low_density_missing
                        else "经验库与本轮已经覆盖该数量区间。"
                    )
                )
            )
        ),
        (
            f"3. **P2—提高慢卡密度到{high_density_text}张**："
            + (
                "分别采用2/2/1/1和2/2/2/2分布，"
                if high_density_missing == [6, 8]
                else (
                    "采用2/2/1/1分布，"
                    if high_density_missing == [6]
                    else (
                        "采用2/2/2/2分布，"
                        if high_density_missing == [8]
                        else ""
                    )
                )
            )
            + (
                "检查深PP隔离、DP副本均衡和满卡收益在高密度异构下是否仍成立。"
                if high_density_missing
                else "经验库与本轮已经覆盖该数量区间。"
            )
        ),
        (
            "4. **P3—补7张近对称边界**：采用2/2/2/1分布，验证只差一张慢卡时"
            "对称映射经验是否失效。"
            if 7 in missing_counts
            else "4. **P3—7张近对称边界**：经验库与本轮已经覆盖，无需重复仿真。"
        ),
        "",
        f"上述对照统一保持：{fixed_text}。先改变拓扑位置和慢卡数量，不在同一批同时改变慢卡速度。",
    ]
    (run_dir / "scenario_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def build_final_report(
    config: ScenarioConfig,
    run_dir: Path,
    database: ProgramDatabase,
    catalog: list[Strategy],
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    for result in results.values():
        if result.get("status") != "pass" or "tp" in result.get("critical_path_category_s", {}):
            continue
        timing_path = Path(result["artifact_dir"]) / "node_timings.json"
        if not timing_path.exists():
            continue
        rows = json.loads(timing_path.read_text(encoding="utf-8"))
        critical_ids = set(result["critical_path"]["node_ids"])
        split: dict[str, float] = {}
        for row in rows:
            if row["node_id"] not in critical_ids:
                continue
            category = str(row["category"])
            duration = float(row["duration_s"])
            if category == "compute":
                detail = row.get("detail", {})
                tp_duration = float(
                    detail.get("tp_duration_s")
                    or detail.get("tp_comm_non_overlapped_s")
                    or 0.0
                )
                split["tp"] = split.get("tp", 0.0) + tp_duration
                duration -= tp_duration
            split[category] = split.get(category, 0.0) + duration
        result["critical_path_category_s"] = split
    passed = sorted(
        (value for value in results.values() if value.get("status") == "pass"),
        key=lambda item: item["latency_s"],
    )
    if not passed:
        raise RuntimeError("No strategy completed numerical simulation")
    best = passed[0]
    best_strategy = best["strategy"]
    best_signature = str(best_strategy["signature"])
    best_strategy_object = next(
        strategy for strategy in catalog if strategy.signature == best_signature
    )
    score_evidence = _score_program_evidence(
        config, run_dir, database, best_strategy_object, results
    )
    reasoning = _automatic_reasoning(best, score_evidence)
    placement_evidence = _slow_mapping_evidence(config, best)
    top10 = passed[:10]
    equivalence_tolerance = max(1e-9, abs(float(best["latency_s"])) * 1e-6)
    equivalent_best = [
        item
        for item in passed
        if abs(float(item["latency_s"]) - float(best["latency_s"]))
        <= equivalence_tolerance
    ]
    dimensions = ("pp", "tp", "dp", "micro_batch_num", "schedule", "dp_communication")
    neighbors = []
    for item in passed[1:]:
        differences = [
            key for key in dimensions if item["strategy"][key] != best_strategy[key]
        ]
        if len(differences) == 1:
            neighbors.append({"changed_dimension": differences[0], **item})
    island_best = {}
    for island in database.populations:
        record = database.best(island)
        island_best[island] = record.to_dict() if record else None
    report = {
        "definition_of_best": "minimum critical-path latency among strategies actually simulated",
        "best": best,
        "evaluated_strategy_count": len(results),
        "passed_strategy_count": len(passed),
        "total_strategy_count": len(catalog),
        "coverage": len(results) / len(catalog),
        "top10": top10,
        "equivalent_best": equivalent_best,
        "one_dimension_neighbors": neighbors[:20],
        "island_best": island_best,
        "best_score_program": score_evidence,
        "placement_evidence": placement_evidence,
    }
    write_json(run_dir / "final_report.json", report)
    (run_dir / "best_score_program.py").write_text(
        score_evidence["formula_source"].rstrip() + "\n", encoding="utf-8"
    )
    write_json(run_dir / "score_program_evidence.json", score_evidence)
    best_artifacts = Path(best["artifact_dir"])
    destination = run_dir / "best_strategy"
    destination.mkdir(exist_ok=True)
    for name in ("dag.json", "weighted_dag.json", "critical_path.json", "node_timings.json", "rule_check.json"):
        source = best_artifacts / name
        if source.exists():
            shutil.copy2(source, destination / name)
    topology_fingerprint = hashlib.sha256(
        json.dumps(
            {"topology": config.topology, "network": config.network},
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    experience = {
        "topology_fingerprint": topology_fingerprint,
        "model": config.model,
        "recommended_strategy": best_strategy,
        "rank_mapping": best["rank_mapping"],
        "applicability": {
            "physical_devices": config.topology["total_devices"],
            "model": config.model["name"],
            "workload": config.workload,
            "slow_card_overrides": config.topology.get("device_overrides", {}),
        },
        "evidence": {
            "critical_path_latency_s": best["latency_s"],
            "critical_path_category_s": best["critical_path_category_s"],
            "evaluated_strategy_count": len(results),
            "search_space_size": len(catalog),
            "coverage": len(results) / len(catalog),
            "equivalent_best": [
                item["strategy"] for item in equivalent_best
            ],
        },
        "score_evidence": score_evidence,
        "placement_evidence": placement_evidence,
        "reasoning": reasoning,
        "boundaries": [
            "结论仅针对该模型、训练负载、网络参数和拓扑快照。",
            "当前最优是已实际仿真候选中的最优，不代表穷举意义上的严格全局最优。",
        ],
    }
    write_json(run_dir / "deployment_experience.json", experience)
    lines = [
        "# 部署经验",
        "",
        f"- 推荐策略：PP={best_strategy['pp']}，TP={best_strategy['tp']}，DP={best_strategy['dp']}，"
        f"micro_batch_num={best_strategy['micro_batch_num']}，{best_strategy['schedule']}，"
        f"{best_strategy['dp_communication']}",
        f"- 最长路径训练时延：{best['latency_s']:.6f} s",
        f"- 已仿真覆盖：{len(results)}/{len(catalog)}（{len(results) / len(catalog):.2%}）",
        f"- 关联打分程序：{score_evidence['program_id']}（{score_evidence['island']}岛，"
        f"第{score_evidence['generation']}代）",
        f"- 归因方式：{score_evidence['attribution']}",
        f"- 该候选的score：{score_evidence['candidate_score']}",
        f"- 该候选的完整排序名次：{score_evidence['candidate_rank']}",
        "",
        "## 打分公式",
        "",
        "```python",
        score_evidence["formula_source"].rstrip(),
        "```",
        "",
        "## 部署经验推理",
        "",
        "### 来自打分策略",
        "",
        *[f"- {item}" for item in reasoning["score_derived"]],
        "",
        "### 来自数值仿真",
        "",
        *[f"- {item}" for item in reasoning["simulation_derived"]],
        "",
        "## 机制解释",
        "",
        "该配置是在实际生成 DAG、通过规则检查并执行数值仿真后得到的当前最优候选。"
        "排名依据是 weighted DAG 的最长路径，不使用启发式分数替代真实性能。",
        "",
        "## 适用边界",
        "",
        *[f"- {item}" for item in experience["boundaries"]],
    ]
    (run_dir / "deployment_experience.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_scenario_analysis(config, run_dir, report, experience)
    return report
