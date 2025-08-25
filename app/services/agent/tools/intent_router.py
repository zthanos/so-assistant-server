"""Intent Router Tool for detecting user intent and extracting targets."""
import json
import logging
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.services.agent.tools.base import BaseAgentTool
from app.services.agent.llm_client import streaming_ollama_client
from app.services.agent.tools.validation import validate_router_output, RetryHandler, JSONResponseParser
from app.services.agent.prompts.templates import prompt_manager, Language

logger = logging.getLogger(__name__)


class RouterOutput(BaseModel):
    """Router output schema."""
    
    intent: str = Field(..., description="Detected intent")
    targets: Dict[str, List[str]] = Field(..., description="Target IDs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reason: str = Field(..., description="Rationale for intent")


class IntentRouterTool(BaseAgentTool):
    """Tool for detecting user intent and extracting target IDs."""
    
    name = "intent_router"
    description = "Analyze user query to detect intent and extract target IDs (SEC-*, REQ-*, SEQ-*, C4-*)"
    tool_category = "routing"
    requires_project_id = False
    
    # Intent keywords for Greek and English
    INTENT_KEYWORDS = {
        "integration_check": {
            "en": [
                "integration", "consistency", "match", "align", "compatible", 
                "diagram", "sequence", "c4", "architecture", "flow", "connect",
                "sync", "coherent", "correspond", "relate"
            ],
            "el": [
                "ολοκλήρωση", "συνέπεια", "ταιριάζει", "ευθυγράμμιση", "συμβατό",
                "διάγραμμα", "ακολουθία", "αρχιτεκτονική", "ροή", "σύνδεση",
                "συγχρονισμός", "συνεκτικό", "αντιστοιχεί", "σχετίζεται"
            ]
        },
        "requirements_coverage": {
            "en": [
                "coverage", "requirement", "cover", "fulfill", "satisfy", "meet",
                "gap", "missing", "complete", "implement", "address", "trace",
                "map", "verify", "check coverage"
            ],
            "el": [
                "κάλυψη", "απαίτηση", "καλύπτει", "εκπληρώνει", "ικανοποιεί", "πληροί",
                "κενό", "λείπει", "πλήρης", "υλοποιεί", "αντιμετωπίζει", "ιχνηλάτηση",
                "χαρτογράφηση", "επαληθεύει", "έλεγχος κάλυψης"
            ]
        },
        "improve_paragraph": {
            "en": [
                "improve", "enhance", "better", "rewrite", "fix", "optimize",
                "paragraph", "section", "text", "content", "quality", "clarity",
                "refactor", "revise", "edit", "update"
            ],
            "el": [
                "βελτίωση", "ενίσχυση", "καλύτερα", "ξαναγράψιμο", "διόρθωση", "βελτιστοποίηση",
                "παράγραφος", "ενότητα", "κείμενο", "περιεχόμενο", "ποιότητα", "σαφήνεια",
                "αναδιοργάνωση", "αναθεώρηση", "επεξεργασία", "ενημέρωση"
            ]
        },
        "qna": {
            "en": [
                "what", "how", "why", "when", "where", "who", "explain", "describe",
                "tell", "show", "question", "answer", "help", "information"
            ],
            "el": [
                "τι", "πώς", "γιατί", "πότε", "πού", "ποιος", "εξήγηση", "περιγραφή",
                "πες", "δείξε", "ερώτηση", "απάντηση", "βοήθεια", "πληροφορία"
            ]
        }
    }
    
    # ID patterns for extracting targets
    ID_PATTERNS = {
        "so_ids": re.compile(r'\bSEC-[A-Za-z0-9.-]+\b'),
        "requirement_ids": re.compile(r'\bREQ-[A-Za-z0-9.-]+\b'),
        "diagram_ids": re.compile(r'\b(?:SEQ|C4)-[A-Za-z0-9.-]+\b')
    }
    
    async def _execute(self, user_message: str, language: str = "auto", **kwargs) -> Dict[str, Any]:
        """Execute intent detection and target extraction."""
        try:
            # Detect language if auto
            detected_language = self._detect_language(user_message) if language == "auto" else language
            
            # Extract explicit target IDs from the message
            targets = self._extract_target_ids(user_message)
            
            # Detect intent using LLM
            intent_result = await self._detect_intent_with_llm(user_message, detected_language, targets)
            
            # Validate and enhance the result
            validated_result = self._validate_and_enhance_result(intent_result, targets, user_message)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"Error in intent router: {str(e)}")
            # Fallback to qna with low confidence
            return {
                "intent": "qna",
                "targets": {"so_ids": [], "requirement_ids": [], "diagram_ids": []},
                "confidence": 0.1,
                "reason": f"Fallback to QnA due to error: {str(e)}"
            }
    
    def _detect_language(self, text: str) -> str:
        """Detect language of the text (simple heuristic)."""
        # Count Greek characters
        greek_chars = sum(1 for char in text if '\u0370' <= char <= '\u03FF' or '\u1F00' <= char <= '\u1FFF')
        total_chars = len([char for char in text if char.isalpha()])
        
        if total_chars == 0:
            return "en"
        
        greek_ratio = greek_chars / total_chars
        return "el" if greek_ratio > 0.3 else "en"
    
    def _extract_target_ids(self, text: str) -> Dict[str, List[str]]:
        """Extract target IDs from the text using regex patterns."""
        targets = {}
        
        for target_type, pattern in self.ID_PATTERNS.items():
            matches = pattern.findall(text)
            targets[target_type] = list(set(matches))  # Remove duplicates
        
        return targets
    
    async def _detect_intent_with_llm(self, user_message: str, language: str, explicit_targets: Dict[str, List[str]]) -> Dict[str, Any]:
        """Use LLM to detect intent with context about explicit targets."""
        
        try:
            # Use retry handler with validation
            async def llm_call():
                # Create prompt for intent detection
                prompt = self._create_intent_detection_prompt(user_message, language, explicit_targets)
                
                # Get LLM response
                response = await streaming_ollama_client.generate(prompt, "intent_detection")
                
                # Parse and validate JSON response
                return JSONResponseParser.parse_json_response(response)
            
            # Execute with retry and validation
            result = await RetryHandler.retry_with_validation(
                llm_call,
                validate_router_output,
                max_retries=1
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LLM intent detection: {str(e)}")
            return self._fallback_intent_detection(user_message, language, explicit_targets)
    
    def _create_intent_detection_prompt(self, user_message: str, language: str, explicit_targets: Dict[str, List[str]]) -> str:
        """Create prompt for intent detection using template manager."""
        
        # Convert language string to Language enum
        lang = Language.GREEK if language == "el" else Language.ENGLISH
        
        # Use prompt manager to format the intent detection template
        return prompt_manager.format_prompt(
            "intent_detection",
            language=lang,
            user_message=user_message,
            project_id="current",  # Will be filled by context
            explicit_targets=json.dumps(explicit_targets, indent=2),
            available_so_sections="[Context will be provided by retrieval tools]",
            available_requirements="[Context will be provided by retrieval tools]",
            available_diagrams="[Context will be provided by retrieval tools]"
        )
    
    def _fallback_intent_detection(self, user_message: str, language: str, explicit_targets: Dict[str, List[str]]) -> Dict[str, Any]:
        """Fallback intent detection using keyword matching."""
        logger.info("Using fallback intent detection with keyword matching")
        
        # Convert message to lowercase for matching
        message_lower = user_message.lower()
        
        # Score each intent based on keyword matches
        intent_scores = {}
        
        for intent, keywords_dict in self.INTENT_KEYWORDS.items():
            keywords = keywords_dict.get(language, keywords_dict.get("en", []))
            score = sum(1 for keyword in keywords if keyword.lower() in message_lower)
            intent_scores[intent] = score
        
        # Boost scores based on explicit targets
        if explicit_targets.get("so_ids") and explicit_targets.get("diagram_ids"):
            intent_scores["integration_check"] += 2
        if explicit_targets.get("requirement_ids"):
            intent_scores["requirements_coverage"] += 2
        if len(explicit_targets.get("so_ids", [])) == 1:  # Single section
            intent_scores["improve_paragraph"] += 1
        
        # Select intent with highest score
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        
        # Calculate confidence based on score
        max_possible_score = len(self.INTENT_KEYWORDS[best_intent].get(language, []))
        confidence = min(0.9, best_score / max(max_possible_score, 1)) if max_possible_score > 0 else 0.3
        
        # If no clear winner, default to qna
        if best_score == 0:
            best_intent = "qna"
            confidence = 0.5
        
        return {
            "intent": best_intent,
            "targets": explicit_targets,
            "confidence": confidence,
            "reason": f"Keyword-based detection (score: {best_score})"
        }
    
    def _validate_and_enhance_result(self, result: Dict[str, Any], explicit_targets: Dict[str, List[str]], user_message: str) -> Dict[str, Any]:
        """Validate and enhance the intent detection result."""
        
        # Use validation utility
        validated_result = validate_router_output(result)
        
        # Merge with explicit targets (explicit targets take precedence)
        targets = validated_result["targets"]
        for key, values in explicit_targets.items():
            if values:  # Only override if explicit targets exist
                targets[key] = list(set(targets[key] + values))
        
        # Intent-specific enhancements
        intent = validated_result["intent"]
        
        if intent == "integration_check":
            # Should have both SO sections and diagrams
            if not targets["so_ids"] or not targets["diagram_ids"]:
                validated_result["confidence"] *= 0.7  # Reduce confidence
        
        elif intent == "requirements_coverage":
            # Should have requirements
            if not targets["requirement_ids"]:
                # Try to infer from message
                req_mentions = re.findall(r'\b(?:requirement|req|απαίτηση)\s*(\d+|[A-Za-z0-9.-]+)', user_message.lower())
                if req_mentions:
                    targets["requirement_ids"] = [f"REQ-{req}" for req in req_mentions[:5]]
        
        elif intent == "improve_paragraph":
            # Should have SO sections
            if not targets["so_ids"]:
                # Try to infer from message
                section_mentions = re.findall(r'\b(?:section|sec|ενότητα)\s*([A-Za-z0-9.-]+)', user_message.lower())
                if section_mentions:
                    targets["so_ids"] = [f"SEC-{sec}" for sec in section_mentions[:3]]
        
        return validated_result


# Register the tool
from app.services.agent.tools.base import tool_registry
intent_router_tool = IntentRouterTool()
tool_registry.register_tool(intent_router_tool)