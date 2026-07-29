from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_RULES = ROOT / "RuleCheck" / "rules" / "default_rules.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "DagGenerator") not in sys.path:
    sys.path.insert(0, str(ROOT / "DagGenerator"))
if str(ROOT / "SearchRunner") not in sys.path:
    sys.path.insert(0, str(ROOT / "SearchRunner"))

from generate_dag import load_config  # noqa: E402
from run_two_stage_search import output_root_from_config, run_candidate, sanitize_name  # noqa: E402
from score_candidates import build_placement, candidate_name, strategy_signature  # noqa: E402
from SearchRunner.deepseek_client import evolve_program, is_enabled  # noqa: E402
from SearchRunner.evolution_runner import next_program_id, parent_ids, select_program_pair  # noqa: E402
from ScoreExpert.evaluator import check_strategy_rules, finite_or_reject, static_check_source, strategy_metrics  # noqa: E402
from ScoreExpert.island_store import (  # noqa: E402
    ISLANDS,
    append_program,
    load_active_program,
    load_active_program_id,
    load_instruction,
    load_program_bank,
    update_leaders,
    update_program_bank,
)
from ScoreExpert.score_expert import call_score_strategy, compile_score_strategy  # noqa: E402
from ScoreExpert.strategy_space import (  # noqa: E402
    Strategy,
    config_to_cluster,
    config_to_model,
    config_to_profile,
    config_to_workload,
    default_target_scenario,
    enumerate_strategies,
    search_config,
    strategy_to_dict,
    workload_for_strategy,
)


