from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any


class DeepSeekUnavailable(RuntimeError):
    pass


def deepseek_config(config: dict[str, Any]) -> dict[str, Any]:
    search = config.get("search_config", {})
    return dict(search.get("deepseek", {}))


def api_key_env(config: dict[str, Any]) -> str:
    return str(deepseek_config(config).get("api_key_env", "DEEPSEEK_API_KEY"))


def is_enabled(config: dict[str, Any]) -> bool:
    cfg = deepseek_config(config)
    return bool(cfg.get("enabled", True)) and bool(os.environ.get(api_key_env(config)))


def summarize_evaluation_feedback(results: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    if not is_enabled(config):
        return {
            "status": "disabled",
            "reason": f"{api_key_env(config)} is not set",
            "summary": "",
            "suggestions": [],
        }
    payload = compact_results(results)
    messages = [
        {
            "role": "system",
            "content": (
                "You summarize DAGBuilder strategy evaluation results. "
                "Return compact JSON with keys summary and suggestions. "
                "Do not mention API keys or secrets."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=False),
        },
    ]
    raw = call_chat(messages, config)
    data = parse_json_object(raw)
    return {
        "status": "pass",
        "summary": str(data.get("summary", "")),
        "suggestions": data.get("suggestions", []),
        "raw": raw,
    }


def evolve_program(
    *,
    island: str,
    instruction: str,
    v0: dict[str, Any],
    v1: dict[str, Any],
    feedback: dict[str, Any],
    config: dict[str, Any],
) -> str | None:
    result = evolve_program_with_usage(island=island, instruction=instruction, v0=v0, v1=v1, feedback=feedback, config=config)
    return result.get("source") if isinstance(result, dict) else None


def evolve_program_with_usage(
    *,
    island: str,
    instruction: str,
    v0: dict[str, Any],
    v1: dict[str, Any],
    feedback: dict[str, Any],
    config: dict[str, Any],
    round_index: int | None = None,
    call_type: str = "evolve_program",
) -> dict[str, Any]:
    if not is_enabled(config):
        return {"source": None, "usage": disabled_usage_record(config, island, round_index, call_type)}
    messages = build_evolve_messages(island, instruction, v0, v1, feedback)
    result = call_chat_with_usage(messages, config, island=island, round_index=round_index, call_type=call_type)
    raw = str(result["content"])
    data = parse_json_object(raw)
    source = data.get("source")
    if not isinstance(source, str) or "def score_strategy" not in source:
        source = extract_code(raw)
    return {"source": source, "usage": result["usage"], "raw": raw}


def build_evolve_messages(island: str, instruction: str, v0: dict[str, Any], v1: dict[str, Any], feedback: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You evolve one Python scoring function for DAGBuilder. "
                "Return only JSON: {\"source\": \"def score_strategy(...):\\n    ...\"}. "
                "The source must define exactly score_strategy(strategy, model_cfg, topo_cfg, profile_cfg). "
                "The function must initialize its score with exactly `score = 1000.0`; do not use any other base score. "
                "Keep changes readable: every new logical term must be introduced by a short code comment. "
                "Do not repeatedly penalize PP depth through bubble, PP communication, and affinity at the same time; keep PP=2/4 viable until real total_latency feedback proves it is worse. "
                "Do not import modules, read files, use randomness, eval, exec, compile, globals or locals."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "island": island,
                    "island_instruction": instruction,
                    "feedback": feedback,
                    "v0": program_for_prompt(v0),
                    "v1": program_for_prompt(v1),
                    "task": "Generate v2 by improving v0 and v1 while preserving the island direction.",
                },
                ensure_ascii=False,
            ),
        },
    ]


def call_chat(messages: list[dict[str, str]], config: dict[str, Any]) -> str:
    return str(call_chat_with_usage(messages, config)["content"])


