from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.domain.models.diagrams import Diagram
from app.services.solution_outlines import solution_outline_service
from app.services.requirement_item_service import requirement_item_service
from app.repositories.project_repository import project_repository
from app.domain.models.solution_outlines import SolutionOutline, SolutionOutlineStatus
from app.api.schemas.solution_outlines import (
    SolutionOutlineCreate,
    SolutionOutlineUpdate,
    SolutionOutlineResponse,
    SolutionOutlineVersionInfo,
)
from app.core.exceptions import (
    NotFoundException,
    ConflictException,
    BadRequestException,
)
from app.api.schemas.requirements import RequirementItemStatus
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter
import logging
import json


logger = logging.getLogger(__name__)


class SORAGService:
    def __init__(
        self,
        db: Session,
        so_service,                 # SolutionOutlineService
        requirement_item_service,   # RequirementItemService
        diagram_service,            # DiagramService
        project_repository,         # ProjectRepository (αν το χρειάζεσαι)
    ):
        self.db = db
        self.so_service = so_service
        self.requirement_item_service = requirement_item_service
        self.project_repository = project_repository
        self.diagram_service = diagram_service

    def get_system_prompt(self):
        return """
        You are an AI assistant helping with solution outline development. 
        """

    async def prepare_rephrase_prompt(
        self, project_id: str, user_query: str, session_history: str
    ) -> str:
        """Rephrase the user query as a standalone request to improve a Solution Outline.
        
        Args:
            project_id: The ID of the project
            user_query: The user's original query/message
            session_history: Summary of the chat session history
            
        Returns:
            Dictionary containing the rephrased prompt or indication of insufficient information
        """
        try:
            # Get the latest solution outline
            so_doc = self.so_service.get_latest_solution_outline(project_id)
            if not so_doc:
                logger.warning(f"No solution outline found for project {project_id}")
                return {"rephrased": "INSUFFICIENT"}
            
            # Get accepted requirements
            requirements = self.requirement_item_service.get_requirement_items_by_status(
                self.db, project_id, [RequirementItemStatus.accepted]
            )
            
            diagrams = self.diagram_service.list_diagrams(project_id)

            # Extract relevant information from solution outline
            so_doc_md_subset = self._extract_so_content_subset(so_doc)
            requirements_bullets = self._format_requirements_bullets(requirements)
            mermaid_diagrams = self._extract_mermaid_diagrams(diagrams)
            
            # Format the prompt
            prompt = self.rephrase_prompt.format(
                so_doc_md_subset=so_doc_md_subset,
                requirements_bullets=requirements_bullets,
                mermaid_diagrams=mermaid_diagrams,
                chat_summary=session_history,
                user_message=user_query
            )
            
            # In a real implementation, you would send this to an LLM API
            # For now, we'll return a placeholder response
            # llm_response = await self._call_llm_api(prompt)
            # return json.loads(llm_response)
            
            # Placeholder implementation - you should replace this with actual LLM call
            return prompt
            # {
            #     "rephrased": f"Improve the solution outline based on: {user_query}"
            # }
            
        except Exception as e:
            logger.error(f"Error rephrasing prompt for project {project_id}: {e}")
            return {"rephrased": "INSUFFICIENT"}

    def _extract_so_content_subset(self, solution_outline: SolutionOutline) -> str:
        """Extract a relevant subset of the solution outline content."""
        # Extract first few sections or key content
        content = solution_outline.content or ""
        # Limit to first 1000 characters for context
        return content[:1000] + "..." if len(content) > 1000 else content

    def _format_requirements_bullets(self, requirements: List[Any]) -> str:
        """Format requirements as bullet points."""
        if not requirements:
            return "No accepted requirements available."
        
        bullets = []
        for req in requirements:
            bullets.append(f"- {req.title or req.description[:800]}...")
        
        return "\n".join(bullets[:10])  # Limit to top 10 requirements

    def _extract_mermaid_diagrams(self, diagrams: Diagram) -> str:
        """Extract mermaid diagrams from solution outline content."""
        list_of_diagrams = []
        for diagram in diagrams:
            list_of_diagrams.append(f'{diagram.title}\n{diagram.mermaid_code}')
        return '\n'.join(list_of_diagrams)


    # The prompt template as a class attribute
    rephrase_prompt = """
Rephrase the latest user message as a standalone request to improve a Solution Outline.

CONTEXT:
SO_DOC_MD:
{so_doc_md_subset}

REQUIREMENTS_BULLETS:
{requirements_bullets}

MERMAID_DIAGRAMS:
{mermaid_diagrams}

CHAT_SUMMARY:
{chat_summary}

QUERY:
{user_message}

Rules:
- Use ONLY the provided context; no outside knowledge.
- Preserve intent, domain terms, and proper names; match QUERY language.
- Respect STYLE_PROFILE (tone/voice/terminology).
- Output only the rephrased text (no preface, no quotes, no JSON).
- If insufficient information, output exactly: INSUFFICIENT.
"""

# STYLE_PROFILE:
# {style_profile_json}
