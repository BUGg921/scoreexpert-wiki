from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

from .config import ScenarioConfig
from .programs import ProgramRecord, validate_source


ISLAND_GUIDANCE = {
    "memory_safe": "优先规避显存超限，同时比较参数分片与激活占用。",
    "topology_affinity": "优先让 TP 保持节点内，并减少跨亲合组的高流量通信。",
    "pipeline_efficiency": "重点权衡 PP 深度、微批数量、流水线气泡与调度方式。",
    "balanced_generalist": "综合计算切分、流水线、DP 通信和拓扑局部性。",
}


def extract_score_function(text: str) -> str:
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1)
    lines = text.strip().splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith("def score_strategy(")),
        None,
    )
    if start is None:
        raise ValueError("DeepSeek response has no score_strategy function")
    function_lines = [lines[start]]
    for line in lines[start + 1 :]:
        if line.startswith((" ", "\t")) or not line.strip():
            function_lines.append(line)
        else:
            break
    source = "\n".join(function_lines).rstrip()
    validate_source(source)
    return source


class MockEvolutionClient:
    def evolve(
        self,
        island: str,
        parent: ProgramRecord,
        inspirations: list[ProgramRecord],
        feedback: dict[str, Any],
        generation: int,
    ) -> str:
        bias = generation + list(ISLAND_GUIDANCE).index(island) + 1
        return f"""
def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):
    pp = int(strategy["pp"])
    tp = int(strategy["tp"])
    dp = int(strategy["dp"])
    mb = int(strategy["micro_batch_num"])
    bubble = float(pp - 1) / float(mb + pp - 1)
    locality = 1.0 if tp <= int(topology_cfg["cards_per_server"]) else 0.0
    schedule_bonus = {12.0 + bias:.1f} if strategy["schedule"] == "1f1b" else 0.0
    comm_bonus = {8.0 + bias:.1f} if strategy["dp_communication"] == "rs_ag" else 0.0
    return 1000.0 + {10.0 + bias:.1f} * tp + 3.0 * dp - 180.0 * bubble + 20.0 * locality + schedule_bonus + comm_bonus
""".strip()


class DeepSeekEvolutionClient:
    def __init__(self, config: ScenarioConfig) -> None:
        self.config = config.deepseek
        self.api_key = os.environ.get(str(self.config["api_key_env"]))
        if not self.api_key:
            raise RuntimeError(
                f"Formal evolution requires environment variable {self.config['api_key_env']}"
            )

    def evolve(
        self,
        island: str,
        parent: ProgramRecord,
        inspirations: list[ProgramRecord],
        feedback: dict[str, Any],
        generation: int,
    ) -> str:
        prompt = {
            "task": "修改启发式打分函数，使其更可能提名仿真时延更低的并行策略。",
            "island": island,
            "guidance": ISLAND_GUIDANCE[island],
            "generation": generation,
            "required_signature": "score_strategy(strategy, model_cfg, topology_cfg, workload_cfg) -> float",
            "available_inputs": {
                "strategy_keys": [
                    "pp", "tp", "dp", "micro_batch_num", "schedule",
                    "dp_communication", "active_gpus", "signature",
                ],
                "model_cfg_keys": [
                    "name", "num_layers", "hidden_size", "ffn_hidden_size",
                    "parameter_count", "dtype_bytes", "gradient_dtype_bytes",
                ],
                "topology_cfg_keys": [
                    "total_devices", "cards_per_server", "affinity_group_count",
                ],
                "workload_cfg_keys": [
                    "global_batch_size", "sequence_length", "compute_efficiency",
                    "backward_flop_multiplier", "activation_multiplier",
                    "optimizer_state_multiplier",
                ],
            },
            "restrictions": [
                "只输出一个 Python 函数，不得 import、读写文件、联网、调用仿真器或使用循环。",
                "可读取 strategy 的 pp/tp/dp/micro_batch_num/schedule/dp_communication/active_gpus。",
                "只能读取 available_inputs 中列出的字段，不能假设存在其他字段。",
                "不得伪造仿真结果；函数只负责排序。",
            ],
            "parent_source": parent.source,
            "inspiration_sources": [item.source for item in inspirations],
            "simulator_feedback": feedback,
        }
        body = {
            "model": self.config["model"],
            "temperature": float(self.config.get("temperature", 0.7)),
            "max_tokens": int(self.config.get("max_tokens", 1500)),
            "thinking": {"type": "disabled"},
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return JSON only, with exactly one key named source. "
                        "source must be executable Python code starting with "
                        "def score_strategy(strategy, model_cfg, topology_cfg, workload_cfg):"
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        }
        request = urllib.request.Request(
            str(self.config["base_url"]).rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=float(self.config["timeout_s"])) as response:
            value = json.loads(response.read().decode("utf-8"))
        content = str(value["choices"][0]["message"]["content"])
        try:
            payload = json.loads(content)
            source = str(payload["source"])
        except (json.JSONDecodeError, KeyError):
            start = content.find("def score_strategy(")
            if start < 0:
                raise
            source = content[start:].replace("\\n", "\n").replace('\\"', '"')
        return extract_score_function(source)