def run_scoreexpert_search(
    config_path: Path,
    rules_path: Path,
    output_root: Path | None = None,
    *,
    rounds: int | None = None,
    seed: int = 20260608,
) -> dict[str, Any]:
    config = load_config(config_path)
    search = search_config(config)
    if output_root is None:
        output_root = output_root_from_config(config)
    run_root = make_run_dir(output_root)
    max_rounds = int(rounds if rounds is not None else search.get("evolution", {}).get("max_rounds", 5))
    initial_top_n = int(search.get("initial_nomination_top_n", 64))
    evolved_top_n = int(search.get("program_nomination_top_n", 32))
    rng = random.Random(seed)
    eval_cache: dict[str, dict[str, Any]] = {}
    score_history: list[dict[str, Any]] = []
    replacement_events: list[dict[str, Any]] = []

    reset_islands_to_seed_programs()
    strategies = enumerate_strategies(config, default_target_scenario(config))
    initialization = run_nomination_evaluation_cycle(
        config=config,
        rules_path=rules_path,
        run_root=run_root,
        cycle_name="initialization",
        strategies=strategies,
        top_n=initial_top_n,
        eval_cache=eval_cache,
        write_initial_matrix=True,
    )
    score_history.extend(round_score_points(0, initialization["leaders_by_island"]))

    round_reports: list[dict[str, Any]] = []
    feedback_contexts = build_feedback_contexts(initialization["nominations_by_island"], initialization["leaders_by_island"])
    for round_number in range(1, max_rounds + 1):
        evolution_results = evolve_all_islands(round_number, feedback_contexts, config, rng)
        cycle = run_nomination_evaluation_cycle(
            config=config,
            rules_path=rules_path,
            run_root=run_root,
            cycle_name=f"round_{round_number:02d}",
            strategies=strategies,
            top_n=evolved_top_n,
            eval_cache=eval_cache,
            write_initial_matrix=False,
        )
        replacements = reinitialize_lagging_islands(cycle["leaders_by_island"], config, rng, round_number)
        replacement_events.extend(replacements)
        feedback_contexts = build_feedback_contexts(cycle["nominations_by_island"], cycle["leaders_by_island"])
        score_history.extend(round_score_points(round_number, cycle["leaders_by_island"]))
        round_reports.append(
            {
                "round": round_number,
                "cycle_dir": cycle["cycle_dir"],
                "nomination_top_n": evolved_top_n,
                "union_candidate_count": cycle["union_candidate_count"],
                "cache_misses": cycle["cache_misses"],
                "leaders": compact_leaders(cycle["leaders_by_island"]),
                "evolution": evolution_results,
                "replacements": replacements,
            }
        )

    cache_path = run_root / "evaluation_cache.json"
    cache_path.write_text(json.dumps(eval_cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    score_chart = run_root / "island_best_latency_trend.png"
    replacement_chart = run_root / "island_replacement_events.png"
    charts_available = plot_latency_history(score_history, score_chart)
    charts_available = plot_replacement_events(replacement_events, replacement_chart) and charts_available

    summary = {
        "status": "pass",
        "run_root": str(run_root.as_posix()),
        "strategy_count": len(strategies),
        "initialization": {
            "nomination_top_n": initial_top_n,
            "union_candidate_count": initialization["union_candidate_count"],
            "cache_misses": initialization["cache_misses"],
            "leaders": compact_leaders(initialization["leaders_by_island"]),
            "initial_score_matrix_md": initialization.get("initial_score_matrix_md"),
        },
        "rounds": round_reports,
        "evaluation_cache_json": str(cache_path.as_posix()),
        "score_chart": str(score_chart.as_posix()) if charts_available else None,
        "replacement_chart": str(replacement_chart.as_posix()) if charts_available else None,
        "deepseek_enabled": is_enabled(config),
        "overlapopt": "disabled",
    }
    report_path = run_root / "scoreexpert_search_report.md"
    report_path.write_text(render_report(summary), encoding="utf-8")
    summary["report_md"] = str(report_path.as_posix())
    return summary


def reset_islands_to_seed_programs() -> None:
    for island in ISLANDS:
        bank = load_program_bank(island)
        seed = next((program for program in bank if str(program.get("program_id")) == "v0"), bank[0])
        seed = copy.deepcopy(seed)
        seed["program_id"] = "v0"
        seed["parent_ids"] = []
        seed["island_score"] = None
        seed["evaluation"] = None
        seed["origin"] = "seed"
        update_program_bank(island, [seed], "v0")


def run_nomination_evaluation_cycle(
    *,
    config: dict[str, Any],
    rules_path: Path,
    run_root: Path,
    cycle_name: str,
    strategies: list[Strategy],
    top_n: int,
    eval_cache: dict[str, dict[str, Any]],
    write_initial_matrix: bool,
) -> dict[str, Any]:
    cycle_dir = run_root / cycle_name
    cycle_dir.mkdir(parents=True, exist_ok=True)
    score_rows_by_island = {island: score_program_full_space(config, island, strategies) for island in ISLANDS}
    nominations_by_island = {
        island: rows[: min(top_n, len(rows))]
        for island, rows in score_rows_by_island.items()
    }
    nominated_by_strategy = nominated_islands_by_strategy(nominations_by_island)
    union_candidates = unique_nominated_candidates(nominations_by_island)
    cache_misses = evaluate_cache_misses(config, rules_path, cycle_dir, union_candidates, eval_cache)
    attach_evaluation_to_nominations(nominations_by_island, eval_cache)
    leaders_by_island = select_latency_leaders(nominations_by_island)
    for island, leaders in leaders_by_island.items():
        update_leaders(island, leaders)
        update_active_program_evaluation(island, leaders)
    matrix_path = None
    if write_initial_matrix:
        matrix_path = cycle_dir / "initial_score_matrix.md"
        matrix_path.write_text(render_initial_score_matrix(score_rows_by_island, nominated_by_strategy, eval_cache), encoding="utf-8")
    return {
        "cycle_dir": str(cycle_dir.as_posix()),
        "score_rows_by_island": score_rows_by_island,
        "nominations_by_island": nominations_by_island,
        "leaders_by_island": leaders_by_island,
        "union_candidate_count": len(union_candidates),
        "cache_misses": cache_misses,
        "initial_score_matrix_md": None if matrix_path is None else str(matrix_path.as_posix()),
    }


def score_program_full_space(config: dict[str, Any], island: str, strategies: list[Strategy]) -> list[dict[str, Any]]:
    source = str(load_active_program(island)["source"])
    sandbox = static_check_source(source, int(search_config(config).get("sandbox", {}).get("max_program_chars", 6000)))
    if not sandbox.get("valid"):
        raise ValueError(f"{island} active program failed safety check: {sandbox.get('reason')}")
    score_fn = compile_score_strategy(source)
    model = config_to_model(config)
    workload = config_to_workload(config)
    profile = config_to_profile(config)
    cluster = config_to_cluster(config, default_target_scenario(config))
    rows: list[dict[str, Any]] = []
    for strategy in strategies:
        metrics = strategy_metrics(strategy, model, cluster, workload)
        rule_check = check_strategy_rules(strategy, metrics, model, cluster)
        try:
            score = finite_or_reject(call_score_strategy(score_fn, strategy, model, cluster, workload, profile))
        except Exception:
            continue
        rows.append(candidate_from_strategy(config, island, strategy, score, metrics, rule_check, cluster))
    rows.sort(key=lambda item: float(item["island_score"]), reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["score_rank"] = rank
    return rows


def candidate_from_strategy(
    config: dict[str, Any],
    island: str,
    strategy: Strategy,
    score: float,
    metrics: Any,
    rule_check: dict[str, Any],
    cluster: dict[str, Any],
) -> dict[str, Any]:
    metrics_payload = asdict(metrics)
    metrics_payload.pop("estimated_iteration_time_s", None)
    return {
        "island": island,
        "source_islands": [island],
        "pp_size": strategy.pp_size,
        "micro_batch_num": strategy.micro_batch_num,
        "tp_size": strategy.tp_size,
        "dp_size": strategy.dp_size,
        "active_gpus": strategy.active_gpus,
        "idle_gpus": strategy.idle_gpus,
        "island_score": float(score),
        "score": float(score),
        "scoring_mode": "score_expert_program_nomination",
        "score_status": "nominated_by_program_score",
        "rule_check": rule_check,
        "risk_labels": list(rule_check.get("risk_labels", [])),
        "metrics": metrics_payload,
        "signature": strategy_signature(strategy),
        "candidate_name": candidate_name(island, strategy),
        "placement": build_placement(
            config,
            strategy.pp_size,
            strategy.micro_batch_num,
            strategy.tp_size,
            strategy.dp_size,
            strategy.active_gpus,
            strategy.idle_gpus,
            cluster,
        ),
        "memory_estimate_gb": {
            "estimated_total_gb": metrics.estimated_total_gb,
            "global_batch_size": metrics.global_batch_size,
            "local_minibatch_size": metrics.local_minibatch_size,
            "derived_microbatch_size": metrics.derived_microbatch_size,
        },
    }


def nominated_islands_by_strategy(nominations_by_island: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for island, nominations in nominations_by_island.items():
        for candidate in nominations:
            key = strategy_key(candidate)
            mapping.setdefault(key, [])
            if island not in mapping[key]:
                mapping[key].append(island)
    return mapping


def unique_nominated_candidates(nominations_by_island: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for nominations in nominations_by_island.values():
        for candidate in nominations:
            selected.setdefault(strategy_key(candidate), candidate)
    return list(selected.values())


def evaluate_cache_misses(
    config: dict[str, Any],
    rules_path: Path,
    cycle_dir: Path,
    candidates: list[dict[str, Any]],
    eval_cache: dict[str, dict[str, Any]],
) -> int:
    misses = 0
    eval_dir = cycle_dir / "evaluations"
    for candidate in candidates:
        key = strategy_key(candidate)
        if key in eval_cache:
            continue
        misses += 1
        output_name = sanitize_name(strategy_output_name(candidate))
        score_rule = candidate.get("rule_check") or {}
        if score_rule.get("status") != "pass":
            eval_cache[key] = {
                "strategy_key": key,
                "evaluation_status": "fail",
                "total_latency_s": None,
                "rulecheck_status": "not_run",
                "valuesim_status": "not_run",
                "failure_reason": ",".join(str(item) for item in score_rule.get("violations", [])) or "score_hard_constraint_failed",
                "hard_oom": "memory_hard_overflow" in set(score_rule.get("violations", [])),
                "timeout": False,
                "candidate_dir": "",
            }
            continue
        try:
            result = run_candidate(
                base_config=config,
                candidate=copy.deepcopy(candidate),
                candidate_dir=eval_dir / output_name,
                rules_path=rules_path,
                enable_overlap=False,
            )
            eval_cache[key] = cache_entry_from_result(key, result)
        except Exception as exc:  # noqa: BLE001
            eval_cache[key] = {
                "strategy_key": key,
                "evaluation_status": "fail",
                "total_latency_s": None,
                "rulecheck_status": "unknown",
                "valuesim_status": "unknown",
                "failure_reason": str(exc),
                "hard_oom": bool("oom" in str(exc).lower()),
                "timeout": bool("timeout" in str(exc).lower()),
                "candidate_dir": str((eval_dir / output_name).as_posix()),
            }
    return misses


def cache_entry_from_result(key: str, result: dict[str, Any]) -> dict[str, Any]:
    flow_status = str(result.get("flow_status", "fail"))
    flow_report = result.get("flow_report") or {}
    steps = {str(step.get("name")): step for step in flow_report.get("steps", []) if isinstance(step, dict)}
    evaluation = result.get("evaluation") or {}
    total_latency = evaluation.get("total_latency_s", evaluation.get("baseline_latency_s"))
    failure = failure_reason(result, steps, evaluation)
    status = "pass" if valid_total_latency(total_latency) and flow_status == "pass" else "fail"
    return {
        "strategy_key": key,
        "evaluation_status": status,
        "total_latency_s": float(total_latency) if valid_total_latency(total_latency) else None,
        "rulecheck_status": str(steps.get("RuleCheck", {}).get("status", "unknown")),
        "valuesim_status": str(steps.get("ValueSim", {}).get("status", "unknown")),
        "failure_reason": failure,
        "hard_oom": bool("memory_hard_overflow" in failure or "oom" in failure.lower()),
        "timeout": bool("timeout" in failure.lower()),
        "candidate_dir": str(result.get("candidate_dir", "")),
    }


def failure_reason(result: dict[str, Any], steps: dict[str, dict[str, Any]], evaluation: dict[str, Any]) -> str:
    if result.get("flow_status") != "pass":
        failed = [step for step in steps.values() if step.get("status") != "pass"]
        if failed:
            return str(failed[0].get("message", failed[0].get("name", "flow_failed")))
        return "flow_failed"
    if not valid_total_latency(evaluation.get("total_latency_s", evaluation.get("baseline_latency_s"))):
        return "missing_total_latency_s"
    return ""


def attach_evaluation_to_nominations(nominations_by_island: dict[str, list[dict[str, Any]]], eval_cache: dict[str, dict[str, Any]]) -> None:
    for nominations in nominations_by_island.values():
        for candidate in nominations:
            entry = eval_cache.get(strategy_key(candidate), {})
            candidate["evaluation_status"] = entry.get("evaluation_status", "not_evaluated")
            candidate["total_latency_s"] = entry.get("total_latency_s")
            candidate["rulecheck_status"] = entry.get("rulecheck_status", "")
            candidate["valuesim_status"] = entry.get("valuesim_status", "")
            candidate["failure_reason"] = entry.get("failure_reason", "")
            candidate["hard_oom"] = bool(entry.get("hard_oom", False))
            candidate["timeout"] = bool(entry.get("timeout", False))
            candidate["candidate_dir"] = entry.get("candidate_dir", "")


def select_latency_leaders(nominations_by_island: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    leaders: dict[str, list[dict[str, Any]]] = {}
    for island, nominations in nominations_by_island.items():
        valid = [candidate for candidate in nominations if is_valid_for_latency_ranking(candidate)]
        valid.sort(key=lambda item: float(item["total_latency_s"]))
        leaders[island] = [leader_payload(candidate) for candidate in valid[:4]]
    return leaders


def is_valid_for_latency_ranking(candidate: dict[str, Any]) -> bool:
    return (
        candidate.get("evaluation_status") == "pass"
        and valid_total_latency(candidate.get("total_latency_s"))
        and candidate.get("rulecheck_status") == "pass"
        and candidate.get("valuesim_status") == "pass"
        and not bool(candidate.get("hard_oom"))
        and not bool(candidate.get("timeout"))
        and (candidate.get("rule_check") or {}).get("status") == "pass"
    )


def leader_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "island",
        "pp_size",
        "micro_batch_num",
        "tp_size",
        "dp_size",
        "active_gpus",
        "idle_gpus",
        "island_score",
        "score_rank",
        "total_latency_s",
        "evaluation_status",
        "rulecheck_status",
        "valuesim_status",
        "failure_reason",
        "candidate_dir",
        "metrics",
        "rule_check",
    )
    return {key: copy.deepcopy(candidate.get(key)) for key in keys if key in candidate}


def update_active_program_evaluation(island: str, leaders: list[dict[str, Any]]) -> None:
    active_id = load_active_program_id(island)
    bank = load_program_bank(island)
    best = leaders[0] if leaders else {}
    for program in bank:
        if str(program.get("program_id")) == active_id:
            program["island_score"] = best.get("island_score")
            program["evaluation"] = {
                "total_latency_s": best.get("total_latency_s"),
                "pp_size": best.get("pp_size"),
                "micro_batch_num": best.get("micro_batch_num"),
                "tp_size": best.get("tp_size"),
                "dp_size": best.get("dp_size"),
            } if best else None
            break
    update_program_bank(island, bank, active_id)


def build_feedback_contexts(
    nominations_by_island: dict[str, list[dict[str, Any]]],
    leaders_by_island: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for island, nominations in nominations_by_island.items():
        valid = [item for item in nominations if valid_total_latency(item.get("total_latency_s"))]
        score_sorted = sorted(valid, key=lambda item: float(item.get("island_score", float("-inf"))), reverse=True)
        latency_sorted = sorted(valid, key=lambda item: float(item.get("total_latency_s", math.inf)))
        bad_cases = [compact_candidate(item) for item in score_sorted[:12] if float(item.get("total_latency_s", math.inf)) > latency_quantile(valid, 0.70)][:4]
        missed_cases = [compact_candidate(item) for item in latency_sorted[:12] if int(item.get("score_rank", 999999)) > max(4, len(nominations) // 2)][:4]
        failures = [compact_candidate(item) for item in nominations if item.get("evaluation_status") != "pass"][:6]
        contexts[island] = {
            "latency_top4": [compact_candidate(item) for item in leaders_by_island.get(island, [])],
            "bad_cases": bad_cases,
            "missed_cases": missed_cases,
            "failures": failures,
            "suggestions": [
                "Use score only to nominate candidates; real total_latency_s determines leaders.",
                "Increase scores for patterns found in missed_cases and reduce scores for bad_cases.",
                "Do not add rough latency proxy terms; prefer interpretable terms tied to strategy shape.",
            ],
        }
    return contexts


def latency_quantile(candidates: list[dict[str, Any]], q: float) -> float:
    values = sorted(float(item["total_latency_s"]) for item in candidates if valid_total_latency(item.get("total_latency_s")))
    if not values:
        return math.inf
    index = min(len(values) - 1, max(0, int(len(values) * q)))
    return values[index]


def evolve_all_islands(round_number: int, feedback_contexts: dict[str, dict[str, Any]], config: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    tasks = [(island, build_evolution_request(island, round_number, feedback_contexts.get(island, {}), rng)) for island in ISLANDS]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=min(4, len(tasks))) as executor:
        future_map = {
            executor.submit(generate_program_source, island, request, config): (island, request)
            for island, request in tasks
        }
        for future in as_completed(future_map):
            island, request = future_map[future]
            try:
                source = future.result()
                result = append_evolved_program(island, source, request)
            except Exception as exc:  # noqa: BLE001
                result = {
                    "island": island,
                    "status": "fail",
                    "reason": str(exc),
                    "parent_ids": request["parent_ids"],
                }
            results.append(result)
    results.sort(key=lambda item: ISLANDS.index(str(item.get("island"))))
    return results


def build_evolution_request(island: str, round_number: int, feedback: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    bank = load_program_bank(island)
    if round_number == 1 or len(bank) == 1:
        v0 = bank[0]
        v1 = bank[0]
        parents = [str(v0.get("program_id", "v0"))]
        mode = "bootstrap"
    else:
        shuffled = list(bank)
        rng.shuffle(shuffled)
        try:
            v0, v1 = select_program_pair(shuffled)
        except Exception:
            v0, v1 = shuffled[0], shuffled[min(1, len(shuffled) - 1)]
        parents = parent_ids(v0, v1)
        mode = "best_shot_k2"
    return {"v0": v0, "v1": v1, "parent_ids": parents, "feedback": feedback, "mode": mode}


def generate_program_source(island: str, request: dict[str, Any], config: dict[str, Any]) -> str | None:
    if not is_enabled(config):
        return None
    return evolve_program(
        island=island,
        instruction=load_instruction(island),
        v0=request["v0"],
        v1=request["v1"],
        feedback={
            "mode": request["mode"],
            "summary": "Evolve the scoring program using real Evaluation feedback. Score is only for nomination; total_latency_s decides leaders.",
            **request["feedback"],
        },
        config=config,
    )


def append_evolved_program(island: str, source: str | None, request: dict[str, Any]) -> dict[str, Any]:
    if not source:
        return {
            "island": island,
            "status": "skipped",
            "reason": "DEEPSEEK_API_KEY is not set or no source was returned",
            "parent_ids": request["parent_ids"],
            "mode": request["mode"],
        }
    check = static_check_source(source)
    if not check.get("valid"):
        return {
            "island": island,
            "status": "fail",
            "reason": str(check.get("reason")),
            "parent_ids": request["parent_ids"],
            "mode": request["mode"],
        }
    bank = load_program_bank(island)
    program_id = next_program_id(bank)
    append_program(
        island,
        {
            "program_id": program_id,
            "parent_ids": request["parent_ids"],
            "source": source,
            "island_score": None,
            "evaluation": None,
            "origin": f"round_{request['mode']}",
        },
        activate=True,
    )
    return {
        "island": island,
        "status": "pass",
        "program_id": program_id,
        "parent_ids": request["parent_ids"],
        "mode": request["mode"],
    }


def reinitialize_lagging_islands(
    leaders_by_island: dict[str, list[dict[str, Any]]],
    config: dict[str, Any],
    rng: random.Random,
    round_number: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    top1 = {island: float(leaders[0]["total_latency_s"]) for island, leaders in leaders_by_island.items() if leaders}
    top4_pool = {
        island: [float(item["total_latency_s"]) for item in leaders]
        for island, leaders in leaders_by_island.items()
        if leaders
    }
    for island, latency in top1.items():
        other_top4 = [value for other, values in top4_pool.items() if other != island for value in values]
        if not other_top4 or latency <= max(other_top4):
            continue
        source_islands = [other for other in ISLANDS if other != island]
        samples = sample_programs(source_islands, rng)
        if len(samples) < 2:
            continue
        source_programs = [samples[0][1], samples[1][1]]
        replacement = build_replacement_program(island, source_programs, samples, config)
        update_program_bank(island, replacement, str(replacement[0]["program_id"]))
        events.append(
            {
                "round": round_number,
                "target_island": island,
                "target_top1_latency_s": latency,
                "other_top4_worst_latency_s": max(other_top4),
                "source_islands": [item[0] for item in samples[:2]],
                "source_program_ids": [str(item[1].get("program_id")) for item in samples[:2]],
            }
        )
    return events


def sample_programs(islands: list[str], rng: random.Random) -> list[tuple[str, dict[str, Any]]]:
    pool: list[tuple[str, dict[str, Any]]] = []
    for island in islands:
        for program in load_program_bank(island):
            if program.get("source"):
                pool.append((island, program))
    rng.shuffle(pool)
    return pool[:2]


def build_replacement_program(
    target_island: str,
    source_programs: list[dict[str, Any]],
    samples: list[tuple[str, dict[str, Any]]],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    parents = parent_ids(source_programs[0], source_programs[1])
    source = str(source_programs[0].get("source", ""))
    if is_enabled(config):
        try:
            adapted = evolve_program(
                island=target_island,
                instruction=load_instruction(target_island),
                v0=source_programs[0],
                v1=source_programs[1],
                feedback={
                    "mode": "cross_island_reinitialization",
                    "summary": "Adapt source programs to the target island instruction. Score only nominates; total_latency_s decides leaders.",
                },
                config=config,
            )
            if adapted and static_check_source(adapted).get("valid"):
                source = adapted
        except Exception:
            source = str(source_programs[0].get("source", ""))
    return [
        {
            "program_id": "v0",
            "parent_ids": parents,
            "source": source,
            "island_score": None,
            "evaluation": None,
            "origin": "latency_reinitialization_from_" + "_and_".join(item[0] for item in samples[:2]),
        }
    ]


def render_initial_score_matrix(
    score_rows_by_island: dict[str, list[dict[str, Any]]],
    nominated_by_strategy: dict[str, list[str]],
    eval_cache: dict[str, dict[str, Any]],
) -> str:
    by_strategy: dict[str, dict[str, Any]] = {}
    for island, rows in score_rows_by_island.items():
        for row in rows:
            key = strategy_key(row)
            item = by_strategy.setdefault(
                key,
                {
                    "pp_size": row["pp_size"],
                    "micro_batch_num": row["micro_batch_num"],
                    "tp_size": row["tp_size"],
                    "dp_size": row["dp_size"],
                    "active_gpus": row["active_gpus"],
                    "idle_gpus": row["idle_gpus"],
                    "scores": {},
                },
            )
            item["scores"][island] = row["island_score"]
    lines = [
        "# Initial Score Matrix",
        "",
        "| PP | MBN | TP | DP | Active GPUs | Idle GPUs | memory_safe score | topology_affinity score | pipeline_efficiency score | balanced_generalist score | nominated_by_islands | evaluation_status | total_latency_s | rulecheck_status | valuesim_status | failure_reason |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---:|---|---|---|",
    ]
    for key, item in sorted(by_strategy.items(), key=lambda pair: strategy_tuple_from_key(pair[0])):
        cache = eval_cache.get(key, {})
        scores = item["scores"]
        latency = cache.get("total_latency_s")
        latency_text = "" if latency is None else f"{float(latency):.9f}"
        lines.append(
            "| "
            + " | ".join(
                [
                    str(item["pp_size"]),
                    str(item["micro_batch_num"]),
                    str(item["tp_size"]),
                    str(item["dp_size"]),
                    str(item["active_gpus"]),
                    str(item["idle_gpus"]),
                    fmt_score(scores.get("memory_safe")),
                    fmt_score(scores.get("topology_affinity")),
                    fmt_score(scores.get("pipeline_efficiency")),
                    fmt_score(scores.get("balanced_generalist")),
                    ", ".join(nominated_by_strategy.get(key, [])),
                    str(cache.get("evaluation_status", "")),
                    latency_text,
                    str(cache.get("rulecheck_status", "")),
                    str(cache.get("valuesim_status", "")),
                    sanitize_md_cell(str(cache.get("failure_reason", ""))),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# ScoreExpert Search Report",
        "",
        f"- Status: `{summary['status']}`",
        f"- Run root: `{summary['run_root']}`",
        f"- Strategy count: {summary['strategy_count']}",
        f"- DeepSeek enabled: `{summary['deepseek_enabled']}`",
        "- OverlapOPT: `disabled`",
        f"- Initial score matrix: `{summary['initialization'].get('initial_score_matrix_md')}`",
        f"- Evaluation cache: `{summary['evaluation_cache_json']}`",
        f"- Latency trend chart: `{summary['score_chart']}`",
        f"- Replacement chart: `{summary['replacement_chart']}`",
        "",
        "## Initialization",
        "",
        f"- Nomination Top-N: {summary['initialization']['nomination_top_n']}",
        f"- Union candidates: {summary['initialization']['union_candidate_count']}",
        f"- Cache misses evaluated: {summary['initialization']['cache_misses']}",
        "",
    ]
    lines.extend(render_leader_section(summary["initialization"]["leaders"]))
    lines.extend(["", "## Evolution Rounds", ""])
    for item in summary.get("rounds", []):
        lines.extend(
            [
                f"### Round {item['round']}",
                "",
                f"- Nomination Top-N: {item['nomination_top_n']}",
                f"- Union candidates: {item['union_candidate_count']}",
                f"- Cache misses evaluated: {item['cache_misses']}",
                f"- Cycle directory: `{item['cycle_dir']}`",
                "",
                "Evolution:",
            ]
        )
        for evo in item.get("evolution", []):
            lines.append(f"- `{evo.get('island')}`: `{evo.get('status')}`, mode=`{evo.get('mode')}`, parents=`{', '.join(str(parent) for parent in evo.get('parent_ids', []))}`")
        replacements = item.get("replacements", [])
        if replacements:
            lines.append("")
            lines.append("Replacements:")
            for event in replacements:
                lines.append(f"- `{event['target_island']}` reset from `{', '.join(event['source_islands'])}`.")
        lines.append("")
        lines.extend(render_leader_section(item["leaders"]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_leader_section(leaders_by_island: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines = [
        "| Island | Rank | Strategy | Score | Score rank | Total latency (s) |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for island in ISLANDS:
        leaders = leaders_by_island.get(island, [])
        if not leaders:
            lines.append(f"| `{island}` |  | no valid leaders |  |  |  |")
            continue
        for rank, leader in enumerate(leaders, start=1):
            strategy = f"PP={leader.get('pp_size')}, MBN={leader.get('micro_batch_num')}, TP={leader.get('tp_size')}, DP={leader.get('dp_size')}"
            lines.append(
                f"| `{island}` | {rank} | {strategy} | {float(leader.get('island_score', 0.0)):.6f} | {leader.get('score_rank', '')} | {float(leader.get('total_latency_s', math.nan)):.9f} |"
            )
    return lines


def plot_latency_history(history: list[dict[str, Any]], output: Path) -> bool:
    try:
        import matplotlib
    except ModuleNotFoundError:
        return False

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    for island in ISLANDS:
        points = [item for item in history if item["island"] == island]
        ax.plot([item["round"] for item in points], [item["total_latency_s"] for item in points], marker="o", label=island)
    ax.set_title("Best Total Latency By Round")
    ax.set_xlabel("Round")
    ax.set_ylabel("Total latency (s)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return True


def plot_replacement_events(events: list[dict[str, Any]], output: Path) -> bool:
    try:
        import matplotlib
    except ModuleNotFoundError:
        return False

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 4))
    island_index = {island: index for index, island in enumerate(ISLANDS)}
    if events:
        xs = [int(item["round"]) for item in events]
        ys = [island_index[str(item["target_island"])] for item in events]
        ax.scatter(xs, ys, s=90)
        for item in events:
            ax.annotate(",".join(item["source_islands"]), (int(item["round"]), island_index[str(item["target_island"])]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    else:
        ax.text(0.5, 0.5, "No island replacements", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Island Program Replacement Events")
    ax.set_xlabel("Round")
    ax.set_ylabel("Reinitialized island")
    ax.set_yticks(list(island_index.values()))
    ax.set_yticklabels(list(island_index.keys()))
    ax.set_xlim(-0.5, max(1.5, max([int(item["round"]) for item in events], default=1) + 0.5))
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return True


def compact_leaders(leaders_by_island: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {
        island: [compact_candidate(leader) for leader in leaders]
        for island, leaders in leaders_by_island.items()
    }


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "island": candidate.get("island"),
        "pp_size": candidate.get("pp_size"),
        "micro_batch_num": candidate.get("micro_batch_num"),
        "tp_size": candidate.get("tp_size"),
        "dp_size": candidate.get("dp_size"),
        "island_score": candidate.get("island_score"),
        "score_rank": candidate.get("score_rank"),
        "total_latency_s": candidate.get("total_latency_s"),
        "evaluation_status": candidate.get("evaluation_status"),
        "failure_reason": candidate.get("failure_reason"),
    }


def round_score_points(round_number: int, leaders_by_island: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for island in ISLANDS:
        leaders = leaders_by_island.get(island, [])
        points.append(
            {
                "round": round_number,
                "island": island,
                "total_latency_s": float(leaders[0]["total_latency_s"]) if leaders else math.nan,
            }
        )
    return points


def strategy_key(candidate: dict[str, Any]) -> str:
    return f"pp{int(candidate['pp_size'])}_mbn{int(candidate['micro_batch_num'])}_tp{int(candidate['tp_size'])}_dp{int(candidate['dp_size'])}"


def strategy_tuple_from_key(key: str) -> tuple[int, int, int, int]:
    parts = dict(part.split("", 1) for part in [])  # never used; keeps type checkers away from regex dependency
    del parts
    values = {}
    for token in key.split("_"):
        if token.startswith("pp"):
            values["pp"] = int(token[2:])
        elif token.startswith("mbn"):
            values["mbn"] = int(token[3:])
        elif token.startswith("tp"):
            values["tp"] = int(token[2:])
        elif token.startswith("dp"):
            values["dp"] = int(token[2:])
    return (values["pp"], values["mbn"], values["tp"], values["dp"])


def strategy_output_name(candidate: dict[str, Any]) -> str:
    return f"eval_pp{candidate['pp_size']}_mbn{candidate['micro_batch_num']}_tp{candidate['tp_size']}_dp{candidate['dp_size']}"


def valid_total_latency(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def fmt_score(value: Any) -> str:
    return "" if value is None else f"{float(value):.6f}"


def sanitize_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def make_run_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"scoreexpert_search_{timestamp}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = output_root / f"scoreexpert_search_{timestamp}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ScoreExpert program-nomination search.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--rules", type=Path, default=DEFAULT_RULES)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260608)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_scoreexpert_search(args.config, args.rules, args.output_root, rounds=args.rounds, seed=args.seed)
    print(f"ScoreExpert search status: {summary['status']}")
    print(f"Run root: {summary['run_root']}")
    print(f"Report: {summary['report_md']}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
