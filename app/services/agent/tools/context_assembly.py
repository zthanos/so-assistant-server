"""Context assembly tools for retrieving and processing project documents."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.agent.tools.base import BaseAgentTool
from app.repositories.solution_outline_repository import solution_outline_repository
from app.repositories.requirement_item_repository import requirement_item_repository
from app.repositories.diagrams_repository import diagrams_repository
from app.core.database import get_db
from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class SOSectionParser:
    """Parser for Solution Outline sections."""
    
    # Standard SO section patterns based on the provided structure
    SECTION_PATTERNS = {
        "introduction": r"(?i)^#\s*introduction\s*$",
        "overview": r"(?i)^##\s*overview\s+and\s+context\s*$",
        "assumptions": r"(?i)^##\s*assumptions\s+and\s+conditions\s*$",
        "references": r"(?i)^##\s*list\s+of\s+references\s*$",
        "risks": r"(?i)^##\s*risks\s*$",
        "adrs": r"(?i)^##\s*adrs\s*$",
        "solution_architecture": r"(?i)^#\s*solution\s+architecture\s*$",
        "solution_overview": r"(?i)^##\s*solution\s+overview\s*$",
        "new_services": r"(?i)^##\s*new\s+or\s+changed\s+services\s*$",
        "data_architecture": r"(?i)^#\s*data\s+architecture.*$",
        "data_overview": r"(?i)^##\s*overview\s*$",
        "data_contracts": r"(?i)^##\s*data\s+contracts\s*$",
        "integration_architecture": r"(?i)^#\s*integration\s+architecture\s*$",
        "security_architecture": r"(?i)^#\s*security\s+architecture\s*$",
        "fault_handling": r"(?i)^#\s*fault-handling\s+architecture\s*$",
        "logging_architecture": r"(?i)^#\s*logging\s+architecture\s*$",
        "monitoring_architecture": r"(?i)^#\s*monitoring\s+architecture\s*$",
        "sustainability": r"(?i)^#\s*sustainability\s*$",
        "implementation_teams": r"(?i)^#\s*implementation\s+teams\s*$"
    }
    
    @classmethod
    def parse_sections(cls, content: str) -> Dict[str, Dict[str, Any]]:
        """Parse SO content into sections with metadata."""
        sections = {}
        lines = content.split('\n')
        current_section = None
        current_content = []
        section_counter = 1
        
        for i, line in enumerate(lines):
            # Check if this line is a section header
            section_match = cls._match_section_header(line)
            
            if section_match:
                # Save previous section if exists
                if current_section:
                    sections[current_section["id"]] = {
                        **current_section,
                        "content": '\n'.join(current_content).strip(),
                        "line_count": len(current_content)
                    }
                
                # Start new section
                section_id = f"SEC-{section_counter}"
                current_section = {
                    "id": section_id,
                    "title": line.strip(),
                    "type": section_match,
                    "level": cls._get_header_level(line),
                    "start_line": i + 1,
                    "parent_id": cls._find_parent_section(sections, cls._get_header_level(line))
                }
                current_content = []
                section_counter += 1
            else:
                # Add content to current section
                if current_section:
                    current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section["id"]] = {
                **current_section,
                "content": '\n'.join(current_content).strip(),
                "line_count": len(current_content)
            }
        
        return sections
    
    @classmethod
    def _match_section_header(cls, line: str) -> Optional[str]:
        """Match line against section patterns."""
        for section_type, pattern in cls.SECTION_PATTERNS.items():
            if re.match(pattern, line.strip()):
                return section_type
        
        # Generic header detection
        if re.match(r'^#{1,6}\s+.+$', line.strip()):
            return "generic"
        
        return None
    
    @classmethod
    def _get_header_level(cls, line: str) -> int:
        """Get header level from markdown header."""
        match = re.match(r'^(#{1,6})\s+', line.strip())
        return len(match.group(1)) if match else 0
    
    @classmethod
    def _find_parent_section(cls, sections: Dict[str, Dict[str, Any]], level: int) -> Optional[str]:
        """Find parent section based on header level."""
        if level <= 1:
            return None
        
        # Find the most recent section with a lower level
        for section_id in reversed(list(sections.keys())):
            section = sections[section_id]
            if section["level"] < level:
                return section_id
        
        return None
    
    @classmethod
    def get_section_by_id(cls, sections: Dict[str, Dict[str, Any]], section_id: str) -> Optional[Dict[str, Any]]:
        """Get section by ID."""
        return sections.get(section_id)
    
    @classmethod
    def get_neighboring_sections(cls, sections: Dict[str, Dict[str, Any]], section_id: str, 
                               before: int = 1, after: int = 1) -> List[Dict[str, Any]]:
        """Get neighboring sections around a target section."""
        section_ids = list(sections.keys())
        
        try:
            target_index = section_ids.index(section_id)
        except ValueError:
            return []
        
        start_index = max(0, target_index - before)
        end_index = min(len(section_ids), target_index + after + 1)
        
        neighboring_sections = []
        for i in range(start_index, end_index):
            neighboring_sections.append(sections[section_ids[i]])
        
        return neighboring_sections


class SOSectionRetrievalTool(BaseAgentTool):
    """Tool for retrieving Solution Outline sections by ID."""
    
    name = "retrieve_so_sections"
    description = "Retrieve Solution Outline sections by SEC-* ID with optional neighboring context"
    tool_category = "context"
    requires_project_id = True
    
    async def _execute(self, project_id: str, section_ids: List[str], 
                      include_neighbors: bool = False, **kwargs) -> Dict[str, Any]:
        """Execute SO section retrieval."""
        try:
            # Get database session
            db = next(get_db())
            
            # Get latest solution outline for the project
            solution_outline = solution_outline_repository.get_latest_version(db, project_id=project_id)
            
            if not solution_outline:
                return {
                    "sections": [],
                    "error": f"No solution outline found for project {project_id}",
                    "project_id": project_id
                }
            
            # Parse sections from content
            parsed_sections = SOSectionParser.parse_sections(solution_outline.content)
            
            # Retrieve requested sections
            retrieved_sections = []
            
            for section_id in section_ids:
                section = SOSectionParser.get_section_by_id(parsed_sections, section_id)
                
                if section:
                    section_data = {
                        "id": section["id"],
                        "title": section["title"],
                        "content": section["content"],
                        "type": section["type"],
                        "level": section["level"],
                        "parent_id": section.get("parent_id"),
                        "line_count": section["line_count"]
                    }
                    
                    # Add neighboring sections if requested
                    if include_neighbors:
                        neighbors = SOSectionParser.get_neighboring_sections(
                            parsed_sections, section_id, before=1, after=1
                        )
                        section_data["neighbors"] = [
                            {
                                "id": neighbor["id"],
                                "title": neighbor["title"],
                                "content": neighbor["content"][:200] + "..." if len(neighbor["content"]) > 200 else neighbor["content"]
                            }
                            for neighbor in neighbors if neighbor["id"] != section_id
                        ]
                    
                    retrieved_sections.append(section_data)
                else:
                    logger.warning(f"Section {section_id} not found in project {project_id}")
            
            # Apply context limits
            max_sections = agent_config.max_so_chunks
            if len(retrieved_sections) > max_sections:
                logger.info(f"Limiting SO sections from {len(retrieved_sections)} to {max_sections}")
                retrieved_sections = retrieved_sections[:max_sections]
            
            return {
                "sections": retrieved_sections,
                "total_sections_available": len(parsed_sections),
                "solution_outline_version": solution_outline.version,
                "project_id": project_id,
                "retrieved_count": len(retrieved_sections)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving SO sections: {str(e)}")
            return {
                "sections": [],
                "error": str(e),
                "project_id": project_id
            }


class RequirementRetrievalTool(BaseAgentTool):
    """Tool for retrieving requirements by ID or semantic search."""
    
    name = "retrieve_requirements"
    description = "Retrieve requirements by REQ-* ID or semantic search with metadata"
    tool_category = "context"
    requires_project_id = True
    
    async def _execute(self, project_id: str, requirement_ids: Optional[List[str]] = None,
                      query: Optional[str] = None, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        """Execute requirement retrieval."""
        try:
            # Get database session
            db = next(get_db())
            
            retrieved_requirements = []
            
            if requirement_ids:
                # Retrieve specific requirements by ID
                for req_id in requirement_ids:
                    # Extract numeric ID from REQ-* format
                    numeric_id = self._extract_numeric_id(req_id)
                    if numeric_id:
                        requirement = requirement_item_repository.get_by_id(db, id=numeric_id)
                        if requirement and requirement.project_id == project_id:
                            retrieved_requirements.append(self._format_requirement(requirement))
                        else:
                            logger.warning(f"Requirement {req_id} not found in project {project_id}")
            
            elif query:
                # Semantic search (simplified - could be enhanced with vector search)
                requirements = requirement_item_repository.search_by_content(
                    db, project_id=project_id, query=query, limit=max_results
                )
                retrieved_requirements = [self._format_requirement(req) for req in requirements]
            
            else:
                # Get all requirements for the project (limited)
                requirements = requirement_item_repository.get_by_project(
                    db, project_id=project_id, limit=max_results
                )
                retrieved_requirements = [self._format_requirement(req) for req in requirements]
            
            # Apply context limits
            max_requirements = agent_config.max_requirements
            if len(retrieved_requirements) > max_requirements:
                logger.info(f"Limiting requirements from {len(retrieved_requirements)} to {max_requirements}")
                retrieved_requirements = retrieved_requirements[:max_requirements]
            
            return {
                "requirements": retrieved_requirements,
                "project_id": project_id,
                "retrieved_count": len(retrieved_requirements),
                "search_query": query
            }
            
        except Exception as e:
            logger.error(f"Error retrieving requirements: {str(e)}")
            return {
                "requirements": [],
                "error": str(e),
                "project_id": project_id
            }
    
    def _extract_numeric_id(self, req_id: str) -> Optional[int]:
        """Extract numeric ID from REQ-* format."""
        match = re.match(r'REQ-(\d+)', req_id)
        return int(match.group(1)) if match else None
    
    def _format_requirement(self, requirement) -> Dict[str, Any]:
        """Format requirement for context."""
        return {
            "id": f"REQ-{requirement.id}",
            "title": getattr(requirement, 'title', ''),
            "description": getattr(requirement, 'description', ''),
            "priority": getattr(requirement, 'priority', 'medium'),
            "status": getattr(requirement, 'status', 'active'),
            "created_at": requirement.created_at.isoformat() if hasattr(requirement, 'created_at') else None
        }


class ChatSummaryTool(BaseAgentTool):
    """Tool for retrieving recent chat interaction summary."""
    
    name = "get_chat_summary"
    description = "Get recent chat interaction summary for context"
    tool_category = "context"
    requires_project_id = True
    
    async def _execute(self, project_id: str, last_n_messages: int = 10, **kwargs) -> str:
        """Execute chat summary retrieval."""
        try:
            # TODO: Implement actual chat history retrieval
            # For now, return a placeholder
            return f"Chat summary for project {project_id}: Recent interactions focused on solution architecture review and requirements analysis. Last {last_n_messages} messages covered integration patterns and security considerations."
            
        except Exception as e:
            logger.error(f"Error retrieving chat summary: {str(e)}")
            return f"Error retrieving chat summary: {str(e)}"


# Register the tools
from app.services.agent.tools.base import tool_registry

so_section_tool = SOSectionRetrievalTool()
requirement_tool = RequirementRetrievalTool()
chat_summary_tool = ChatSummaryTool()

tool_registry.register_tool(so_section_tool)
tool_registry.register_tool(requirement_tool)
tool_registry.register_tool(chat_summary_tool)