from configs.scenario_7b_32g_4node_base import make_config


CONFIG = make_config(
    "campaign_s7_rerun_max3_20260730",
    [6, 7, 15, 23, 31],
)

CONFIG["analysis"]["campaign"] = {
    "max_followup_rounds": 2,
    "scenarios_per_round": 1,
    "max_total_scenarios": 3,
    "max_wall_time_s": None,
    "convergence_rounds": None,
    "convergence_mode": None,
    "min_latency_improvement_ratio": None,
    "stop_on_no_new_recommendation": True,
    "stop_on_duplicate_scene": True,
    "allow_multi_variable_followup": False,
    "completed_report_paths": [],
}
