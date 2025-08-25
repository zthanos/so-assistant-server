"""Validation utilities for agent tools and responses."""
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class RouterOutputValidator:
    """Validator for intent router output."""
    
    VALID_INTENTS = ["integration_check", "requirements_coverage", "improve_paragraph", "qna"]
    VALID_SEVERITIES = ["info", "minor", "major", "critical"]
    VALID_SUGGESTION_TYPES = [
        "integration", "coverage", "rewrite", "security", 
        "performance", "observability", "fault_handling"
    ]
    
    @classmethod
    def validate_router_output(cls, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean router output."""
        validated = {}
        
        # Validate intent
        intent = output.get("intent", "qna")
        if intent not in cls.VALID_INTENTS:
            logger.warning(f"Invalid intent '{intent}', defaulting to 'qna'")
            intent = "qna"
        validated["intent"] = intent
        
        # Validate targets
        targets = output.get("targets", {})
        if not isinstance(targets, dict):
            targets = {}
        
        validated_targets = {}
        for key in ["so_ids", "requirement_ids", "diagram_ids"]:
            value = targets.get(key, [])
            if not isinstance(value, list):
                value = []
            # Validate ID format
            validated_targets[key] = [
                id_val for id_val in value 
                if cls._validate_id_format(id_val, key)
            ]
        validated["targets"] = validated_targets
        
        # Validate confidence
        confidence = output.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
            confidence = 0.5
        validated["confidence"] = float(confidence)
        
        # Validate reason
        reason = output.get("reason", "")
        if not isinstance(reason, str) or not reason.strip():
            reason = f"Detected {intent} intent"
        validated["reason"] = reason.strip()
        
        return validated
    
    @classmethod
    def _validate_id_format(cls, id_value: str, id_type: str) -> bool:
        """Validate ID format based on type."""
        if not isinstance(id_value, str):
            return False
        
        if id_type == "so_ids":
            return id_value.startswith("SEC-") and len(id_value) > 4
        elif id_type == "requirement_ids":
            return id_value.startswith("REQ-") and len(id_value) > 4
        elif id_type == "diagram_ids":
            return (id_value.startswith("SEQ-") or id_value.startswith("C4-")) and len(id_value) > 4
        
        return False


class StructuredResponseValidator:
    """Validator for structured analysis responses."""
    
    @classmethod
    def validate_structured_response(cls, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean structured analysis response."""
        validated = {}
        
        # Validate suggestions
        suggestions = response.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []
        
        validated_suggestions = []
        for i, suggestion in enumerate(suggestions):
            if isinstance(suggestion, dict):
                validated_suggestion = cls._validate_suggestion(suggestion, i)
                if validated_suggestion:
                    validated_suggestions.append(validated_suggestion)
        
        validated["suggestions"] = validated_suggestions
        
        # Validate scores
        scores = response.get("scores", {})
        validated["scores"] = cls._validate_scores(scores)
        
        # Validate status
        status = response.get("status", "ok")
        if status not in ["ok", "insufficient"]:
            status = "ok"
        validated["status"] = status
        
        return validated
    
    @classmethod
    def _validate_suggestion(cls, suggestion: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Validate a single suggestion."""
        try:
            validated = {}
            
            # ID
            validated["id"] = suggestion.get("id", f"SUG-{index+1:03d}")
            
            # Type
            suggestion_type = suggestion.get("type", "rewrite")
            if suggestion_type not in RouterOutputValidator.VALID_SUGGESTION_TYPES:
                suggestion_type = "rewrite"
            validated["type"] = suggestion_type
            
            # Severity
            severity = suggestion.get("severity", "minor")
            if severity not in RouterOutputValidator.VALID_SEVERITIES:
                severity = "minor"
            validated["severity"] = severity
            
            # Location
            location = suggestion.get("location", {})
            if not isinstance(location, dict):
                location = {}
            validated["location"] = {
                "so_section_id": location.get("so_section_id", ""),
                "paragraph_index": max(0, int(location.get("paragraph_index", 0)))
            }
            
            # Required text fields
            for field in ["summary", "rationale", "recommendation"]:
                value = suggestion.get(field, "")
                if not isinstance(value, str):
                    value = ""
                validated[field] = value.strip()
            
            # Evidence
            evidence = suggestion.get("evidence", {})
            validated["evidence"] = cls._validate_evidence(evidence)
            
            # Proposed text (optional)
            proposed_text = suggestion.get("proposed_text")
            if proposed_text is not None and not isinstance(proposed_text, str):
                proposed_text = None
            validated["proposed_text"] = proposed_text
            
            # Confidence
            confidence = suggestion.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                confidence = 0.5
            validated["confidence"] = float(confidence)
            
            return validated
            
        except Exception as e:
            logger.error(f"Error validating suggestion {index}: {str(e)}")
            return None
    
    @classmethod
    def _validate_evidence(cls, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Validate evidence structure."""
        validated = {}
        
        # Requirements
        requirements = evidence.get("requirements", [])
        if isinstance(requirements, list):
            validated["requirements"] = [
                req for req in requirements 
                if isinstance(req, str) and req.startswith("REQ-")
            ]
        else:
            validated["requirements"] = []
        
        # Diagrams
        diagrams = evidence.get("diagrams", [])
        if isinstance(diagrams, list):
            validated_diagrams = []
            for diagram in diagrams:
                if isinstance(diagram, dict):
                    diagram_id = diagram.get("diagram_id", "")
                    if isinstance(diagram_id, str) and (diagram_id.startswith("SEQ-") or diagram_id.startswith("C4-")):
                        steps = diagram.get("steps", [])
                        if isinstance(steps, list):
                            validated_diagrams.append({
                                "diagram_id": diagram_id,
                                "steps": [int(step) for step in steps if isinstance(step, (int, str)) and str(step).isdigit()]
                            })
            validated["diagrams"] = validated_diagrams
        else:
            validated["diagrams"] = []
        
        # SO quotes
        so_quotes = evidence.get("so_quotes", [])
        if isinstance(so_quotes, list):
            validated["so_quotes"] = [
                quote for quote in so_quotes 
                if isinstance(quote, str) and quote.strip()
            ]
        else:
            validated["so_quotes"] = []
        
        return validated
    
    @classmethod
    def _validate_scores(cls, scores: Dict[str, Any]) -> Dict[str, float]:
        """Validate analysis scores."""
        required_scores = [
            "integration_consistency",
            "requirements_coverage", 
            "security_readiness",
            "operability"
        ]
        
        validated = {}
        for score_name in required_scores:
            score_value = scores.get(score_name, 0.5)
            if not isinstance(score_value, (int, float)) or score_value < 0 or score_value > 1:
                score_value = 0.5
            validated[score_name] = float(score_value)
        
        return validated


class JSONResponseParser:
    """Parser for JSON responses with error handling."""
    
    @classmethod
    def parse_json_response(cls, response: str, expected_schema: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
        """Parse JSON response with validation and error handling."""
        try:
            # Clean the response
            cleaned_response = cls._clean_json_response(response)
            
            # Parse JSON
            parsed = json.loads(cleaned_response)
            
            # Validate against schema if provided
            if expected_schema:
                try:
                    validated = expected_schema(**parsed)
                    return validated.dict()
                except ValidationError as e:
                    logger.warning(f"Schema validation failed: {str(e)}")
                    # Continue with basic validation
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response content: {response[:500]}...")
            raise ValueError(f"Invalid JSON response: {str(e)}")
    
    @classmethod
    def _clean_json_response(cls, response: str) -> str:
        """Clean JSON response by removing common formatting issues."""
        # Remove leading/trailing whitespace
        cleaned = response.strip()
        
        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        # Remove any text before the first {
        first_brace = cleaned.find("{")
        if first_brace > 0:
            cleaned = cleaned[first_brace:]
        
        # Remove any text after the last }
        last_brace = cleaned.rfind("}")
        if last_brace > 0:
            cleaned = cleaned[:last_brace + 1]
        
        return cleaned.strip()


class RetryHandler:
    """Handler for retry logic with validation."""
    
    @classmethod
    async def retry_with_validation(
        cls,
        func,
        validator_func,
        max_retries: int = 1,
        *args,
        **kwargs
    ) -> Any:
        """Retry function execution with validation."""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Execute function
                result = await func(*args, **kwargs) if hasattr(func, '__call__') else func
                
                # Validate result
                validated_result = validator_func(result)
                
                # Return if validation passes
                return validated_result
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_retries:
                    break
        
        # All retries failed
        logger.error(f"All retry attempts failed. Last error: {str(last_error)}")
        raise last_error or Exception("Retry attempts exhausted")


# Validation utility functions
def validate_router_output(output: Any) -> Dict[str, Any]:
    """Validate router output with fallback."""
    if isinstance(output, str):
        try:
            output = JSONResponseParser.parse_json_response(output)
        except Exception:
            # Fallback to default
            return {
                "intent": "qna",
                "targets": {"so_ids": [], "requirement_ids": [], "diagram_ids": []},
                "confidence": 0.1,
                "reason": "Failed to parse router response"
            }
    
    if not isinstance(output, dict):
        return {
            "intent": "qna", 
            "targets": {"so_ids": [], "requirement_ids": [], "diagram_ids": []},
            "confidence": 0.1,
            "reason": "Invalid router output format"
        }
    
    return RouterOutputValidator.validate_router_output(output)


def validate_structured_response(response: Any) -> Dict[str, Any]:
    """Validate structured analysis response with fallback."""
    if isinstance(response, str):
        try:
            response = JSONResponseParser.parse_json_response(response)
        except Exception:
            return {"suggestions": [], "scores": {}, "status": "insufficient"}
    
    if not isinstance(response, dict):
        return {"suggestions": [], "scores": {}, "status": "insufficient"}
    
    return StructuredResponseValidator.validate_structured_response(response)