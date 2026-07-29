from copy import deepcopy

from configs.scenario_7b_32g_flash import CONFIG as BASE_CONFIG


CONFIG = deepcopy(BASE_CONFIG)
CONFIG["name"] = "7b_32g_quick"
CONFIG["search"]["nominations_per_program"] = 2
CONFIG["evolution"]["rounds"] = 1
CONFIG["evolution"]["migration_rounds"] = []
