"""Diagram parsing tools for Mermaid sequence and C4 diagrams."""
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.services.agent.tools.base import BaseAgentTool
from app.repositories.diagrams_repository import diagrams_repository
from app.core.database import get_db
from app.services.agent.config import agent_config

logger = logging.getLogger(__name__)


class SequenceDiagramParser:
    """Parser for Mermaid sequence diagrams."""
    
    @classmethod
    def parse_sequence_diagram(cls, mermaid_content: str) -> Dict[str, Any]:
        """Parse Mermaid sequence diagram content."""
        try:
            lines = [line.strip() for line in mermaid_content.split('\n') if line.strip()]
            
            participants = []
            interactions = []
            steps = []
            step_counter = 1
            
            for line in lines:
                # Skip sequenceDiagram declaration
                if line.startswith('sequenceDiagram'):
                    continue
                
                # Parse participant declarations
                participant_match = re.match(r'participant\s+(\w+)(?:\s+as\s+(.+))?', line)
                if participant_match:
                    participant_id = participant_match.group(1)
                    participant_label = participant_match.group(2) or participant_id
                    participants.append({
                        "id": participant_id,
                        "label": participant_label
                    })
                    continue
                
                # Parse actor declarations
                actor_match = re.match(r'actor\s+(\w+)(?:\s+as\s+(.+))?', line)
                if actor_match:
                    actor_id = actor_match.group(1)
                    actor_label = actor_match.group(2) or actor_id
                    participants.append({
                        "id": actor_id,
                        "label": actor_label,
                        "type": "actor"
                    })
                    continue
                
                # Parse interactions (arrows)
                interaction_match = re.match(
                    r'(\w+)\s*([-=]*)([>x\-+)]*)([>x\-+]*)\s*(\w+)\s*:\s*(.+)', 
                    line
                )
                if interaction_match:
                    from_participant = interaction_match.group(1)
                    arrow_type = interaction_match.group(3) + interaction_match.group(4)
                    to_participant = interaction_match.group(5)
                    message = interaction_match.group(6)
                    
                    interaction = {
                        "step": step_counter,
                        "from": from_participant,
                        "to": to_participant,
                        "message": message,
                        "arrow_type": arrow_type,
                        "interaction_type": cls._classify_interaction_type(arrow_type)
                    }
                    
                    interactions.append(interaction)
                    steps.append({
                        "step_number": step_counter,
                        "description": f"{from_participant} -> {to_participant}: {message}",
                        "participants": [from_participant, to_participant]
                    })
                    step_counter += 1
                    continue
                
                # Parse notes
                note_match = re.match(r'Note\s+(right\s+of|left\s+of|over)\s+([^:]+):\s*(.+)', line)
                if note_match:
                    note_position = note_match.group(1)
                    note_participants = note_match.group(2).split(',')
                    note_text = note_match.group(3)
                    
                    steps.append({
                        "step_number": step_counter,
                        "description": f"Note {note_position} {', '.join(note_participants)}: {note_text}",
                        "type": "note",
                        "participants": [p.strip() for p in note_participants]
                    })
                    step_counter += 1
                    continue
                
                # Parse loops, alts, etc.
                control_match = re.match(r'(loop|alt|opt|par)\s+(.+)', line)
                if control_match:
                    control_type = control_match.group(1)
                    control_condition = control_match.group(2)
                    
                    steps.append({
                        "step_number": step_counter,
                        "description": f"{control_type.upper()}: {control_condition}",
                        "type": "control_start",
                        "control_type": control_type
                    })
                    step_counter += 1
                    continue
                
                # Parse end statements
                if line == 'end':
                    steps.append({
                        "step_number": step_counter,
                        "description": "END",
                        "type": "control_end"
                    })
                    step_counter += 1
                    continue
            
            # Auto-detect participants from interactions if not explicitly declared
            if not participants:
                participant_ids = set()
                for interaction in interactions:
                    participant_ids.add(interaction["from"])
                    participant_ids.add(interaction["to"])
                
                participants = [{"id": pid, "label": pid} for pid in participant_ids]
            
            return {
                "participants": participants,
                "interactions": interactions,
                "steps": steps,
                "total_steps": len(steps),
                "participant_count": len(participants)
            }
            
        except Exception as e:
            logger.error(f"Error parsing sequence diagram: {str(e)}")
            return {
                "participants": [],
                "interactions": [],
                "steps": [],
                "error": str(e)
            }
    
    @classmethod
    def _classify_interaction_type(cls, arrow_type: str) -> str:
        """Classify interaction type based on arrow."""
        if 'x' in arrow_type:
            return "termination"
        elif '--' in arrow_type:
            return "async_response"
        elif '->' in arrow_type:
            return "sync_call"
        elif ')' in arrow_type:
            return "async_call"
        else:
            return "unknown"


