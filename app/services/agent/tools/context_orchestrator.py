"""Context assembly orchestration for coordinating multiple retrieval tools."""
import asyncio
import logging
from typing import Any, Dict, List, Optional
import time

from app.services.agent.tools.base import BaseAgentTool, execute_tools_in_parallel
from app.services.agent.tools.context_assembly import (
    SOSectionRetrievalTool, RequirementRetrievalTool, ChatSummaryTool
)
from app.services.agent.tools.diagram_parser import DiagramRetrievalTool
from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class ContextAssemblyOrchestrator(BaseAgentTool):
    """Orchestrator for assembling complete context from multiple sources."""
    
    name = "assemble_context"
    description = "Orchestrate context assembly from SO sections, requirements, diagrams, and chat history"
    tool_category = "context"
    requires_project_id = True
    
    def __init__(self):
        """Initialize the orchestrator with component tools."""
        super().__init__()
        self.so_tool = SOSectionRetrievalTool()
        self.requirement_tool = RequirementRetrievalTool()
        self.diagram_tool = DiagramRetrievalTool()
        self.chat_tool = ChatSummaryTool()
    
    async def _execute(self, project_id: str, targets: Dict[str, List[str]], 
                      intent: str = "qna", include_chat: bool = True, **kwargs) -> Dict[str, Any]:
        """Execute context assembly orchestration."""
        start_time = time.time()
        
        try:
            # Prepare context assembly tasks
            assembly_tasks = []
            
            # SO sections
            so_ids = targets.get("so_ids", [])
            if so_ids:
                assembly_tasks.append(
                    self._assemble_so_context(project_id, so_ids, intent)
                )
            
            # Requirements
            requirement_ids = targets.get("requirement_ids", [])
            if requirement_ids:
                assembly_tasks.append(
                    self._assemble_requirements_context(project_id, requirement_ids)
                )
            
            # Diagrams
            diagram_ids = targets.get("diagram_ids", [])
            if diagram_ids:
                assembly_tasks.append(
                    self._assemble_diagrams_context(project_id, diagram_ids)
                )
            
            # Chat summary
            if include_chat:
                assembly_tasks.append(
                    self._assemble_chat_context(project_id)
                )
            
            # Execute all assembly tasks in parallel if enabled
            if agent_config.parallel_processing and len(assembly_tasks) > 1:
                results = await asyncio.gather(*assembly_tasks, return_exceptions=True)
            else:
                results = []
                for task in assembly_tasks:
                    try:
                        result = await task
                        results.append(result)
                    except Exception as e:
                        results.append(e)
            
            # Process results and handle exceptions
            assembled_context = {
                "so_sections": [],
                "requirements": [],
                "diagrams": [],
                "chat_summary": "",
                "metadata": {
                    "project_id": project_id,
                    "intent": intent,
                    "targets": targets,
                    "assembly_time_ms": int((time.time() - start_time) * 1000)
                }
            }
            
            # Merge results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Context assembly task {i} failed: {str(result)}")
                    continue
                
                if isinstance(result, dict):
                    if "sections" in result:
                        assembled_context["so_sections"].extend(result["sections"])
                    elif "requirements" in result:
                        assembled_context["requirements"].extend(result["requirements"])
                    elif "diagrams" in result:
                        assembled_context["diagrams"].extend(result["diagrams"])
                    elif "chat_summary" in result:
                        assembled_context["chat_summary"] = result["chat_summary"]
            
            # Apply context packing and prioritization
            packed_context = self._pack_context(assembled_context, intent)
            
            # Add context statistics
            packed_context["metadata"]["statistics"] = self._calculate_context_stats(packed_context)
            
            return packed_context
            
        except Exception as e:
            logger.error(f"Error in context assembly orchestration: {str(e)}")
            return {
                "so_sections": [],
                "requirements": [],
                "diagrams": [],
                "chat_summary": "",
                "error": str(e),
                "metadata": {
                    "project_id": project_id,
                    "intent": intent,
                    "assembly_time_ms": int((time.time() - start_time) * 1000)
                }
            }
    
    async def _assemble_so_context(self, project_id: str, so_ids: List[str], intent: str) -> Dict[str, Any]:
        """Assemble SO section context."""
        include_neighbors = intent in ["improve_paragraph", "integration_check"]
        
        return await self.so_tool._execute(
            project_id=project_id,
            section_ids=so_ids,
            include_neighbors=include_neighbors
        )
    
    async def _assemble_requirements_context(self, project_id: str, requirement_ids: List[str]) -> Dict[str, Any]:
        """Assemble requirements context."""
        return await self.requirement_tool._execute(
            project_id=project_id,
            requirement_ids=requirement_ids
        )
    
    async def _assemble_diagrams_context(self, project_id: str, diagram_ids: List[str]) -> Dict[str, Any]:
        """Assemble diagrams context."""
        return await self.diagram_tool._execute(
            project_id=project_id,
            diagram_ids=diagram_ids
        )
    
    async def _assemble_chat_context(self, project_id: str) -> Dict[str, str]:
        """Assemble chat context."""
        chat_summary = await self.chat_tool._execute(project_id=project_id)
        return {"chat_summary": chat_summary}
    
    def _pack_context(self, context: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """Pack context according to limits and prioritization."""
        packed = context.copy()
        
        # Apply SO section limits
        if len(packed["so_sections"]) > agent_config.max_so_chunks:
            # Prioritize based on intent
            packed["so_sections"] = self._prioritize_so_sections(
                packed["so_sections"], intent, agent_config.max_so_chunks
            )
        
        # Apply diagram limits
        if len(packed["diagrams"]) > agent_config.max_diagrams:
            packed["diagrams"] = packed["diagrams"][:agent_config.max_diagrams]
        
        # Apply requirement limits
        if len(packed["requirements"]) > agent_config.max_requirements:
            packed["requirements"] = packed["requirements"][:agent_config.max_requirements]
        
        # Estimate token count and truncate if necessary
        estimated_tokens = self._estimate_context_tokens(packed)
        if estimated_tokens > agent_config.max_context_tokens:
            packed = self._truncate_context(packed, agent_config.max_context_tokens)
        
        return packed
    
    def _prioritize_so_sections(self, sections: List[Dict[str, Any]], intent: str, max_count: int) -> List[Dict[str, Any]]:
        """Prioritize SO sections based on intent."""
        if intent == "integration_check":
            # Prioritize architecture sections
            priority_types = ["solution_architecture", "integration_architecture", "solution_overview"]
        elif intent == "requirements_coverage":
            # Prioritize sections that typically contain requirements mappings
            priority_types = ["solution_overview", "new_services", "data_architecture"]
        elif intent == "improve_paragraph":
            # Keep original order for targeted improvement
            return sections[:max_count]
        else:
            # Default prioritization
            priority_types = ["solution_architecture", "solution_overview"]
        
        # Sort sections by priority
        def section_priority(section):
            section_type = section.get("type", "generic")
            if section_type in priority_types:
                return priority_types.index(section_type)
            return len(priority_types)
        
        sorted_sections = sorted(sections, key=section_priority)
        return sorted_sections[:max_count]
    
    def _estimate_context_tokens(self, context: Dict[str, Any]) -> int:
        """Estimate token count for context (rough approximation)."""
        total_chars = 0
        
        # SO sections
        for section in context.get("so_sections", []):
            total_chars += len(section.get("content", ""))
            total_chars += len(section.get("title", ""))
        
        # Requirements
        for req in context.get("requirements", []):
            total_chars += len(req.get("description", ""))
            total_chars += len(req.get("title", ""))
        
        # Diagrams (content can be large)
        for diagram in context.get("diagrams", []):
            # Count parsed content more heavily than raw content
            parsed = diagram.get("parsed", {})
            total_chars += len(str(parsed)) * 2  # Parsed content is more token-dense
        
        # Chat summary
        total_chars += len(context.get("chat_summary", ""))
        
        # Rough approximation: 4 characters per token
        return total_chars // 4
    
    def _truncate_context(self, context: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Truncate context to fit within token limits."""
        target_chars = max_tokens * 4  # Rough approximation
        current_chars = self._estimate_context_tokens(context) * 4
        
        if current_chars <= target_chars:
            return context
        
        # Calculate reduction ratio
        reduction_ratio = target_chars / current_chars
        
        truncated = context.copy()
        
        # Truncate SO sections content
        for section in truncated.get("so_sections", []):
            content = section.get("content", "")
            if content:
                new_length = int(len(content) * reduction_ratio)
                section["content"] = content[:new_length] + "..." if new_length < len(content) else content
        
        # Truncate requirements descriptions
        for req in truncated.get("requirements", []):
            description = req.get("description", "")
            if description:
                new_length = int(len(description) * reduction_ratio)
                req["description"] = description[:new_length] + "..." if new_length < len(description) else description
        
        # Remove some diagrams if necessary (keep most important)
        if len(truncated.get("diagrams", [])) > 1:
            keep_count = max(1, int(len(truncated["diagrams"]) * reduction_ratio))
            truncated["diagrams"] = truncated["diagrams"][:keep_count]
        
        return truncated
    
    def _calculate_context_stats(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate context statistics."""
        return {
            "so_sections_count": len(context.get("so_sections", [])),
            "requirements_count": len(context.get("requirements", [])),
            "diagrams_count": len(context.get("diagrams", [])),
            "estimated_tokens": self._estimate_context_tokens(context),
            "has_chat_summary": bool(context.get("chat_summary", "").strip()),
            "total_content_length": sum([
                len(str(section.get("content", ""))) for section in context.get("so_sections", [])
            ]) + sum([
                len(str(req.get("description", ""))) for req in context.get("requirements", [])
            ]) + sum([
                len(str(diagram.get("content", ""))) for diagram in context.get("diagrams", [])
            ])
        }


class ContextFormatter:
    """Formatter for context data into prompt-ready strings."""
    
    @classmethod
    def format_context_for_prompt(cls, context: Dict[str, Any], intent: str, language: str = "en") -> Dict[str, str]:
        """Format assembled context for prompt templates."""
        formatted = {}
        
        # Format SO sections
        formatted["so_sections"] = cls._format_so_sections(
            context.get("so_sections", []), language
        )
        
        # Format requirements
        formatted["requirements"] = cls._format_requirements(
            context.get("requirements", []), language
        )
        
        # Format diagrams
        formatted["diagrams"] = cls._format_diagrams(
            context.get("diagrams", []), language
        )
        
        # Format chat summary
        formatted["chat_summary"] = context.get("chat_summary", "")
        
        return formatted
    
    @classmethod
    def _format_so_sections(cls, sections: List[Dict[str, Any]], language: str) -> str:
        """Format SO sections for prompt."""
        if not sections:
            return "No SO sections available." if language == "en" else "Δεν υπάρχουν διαθέσιμες ενότητες SO."
        
        formatted_sections = []
        for section in sections:
            section_text = f"## {section['id']}: {section['title']}\n{section['content']}"
            
            # Add neighbor context if available
            if section.get("neighbors"):
                neighbor_text = "\n### Related sections:\n"
                for neighbor in section["neighbors"]:
                    neighbor_text += f"- {neighbor['id']}: {neighbor['title']}\n"
                section_text += neighbor_text
            
            formatted_sections.append(section_text)
        
        return "\n\n".join(formatted_sections)
    
    @classmethod
    def _format_requirements(cls, requirements: List[Dict[str, Any]], language: str) -> str:
        """Format requirements for prompt."""
        if not requirements:
            return "No requirements available." if language == "en" else "Δεν υπάρχουν διαθέσιμες απαιτήσεις."
        
        formatted_reqs = []
        for req in requirements:
            req_text = f"**{req['id']}**: {req.get('title', 'Untitled')}\n"
            req_text += f"Description: {req.get('description', 'No description')}\n"
            req_text += f"Priority: {req.get('priority', 'Unknown')}, Status: {req.get('status', 'Unknown')}"
            formatted_reqs.append(req_text)
        
        return "\n\n".join(formatted_reqs)
    
    @classmethod
    def _format_diagrams(cls, diagrams: List[Dict[str, Any]], language: str) -> str:
        """Format diagrams for prompt."""
        if not diagrams:
            return "No diagrams available." if language == "en" else "Δεν υπάρχουν διαθέσιμα διαγράμματα."
        
        formatted_diagrams = []
        for diagram in diagrams:
            diagram_text = f"## {diagram['id']}: {diagram.get('title', 'Untitled Diagram')}\n"
            diagram_text += f"Type: {diagram.get('type', 'Unknown')}\n"
            
            parsed = diagram.get("parsed", {})
            if diagram["type"] == "sequence":
                diagram_text += cls._format_sequence_diagram(parsed)
            elif diagram["type"] == "c4":
                diagram_text += cls._format_c4_diagram(parsed)
            else:
                diagram_text += f"Raw content: {diagram.get('content', '')[:200]}..."
            
            formatted_diagrams.append(diagram_text)
        
        return "\n\n".join(formatted_diagrams)
    
    @classmethod
    def _format_sequence_diagram(cls, parsed: Dict[str, Any]) -> str:
        """Format parsed sequence diagram."""
        text = "### Participants:\n"
        for participant in parsed.get("participants", []):
            text += f"- {participant['id']}: {participant.get('label', participant['id'])}\n"
        
        text += "\n### Interactions:\n"
        for interaction in parsed.get("interactions", []):
            text += f"{interaction['step']}. {interaction['from']} -> {interaction['to']}: {interaction['message']}\n"
        
        return text
    
    @classmethod
    def _format_c4_diagram(cls, parsed: Dict[str, Any]) -> str:
        """Format parsed C4 diagram."""
        text = f"### Diagram Type: {parsed.get('diagram_type', 'Unknown')}\n"
        
        if parsed.get("systems"):
            text += "\n### Systems:\n"
            for system in parsed["systems"]:
                text += f"- {system['id']}: {system['name']} ({system.get('technology', 'N/A')})\n"
        
        if parsed.get("containers"):
            text += "\n### Containers:\n"
            for container in parsed["containers"]:
                text += f"- {container['id']}: {container['name']} ({container.get('technology', 'N/A')})\n"
        
        if parsed.get("relationships"):
            text += "\n### Relationships:\n"
            for rel in parsed["relationships"]:
                text += f"- {rel['from']} -> {rel['to']}: {rel['label']}\n"
        
        return text


# Register the orchestrator tool
from app.services.agent.tools.base import tool_registry

context_orchestrator = ContextAssemblyOrchestrator()
tool_registry.register_tool(context_orchestrator)