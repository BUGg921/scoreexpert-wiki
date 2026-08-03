from configs.scenario_7b_32g_4node_base import make_config


CONFIG = make_config(
    "followup4_r1_two_slow_same_node_20260802",
    [6, 7],
)

# Four-scene sequential campaign requested on 2026-08-02.  The previous
# five-slow-card report is the recommendation source and is campaign-local
# coverage, not formal Wiki experience.
CONFIG["analysis"]["campaign"] = {
    "max_followup_rounds": 3,
    "scenarios_per_round": 1,
    "max_total_scenarios": 4,
    "max_wall_time_s": None,
    "convergence_rounds": None,
    "convergence_mode": None,
    "min_latency_improvement_ratio": None,
    "stop_on_no_new_recommendation": True,
    "stop_on_duplicate_scene": True,
    "allow_multi_variable_followup": False,
    "completed_report_paths": [
        "/Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/"
        "prompt-contract-five-slow-2-1-1-1-20260802_"
        "20260802_214725_scenario_analysis.md",
    ],
}
