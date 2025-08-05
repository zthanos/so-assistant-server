import os
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
THIN_LLM_MODEL = "deepseek-coder-v2:latest"
LLM_MODEL = "pparikh2/phi3.5Q4_K_M"
CALC_MODEL = "pparikh2/phi3.5Q4_K_M"
MODEL_CONTEXT_LIMIT = 160_000  # max token window for deepseek-coder
REQUIREMENTS_LLM_MODEL = "pparikh2/phi3.5Q4_K_M"
LOGGING_LEVEL = "DEBUG"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