class C4DiagramParser:
    """Parser for C4 diagrams."""
    
    @classmethod
    def parse_c4_diagram(cls, mermaid_content: str) -> Dict[str, Any]:
        """Parse C4 diagram content."""
        try:
            lines = [line.strip() for line in mermaid_content.split('\n') if line.strip()]
            
            diagram_type = "Unknown"
            systems = []
            containers = []
            components = []
            relationships = []
            boundaries = []
            
            for line in lines:
                # Detect diagram type
                if line.startswith('C4'):
                    diagram_type = line.replace('C4', '').strip()
                    continue
                
                # Parse title
                title_match = re.match(r'title\s+(.+)', line)
                if title_match:
                    continue
                
                # Parse systems
                system_match = re.match(
                    r'System(?:_Ext)?\s*\(\s*([^,]+),\s*"([^"]+)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\s*\)',
                    line
                )
                if system_match:
                    system_id = system_match.group(1)
                    system_name = system_match.group(2)
                    system_tech = system_match.group(3) or ""
                    system_desc = system_match.group(4) or ""
                    
                    systems.append({
                        "id": system_id,
                        "name": system_name,
                        "technology": system_tech,
                        "description": system_desc,
                        "external": "_Ext" in line
                    })
                    continue
                
                # Parse containers
                container_match = re.match(
                    r'Container(?:_Ext|Db|Queue)?\s*\(\s*([^,]+),\s*"([^"]+)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\s*\)',
                    line
                )
                if container_match:
                    container_id = container_match.group(1)
                    container_name = container_match.group(2)
                    container_tech = container_match.group(3) or ""
                    container_desc = container_match.group(4) or ""
                    
                    container_type = "container"
                    if "Db" in line:
                        container_type = "database"
                    elif "Queue" in line:
                        container_type = "queue"
                    
                    containers.append({
                        "id": container_id,
                        "name": container_name,
                        "technology": container_tech,
                        "description": container_desc,
                        "type": container_type,
                        "external": "_Ext" in line
                    })
                    continue
                
                # Parse components
                component_match = re.match(
                    r'Component(?:_Ext|Db|Queue)?\s*\(\s*([^,]+),\s*"([^"]+)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\s*\)',
                    line
                )
                if component_match:
                    component_id = component_match.group(1)
                    component_name = component_match.group(2)
                    component_tech = component_match.group(3) or ""
                    component_desc = component_match.group(4) or ""
                    
                    components.append({
                        "id": component_id,
                        "name": component_name,
                        "technology": component_tech,
                        "description": component_desc,
                        "external": "_Ext" in line
                    })
                    continue
                
                # Parse relationships
                rel_match = re.match(
                    r'(?:Bi)?Rel(?:_[UDLR]|_Back)?\s*\(\s*([^,]+),\s*([^,]+),\s*"([^"]+)"(?:,\s*"([^"]*)")?(?:,\s*"([^"]*)")?\s*\)',
                    line
                )
                if rel_match:
                    from_id = rel_match.group(1)
                    to_id = rel_match.group(2)
                    label = rel_match.group(3)
                    technology = rel_match.group(4) or ""
                    description = rel_match.group(5) or ""
                    
                    relationships.append({
                        "from": from_id,
                        "to": to_id,
                        "label": label,
                        "technology": technology,
                        "description": description,
                        "bidirectional": line.startswith("BiRel")
                    })
                    continue
                
                # Parse boundaries
                boundary_match = re.match(
                    r'(?:Enterprise_|System_|Container_)?Boundary\s*\(\s*([^,]+),\s*"([^"]+)"(?:,\s*"([^"]*)")?\s*\)\s*\{',
                    line
                )
                if boundary_match:
                    boundary_id = boundary_match.group(1)
                    boundary_name = boundary_match.group(2)
                    boundary_type = boundary_match.group(3) or "generic"
                    
                    boundaries.append({
                        "id": boundary_id,
                        "name": boundary_name,
                        "type": boundary_type
                    })
                    continue
            
            return {
                "diagram_type": diagram_type,
                "systems": systems,
                "containers": containers,
                "components": components,
                "relationships": relationships,
                "boundaries": boundaries,
                "element_count": len(systems) + len(containers) + len(components),
                "relationship_count": len(relationships)
            }
            
        except Exception as e:
            logger.error(f"Error parsing C4 diagram: {str(e)}")
            return {
                "diagram_type": "Unknown",
                "systems": [],
                "containers": [],
                "components": [],
                "relationships": [],
                "boundaries": [],
                "error": str(e)
            }


