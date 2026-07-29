"""128 卡物理拓扑。

这里是 30B 示例实际使用的拓扑入口。亲合组、Server、卡号和异常项均可直接编辑。
"""

from __future__ import annotations

from copy import deepcopy


TOPOLOGY_128G = {
    "name": "128g_4_affinity_8_server",
    "total_devices": 128,
    "default_compute_tflops": 312.0,
    # 4 个亲合组；每组 2 台 Server；每台 Server 16 张卡。
    "affinity_groups": [
        {
            "affinity_group_id": 0,
            "servers": [
                {"server_id": 0, "ranks": list(range(0, 16))},
                {"server_id": 1, "ranks": list(range(16, 32))},
            ],
        },
        {
            "affinity_group_id": 1,
            "servers": [
                {"server_id": 2, "ranks": list(range(32, 48))},
                {"server_id": 3, "ranks": list(range(48, 64))},
            ],
        },
        {
            "affinity_group_id": 2,
            "servers": [
                {"server_id": 4, "ranks": list(range(64, 80))},
                {"server_id": 5, "ranks": list(range(80, 96))},
            ],
        },
        {
            "affinity_group_id": 3,
            "servers": [
                {"server_id": 6, "ranks": list(range(96, 112))},
                {"server_id": 7, "ranks": list(range(112, 128))},
            ],
        },
    ],
    # 慢卡示例（取消注释后生效）：
    # 17: {"compute_tflops": 180.0, "status": "slow", "note": "人工注入慢卡"},
    "device_overrides": {},
    # 慢链路/故障链路示例见 topology/README.md。默认拓扑没有异常。
    "link_overrides": [],
    "domains": {
        "tp": {"size": 4, "stride": 1},
        "dp_cp": {"size": 32, "stride": 4},
        "dp_ep": {"size": 4, "stride": 32},
        "ep": {"size": 8, "stride": 4},
        "ep_tp": {"size": 32, "stride": 1},
        "pp": {"size": 1, "stride": 1},
    },
}


def get_topology_128g() -> dict:
    return deepcopy(TOPOLOGY_128G)
