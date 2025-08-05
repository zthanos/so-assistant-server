"""RequirementSuggestionService for AI-powered requirement suggestions."""

import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.services.llm.streaming import LLMStreamingService
from app.repositories.requirement_document_repository import RequirementDocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.api.schemas.requirements import RequirementSuggestion, RequirementItemPriority
from app.core.events import SSEManager
from app.core.exceptions import NotFoundException, BadRequestException, LLMException
from app.config.config import REQUIREMENTS_LLM_MODEL

logger = logging.getLogger(__name__)


class RequirementSuggestionService:
    """Service for AI-powered requirement suggestions."""
    
    def __init__(
        self,
        llm_streaming_service: LLMStreamingService,
        requirement_document_repository: RequirementDocumentRepository,
        project_repository: ProjectRepository,
        sse_manager: SSEManager
    ):
        """Initialize the service with dependencies.
        
        Args:
            llm_streaming_service: The LLM streaming service.
            requirement_document_repository: Repository for requirement documents.
            project_repository: Repository for projects.
            sse_manager: SSE manager for streaming responses.
        """
        self.llm_streaming_service = llm_streaming_service
        self.requirement_document_repository = requirement_document_repository
        self.project_repository = project_repository
        self.sse_manager = sse_manager
    
    async def stream_requirement_suggestions(
        self,
        db: Session,
        client_id: str,
        project_id: str,
        max_suggestions: int = 10
    ) -> None:
        """Stream requirement suggestions using SSE with REQUIREMENTS_LLM_MODEL.
        
        Args:
            db: Database session.
            client_id: The SSE client ID.
            project_id: The project ID to generate suggestions for.
            max_suggestions: Maximum number of suggestions to generate.
            
        Raises:
            NotFoundException: If project or requirements document not found.
            BadRequestException: If parameters are invalid.
            LLMException: If LLM processing fails.
        """
        try:
            # Validate parameters
            if max_suggestions < 1 or max_suggestions > 50:
                raise BadRequestException("max_suggestions must be between 1 and 50")
            
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Get the latest requirements document
            requirements_doc = self.requirement_document_repository.get_latest_version(db, project_id)
            if not requirements_doc:
                raise NotFoundException(
                    f"No requirements document found for project {project_id}",
                    resource_type="RequirementDocument",
                    resource_id=project_id
                )
            
            # Send initial event
            await self.sse_manager.send_event(
                client_id,
                "suggestion.start",
                {
                    "message": "Starting requirement suggestions generation",
                    "project_id": project_id,
                    "max_suggestions": max_suggestions
                }
            )
            
            # Build the LLM prompt
            prompt = self._build_suggestion_prompt(requirements_doc.content, max_suggestions)
            
            # Configure LLM options to use REQUIREMENTS_LLM_MODEL
            llm_options = {
                "model": REQUIREMENTS_LLM_MODEL,
                "temperature": 0.7,  # Some creativity for suggestions
                "max_tokens": 4000,  # Enough for multiple suggestions
            }
            
            # Stream the LLM response and parse suggestions
            full_response = ""
            async for event_type, data in self.llm_streaming_service.create_streaming_response(
                prompt=prompt,
                prompt_key="requirement_suggestions",
                system_prompt=self._get_system_prompt(),
                options=llm_options
            ):
                if event_type == "llm.chunk":
                    chunk_content = data.get("content", "")
                    full_response += chunk_content
                    
                    # Try to parse partial suggestions as they come in
                    suggestions = self._try_parse_partial_suggestions(full_response)
                    if suggestions:
                        for suggestion in suggestions:
                            await self.sse_manager.send_event(
                                client_id,
                                "suggestion.item",
                                {
                                    "suggestion": suggestion.dict(),
                                    "project_id": project_id
                                }
                            )
                
                elif event_type == "llm.complete":
                    # Final parsing of complete response
                    final_suggestions = self._parse_suggestion_response(full_response)
                    
                    # Send any remaining suggestions that weren't sent during streaming
                    for suggestion in final_suggestions:
                        await self.sse_manager.send_event(
                            client_id,
                            "suggestion.item",
                            {
                                "suggestion": suggestion.dict(),
                                "project_id": project_id
                            }
                        )
                    
                    # Send completion event
                    await self.sse_manager.send_event(
                        client_id,
                        "suggestion.complete",
                        {
                            "message": "Requirement suggestions generation complete",
                            "project_id": project_id,
                            "total_suggestions": len(final_suggestions)
                        }
                    )
                
                elif event_type == "llm.error":
                    # Send error event
                    await self.sse_manager.send_event(
                        client_id,
                        "suggestion.error",
                        {
                            "message": data.get("message", "Error generating suggestions"),
                            "project_id": project_id,
                            "error_type": data.get("error_type", "llm_error")
                        }
                    )
                    raise LLMException(f"LLM error: {data.get('message')}")
            
        except (NotFoundException, BadRequestException, LLMException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating suggestions for project {project_id}: {str(e)}")
            # Send error event
            try:
                await self.sse_manager.send_event(
                    client_id,
                    "suggestion.error",
                    {
                        "message": "An unexpected error occurred while generating suggestions",
                        "project_id": project_id,
                        "error_type": "unexpected_error"
                    }
                )
            except Exception:
                pass
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for requirement suggestions.
        
        Returns:
            The system prompt string.
        """
        return """You are an expert business analyst and requirements engineer specializing in software requirements analysis. Your task is to analyze existing requirements documents and suggest additional individual requirement items that might be missing or would complement the existing requirements.

Focus on:
1. Functional requirements that might be implied but not explicitly stated
2. Non-functional requirements (performance, security, usability, reliability)
3. Edge cases and error handling scenarios
4. Integration and compatibility requirements
5. Compliance and regulatory requirements
6. User experience and accessibility requirements

Provide practical, actionable suggestions that would be valuable for the development team."""
    
    def _build_suggestion_prompt(self, requirements_content: str, max_suggestions: int) -> str:
        """Build the LLM prompt for requirement suggestions.
        
        Args:
            requirements_content: The content of the requirements document.
            max_suggestions: Maximum number of suggestions to generate.
            
        Returns:
            The formatted prompt string.
        """
        return f"""Based on the following requirements document, suggest up to {max_suggestions} additional individual requirement items that might be missing or would complement the existing requirements.

Requirements Document:
{requirements_content}

Please suggest up to {max_suggestions} requirement items in the following JSON format:
[
  {{
    "title": "Brief descriptive title (max 100 characters)",
    "description": "Detailed description of the requirement (2-3 sentences)",
    "priority": "low|medium|high|critical",
    "rationale": "Explanation of why this requirement is suggested and how it relates to the existing requirements"
  }}
]

Guidelines:
- Each suggestion should be a specific, actionable requirement
- Prioritize suggestions that address gaps in the current requirements
- Consider non-functional requirements like security, performance, and usability
- Think about edge cases and error handling scenarios
- Consider integration points and external dependencies
- Ensure each suggestion is distinct and valuable

Respond with valid JSON only, no additional text or formatting."""
    
    def _try_parse_partial_suggestions(self, partial_response: str) -> List[RequirementSuggestion]:
        """Try to parse partial suggestions from incomplete response.
        
        This method attempts to extract complete suggestion objects from a partial
        JSON response that may be incomplete.
        
        Args:
            partial_response: The partial response string.
            
        Returns:
            List of parsed suggestions (may be empty if no complete suggestions found).
        """
        try:
            # Try to find complete JSON objects in the partial response
            # Look for patterns like {"title": "...", "description": "...", "priority": "...", "rationale": "..."}
            suggestions = []
            
            # Simple approach: try to parse as JSON, return empty list if it fails
            # In a more sophisticated implementation, we could use regex to extract
            # complete objects from partial JSON
            
            if partial_response.strip().startswith('[') and partial_response.strip().endswith(']'):
                parsed = json.loads(partial_response.strip())
                if isinstance(parsed, list):
                    for item in parsed:
                        if self._is_complete_suggestion(item):
                            suggestion = self._create_suggestion_from_dict(item)
                            if suggestion:
                                suggestions.append(suggestion)
            
            return suggestions
            
        except (json.JSONDecodeError, KeyError, ValueError):
            # Partial response is not yet parseable
            return []
    
    def _parse_suggestion_response(self, response: str) -> List[RequirementSuggestion]:
        """Parse LLM response into structured suggestions.
        
        Args:
            response: The complete LLM response string.
            
        Returns:
            List of parsed requirement suggestions.
        """
        try:
            # Clean the response - remove any markdown formatting or extra text
            cleaned_response = response.strip()
            
            # Find JSON content (look for array brackets)
            start_idx = cleaned_response.find('[')
            end_idx = cleaned_response.rfind(']')
            
            if start_idx == -1 or end_idx == -1:
                logger.warning("No JSON array found in LLM response")
                return []
            
            json_content = cleaned_response[start_idx:end_idx + 1]
            
            # Parse JSON
            parsed_data = json.loads(json_content)
            
            if not isinstance(parsed_data, list):
                logger.warning("LLM response is not a JSON array")
                return []
            
            suggestions = []
            for item in parsed_data:
                suggestion = self._create_suggestion_from_dict(item)
                if suggestion:
                    suggestions.append(suggestion)
            
            return suggestions
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            return []
    
    def _is_complete_suggestion(self, item: Dict[str, Any]) -> bool:
        """Check if a dictionary contains all required fields for a suggestion.
        
        Args:
            item: Dictionary to check.
            
        Returns:
            True if all required fields are present.
        """
        required_fields = ["title", "description", "priority", "rationale"]
        return all(field in item and item[field] for field in required_fields)
    
    def _create_suggestion_from_dict(self, item: Dict[str, Any]) -> Optional[RequirementSuggestion]:
        """Create a RequirementSuggestion from a dictionary.
        
        Args:
            item: Dictionary containing suggestion data.
            
        Returns:
            RequirementSuggestion object or None if creation fails.
        """
        try:
            # Validate required fields
            if not self._is_complete_suggestion(item):
                logger.warning(f"Incomplete suggestion data: {item}")
                return None
            
            # Validate priority value
            priority_str = item["priority"].lower()
            if priority_str not in ["low", "medium", "high", "critical"]:
                logger.warning(f"Invalid priority '{priority_str}', defaulting to 'medium'")
                priority_str = "medium"
            
            # Create the suggestion
            return RequirementSuggestion(
                title=str(item["title"])[:500],  # Truncate if too long
                description=str(item["description"]),
                priority=RequirementItemPriority(priority_str),
                rationale=str(item["rationale"])
            )
            
        except Exception as e:
            logger.error(f"Error creating suggestion from dict {item}: {e}")
            return None
    
    async def generate_suggestions_batch(
        self,
        db: Session,
        project_id: str,
        max_suggestions: int = 10
    ) -> List[RequirementSuggestion]:
        """Generate requirement suggestions without streaming (for testing/batch processing).
        
        Args:
            db: Database session.
            project_id: The project ID to generate suggestions for.
            max_suggestions: Maximum number of suggestions to generate.
            
        Returns:
            List of requirement suggestions.
            
        Raises:
            NotFoundException: If project or requirements document not found.
            BadRequestException: If parameters are invalid.
            LLMException: If LLM processing fails.
        """
        try:
            # Validate parameters
            if max_suggestions < 1 or max_suggestions > 50:
                raise BadRequestException("max_suggestions must be between 1 and 50")
            
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Get the latest requirements document
            requirements_doc = self.requirement_document_repository.get_latest_version(db, project_id)
            if not requirements_doc:
                raise NotFoundException(
                    f"No requirements document found for project {project_id}",
                    resource_type="RequirementDocument",
                    resource_id=project_id
                )
            
            # Build the LLM prompt
            prompt = self._build_suggestion_prompt(requirements_doc.content, max_suggestions)
            
            # Configure LLM options to use REQUIREMENTS_LLM_MODEL
            llm_options = {
                "model": REQUIREMENTS_LLM_MODEL,
                "temperature": 0.7,
                "max_tokens": 4000,
            }
            
            # Get the complete response
            full_response = ""
            async for event_type, data in self.llm_streaming_service.create_streaming_response(
                prompt=prompt,
                prompt_key="requirement_suggestions_batch",
                system_prompt=self._get_system_prompt(),
                options=llm_options
            ):
                if event_type == "llm.chunk":
                    full_response += data.get("content", "")
                elif event_type == "llm.error":
                    raise LLMException(f"LLM error: {data.get('message')}")
            
            # Parse and return suggestions
            return self._parse_suggestion_response(full_response)
            
        except (NotFoundException, BadRequestException, LLMException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating batch suggestions for project {project_id}: {str(e)}")
            raise