def call_chat_with_usage(
    messages: list[dict[str, str]],
    config: dict[str, Any],
    *,
    island: str | None = None,
    round_index: int | None = None,
    call_type: str = "chat",
) -> dict[str, Any]:
    cfg = deepseek_config(config)
    key = os.environ.get(api_key_env(config))
    if not key:
        raise DeepSeekUnavailable(f"{api_key_env(config)} is not set")
    base_url = str(cfg.get("base_url", "https://api.deepseek.com")).rstrip("/")
    url = f"{base_url}/chat/completions"
    payload = {
        "model": str(cfg.get("model", "deepseek-v4-pro")),
        "messages": messages,
        "temperature": float(cfg.get("temperature", 0.7)),
    }
    input_chars = len(json.dumps(messages, ensure_ascii=False))
    started = time.perf_counter()
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=float(cfg.get("timeout_seconds", 120))) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"DeepSeek API error {exc.code}: {body}") from exc
    elapsed = time.perf_counter() - started
    content = str(data["choices"][0]["message"]["content"])
    usage = usage_record(
        config=config,
        model=str(payload["model"]),
        island=island,
        round_index=round_index,
        call_type=call_type,
        status="pass",
        elapsed_s=elapsed,
        input_chars=input_chars,
        output_chars=len(content),
        usage=data.get("usage"),
    )
    return {"content": content, "usage": usage}


def usage_record(
    *,
    config: dict[str, Any],
    model: str,
    island: str | None,
    round_index: int | None,
    call_type: str,
    status: str,
    elapsed_s: float,
    input_chars: int,
    output_chars: int,
    usage: Any,
    reason: str = "",
) -> dict[str, Any]:
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    token_source = "estimated"
    if isinstance(usage, dict):
        prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
        completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
        total_tokens = usage.get("total_tokens")
        token_source = "api"
    if not isinstance(prompt_tokens, (int, float)):
        prompt_tokens = max(1, round(input_chars / 4))
    if not isinstance(completion_tokens, (int, float)):
        completion_tokens = max(1, round(output_chars / 4))
    if not isinstance(total_tokens, (int, float)):
        total_tokens = int(prompt_tokens) + int(completion_tokens)
    pricing = deepseek_config(config).get("pricing_per_1m_tokens", {})
    input_price = float(pricing.get("input", 0.0)) if isinstance(pricing, dict) else 0.0
    output_price = float(pricing.get("output", 0.0)) if isinstance(pricing, dict) else 0.0
    estimated_cost = (float(prompt_tokens) / 1_000_000.0 * input_price) + (float(completion_tokens) / 1_000_000.0 * output_price)
    return {
        "round": round_index,
        "island": island,
        "call_type": call_type,
        "model": model,
        "status": status,
        "reason": reason,
        "elapsed_s": round(elapsed_s, 3),
        "input_chars": input_chars,
        "output_chars": output_chars,
        "input_tokens": int(prompt_tokens),
        "output_tokens": int(completion_tokens),
        "total_tokens": int(total_tokens),
        "token_source": token_source,
        "estimated_cost": round(estimated_cost, 8),
    }


def disabled_usage_record(config: dict[str, Any], island: str | None, round_index: int | None, call_type: str) -> dict[str, Any]:
    return usage_record(
        config=config,
        model=str(deepseek_config(config).get("model", "deepseek-v4-pro")),
        island=island,
        round_index=round_index,
        call_type=call_type,
        status="skipped",
        elapsed_s=0.0,
        input_chars=0,
        output_chars=0,
        usage=None,
        reason=f"{api_key_env(config)} is not set",
    )


def compact_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in results:
        candidate = item.get("candidate", {})
        evaluation = item.get("evaluation") or {}
        overlap = evaluation.get("overlap_evaluation", {})
        compact.append(
            {
                "candidate_name": candidate.get("candidate_name"),
                "source_islands": candidate.get("source_islands"),
                "pp_size": candidate.get("pp_size"),
                "micro_batch_num": candidate.get("micro_batch_num"),
                "tp_size": candidate.get("tp_size"),
                "dp_size": candidate.get("dp_size"),
                "baseline_latency_s": evaluation.get("baseline_latency_s"),
                "overlap_latency_s": overlap.get("overlap_latency_s"),
                "overlap_saved_ratio": overlap.get("overlap_saved_ratio"),
                "flow_status": item.get("flow_status"),
            }
        )
    return compact


def parse_json_object(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        return {}
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def extract_code(raw: str) -> str | None:
    match = re.search(r"```(?:python)?\s*(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip() + "\n"
    if "def score_strategy" in raw:
        return raw[raw.index("def score_strategy") :].strip() + "\n"
    return None


def program_for_prompt(program: dict[str, Any]) -> dict[str, Any]:
    return {
        "program_id": program.get("program_id"),
        "island_score": program.get("island_score"),
        "evaluation": program.get("evaluation"),
        "source": program.get("source"),
    }
