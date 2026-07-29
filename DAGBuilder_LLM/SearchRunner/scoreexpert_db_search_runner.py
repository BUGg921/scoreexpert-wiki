from __future__ import annotations

import argparse
import ast
import csv
import copy
import json
import math
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "config.py"
DEFAULT_DATABASE = ROOT / "EVALUATION_DATABASE.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "DagGenerator") not in sys.path:
    sys.path.insert(0, str(ROOT / "DagGenerator"))
if str(ROOT / "SearchRunner") not in sys.path:
    sys.path.insert(0, str(ROOT / "SearchRunner"))

from generate_dag import load_config  # noqa: E402
from run_two_stage_search import output_root_from_config  # noqa: E402
from SearchRunner.deepseek_client import evolve_program, evolve_program_with_usage, is_enabled  # noqa: E402
from SearchRunner.evolution_runner import next_program_id, parent_ids, select_program_pair  # noqa: E402
from ScoreExpert.evaluator import finite_or_reject, static_check_source  # noqa: E402
from ScoreExpert.island_store import (  # noqa: E402
    ISLANDS,
    append_program,
    extract_score_source,
    load_instruction,
    load_program_bank,
    read_seed_source,
    update_program_bank,
)
from ScoreExpert.score_expert import call_score_strategy, compile_score_strategy  # noqa: E402
from ScoreExpert.strategy_space import config_to_cluster, config_to_model, config_to_profile, config_to_workload  # noqa: E402


StrategyKey = tuple[int, int, int, int]
EXPERIENCE_BANK = ROOT / "ScoreExpert" / "experience_bank.md"


def run_db_search(
    config_path: Path,
    database_path: Path,
    output_root: Path | None = None,
    *,
    max_rounds: int | None = None,
    seed: int = 20260613,
    reset_islands: bool = True,
) -> dict[str, Any]:
    config = load_config(config_path)
    if output_root is None:
        output_root = output_root_from_config(config)
    search_cfg = dict(config.get("search_config", {}))
    max_rounds = int(max_rounds if max_rounds is not None else search_cfg.get("score_db_search", {}).get("max_rounds", 100))
    patience_rounds = int(search_cfg.get("score_db_search", {}).get("patience_rounds", 10))
    min_improvement = float(search_cfg.get("score_db_search", {}).get("min_relative_improvement", 0.001))
    target_gap = float(search_cfg.get("score_db_search", {}).get("target_gap_to_database_best", 0.01))
    stop_on_target_gap = bool(search_cfg.get("score_db_search", {}).get("stop_on_target_gap", False))
    stop_on_patience = bool(search_cfg.get("score_db_search", {}).get("stop_on_patience", False))
    ranking_top_k = int(search_cfg.get("score_db_search", {}).get("ranking_top_k", 16))
    rng = random.Random(seed)

    run_root = make_run_dir(output_root)
    db = load_evaluation_database(database_path)
    if reset_islands:
        reset_islands_to_seed_programs()
    adaptive_contexts = initialize_adaptive_contexts(db)
    llm_usage: list[dict[str, Any]] = []
    if reset_islands:
        seed_results, seed_usage, seed_timing = ensure_second_seed_programs(adaptive_contexts, db, config)
        llm_usage.extend(seed_usage)
        llm_timing_records: list[dict[str, Any]] = []
        llm_timing_records.extend(seed_timing)
    else:
        seed_results = current_program_bank_summary()
        llm_timing_records = []

    best: dict[str, Any] | None = None
    best_history: list[float] = []
    rounds: list[dict[str, Any]] = []
    replacements: list[dict[str, Any]] = []
    db_best = best_database_entry(db)
    stop_reason = "max_rounds"

    for round_index in range(1, max_rounds + 1):
        ranking = evaluate_all_programs_against_database(config, db, ranking_top_k)
        scores = ranking["island_scores"]
        best_candidate = ranking.get("best_candidate")
        if isinstance(best_candidate, dict):
            best = best_candidate
            best_history.append(float(best_candidate["total_latency_s"]))
        else:
            best_history.append(math.inf)

        feedback_payload = build_ranking_feedback_payload(ranking, db)
        experience_events = update_experience_bank(round_index, feedback_payload)
        update_program_ranking_feedback(ranking, round_index)
        adaptive_contexts = update_adaptive_contexts_from_ranking(adaptive_contexts, ranking, db, feedback_payload)
        evolution_results, round_usage, round_timing = evolve_all_islands(round_index, adaptive_contexts, config, rng)
        llm_usage.extend(round_usage)
        llm_timing_records.extend(round_timing)
        replacement_events = maybe_replace_islands(round_index, adaptive_contexts, config, rng)
        replacements.extend(replacement_events)

        round_record = {
            "round": round_index,
            "mode": "full_database_ranking",
            "strategy": "all_database_strategies",
            "scores": scores,
            "evaluation": {"status": "pass", "mode": "full_database_ranking"},
            "evaluation_feedback": feedback_payload,
            "latency": None if not isinstance(best_candidate, dict) else best_candidate.get("total_latency_s"),
            "ranking": ranking,
            "diversity": compute_diversity_metrics(ranking),
            "adjustment": {"type": "none", "reason": "full database ranking feedback"},
            "next_strategy": "all_database_strategies",
            "evolution": evolution_results,
            "experience_events": experience_events,
            "adaptive_context": copy.deepcopy(adaptive_contexts),
            "replacements": replacement_events,
            "best_so_far": None if best is None else {"strategy": strategy_payload(best["strategy"]), "total_latency_s": best["total_latency_s"]},
        }
        rounds.append(round_record)
        write_run_outputs(
            run_root,
            build_summary(
                run_root=run_root,
                database_path=database_path,
                db=db,
                db_best=db_best,
                seed_results=seed_results,
                max_rounds=max_rounds,
                stop_on_target_gap=stop_on_target_gap,
                stop_on_patience=stop_on_patience,
                stop_reason="running",
                best=best,
                rounds=rounds,
                replacements=replacements,
                llm_usage=llm_usage,
                llm_timing=llm_timing_records,
                deepseek_enabled=is_enabled(config),
                final=False,
            ),
        )

        if best is not None:
            gap = (float(best["total_latency_s"]) - float(db_best["total_latency_s"])) / float(db_best["total_latency_s"])
            if stop_on_target_gap and gap <= target_gap:
                stop_reason = "target_gap_reached"
                break
        if stop_on_patience and has_converged(best_history, patience_rounds, min_improvement):
            stop_reason = "patience_converged"
            break

    summary = build_summary(
        run_root=run_root,
        database_path=database_path,
        db=db,
        db_best=db_best,
        seed_results=seed_results,
        max_rounds=max_rounds,
        stop_on_target_gap=stop_on_target_gap,
        stop_on_patience=stop_on_patience,
        stop_reason=stop_reason,
        best=best,
        rounds=rounds,
        replacements=replacements,
        llm_usage=llm_usage,
        llm_timing=llm_timing_records,
        deepseek_enabled=is_enabled(config),
        final=True,
    )
    write_run_outputs(run_root, summary)
    return summary


def load_evaluation_database(path: Path) -> dict[StrategyKey, dict[str, Any]]:
    rows: dict[StrategyKey, dict[str, Any]] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        if not line.startswith("| ") or line.startswith("| Rank ") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 16 or not cells[0].isdigit():
            continue
        try:
            pp = int(cells[1])
            tp = int(cells[2])
            dp = int(cells[3])
            mb = int(cells[4])
            overlap_latency = float(cells[10])
            baseline_latency = float(cells[9])
        except ValueError:
            continue
        if cells[14].lower() != "pass":
            continue
        key = (pp, tp, dp, mb)
        entry = {
            "strategy": key,
            "status": "pass",
            "total_latency_s": overlap_latency,
            "baseline_latency_s": baseline_latency,
            "pp_strategy": cells[7],
            "dp_strategy": cells[8],
            "overlap_ratio": cells[12],
            "events": int(cells[13]) if cells[13].isdigit() else None,
            "rulecheck": cells[14],
            "dag_id": cells[15],
        }
        if key not in rows or overlap_latency < float(rows[key]["total_latency_s"]):
            rows[key] = entry
    return rows


