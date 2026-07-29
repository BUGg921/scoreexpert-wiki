from copy import deepcopy

from configs.scenario_7b_32g import CONFIG as BASE_CONFIG


CONFIG = deepcopy(BASE_CONFIG)
# CONFIG["name"] = "7b_32g_deepseek_flash"
# CONFIG["deepseek"]["model"] = "deepseek-v4-flash"

