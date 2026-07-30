from copy import deepcopy
from pathlib import Path

from configs.scenario_7b_32g_flash import CONFIG as BASE_CONFIG


PROJECT = Path(__file__).resolve().parents[1]


def make_config(name: str, slow_ranks: list[int]) -> dict:
    config = deepcopy(BASE_CONFIG)
    config["name"] = name
    config["topology"] = {
        "total_devices": 32,
        "default_compute_tflops": 312.0,
        "affinity_groups": [
            {
                "affinity_group_id": 0,
                "servers": [
                    {"server_id": 0, "ranks": list(range(0, 8))},
                    {"server_id": 1, "ranks": list(range(8, 16))},
                ],
            },
            {
                "affinity_group_id": 1,
                "servers": [
                    {"server_id": 2, "ranks": list(range(16, 24))},
                    {"server_id": 3, "ranks": list(range(24, 32))},
                ],
            },
        ],
        "device_overrides": {
            rank: {"compute_tflops": 156.0, "note": "0.5x slow GPU"}
            for rank in slow_ranks
        },
        "link_overrides": [],
    }
    config["search"]["nominations_per_program"] = 2
    config["evolution"]["rounds"] = 10
    config["evolution"]["migration_rounds"] = []
    config["analysis"] = {
        "experience_summary_path": str(
            PROJECT.parent / "concepts" / "latency-first-experience-summary.md"
        ),
        "fixed_dimensions": [
            "慢卡倍率保持当前值，不在下一批中改变",
            "模型、batch、显存和网络参数保持不变",
        ],
    }
    return config