def lookup_strategy(db: dict[StrategyKey, dict[str, Any]], strategy: StrategyKey) -> dict[str, Any]:
    entry = db.get(strategy)
    if entry is None:
        return {"status": "invalid", "reason": "strategy_not_found_in_database", "total_latency_s": None}
    return dict(entry)


def best_database_entry(db: dict[StrategyKey, dict[str, Any]]) -> dict[str, Any]:
    return min(db.values(), key=lambda item: float(item["total_latency_s"]))


def reset_islands_to_seed_programs() -> None:
    for island in ISLANDS:
        seed_source = extract_score_source(read_seed_source(island))
        program = {
            "program_id": "v0",
            "parent_ids": [],
            "source": seed_source,
            "island_score": None,
            "evaluation": None,
            "origin": "seed",
        }
        update_program_bank(island, [program], "v0")


def initialize_adaptive_contexts(db: dict[StrategyKey, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    best = sorted(db.values(), key=lambda item: float(item["total_latency_s"]))[:8]
    good = [strategy_summary(item) for item in best]
    return {
        island: {
            "good_patterns": good,
            "bad_patterns": [],
            "mutation_guidance": ["Keep the core island direction fixed; adapt scoring terms using database latency feedback."],
        }
        for island in ISLANDS
    }


def run_evolve_program_with_timing(**kwargs: Any) -> dict[str, Any]:
    start_time = datetime.now()
    start_perf = time.perf_counter()
    island = str(kwargs.get("island"))
    round_index = kwargs.get("round_index")
    call_type = str(kwargs.get("call_type", "evolve_program"))
    timing: dict[str, Any] = {
        "round": round_index,
        "island": island,
        "call_type": call_type,
        "start_time": start_time.isoformat(timespec="milliseconds"),
        "end_time": "",
        "elapsed_s": 0.0,
        "status": "running",
        "reason": "",
    }
    try:
        call_result = evolve_program_with_usage(**kwargs)
        usage = call_result.get("usage", {}) if isinstance(call_result, dict) else {}
        timing["status"] = str(usage.get("status") or "pass") if isinstance(usage, dict) else "pass"
        timing["reason"] = str(usage.get("reason") or "") if isinstance(usage, dict) else ""
        return {"call_result": call_result, "timing": timing, "error": None}
    except Exception as exc:  # noqa: BLE001
        timing["status"] = "fail"
        timing["reason"] = str(exc)[:300]
        return {"call_result": None, "timing": timing, "error": exc}
    finally:
        timing["end_time"] = datetime.now().isoformat(timespec="milliseconds")
        timing["elapsed_s"] = round(time.perf_counter() - start_perf, 3)


def ensure_second_seed_programs(contexts: dict[str, dict[str, Any]], db: dict[StrategyKey, dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    usage_records: list[dict[str, Any]] = []
    timing_records: list[dict[str, Any]] = []
    if not is_enabled(config):
        return ([{"island": island, "status": "skipped", "reason": "DEEPSEEK_API_KEY is not set"} for island in ISLANDS], usage_records, timing_records)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for island in ISLANDS:
            bank = load_program_bank(island)
            feedback = {
                "mode": "second_seed_initialization",
                "core_instruction": load_core_instruction(island),
                "adaptive_context": contexts[island],
                "database_best": [strategy_summary(item) for item in sorted(db.values(), key=lambda row: float(row["total_latency_s"]))[:8]],
            }
            futures[executor.submit(run_evolve_program_with_timing, island=island, instruction=prompt_instruction(island, contexts[island]), v0=bank[0], v1=bank[0], feedback=feedback, config=config, round_index=0, call_type="second_seed")] = island
        for future in as_completed(futures):
            island = futures[future]
            try:
                timed_result = future.result()
                timing_records.append(dict(timed_result["timing"]))
                if timed_result.get("error") is not None:
                    raise timed_result["error"]
                call_result = timed_result["call_result"]
                usage_records.append(dict(call_result.get("usage", {})))
                source = call_result.get("source")
                if not source:
                    results.append({"island": island, "status": "fail", "reason": "no_source"})
                    continue
                check = static_check_source(source)
                if not check.get("valid"):
                    results.append({"island": island, "status": "fail", "reason": check.get("reason")})
                    continue
                append_program(island, {"program_id": "v1", "parent_ids": ["v0"], "source": source, "island_score": None, "evaluation": None, "origin": "second_seed"}, activate=True)
                results.append({"island": island, "status": "pass", "program_id": "v1", "parent_ids": ["v0"]})
            except Exception as exc:  # noqa: BLE001
                usage_records.append(failed_usage_record(config, island, 0, "second_seed", str(exc)))
                results.append({"island": island, "status": "fail", "reason": str(exc)})
    results.sort(key=lambda item: ISLANDS.index(str(item["island"])))
    usage_records.sort(key=lambda item: (int(item.get("round") or 0), str(item.get("island") or "")))
    timing_records.sort(key=lambda item: (int(item.get("round") or 0), str(item.get("call_type") or ""), ISLANDS.index(str(item["island"]))))
    return results, usage_records, timing_records


def current_program_bank_summary() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for island in ISLANDS:
        bank = load_program_bank(island)
        results.append(
            {
                "island": island,
                "status": "continued",
                "program_id": None,
                "program_count": len(bank),
                "reason": "reset skipped; using current active program bank",
            }
        )
    return results


def score_all_islands(config: dict[str, Any], strategy: StrategyKey) -> dict[str, dict[str, Any]]:
    return {island: score_island_programs(config, island, strategy) for island in ISLANDS}


def score_island_programs(config: dict[str, Any], island: str, strategy: StrategyKey) -> dict[str, Any]:
    model = config_to_model(config)
    workload = config_to_workload(config)
    profile = config_to_profile(config)
    cluster = config_to_cluster(config)
    strategy_dict_payload = {"pp": strategy[0], "tp": strategy[1], "dp": strategy[2], "micro_batch_num": strategy[3]}
    scores: list[dict[str, Any]] = []
    for program in load_program_bank(island):
        try:
            fn = compile_score_strategy(str(program["source"]))
            value = finite_or_reject(call_score_strategy_for_dict(fn, strategy_dict_payload, model, cluster, workload, profile))
            scores.append({"program_id": program.get("program_id"), "score": value})
        except Exception as exc:  # noqa: BLE001
            scores.append({"program_id": program.get("program_id"), "score": None, "error": str(exc)})
    valid = [item for item in scores if isinstance(item.get("score"), (int, float))]
    best = max(valid, key=lambda item: float(item["score"])) if valid else None
    return {"scores": scores, "best_program_id": None if best is None else best["program_id"], "best_score": None if best is None else best["score"]}


def evaluate_all_programs_against_database(config: dict[str, Any], db: dict[StrategyKey, dict[str, Any]], top_k: int) -> dict[str, Any]:
    model = config_to_model(config)
    workload = config_to_workload(config)
    profile = config_to_profile(config)
    cluster = config_to_cluster(config)
    db_entries = list(db.values())
    globally_best = best_database_entry(db)
    island_results: dict[str, dict[str, Any]] = {}
    island_scores: dict[str, dict[str, Any]] = {}
    best_candidate: dict[str, Any] | None = None

    for island in ISLANDS:
        program_results: list[dict[str, Any]] = []
        for program in load_program_bank(island):
            result = evaluate_program_ranking(program, db_entries, model, cluster, workload, profile, top_k, globally_best)
            program_results.append(result)
        valid_programs = [item for item in program_results if item.get("status") == "pass"]
        best_program = max(valid_programs, key=lambda item: float(item["ranking_quality"])) if valid_programs else None
        island_results[island] = {
            "programs": compact_program_results(program_results),
            "best_program": best_program,
        }
        island_scores[island] = {
            "best_program_id": None if best_program is None else best_program.get("program_id"),
            "best_score": None if best_program is None else best_program.get("ranking_quality"),
            "spearman_score_vs_negative_latency": None if best_program is None else best_program.get("spearman_score_vs_negative_latency"),
            "top_k_best_latency_s": None if best_program is None else best_program.get("top_k_best_latency_s"),
            "top_k_avg_latency_s": None if best_program is None else best_program.get("top_k_avg_latency_s"),
        }
        if best_program and best_program.get("top_candidate"):
            candidate = dict(best_program["top_candidate"])
            candidate["island"] = island
            candidate["program_id"] = best_program.get("program_id")
            if best_candidate is None or float(candidate["total_latency_s"]) < float(best_candidate["total_latency_s"]):
                best_candidate = candidate

    return {
        "status": "pass",
        "top_k": top_k,
        "database_size": len(db_entries),
        "database_global_best": strategy_summary(globally_best),
        "islands": island_results,
        "island_scores": island_scores,
        "best_candidate": best_candidate,
    }


def evaluate_program_ranking(
    program: dict[str, Any],
    db_entries: list[dict[str, Any]],
    model: dict[str, Any],
    cluster: dict[str, Any],
    workload: dict[str, Any],
    profile: dict[str, Any],
    top_k: int,
    globally_best: dict[str, Any],
) -> dict[str, Any]:
    try:
        fn = compile_score_strategy(str(program["source"]))
    except Exception as exc:  # noqa: BLE001
        return {"program_id": program.get("program_id"), "status": "fail", "reason": f"compile_error: {exc}"}

    scored: list[dict[str, Any]] = []
    errors = 0
    for entry in db_entries:
        strategy = entry["strategy"]
        payload = {"pp": strategy[0], "tp": strategy[1], "dp": strategy[2], "micro_batch_num": strategy[3]}
        try:
            score = finite_or_reject(call_score_strategy_for_dict(fn, payload, model, cluster, workload, profile))
        except Exception:  # noqa: BLE001
            errors += 1
            continue
        scored.append(
            {
                "strategy": strategy,
                "strategy_dict": strategy_dict(strategy),
                "score": float(score),
                "total_latency_s": float(entry["total_latency_s"]),
                "pp_strategy": entry.get("pp_strategy"),
                "dp_strategy": entry.get("dp_strategy"),
                "dag_id": entry.get("dag_id"),
            }
        )
    if not scored:
        return {"program_id": program.get("program_id"), "status": "fail", "reason": "no_valid_scores", "score_errors": errors}

    by_score = sorted(scored, key=lambda item: float(item["score"]), reverse=True)
    by_latency = sorted(scored, key=lambda item: float(item["total_latency_s"]))
    selected = by_score[: max(1, min(top_k, len(by_score)))]
    top_candidate = min(selected, key=lambda item: float(item["total_latency_s"]))
    top_avg_latency = sum(float(item["total_latency_s"]) for item in selected) / len(selected)
    top_best_latency = float(top_candidate["total_latency_s"])
    spearman = spearman_correlation(
        [float(item["score"]) for item in scored],
        [-float(item["total_latency_s"]) for item in scored],
    )
    median_latency = sorted(float(item["total_latency_s"]) for item in scored)[len(scored) // 2]
    score_rank = {id(item): index + 1 for index, item in enumerate(by_score)}
    latency_best_set = {tuple(item["strategy"]) for item in by_latency[: max(1, min(top_k, len(by_latency)))]}
    bad_cases = [
        compact_case(item, score_rank[id(item)])
        for item in selected
        if float(item["total_latency_s"]) >= median_latency
    ][:5]
    missed_cases = [
        compact_case(item, score_rank[id(item)])
        for item in by_latency[: max(1, min(top_k, len(by_latency)))]
        if score_rank[id(item)] > max(top_k * 2, len(scored) // 3)
    ][:5]
    db_best_latency = float(globally_best["total_latency_s"])
    ranking_quality = (spearman * 1000.0) - ((top_avg_latency / db_best_latency) * 10.0) - (len(bad_cases) * 5.0) + (top_k / max(1, score_rank[id(next(item for item in scored if tuple(item["strategy"]) == tuple(globally_best["strategy"])))]))

    return {
        "program_id": program.get("program_id"),
        "status": "pass",
        "ranking_quality": ranking_quality,
        "spearman_score_vs_negative_latency": spearman,
        "top_k_avg_latency_s": top_avg_latency,
        "top_k_best_latency_s": top_best_latency,
        "top_candidate": compact_case(top_candidate, score_rank[id(top_candidate)]),
        "database_best_score_rank": score_rank[id(next(item for item in scored if tuple(item["strategy"]) == tuple(globally_best["strategy"])))],
        "bad_cases": bad_cases,
        "missed_cases": missed_cases,
        "score_errors": errors,
        "top_score_cases": [compact_case(item, score_rank[id(item)]) for item in selected[:5]],
        "top_latency_cases": [compact_case(item, score_rank[id(item)]) for item in by_latency[:5]],
        "latency_best_covered_in_top_k": any(tuple(item["strategy"]) in latency_best_set for item in selected),
    }


def compact_case(item: dict[str, Any], score_rank_value: int) -> dict[str, Any]:
    return {
        "strategy": item["strategy_dict"],
        "score_rank": score_rank_value,
        "score": round(float(item["score"]), 6),
        "total_latency_s": float(item["total_latency_s"]),
        "pp_strategy": item.get("pp_strategy"),
        "dp_strategy": item.get("dp_strategy"),
        "dag_id": item.get("dag_id"),
    }


def compact_program_results(program_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in program_results:
        compact.append(
            {
                "program_id": item.get("program_id"),
                "status": item.get("status"),
                "reason": item.get("reason"),
                "ranking_quality": item.get("ranking_quality"),
                "spearman_score_vs_negative_latency": item.get("spearman_score_vs_negative_latency"),
                "top_k_avg_latency_s": item.get("top_k_avg_latency_s"),
                "top_k_best_latency_s": item.get("top_k_best_latency_s"),
                "database_best_score_rank": item.get("database_best_score_rank"),
                "score_errors": item.get("score_errors"),
            }
        )
    return compact


def spearman_correlation(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    rx = ranks(xs)
    ry = ranks(ys)
    mean_x = sum(rx) / len(rx)
    mean_y = sum(ry) / len(ry)
    cov = sum((a - mean_x) * (b - mean_y) for a, b in zip(rx, ry))
    var_x = sum((a - mean_x) ** 2 for a in rx)
    var_y = sum((b - mean_y) ** 2 for b in ry)
    if var_x <= 0 or var_y <= 0:
        return 0.0
    return cov / math.sqrt(var_x * var_y)


def ranks(values: list[float]) -> list[float]:
    order = sorted(enumerate(values), key=lambda item: item[1])
    out = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and order[end][1] == order[index][1]:
            end += 1
        rank = (index + 1 + end) / 2.0
        for original_index, _ in order[index:end]:
            out[original_index] = rank
        index = end
    return out


def call_score_strategy_for_dict(fn: Any, strategy: dict[str, int], model: dict[str, Any], cluster: dict[str, Any], workload: dict[str, Any], profile: dict[str, Any]) -> float:
    import inspect

    params = list(inspect.signature(fn).parameters)
    if params == ["strategy", "model_cfg", "topo_cfg", "profile_cfg"]:
        return float(fn(strategy, model, cluster, profile))
    if params == ["pp", "tp", "dp", "model", "cluster", "workload"]:
        return float(fn(strategy["pp"], strategy["tp"], strategy["dp"], model, cluster, workload))
    raise ValueError("unsupported score_strategy signature")


def choose_next_strategy(current: StrategyKey, evaluation: dict[str, Any], db: dict[StrategyKey, dict[str, Any]], config: dict[str, Any], visited: set[StrategyKey]) -> tuple[StrategyKey, dict[str, Any]]:
    db_best = best_database_entry(db)["strategy"]
    if evaluation["status"] != "pass":
        next_key, changed = move_one_parameter_toward(current, db_best)
        if next_key == current or next_key not in db:
            nearest = nearest_database_strategy(current, db)
            next_key, changed = move_one_parameter_toward(current, nearest)
        return next_key, {"type": "repair_illegal", "changed": changed, "reason": evaluation.get("reason"), "target": strategy_dict(next_key)}
    unvisited = [key for key in db if key not in visited]
    if not unvisited:
        return current, {"type": "stay", "reason": "all_database_strategies_visited"}
    current_latency = float(evaluation["total_latency_s"])
    better = [key for key in unvisited if float(db[key]["total_latency_s"]) < current_latency]
    target = min(better or unvisited, key=lambda key: float(db[key]["total_latency_s"]))
    next_key, changed = move_one_parameter_toward(current, target)
    if next_key not in db and target in db:
        next_key = target
        changed = "multi_parameter_jump_to_database_candidate"
    return next_key, {"type": "latency_guided", "changed": changed, "target": strategy_dict(target), "next": strategy_dict(next_key)}


def move_one_parameter_toward(current: StrategyKey, target: StrategyKey) -> tuple[StrategyKey, str]:
    labels = ("pp", "tp", "dp", "mb")
    values = list(current)
    for index, label in enumerate(labels):
        if values[index] != target[index]:
            values[index] = target[index]
            return tuple(values), label  # type: ignore[return-value]
    return current, "none"


def nearest_database_strategy(current: StrategyKey, db: dict[StrategyKey, dict[str, Any]]) -> StrategyKey:
    return min(db, key=lambda key: (sum(1 for a, b in zip(current, key) if a != b), float(db[key]["total_latency_s"])))


def build_evaluation_feedback_payload(
    strategy: StrategyKey,
    scores: dict[str, dict[str, Any]],
    evaluation: dict[str, Any],
    db: dict[StrategyKey, dict[str, Any]],
    best: dict[str, Any] | None,
) -> dict[str, Any]:
    db_best = best_database_entry(db)
    payload: dict[str, Any] = {
        "strategy": strategy_dict(strategy),
        "evaluation_status": evaluation.get("status"),
        "failure_reason": evaluation.get("reason"),
        "total_latency_s": evaluation.get("total_latency_s"),
        "baseline_latency_s": evaluation.get("baseline_latency_s"),
        "pp_strategy": evaluation.get("pp_strategy"),
        "dp_strategy": evaluation.get("dp_strategy"),
        "rulecheck": evaluation.get("rulecheck"),
        "dag_id": evaluation.get("dag_id"),
        "database_global_best": strategy_summary(db_best),
        "best_found_so_far": None if best is None else strategy_summary(best),
        "island_scores": {
            island: {
                "best_program_id": item.get("best_program_id"),
                "best_score": item.get("best_score"),
            }
            for island, item in scores.items()
        },
    }
    if evaluation.get("status") == "pass":
        latency = float(evaluation["total_latency_s"])
        best_latency = float(db_best["total_latency_s"])
        payload["gap_to_database_best"] = (latency - best_latency) / best_latency if best_latency > 0 else None
        ranked_scores = sorted(
            (
                (island, item.get("best_score"))
                for island, item in scores.items()
                if isinstance(item.get("best_score"), (int, float))
            ),
            key=lambda item: float(item[1]),
            reverse=True,
        )
        payload["score_latency_alignment"] = {
            "highest_score_island": ranked_scores[0][0] if ranked_scores else None,
            "interpretation": (
                "Use this as direct supervision: high score should increasingly mean low total_latency_s for similar strategy shapes."
            ),
        }
    else:
        payload["score_latency_alignment"] = {
            "interpretation": "This strategy is illegal or missing in the database; reduce score for nearby shapes unless one parameter repair makes it valid."
        }
    return payload


def update_program_feedback(scores: dict[str, dict[str, Any]], evaluation: dict[str, Any], feedback_payload: dict[str, Any], round_index: int) -> None:
    for island in ISLANDS:
        best_program_id = scores.get(island, {}).get("best_program_id")
        if not best_program_id:
            continue
        bank = load_program_bank(island)
        active_id = load_active_program_id_for_bank(bank, island)
        changed = False
        for program in bank:
            if str(program.get("program_id")) != str(best_program_id):
                continue
            score_value = scores.get(island, {}).get("best_score")
            if isinstance(score_value, (int, float)):
                program["island_score"] = float(score_value)
            program["evaluation"] = compact_program_evaluation(evaluation, feedback_payload, round_index)
            observations = list(program.get("observations", [])) if isinstance(program.get("observations"), list) else []
            observations.append(compact_program_evaluation(evaluation, feedback_payload, round_index))
            program["observations"] = observations[-8:]
            changed = True
            break
        if changed:
            update_program_bank(island, bank, active_id)


def build_ranking_feedback_payload(ranking: dict[str, Any], db: dict[StrategyKey, dict[str, Any]]) -> dict[str, Any]:
    feedback: dict[str, Any] = {
        "mode": "full_database_ranking",
        "database_size": ranking.get("database_size"),
        "top_k": ranking.get("top_k"),
        "database_global_best": ranking.get("database_global_best"),
        "best_candidate_found_by_scoring": ranking.get("best_candidate"),
        "islands": {},
        "objective": (
            "Improve the scoring function's ranking quality over the full database: high score should correspond to low total_latency_s, "
            "bad high-score/high-latency cases should move down, and missed low-latency cases should move up."
        ),
    }
    for island in ISLANDS:
        best_program = ranking.get("islands", {}).get(island, {}).get("best_program")
        if not isinstance(best_program, dict):
            feedback["islands"][island] = {"status": "no_valid_program"}
            continue
        feedback["islands"][island] = {
            "best_program_id": best_program.get("program_id"),
            "ranking_quality": best_program.get("ranking_quality"),
            "spearman_score_vs_negative_latency": best_program.get("spearman_score_vs_negative_latency"),
            "top_k_avg_latency_s": best_program.get("top_k_avg_latency_s"),
            "top_k_best_latency_s": best_program.get("top_k_best_latency_s"),
            "database_best_score_rank": best_program.get("database_best_score_rank"),
            "top_score_cases": best_program.get("top_score_cases", []),
            "bad_cases": best_program.get("bad_cases", []),
            "missed_cases": best_program.get("missed_cases", []),
            "top_latency_cases": best_program.get("top_latency_cases", []),
        }
    return feedback


def update_program_ranking_feedback(ranking: dict[str, Any], round_index: int) -> None:
    for island in ISLANDS:
        program_results = ranking.get("islands", {}).get(island, {}).get("programs", [])
        by_id = {str(item.get("program_id")): item for item in program_results if item.get("program_id") is not None}
        if not by_id:
            continue
        bank = load_program_bank(island)
        active_id = load_active_program_id_for_bank(bank, island)
        changed = False
        for program in bank:
            metrics = by_id.get(str(program.get("program_id")))
            if not metrics or metrics.get("status") != "pass":
                continue
            quality = metrics.get("ranking_quality")
            if isinstance(quality, (int, float)):
                program["island_score"] = float(quality)
            evaluation = {
                "round": round_index,
                "mode": "full_database_ranking",
                "status": metrics.get("status"),
                "ranking_quality": metrics.get("ranking_quality"),
                "spearman_score_vs_negative_latency": metrics.get("spearman_score_vs_negative_latency"),
                "top_k_avg_latency_s": metrics.get("top_k_avg_latency_s"),
                "top_k_best_latency_s": metrics.get("top_k_best_latency_s"),
                "database_best_score_rank": metrics.get("database_best_score_rank"),
                "total_latency_s": metrics.get("top_k_avg_latency_s"),
            }
            program["evaluation"] = evaluation
            observations = list(program.get("observations", [])) if isinstance(program.get("observations"), list) else []
            observations.append(evaluation)
            program["observations"] = observations[-8:]
            changed = True
        if changed:
            update_program_bank(island, bank, active_id)


def update_adaptive_contexts_from_ranking(
    contexts: dict[str, dict[str, Any]],
    ranking: dict[str, Any],
    db: dict[StrategyKey, dict[str, Any]],
    feedback_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    updated = copy.deepcopy(contexts)
    for island in ISLANDS:
        context = updated[island]
        island_feedback = feedback_payload.get("islands", {}).get(island, {})
        context["last_evaluation_feedback"] = compact_island_feedback(island_feedback)
        context["good_patterns"] = list(island_feedback.get("top_latency_cases", []))[:3]
        context["bad_patterns"] = list(island_feedback.get("bad_cases", []))[:3]
        stable = list(context.get("stable_findings", [])) if isinstance(context.get("stable_findings"), list) else []
        for case in island_feedback.get("top_latency_cases", [])[:2]:
            stable.append(pattern_sentence("good", case))
        context["stable_findings"] = unique_keep_last(stable, 5)
        open_issues = [pattern_sentence("bad", case) for case in island_feedback.get("bad_cases", [])[:2]]
        open_issues += [pattern_sentence("missed", case) for case in island_feedback.get("missed_cases", [])[:1]]
        context["open_issues"] = unique_keep_last(open_issues, 3)
        context["mutation_guidance"] = [
            "Optimize the explanation/ranking behavior of score_strategy over the full database, not a single strategy path.",
            "Increase scores for missed low-latency cases and reduce scores for bad high-score/high-latency cases.",
        ]
    return updated


def compact_island_feedback(feedback: dict[str, Any]) -> dict[str, Any]:
    return {
        "best_program_id": feedback.get("best_program_id"),
        "ranking_quality": feedback.get("ranking_quality"),
        "spearman_score_vs_negative_latency": feedback.get("spearman_score_vs_negative_latency"),
        "top_k_avg_latency_s": feedback.get("top_k_avg_latency_s"),
        "top_k_best_latency_s": feedback.get("top_k_best_latency_s"),
        "database_best_score_rank": feedback.get("database_best_score_rank"),
        "top_score_cases": list(feedback.get("top_score_cases", []))[:3],
        "bad_cases": list(feedback.get("bad_cases", []))[:3],
        "missed_cases": list(feedback.get("missed_cases", []))[:3],
        "top_latency_cases": list(feedback.get("top_latency_cases", []))[:3],
    }


def unique_keep_last(items: list[str], limit: int) -> list[str]:
    out: list[str] = []
    for item in items:
        if item and item not in out:
            out.append(item)
    return out[-limit:]


def pattern_sentence(kind: str, case: dict[str, Any]) -> str:
    strategy = case.get("strategy", {})
    return (
        f"{kind}: PP={strategy.get('pp')}, TP={strategy.get('tp')}, DP={strategy.get('dp')}, "
        f"MB={strategy.get('micro_batch_num')}, latency={case.get('total_latency_s')}, score_rank={case.get('score_rank')}"
    )


def update_experience_bank(round_index: int, feedback_payload: dict[str, Any]) -> list[dict[str, Any]]:
    EXPERIENCE_BANK.parent.mkdir(parents=True, exist_ok=True)
    if not EXPERIENCE_BANK.exists():
        EXPERIENCE_BANK.write_text("# ScoreExpert Experience Bank\n\n## Global Experience\n\n## Island Interpretations\n", encoding="utf-8")
    existing = EXPERIENCE_BANK.read_text(encoding="utf-8")
    additions: list[str] = []
    events: list[dict[str, Any]] = []
    for island in ISLANDS:
        feedback = feedback_payload.get("islands", {}).get(island, {})
        for case in list(feedback.get("bad_cases", []))[:2]:
            entry = experience_entry("global_experience", island, round_index, case, "High score selected a high-latency strategy; reduce this pattern unless an island-specific reason explains it.")
            if entry["description"] not in existing and entry["description"] not in "\n".join(additions):
                additions.append(render_experience_entry(entry))
                events.append({"action": "add", **entry})
        for case in list(feedback.get("missed_cases", []))[:2]:
            entry = experience_entry("island_interpretation", island, round_index, case, "Low-latency strategy was missed; add an island-specific reward for this shape if it matches the core direction.")
            if entry["description"] not in existing and entry["description"] not in "\n".join(additions):
                additions.append(render_experience_entry(entry))
                events.append({"action": "add", **entry})
    if additions:
        with EXPERIENCE_BANK.open("a", encoding="utf-8") as handle:
            handle.write("\n".join(additions).rstrip() + "\n")
    return events[:12]


def experience_entry(kind: str, island: str, round_index: int, case: dict[str, Any], recommendation: str) -> dict[str, Any]:
    strategy = case.get("strategy", {})
    description = (
        f"{kind}: PP={strategy.get('pp')}, TP={strategy.get('tp')}, DP={strategy.get('dp')}, "
        f"MB={strategy.get('micro_batch_num')}, pp_strategy={case.get('pp_strategy')}, dp_strategy={case.get('dp_strategy')}"
    )
    return {
        "kind": kind,
        "description": description,
        "evidence": f"round={round_index}, island={island}, latency={case.get('total_latency_s')}, score_rank={case.get('score_rank')}, score={case.get('score')}",
        "recommendation": recommendation,
        "applies_to": strategy,
        "source_islands": [island],
        "confidence": 0.6,
        "last_seen_round": round_index,
    }


def render_experience_entry(entry: dict[str, Any]) -> str:
    heading = "Global Experience" if entry["kind"] == "global_experience" else "Island Interpretations"
    return (
        f"\n### {heading}: {entry['description']}\n"
        f"- description: {entry['description']}\n"
        f"- evidence: {entry['evidence']}\n"
        f"- recommendation: {entry['recommendation']}\n"
        f"- applies_to: {entry['applies_to']}\n"
        f"- source_islands: {entry['source_islands']}\n"
        f"- confidence: {entry['confidence']}\n"
        f"- last_seen_round: {entry['last_seen_round']}\n"
    )


def retrieve_experience(island: str, context: dict[str, Any], limit: int = 3) -> list[str]:
    if not EXPERIENCE_BANK.exists():
        return []
    text = EXPERIENCE_BANK.read_text(encoding="utf-8")
    blocks = [block.strip() for block in text.split("\n### ") if "description:" in block]
    query_terms = set(re.findall(r"[A-Za-z0-9_]+", json.dumps(context, ensure_ascii=False).lower()))
    scored: list[tuple[int, str]] = []
    for block in blocks:
        block_lower = block.lower()
        score = sum(1 for term in query_terms if term and term in block_lower)
        if island.lower() in block_lower:
            score += 3
        if score > 0:
            scored.append((score, "### " + block))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [block for _, block in scored[:limit]]


def load_active_program_id_for_bank(bank: list[dict[str, Any]], island: str) -> str:
    try:
        from ScoreExpert.island_store import load_active_program_id

        return load_active_program_id(island)
    except Exception:  # noqa: BLE001
        return str(bank[0].get("program_id", "v0")) if bank else "v0"


def compact_program_evaluation(evaluation: dict[str, Any], feedback_payload: dict[str, Any], round_index: int) -> dict[str, Any]:
    return {
        "round": round_index,
        "strategy": feedback_payload.get("strategy"),
        "status": evaluation.get("status"),
        "total_latency_s": evaluation.get("total_latency_s"),
        "baseline_latency_s": evaluation.get("baseline_latency_s"),
        "pp_strategy": evaluation.get("pp_strategy"),
        "dp_strategy": evaluation.get("dp_strategy"),
        "failure_reason": evaluation.get("reason"),
        "gap_to_database_best": feedback_payload.get("gap_to_database_best"),
    }


def update_adaptive_contexts(
    contexts: dict[str, dict[str, Any]],
    strategy: StrategyKey,
    scores: dict[str, dict[str, Any]],
    evaluation: dict[str, Any],
    db: dict[StrategyKey, dict[str, Any]],
    feedback_payload: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    updated = copy.deepcopy(contexts)
    summary = {"strategy": strategy_dict(strategy), "evaluation": evaluation}
    for island in ISLANDS:
        context = updated[island]
        if evaluation["status"] == "pass":
            pattern = {**summary, "score": scores[island].get("best_score")}
            context.setdefault("good_patterns", [])
            context["good_patterns"] = ([pattern] + context["good_patterns"])[:8]
            context["mutation_guidance"] = [
                "Use database total_latency_s as the direct feedback signal; score should become a better explanation of why latency is low.",
                f"Current strategy feedback: {json.dumps(feedback_payload, ensure_ascii=False)}",
            ]
        else:
            context.setdefault("bad_patterns", [])
            context["bad_patterns"] = ([summary] + context["bad_patterns"])[:8]
            context["mutation_guidance"] = [
                "Avoid scoring invalid or database-missing strategy shapes too highly, but keep one-parameter repairs visible.",
                f"Invalid strategy feedback: {json.dumps(feedback_payload, ensure_ascii=False)}",
            ]
        context["last_evaluation_feedback"] = feedback_payload
    return updated


def evolve_all_islands(round_index: int, contexts: dict[str, dict[str, Any]], config: dict[str, Any], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not is_enabled(config):
        return ([{"island": island, "status": "skipped", "reason": "DEEPSEEK_API_KEY is not set"} for island in ISLANDS], [], [])
    requests = {island: build_evolution_request(island, contexts[island], rng) for island in ISLANDS}
    results: list[dict[str, Any]] = []
    usage_records: list[dict[str, Any]] = []
    timing_records: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                run_evolve_program_with_timing,
                island=island,
                instruction=prompt_instruction(island, contexts[island]),
                v0=req["v0"],
                v1=req["v1"],
                feedback=req["feedback"],
                config=config,
                round_index=round_index,
                call_type="score_evolution",
            ): island
            for island, req in requests.items()
        }
        for future in as_completed(futures):
            island = futures[future]
            req = requests[island]
            try:
                timed_result = future.result()
                timing_records.append(dict(timed_result["timing"]))
                if timed_result.get("error") is not None:
                    raise timed_result["error"]
                call_result = timed_result["call_result"]
                usage_records.append(dict(call_result.get("usage", {})))
                source = call_result.get("source")
                results.append(append_evolved_program(island, source, req))
            except Exception as exc:  # noqa: BLE001
                usage_records.append(failed_usage_record(config, island, round_index, "score_evolution", str(exc)))
                results.append({"island": island, "status": "fail", "reason": str(exc), "parent_ids": req["parent_ids"]})
    results.sort(key=lambda item: ISLANDS.index(str(item["island"])))
    timing_records.sort(key=lambda item: (int(item.get("round") or 0), str(item.get("call_type") or ""), ISLANDS.index(str(item["island"]))))
    return results, usage_records, timing_records


def failed_usage_record(config: dict[str, Any], island: str, round_index: int, call_type: str, reason: str) -> dict[str, Any]:
    cfg = config.get("search_config", {}).get("deepseek", {})
    return {
        "round": round_index,
        "island": island,
        "call_type": call_type,
        "model": str(cfg.get("model", "deepseek-v4-pro")) if isinstance(cfg, dict) else "deepseek-v4-pro",
        "status": "fail",
        "reason": reason[:300],
        "elapsed_s": 0.0,
        "input_chars": 0,
        "output_chars": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "token_source": "unavailable",
        "estimated_cost": 0.0,
    }


def build_evolution_request(island: str, context: dict[str, Any], rng: random.Random) -> dict[str, Any]:
    bank = load_program_bank(island)
    ranked = sorted(bank, key=program_rank_key, reverse=True)
    if len(ranked) < 2:
        v0 = ranked[0]
        v1 = ranked[0]
    else:
        v0 = ranked[0]
        diverse_pool = sorted(ranked[1 : min(10, len(ranked))], key=lambda item: source_similarity(v0, item))
        v1 = rng.choice(diverse_pool[: max(1, min(4, len(diverse_pool)))])
    compact_context = compact_adaptive_context(context)
    relevant_experience = retrieve_experience(island, compact_context, limit=3)
    return {
        "v0": v0,
        "v1": v1,
        "parent_ids": parent_ids(v0, v1),
        "feedback": {
            "adaptive_context": compact_context,
            "relevant_experience": relevant_experience,
            "parent_cards": [program_card(v0), program_card(v1)],
            "evaluation_feedback": compact_context.get("last_evaluation_feedback"),
            "summary": (
                "Use database total_latency_s feedback as supervision for explanation quality. "
                "Score is not the final objective, but the program should increasingly assign higher scores to strategy patterns "
                "that the database shows have lower total latency."
            ),
        },
    }


def compact_adaptive_context(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "stable_findings": list(context.get("stable_findings", []))[:5],
        "open_issues": list(context.get("open_issues", []))[:3],
        "mutation_guidance": list(context.get("mutation_guidance", []))[:2],
        "last_evaluation_feedback": compact_island_feedback(context.get("last_evaluation_feedback", {})),
    }


def program_card(program: dict[str, Any]) -> dict[str, Any]:
    evaluation = program.get("evaluation") if isinstance(program.get("evaluation"), dict) else {}
    return {
        "program_id": program.get("program_id"),
        "origin": program.get("origin"),
        "ranking_quality": evaluation.get("ranking_quality") or program.get("island_score"),
        "spearman_score_vs_negative_latency": evaluation.get("spearman_score_vs_negative_latency"),
        "top_k_avg_latency_s": evaluation.get("top_k_avg_latency_s"),
        "top_k_best_latency_s": evaluation.get("top_k_best_latency_s"),
        "source_chars": len(str(program.get("source", ""))),
    }


def source_similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    a_tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(a.get("source", ""))))
    b_tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(b.get("source", ""))))
    if not a_tokens or not b_tokens:
        return 0.0
    return len(a_tokens & b_tokens) / len(a_tokens | b_tokens)


def compute_diversity_metrics(ranking: dict[str, Any]) -> dict[str, Any]:
    top_sets: dict[str, set[str]] = {}
    active_sources: list[dict[str, Any]] = []
    for island in ISLANDS:
        best_program = ranking.get("islands", {}).get(island, {}).get("best_program")
        if isinstance(best_program, dict):
            cases = best_program.get("top_score_cases", [])
            top_sets[island] = {json.dumps(case.get("strategy", {}), sort_keys=True) for case in cases}
        active = load_program_bank(island)
        active_sources.extend(active[-3:])
    overlaps: list[float] = []
    islands = list(top_sets)
    for i, left in enumerate(islands):
        for right in islands[i + 1 :]:
            a = top_sets[left]
            b = top_sets[right]
            if a or b:
                overlaps.append(len(a & b) / len(a | b))
    similarities: list[float] = []
    for i, left in enumerate(active_sources):
        for right in active_sources[i + 1 :]:
            similarities.append(source_similarity(left, right))
    return {
        "avg_top_strategy_overlap": sum(overlaps) / len(overlaps) if overlaps else 0.0,
        "avg_recent_program_similarity": sum(similarities) / len(similarities) if similarities else 0.0,
    }


def append_evolved_program(island: str, source: str | None, request: dict[str, Any]) -> dict[str, Any]:
    if not source:
        return {"island": island, "status": "fail", "reason": "no_source", "parent_ids": request["parent_ids"]}
    check = static_check_source(source)
    if not check.get("valid"):
        return {"island": island, "status": "fail", "reason": check.get("reason"), "parent_ids": request["parent_ids"]}
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
            "origin": "db_search_evolution",
        },
        activate=True,
        max_programs=20,
    )
    return {"island": island, "status": "pass", "program_id": program_id, "parent_ids": request["parent_ids"]}


def maybe_replace_islands(round_index: int, contexts: dict[str, dict[str, Any]], config: dict[str, Any], rng: random.Random) -> list[dict[str, Any]]:
    interval = int(config.get("search_config", {}).get("score_db_search", {}).get("migration_interval", 10))
    if round_index <= 0 or round_index % max(1, interval) != 0:
        return []
    best_by_island: dict[str, float] = {}
    for island in ISLANDS:
        values = [program.get("evaluation", {}).get("total_latency_s") for program in load_program_bank(island) if isinstance(program.get("evaluation"), dict)]
        finite = [float(value) for value in values if isinstance(value, (int, float)) and math.isfinite(float(value))]
        if finite:
            best_by_island[island] = min(finite)
    if len(best_by_island) < 2:
        return []
    global_best = min(best_by_island.values())
    events: list[dict[str, Any]] = []
    for island, latency in best_by_island.items():
        if latency <= global_best * 1.05:
            continue
        sources = [item for item in ISLANDS if item != island]
        samples = sample_programs(sources, rng)
        if len(samples) < 2:
            continue
        source = str(samples[0][1].get("source", ""))
        update_program_bank(
            island,
            [{
                "program_id": "v0",
                "parent_ids": [str(samples[0][1].get("program_id")), str(samples[1][1].get("program_id"))],
                "source": source,
                "island_score": None,
                "evaluation": None,
                "origin": "db_search_replacement",
            }],
            "v0",
        )
        events.append({"round": round_index, "target_island": island, "source_islands": [samples[0][0], samples[1][0]], "reason": "latency_lagging"})
    return events


def sample_programs(islands: list[str], rng: random.Random) -> list[tuple[str, dict[str, Any]]]:
    by_island: dict[str, list[dict[str, Any]]] = {}
    for island in islands:
        by_island[island] = []
        for program in load_program_bank(island):
            if program.get("source"):
                by_island[island].append(program)
    available = [island for island, programs in by_island.items() if programs]
    rng.shuffle(available)
    if len(available) < 2:
        return []
    selected = available[:2]
    return [(island, rng.choice(by_island[island])) for island in selected]


def program_rank_key(program: dict[str, Any]) -> tuple[int, float, int]:
    evaluation = program.get("evaluation") if isinstance(program.get("evaluation"), dict) else {}
    latency = evaluation.get("total_latency_s") if isinstance(evaluation, dict) else None
    has_latency = isinstance(latency, (int, float))
    score = program.get("island_score")
    score_value = float(score) if isinstance(score, (int, float)) else float("-inf")
    version = int(str(program.get("program_id", "v0")).lstrip("v") or 0) if str(program.get("program_id", "")).startswith("v") else 0
    return (1 if has_latency else 0, -float(latency) if has_latency else score_value, version)


def has_converged(history: list[float], patience: int, min_relative_improvement: float) -> bool:
    finite = [value for value in history if math.isfinite(value)]
    if len(finite) <= patience:
        return False
    old = finite[-patience - 1]
    recent = min(finite[-patience:])
    if old <= 0:
        return False
    return (old - recent) / old < min_relative_improvement


def load_core_instruction(island: str) -> str:
    doc = load_instruction(island)
    return doc.split("Active evolution file.")[0].strip()


def prompt_instruction(island: str, context: dict[str, Any]) -> str:
    return f"{load_core_instruction(island)}\n\nCOMPACT_ISLAND_ADAPTIVE_CONTEXT:\n{json.dumps(compact_adaptive_context(context), ensure_ascii=False)}"


def strategy_summary(entry: dict[str, Any]) -> dict[str, Any]:
    return {"strategy": strategy_dict(entry["strategy"]), "total_latency_s": entry["total_latency_s"], "pp_strategy": entry.get("pp_strategy"), "dp_strategy": entry.get("dp_strategy")}


def strategy_dict(strategy: StrategyKey) -> dict[str, int]:
    return {"pp": strategy[0], "tp": strategy[1], "dp": strategy[2], "micro_batch_num": strategy[3]}


def strategy_payload(strategy: Any) -> dict[str, int]:
    if isinstance(strategy, dict):
        return {
            "pp": int(strategy["pp"]),
            "tp": int(strategy["tp"]),
            "dp": int(strategy["dp"]),
            "micro_batch_num": int(strategy["micro_batch_num"]),
        }
    return strategy_dict(strategy)


def make_run_dir(output_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_root / f"scoreexpert_db_search_{timestamp}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = output_root / f"scoreexpert_db_search_{timestamp}_{suffix}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def build_summary(
    *,
    run_root: Path,
    database_path: Path,
    db: dict[StrategyKey, dict[str, Any]],
    db_best: dict[str, Any],
    seed_results: list[dict[str, Any]],
    max_rounds: int,
    stop_on_target_gap: bool,
    stop_on_patience: bool,
    stop_reason: str,
    best: dict[str, Any] | None,
    rounds: list[dict[str, Any]],
    replacements: list[dict[str, Any]],
    llm_usage: list[dict[str, Any]],
    llm_timing: list[dict[str, Any]],
    deepseek_enabled: bool,
    final: bool,
) -> dict[str, Any]:
    latency_chart = run_root / "latency_trend.png"
    score_chart = run_root / "score_trend.png"
    replacement_chart = run_root / "island_replacement_events.png"
    return {
        "status": "pass" if final else "running",
        "run_root": str(run_root.as_posix()),
        "database": str(database_path.as_posix()),
        "database_entries": len(db),
        "database_best": {"strategy": strategy_dict(db_best["strategy"]), "total_latency_s": db_best["total_latency_s"], "pp_strategy": db_best["pp_strategy"], "dp_strategy": db_best["dp_strategy"]},
        "deepseek_enabled": deepseek_enabled,
        "seed_results": seed_results,
        "max_rounds": max_rounds,
        "stop_on_target_gap": stop_on_target_gap,
        "stop_on_patience": stop_on_patience,
        "rounds_run": len(rounds),
        "stop_reason": stop_reason,
        "best": None if best is None else {"strategy": strategy_payload(best["strategy"]), "total_latency_s": best["total_latency_s"], "pp_strategy": best.get("pp_strategy"), "dp_strategy": best.get("dp_strategy")},
        "latency_chart": str(latency_chart.as_posix()),
        "score_chart": str(score_chart.as_posix()),
        "replacement_chart": str(replacement_chart.as_posix()),
        "rounds": rounds,
        "replacements": replacements,
        "llm_usage": llm_usage,
        "llm_usage_csv": str((run_root / "llm_usage_by_round.csv").as_posix()),
        "llm_usage_summary": summarize_llm_usage(llm_usage),
        "llm_timing": llm_timing,
        "llm_timing_csv": str((run_root / "island_api_timing.csv").as_posix()),
    }


def write_run_outputs(run_root: Path, summary: dict[str, Any]) -> None:
    plot_latency(summary["rounds"], run_root / "latency_trend.png")
    plot_scores(summary["rounds"], run_root / "score_trend.png")
    plot_replacements(summary.get("replacements", []), run_root / "island_replacement_events.png")
    report_path = run_root / "scoreexpert_db_search_report.md"
    summary["report_md"] = str(report_path.as_posix())
    report_path.write_text(render_report(summary), encoding="utf-8")
    (run_root / "round_trace.json").write_text(json.dumps(sanitize_for_json(summary), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_llm_usage_csv(run_root / "llm_usage_by_round.csv", summary.get("llm_usage", []))
    write_llm_timing_csv(run_root / "island_api_timing.csv", summary.get("llm_timing", []))


def write_llm_usage_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = ["round", "island", "call_type", "model", "status", "reason", "elapsed_s", "input_tokens", "output_tokens", "total_tokens", "token_source", "estimated_cost", "input_chars", "output_chars"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def write_llm_timing_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = ["round", "island", "call_type", "start_time", "end_time", "elapsed_s", "status", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in fields})


def summarize_llm_usage(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_round: dict[str, dict[str, Any]] = {}
    for record in records:
        key = str(record.get("round"))
        bucket = by_round.setdefault(key, {"calls": 0, "failures": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "elapsed_s": 0.0, "estimated_cost": 0.0})
        bucket["calls"] += 1
        if record.get("status") != "pass":
            bucket["failures"] += 1
        bucket["input_tokens"] += int(record.get("input_tokens") or 0)
        bucket["output_tokens"] += int(record.get("output_tokens") or 0)
        bucket["total_tokens"] += int(record.get("total_tokens") or 0)
        bucket["elapsed_s"] += float(record.get("elapsed_s") or 0.0)
        bucket["estimated_cost"] += float(record.get("estimated_cost") or 0.0)
    return by_round


def compact_round_feedback_for_report(feedback: Any) -> dict[str, Any]:
    if not isinstance(feedback, dict):
        return {}
    islands: dict[str, Any] = {}
    for island, item in feedback.get("islands", {}).items():
        if not isinstance(item, dict):
            continue
        islands[island] = {
            "best_program_id": item.get("best_program_id"),
            "ranking_quality": item.get("ranking_quality"),
            "spearman": item.get("spearman_score_vs_negative_latency"),
            "top_k_avg_latency_s": item.get("top_k_avg_latency_s"),
            "bad_cases": list(item.get("bad_cases", []))[:1],
            "missed_cases": list(item.get("missed_cases", []))[:1],
        }
    return {
        "mode": feedback.get("mode"),
        "database_size": feedback.get("database_size"),
        "top_k": feedback.get("top_k"),
        "best_candidate_found_by_scoring": feedback.get("best_candidate_found_by_scoring"),
        "islands": islands,
    }


def plot_latency(rounds: list[dict[str, Any]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = [item["round"] for item in rounds]
    ys = [item["latency"] if item["latency"] is not None else math.nan for item in rounds]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(xs, ys, marker="o")
    ax.set_title("Database Total Latency By Round")
    ax.set_xlabel("Round")
    ax.set_ylabel("Total latency (s)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_scores(rounds: list[dict[str, Any]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 5))
    for island in ISLANDS:
        xs = [item["round"] for item in rounds]
        ys = [item["scores"].get(island, {}).get("best_score", math.nan) for item in rounds]
        ax.plot(xs, ys, marker="o", label=island)
    ax.set_title("Island Score By Round")
    ax.set_xlabel("Round")
    ax.set_ylabel("Score")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_replacements(events: list[dict[str, Any]], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 4))
    island_index = {island: index for index, island in enumerate(ISLANDS)}
    if events:
        ax.scatter([item["round"] for item in events], [island_index[item["target_island"]] for item in events])
    else:
        ax.text(0.5, 0.5, "No island replacements", ha="center", va="center", transform=ax.transAxes)
    ax.set_yticks(list(island_index.values()))
    ax.set_yticklabels(list(island_index.keys()))
    ax.set_xlabel("Round")
    ax.set_title("Island Replacement Events")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# ScoreExpert DB Search Report",
        "",
        f"- Status: `{summary['status']}`",
        f"- Run root: `{summary['run_root']}`",
        f"- Database entries: {summary['database_entries']}",
        f"- DeepSeek enabled: `{summary['deepseek_enabled']}`",
        f"- Rounds run: {summary['rounds_run']}",
        f"- Stop reason: `{summary['stop_reason']}`",
        f"- Stop on target gap: `{summary.get('stop_on_target_gap')}`",
        f"- Stop on patience: `{summary.get('stop_on_patience')}`",
        f"- Database best: {summary['database_best']}",
        f"- Best found: {summary['best']}",
        f"- Latency chart: `{summary['latency_chart']}`",
        f"- Score chart: `{summary['score_chart']}`",
        f"- Replacement chart: `{summary['replacement_chart']}`",
        f"- LLM usage CSV: `{summary.get('llm_usage_csv')}`",
        f"- Island API timing CSV: `{summary.get('llm_timing_csv')}`",
        "",
        "## LLM Usage",
        "",
        "| Round | Calls | Failures | Input Tokens | Output Tokens | Total Tokens | Elapsed s | Estimated Cost |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for round_key, item in sorted(summary.get("llm_usage_summary", {}).items(), key=lambda pair: int(pair[0]) if str(pair[0]).isdigit() else -1):
        lines.append(
            f"| {round_key} | {item.get('calls', 0)} | {item.get('failures', 0)} | {item.get('input_tokens', 0)} | "
            f"{item.get('output_tokens', 0)} | {item.get('total_tokens', 0)} | {float(item.get('elapsed_s', 0.0)):.3f} | {float(item.get('estimated_cost', 0.0)):.8f} |"
        )
    lines.extend([
        "",
        "## Second Seed Initialization",
        "",
    ])
    for item in summary["seed_results"]:
        lines.append(f"- `{item.get('island')}`: `{item.get('status')}`, program=`{item.get('program_id', '')}`, reason=`{item.get('reason', '')}`")
    lines.extend(["", "## Rounds", ""])
    for item in summary["rounds"]:
        eval_status = item["evaluation"].get("status")
        lines.extend(
            [
                f"### Round {item['round']}",
                "",
                f"- Strategy: `{item['strategy']}`",
                f"- Evaluation status: `{eval_status}`",
                f"- Latency: `{item.get('latency')}`",
                f"- Evaluation feedback summary: `{json.dumps(compact_round_feedback_for_report(item.get('evaluation_feedback')), ensure_ascii=False)}`",
                f"- Diversity: `{item.get('diversity', {})}`",
                f"- Adjustment: `{item['adjustment']}`",
                f"- Next strategy: `{item['next_strategy']}`",
                "",
                "| Island | Best Program | Ranking Quality | Spearman | Top-K Avg Latency | Top-K Best Latency |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for island in ISLANDS:
            score = item["scores"].get(island, {})
            value = score.get("best_score")
            rho = score.get("spearman_score_vs_negative_latency")
            top_avg = score.get("top_k_avg_latency_s")
            top_best = score.get("top_k_best_latency_s")
            lines.append(
                f"| `{island}` | `{score.get('best_program_id')}` | {'' if value is None else f'{float(value):.6f}'} | "
                f"{'' if rho is None else f'{float(rho):.6f}'} | {'' if top_avg is None else f'{float(top_avg):.6f}'} | {'' if top_best is None else f'{float(top_best):.6f}'} |"
            )
        lines.append("")
        lines.append("Evolution:")
        for evo in item["evolution"]:
            lines.append(f"- `{evo.get('island')}`: `{evo.get('status')}`, program=`{evo.get('program_id', '')}`, parents=`{', '.join(str(x) for x in evo.get('parent_ids', []))}`")
        if item.get("experience_events"):
            lines.append("")
            lines.append("Experience events:")
            for event in item["experience_events"][:6]:
                lines.append(f"- `{event.get('action')}` `{event.get('kind')}`: {event.get('description')}")
        lines.append("")
        lines.append("Adaptive context:")
        for island in ISLANDS:
            context = item["adaptive_context"][island]
            lines.append(f"- `{island}` guidance: {context.get('mutation_guidance', [])}")
        if item.get("replacements"):
            lines.append("")
            lines.append("Replacements:")
            for event in item["replacements"]:
                lines.append(f"- `{event['target_island']}` from `{', '.join(event['source_islands'])}`")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def sanitize_for_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): sanitize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize_for_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run database-driven ScoreExpert search.")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "config.py")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--rounds", type=int, default=None)
    parser.add_argument("--seed", type=int, default=20260613)
    parser.add_argument("--no-reset-islands", action="store_true", help="Continue from the current active island program banks.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_db_search(args.config, args.database, args.output_root, max_rounds=args.rounds, seed=args.seed, reset_islands=not args.no_reset_islands)
    print(f"ScoreExpert DB search status: {summary['status']}")
    print(f"Run root: {summary['run_root']}")
    print(f"Report: {summary['report_md']}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
