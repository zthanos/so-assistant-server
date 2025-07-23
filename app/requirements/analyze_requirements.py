from app.ollama_client import call_ollama
from app.logger import get_logger
from app.utils.llm_response_utils import extract_json_array_or_object_from_text

logger = get_logger()

def analyze_requirements(content: str):
    prompt = f"""
You are an experienced business analyst.

Analyze the following document written in Greek, describing the current (as-is) and desired (to-be) business processes.

Extract ONLY the requirements related to the "to-be" state.

Return ONLY a JSON array, where each requirement has:
- title: short title (keep in Greek)
- description: short description (1-2 sentences, in Greek)
- functional: true if functional requirement, false if non-functional

### Example format:
[
    {{
        "title": "Cardless ανάληψη με QR",
        "description": "Ο πελάτης μπορεί να κάνει ανάληψη μετρητών στο ATM χρησιμοποιώντας QR code χωρίς κάρτα.",
        "functional": true
    }}
]

DO NOT include any explanation or commentary, only the JSON array.

    {content}
    ```
    return only the json nothing else
    """

    answer = call_ollama(prompt, prompt_key="")
    logger.debug(f"Raw Answer:{answer}")
    json_response = extract_json_array_or_object_from_text(answer)
    return json_response