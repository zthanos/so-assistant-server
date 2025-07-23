import re
import json

def safe_extract_json(response_text):
    try:
        json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
        json_content = json_match.group(1) if json_match else response_text
        return json.loads(json_content)
    except Exception:
        return None


def extract_json_from_text(text):
    matches = re.findall(r"```json\s*([\s\S]*?)\s*```", text)
    if not matches:
        raise ValueError("No valid JSON found in LLM response")
    return json.loads(matches[0])        


def extract_json_array_or_object_from_text(text):
    """
    Extracts either a JSON array or object from a code block (```json ... ```) or from the text.
    Returns the parsed JSON (list or dict).
    """
    # Try to extract from code block first
    matches = re.findall(r"```json\s*([\s\S]*?)\s*```", text)
    if matches:
        candidate = matches[0].strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass
    # Fallback: search for first array or object in the text
    array_match = re.search(r'(\[.*?\])', text, re.DOTALL)
    if array_match:
        try:
            return json.loads(array_match.group(1))
        except Exception:
            pass
    object_match = re.search(r'(\{.*?\})', text, re.DOTALL)
    if object_match:
        try:
            return json.loads(object_match.group(1))
        except Exception:
            pass
    raise ValueError("No valid JSON array or object found in LLM response")        