import httpx
from app.logger import get_logger
from app.prompt_analytics import (
    check_prompt_fits,
    log_prompt_run
)
from app.config.config import OLLAMA_HOST, LLM_MODEL, CALC_MODEL, MODEL_CONTEXT_LIMIT


logger = get_logger()



def call_ollama(prompt, prompt_key="unknown"):
    # Check token size and cost estimate before sending
    stats = check_prompt_fits(prompt, model_context_limit=MODEL_CONTEXT_LIMIT)
    prompt_tokens = stats["prompt_tokens"]

    if stats["total_tokens"] > MODEL_CONTEXT_LIMIT:
        logger.warning(
            f"⚠️ Estimated total tokens {stats['total_tokens']} exceed context window ({MODEL_CONTEXT_LIMIT})."
        )

    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        with httpx.Client(timeout=2000.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            result = data.get("response", "").strip()

            # Optionally, you could measure actual response tokens here:
            measured_response_tokens = None
            # Example: measured_response_tokens = len(result.split())
            logger.debug(f"Prompt to LLM: {prompt}")
            # Log prompt run to CSV analytics
            log_prompt_run(
                prompt_key=prompt_key,
                model_name=CALC_MODEL,
                prompt_text=prompt,
                measured_response_tokens=measured_response_tokens
            )
            logger.debug(f"LLM Response: {result}")
            return result

    except Exception as e:
        logger.error(f"❌ Error calling Ollama: {e}")
        return None
