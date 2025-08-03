import os
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
THIN_LLM_MODEL = "deepseek-coder-v2:latest"
LLM_MODEL = "gemma3"
CALC_MODEL = "gemma3"
MODEL_CONTEXT_LIMIT = 160_000  # max token window for deepseek-coder

LOGGING_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
