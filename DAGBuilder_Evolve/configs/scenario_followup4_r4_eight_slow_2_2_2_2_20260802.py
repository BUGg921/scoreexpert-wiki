from configs.scenario_7b_32g_4node_base import make_config


CONFIG = make_config(
    "followup4_r4_eight_slow_2_2_2_2_20260802",
    [6, 7, 14, 15, 22, 23, 30, 31],
)

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
        "/Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/"
        "followup4-r1-two-slow-same-node-20260802_"
        "20260802_232854_scenario_analysis.md",
        "/Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/"
        "followup4-r2-two-slow-same-affinity-20260802_"
        "20260802_233622_scenario_analysis.md",
        "/Users/cookie/Documents/wiki/DAGBuilder_Evolve/outputs/"
        "followup4-r3-three-slow-1-1-1-0-20260802_"
        "20260802_234416_scenario_analysis.md",
    ],
}
