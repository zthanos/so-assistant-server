import os
import csv
import datetime
import tiktoken
from app.logger import get_logger

logger = get_logger()
ANALYTICS_LOG = "output/prompt_analytics_log.csv"

MODEL_CONTEXT_LIMIT = 4_096  # e.g., deepseek-coder
DEFAULT_MODEL = "deepseek-coder"

MODEL_COSTS = {
    "gpt-3.5-turbo": 0.0015,
    "gpt-4": 0.03,
    "gpt-4-turbo": 0.01,
    "deepseek-coder": 0.002,  # hypothetical — adjust as needed
}

def estimate_size(text):
    enc = tiktoken.encoding_for_model("gpt-4")  # fallback
    tokens = enc.encode(text)
    prompt_token_count = len(tokens)
    return prompt_token_count

def estimate_token_cost(text, model_name=DEFAULT_MODEL):
    enc = tiktoken.encoding_for_model("gpt-4")  # fallback
    tokens = enc.encode(text)
    prompt_token_count = len(tokens)
    expected_response_tokens = int(prompt_token_count * 0.5)
    total_estimated_tokens = prompt_token_count + expected_response_tokens
    cost_per_k = MODEL_COSTS.get(model_name, 0.002)
    cost_estimate = (prompt_token_count / 1000) * cost_per_k

    # logger.info(f"🧮 Prompt tokens: {prompt_token_count}")
    # logger.info(f"📤 Expected response tokens (~50% extra): {expected_response_tokens}")
    # logger.info(f"📦 Total estimated tokens: {total_estimated_tokens}")
    # logger.info(f"💲 Estimated input cost: ${cost_estimate:.4f} (response cost not included)")

    return {
        "prompt_tokens": prompt_token_count,
        "expected_response_tokens": expected_response_tokens,
        "total_tokens": total_estimated_tokens,
        "cost_estimate": cost_estimate,
    }

def check_prompt_fits(text, model_context_limit=MODEL_CONTEXT_LIMIT):
    stats = estimate_token_cost(text)
    margin = model_context_limit - stats["total_tokens"]
    if stats["total_tokens"] > model_context_limit:
        logger.warning(f"⚠️ WARNING: Total tokens exceed context window by {abs(margin)} tokens!")
    else:
        logger.info(f"✅ OK: Fits within context window (margin: {margin} tokens)")
    return stats

def log_prompt_run(prompt_key, model_name, prompt_text, measured_response_tokens=None):
    os.makedirs(os.path.dirname(ANALYTICS_LOG), exist_ok=True)
    stats = estimate_token_cost(prompt_text, model_name=model_name)
    if measured_response_tokens is not None:
        stats["total_tokens"] = stats["prompt_tokens"] + measured_response_tokens

    with open(ANALYTICS_LOG, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if csvfile.tell() == 0:
            writer.writerow([
                "timestamp", "prompt_key", "model", "prompt_tokens",
                "response_tokens", "total_tokens", "cost_estimate"
            ])
        writer.writerow([
            datetime.datetime.now().isoformat(),
            prompt_key,
            model_name,
            stats["prompt_tokens"],
            measured_response_tokens if measured_response_tokens is not None else stats["expected_response_tokens"],
            stats["total_tokens"],
            f"${stats['cost_estimate']:.4f}"
        ])
    logger.info(f"📊 Prompt analytics logged to {ANALYTICS_LOG}")

def summarize_prompt_runs():
    if not os.path.exists(ANALYTICS_LOG):
        logger.info("No analytics log file found.")
        return

    summary = {}
    with open(ANALYTICS_LOG, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = row["prompt_key"]
            summary.setdefault(key, {
                "runs": 0,
                "total_prompt_tokens": 0,
                "total_response_tokens": 0,
                "total_cost": 0.0
            })
            summary[key]["runs"] += 1
            summary[key]["total_prompt_tokens"] += int(row["prompt_tokens"])
            summary[key]["total_response_tokens"] += int(row["response_tokens"])
            summary[key]["total_cost"] += float(row["cost_estimate"].replace("$", ""))

    logger.info("\n📈 Summary of Prompt Runs:")
    for key, stats in summary.items():
        logger.info(
            f"🔑 {key} → {stats['runs']} runs, "
            f"{stats['total_prompt_tokens']} prompt tokens, "
            f"{stats['total_response_tokens']} response tokens, "
            f"💰 Total cost: ${stats['total_cost']:.4f}"
        )
