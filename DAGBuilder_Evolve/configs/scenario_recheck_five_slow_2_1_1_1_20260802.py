from configs.scenario_7b_32g_4node_base import make_config


CONFIG = make_config(
    "recheck_five_slow_2_1_1_1_20260802",
    [6, 7, 15, 23, 31],
)

# The request is for one scene only. Keep the campaign explicitly bounded to
# this reproduction and do not launch report-selected follow-up scenes.
CONFIG["analysis"]["campaign"] = {
    "max_followup_rounds": 0,
    "scenarios_per_round": 1,
    "max_total_scenarios": 1,
    "max_wall_time_s": None,
    "convergence_rounds": None,
    "convergence_mode": None,
    "min_latency_improvement_ratio": None,
    "stop_on_no_new_recommendation": True,
    "stop_on_duplicate_scene": True,
    "allow_multi_variable_followup": False,
    "completed_report_paths": [],
}
