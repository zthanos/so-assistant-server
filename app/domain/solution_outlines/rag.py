from typing import Optional
from services.diagrams import DiagramService
from services.requirement_item_service import requirement_item_repository


def get_solution_outline():
    pass
def get_accepted_requirements():
    pass

# ---------- Prompt builders ----------
def build_rephrase_prompt(so_doc: str, reqs: str, mermaid: str, chat_summary: str,
                          user_message: str, style_snippet: Optional[str]) -> str:
    return f"""
Rephrase the latest user message as a standalone request to improve a Solution Outline.

CONTEXT:
SO_DOC_MD:
{so_doc}

REQUIREMENTS_BULLETS:
{reqs}

MERMAID_DIAGRAMS:
{mermaid}

CHAT_SUMMARY:
{chat_summary}

STYLE_SNIPPET (optional, 100–300 words):
{style_snippet or ""}

QUERY:
{user_message}

Rules:
- Use ONLY the provided context; no outside knowledge.
- Preserve intent, domain terms, and proper names; match QUERY language.
- Return ONLY valid JSON:
{{
  "rephrased": "<one or two sentences, self-contained>",
  "style": {{
    "tone": "<formal/informal>",
    "voice": "<active/passive>",
    "sentence_length": "<concise/medium/long>",
    "bullets_preference": "<low/medium/high>",
    "terminology_to_preserve": ["..."]
  }}
}}
- If insufficient information:
{{"rephrased": "INSUFFICIENT", "style": null}}
""".strip()