class DiagramRetrievalTool(BaseAgentTool):
    """Tool for retrieving and parsing diagrams by ID."""
    
    name = "retrieve_diagrams"
    description = "Retrieve and parse diagrams by SEQ-*/C4-* ID with structural analysis"
    tool_category = "context"
    requires_project_id = True
    
    async def _execute(self, project_id: str, diagram_ids: List[str], **kwargs) -> Dict[str, Any]:
        """Execute diagram retrieval and parsing."""
        try:
            # Get database session
            db = next(get_db())
            
            retrieved_diagrams = []
            
            for diagram_id in diagram_ids:
                # Extract numeric ID from diagram format
                numeric_id = self._extract_numeric_id(diagram_id)
                if not numeric_id:
                    logger.warning(f"Invalid diagram ID format: {diagram_id}")
                    continue
                
                # Retrieve diagram from database
                diagram = diagrams_repository.get_by_id(db, id=numeric_id)
                
                if not diagram or diagram.project_id != project_id:
                    logger.warning(f"Diagram {diagram_id} not found in project {project_id}")
                    continue
                
                # Parse diagram based on type
                parsed_data = self._parse_diagram_content(diagram_id, diagram.content)
                
                diagram_data = {
                    "id": diagram_id,
                    "original_id": diagram.id,
                    "title": getattr(diagram, 'title', f"Diagram {diagram_id}"),
                    "type": self._get_diagram_type(diagram_id),
                    "content": diagram.content,
                    "parsed": parsed_data,
                    "created_at": diagram.created_at.isoformat() if hasattr(diagram, 'created_at') else None
                }
                
                retrieved_diagrams.append(diagram_data)
            
            # Apply context limits
            max_diagrams = agent_config.max_diagrams
            if len(retrieved_diagrams) > max_diagrams:
                logger.info(f"Limiting diagrams from {len(retrieved_diagrams)} to {max_diagrams}")
                retrieved_diagrams = retrieved_diagrams[:max_diagrams]
            
            return {
                "diagrams": retrieved_diagrams,
                "project_id": project_id,
                "retrieved_count": len(retrieved_diagrams)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving diagrams: {str(e)}")
            return {
                "diagrams": [],
                "error": str(e),
                "project_id": project_id
            }
    
    def _extract_numeric_id(self, diagram_id: str) -> Optional[int]:
        """Extract numeric ID from SEQ-*/C4-* format."""
        match = re.match(r'(?:SEQ|C4)-(\d+)', diagram_id)
        return int(match.group(1)) if match else None
    
    def _get_diagram_type(self, diagram_id: str) -> str:
        """Get diagram type from ID."""
        if diagram_id.startswith("SEQ-"):
            return "sequence"
        elif diagram_id.startswith("C4-"):
            return "c4"
        else:
            return "unknown"
    
    def _parse_diagram_content(self, diagram_id: str, content: str) -> Dict[str, Any]:
        """Parse diagram content based on type."""
        diagram_type = self._get_diagram_type(diagram_id)
        
        if diagram_type == "sequence":
            return SequenceDiagramParser.parse_sequence_diagram(content)
        elif diagram_type == "c4":
            return C4DiagramParser.parse_c4_diagram(content)
        else:
            return {
                "error": f"Unknown diagram type for {diagram_id}",
                "raw_content": content[:500] + "..." if len(content) > 500 else content
            }


# Register the tool
from app.services.agent.tools.base import tool_registry

diagram_tool = DiagramRetrievalTool()
tool_registry.register_tool(diagram_tool)