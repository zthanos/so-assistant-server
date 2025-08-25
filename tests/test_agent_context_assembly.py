"""Unit tests for Context Assembly Tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from app.services.agent.tools.context_assembly import (
    SOSectionRetrievalTool,
    RequirementRetrievalTool,
    DiagramRetrievalTool,
    ChatSummaryTool
)


class TestSOSectionRetrievalTool:
    """Test cases for SOSectionRetrievalTool."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock SO repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def so_tool(self, mock_repository):
        """Create SOSectionRetrievalTool instance."""
        return SOSectionRetrievalTool(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_retrieve_single_section(self, so_tool, mock_repository):
        """Test retrieving a single SO section."""
        # Mock repository response
        mock_section = {
            "id": "SEC-2.1",
            "title": "Solution Architecture",
            "content": "This section describes the overall solution architecture...",
            "parent_id": "SEC-2",
            "level": 2
        }
        
        mock_repository.get_sections_by_ids.return_value = [mock_section]
        
        # Test
        result = await so_tool._arun(
            project_id="test-project",
            section_ids=["SEC-2.1"],
            include_neighbors=False
        )
        
        # Assertions
        assert "sections" in result
        assert len(result["sections"]) == 1
        assert result["sections"][0]["id"] == "SEC-2.1"
        assert result["sections"][0]["title"] == "Solution Architecture"
        
        mock_repository.get_sections_by_ids.assert_called_once_with(
            project_id="test-project",
            section_ids=["SEC-2.1"]
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_multiple_sections(self, so_tool, mock_repository):
        """Test retrieving multiple SO sections."""
        mock_sections = [
            {
                "id": "SEC-2.1",
                "title": "Solution Architecture",
                "content": "Solution content...",
                "parent_id": "SEC-2",
                "level": 2
            },
            {
                "id": "SEC-3.1",
                "title": "Data Architecture",
                "content": "Data content...",
                "parent_id": "SEC-3",
                "level": 2
            }
        ]
        
        mock_repository.get_sections_by_ids.return_value = mock_sections
        
        result = await so_tool._arun(
            project_id="test-project",
            section_ids=["SEC-2.1", "SEC-3.1"],
            include_neighbors=False
        )
        
        assert len(result["sections"]) == 2
        assert result["sections"][0]["id"] == "SEC-2.1"
        assert result["sections"][1]["id"] == "SEC-3.1"
    
    @pytest.mark.asyncio
    async def test_retrieve_with_neighbors(self, so_tool, mock_repository):
        """Test retrieving sections with neighboring context."""
        mock_sections = [
            {
                "id": "SEC-2.1",
                "title": "Solution Architecture",
                "content": "Main content...",
                "parent_id": "SEC-2",
                "level": 2
            }
        ]
        
        mock_neighbors = [
            {
                "id": "SEC-2.0",
                "title": "Architecture Overview",
                "content": "Overview content...",
                "parent_id": "SEC-2",
                "level": 2
            },
            {
                "id": "SEC-2.2",
                "title": "Component Architecture",
                "content": "Component content...",
                "parent_id": "SEC-2",
                "level": 2
            }
        ]
        
        mock_repository.get_sections_by_ids.return_value = mock_sections
        mock_repository.get_neighboring_sections.return_value = mock_neighbors
        
        result = await so_tool._arun(
            project_id="test-project",
            section_ids=["SEC-2.1"],
            include_neighbors=True
        )
        
        assert len(result["sections"]) == 3  # Main + 2 neighbors
        
        # Verify neighbor retrieval was called
        mock_repository.get_neighboring_sections.assert_called_once_with(
            project_id="test-project",
            section_ids=["SEC-2.1"]
        )
    
    @pytest.mark.asyncio
    async def test_section_not_found(self, so_tool, mock_repository):
        """Test handling of non-existent sections."""
        mock_repository.get_sections_by_ids.return_value = []
        
        result = await so_tool._arun(
            project_id="test-project",
            section_ids=["SEC-999"],
            include_neighbors=False
        )
        
        assert result["sections"] == []
        assert "metadata" in result
        assert result["metadata"]["sections_found"] == 0


class TestRequirementRetrievalTool:
    """Test cases for RequirementRetrievalTool."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock requirements repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def req_tool(self, mock_repository):
        """Create RequirementRetrievalTool instance."""
        return RequirementRetrievalTool(repository=mock_repository)
    
    @pytest.mark.asyncio
    async def test_retrieve_by_ids(self, req_tool, mock_repository):
        """Test retrieving requirements by IDs."""
        mock_requirements = [
            {
                "id": "REQ-001",
                "title": "User Authentication",
                "description": "System shall support user authentication",
                "priority": "high",
                "status": "approved"
            },
            {
                "id": "REQ-002",
                "title": "Data Encryption",
                "description": "System shall encrypt sensitive data",
                "priority": "high",
                "status": "approved"
            }
        ]
        
        mock_repository.get_requirements_by_ids.return_value = mock_requirements
        
        result = await req_tool._arun(
            project_id="test-project",
            requirement_ids=["REQ-001", "REQ-002"]
        )
        
        assert "requirements" in result
        assert len(result["requirements"]) == 2
        assert result["requirements"][0]["id"] == "REQ-001"
        assert result["requirements"][1]["id"] == "REQ-002"
    
    @pytest.mark.asyncio
    async def test_semantic_search(self, req_tool, mock_repository):
        """Test semantic search for requirements."""
        mock_requirements = [
            {
                "id": "REQ-003",
                "title": "Security Requirements",
                "description": "Authentication and authorization requirements",
                "priority": "high",
                "status": "approved"
            }
        ]
        
        mock_repository.search_requirements.return_value = mock_requirements
        
        result = await req_tool._arun(
            project_id="test-project",
            query="authentication security",
            max_results=5
        )
        
        assert len(result["requirements"]) == 1
        assert result["requirements"][0]["id"] == "REQ-003"
        
        mock_repository.search_requirements.assert_called_once_with(
            project_id="test-project",
            query="authentication security",
            max_results=5
        )
    
    @pytest.mark.asyncio
    async def test_combined_id_and_search(self, req_tool, mock_repository):
        """Test combining ID retrieval with semantic search."""
        mock_id_requirements = [
            {
                "id": "REQ-001",
                "title": "User Authentication",
                "description": "System shall support user authentication",
                "priority": "high",
                "status": "approved"
            }
        ]
        
        mock_search_requirements = [
            {
                "id": "REQ-004",
                "title": "Related Security Requirement",
                "description": "Additional security requirement",
                "priority": "medium",
                "status": "draft"
            }
        ]
        
        mock_repository.get_requirements_by_ids.return_value = mock_id_requirements
        mock_repository.search_requirements.return_value = mock_search_requirements
        
        result = await req_tool._arun(
            project_id="test-project",
            requirement_ids=["REQ-001"],
            query="security",
            max_results=3
        )
        
        # Should combine results from both methods
        assert len(result["requirements"]) == 2
        req_ids = [req["id"] for req in result["requirements"]]
        assert "REQ-001" in req_ids
        assert "REQ-004" in req_ids


class TestDiagramRetrievalTool:
    """Test cases for DiagramRetrievalTool."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock diagram repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_parser(self):
        """Mock diagram parser."""
        parser = AsyncMock()
        return parser
    
    @pytest.fixture
    def diagram_tool(self, mock_repository, mock_parser):
        """Create DiagramRetrievalTool instance."""
        return DiagramRetrievalTool(repository=mock_repository, parser=mock_parser)
    
    @pytest.mark.asyncio
    async def test_retrieve_sequence_diagram(self, diagram_tool, mock_repository, mock_parser):
        """Test retrieving and parsing sequence diagram."""
        # Mock diagram data
        mock_diagram = {
            "id": "SEQ-001",
            "title": "User Authentication Flow",
            "content": "sequenceDiagram\n    User->>System: Login\n    System->>DB: Validate",
            "type": "sequence"
        }
        
        # Mock parsed data
        mock_parsed = {
            "id": "SEQ-001",
            "participants": ["User", "System", "DB"],
            "interactions": [
                {"from": "User", "to": "System", "message": "Login"},
                {"from": "System", "to": "DB", "message": "Validate"}
            ],
            "steps": [
                {"step": 1, "action": "User sends Login to System"},
                {"step": 2, "action": "System sends Validate to DB"}
            ]
        }
        
        mock_repository.get_diagrams_by_ids.return_value = [mock_diagram]
        mock_parser.parse_sequence_diagram.return_value = mock_parsed
        
        result = await diagram_tool._arun(
            project_id="test-project",
            diagram_ids=["SEQ-001"]
        )
        
        assert "diagrams" in result
        assert len(result["diagrams"]) == 1
        
        parsed_diagram = result["diagrams"][0]
        assert parsed_diagram["id"] == "SEQ-001"
        assert "User" in parsed_diagram["participants"]
        assert len(parsed_diagram["interactions"]) == 2
    
    @pytest.mark.asyncio
    async def test_retrieve_c4_diagram(self, diagram_tool, mock_repository, mock_parser):
        """Test retrieving and parsing C4 diagram."""
        mock_diagram = {
            "id": "C4-001",
            "title": "System Context",
            "content": "C4Context\n    Person(user, \"User\")\n    System(sys, \"System\")",
            "type": "c4"
        }
        
        mock_parsed = {
            "id": "C4-001",
            "diagram_type": "Context",
            "systems": [
                {"id": "sys", "name": "System", "type": "system"}
            ],
            "containers": [],
            "components": [],
            "relationships": [
                {"from": "user", "to": "sys", "description": "Uses"}
            ]
        }
        
        mock_repository.get_diagrams_by_ids.return_value = [mock_diagram]
        mock_parser.parse_c4_diagram.return_value = mock_parsed
        
        result = await diagram_tool._arun(
            project_id="test-project",
            diagram_ids=["C4-001"]
        )
        
        parsed_diagram = result["diagrams"][0]
        assert parsed_diagram["id"] == "C4-001"
        assert parsed_diagram["diagram_type"] == "Context"
        assert len(parsed_diagram["systems"]) == 1
        assert len(parsed_diagram["relationships"]) == 1
    
    @pytest.mark.asyncio
    async def test_mixed_diagram_types(self, diagram_tool, mock_repository, mock_parser):
        """Test retrieving mixed sequence and C4 diagrams."""
        mock_diagrams = [
            {
                "id": "SEQ-001",
                "title": "Sequence Diagram",
                "content": "sequenceDiagram\n    A->>B: Message",
                "type": "sequence"
            },
            {
                "id": "C4-001",
                "title": "C4 Diagram",
                "content": "C4Context\n    System(sys, \"System\")",
                "type": "c4"
            }
        ]
        
        mock_seq_parsed = {
            "id": "SEQ-001",
            "participants": ["A", "B"],
            "interactions": [{"from": "A", "to": "B", "message": "Message"}],
            "steps": []
        }
        
        mock_c4_parsed = {
            "id": "C4-001",
            "diagram_type": "Context",
            "systems": [{"id": "sys", "name": "System"}],
            "containers": [],
            "components": [],
            "relationships": []
        }
        
        mock_repository.get_diagrams_by_ids.return_value = mock_diagrams
        mock_parser.parse_sequence_diagram.return_value = mock_seq_parsed
        mock_parser.parse_c4_diagram.return_value = mock_c4_parsed
        
        result = await diagram_tool._arun(
            project_id="test-project",
            diagram_ids=["SEQ-001", "C4-001"]
        )
        
        assert len(result["diagrams"]) == 2
        
        # Find diagrams by ID
        seq_diagram = next(d for d in result["diagrams"] if d["id"] == "SEQ-001")
        c4_diagram = next(d for d in result["diagrams"] if d["id"] == "C4-001")
        
        assert "participants" in seq_diagram
        assert "diagram_type" in c4_diagram
    
    @pytest.mark.asyncio
    async def test_parsing_error_handling(self, diagram_tool, mock_repository, mock_parser):
        """Test handling of diagram parsing errors."""
        mock_diagram = {
            "id": "SEQ-001",
            "title": "Invalid Diagram",
            "content": "invalid mermaid syntax",
            "type": "sequence"
        }
        
        mock_repository.get_diagrams_by_ids.return_value = [mock_diagram]
        mock_parser.parse_sequence_diagram.side_effect = Exception("Parsing error")
        
        result = await diagram_tool._arun(
            project_id="test-project",
            diagram_ids=["SEQ-001"]
        )
        
        # Should still return diagram but with error info
        assert len(result["diagrams"]) == 1
        diagram = result["diagrams"][0]
        assert diagram["id"] == "SEQ-001"
        assert "error" in diagram
        assert "parsing" in diagram["error"].lower()


class TestChatSummaryTool:
    """Test cases for ChatSummaryTool."""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock chat repository."""
        repo = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for summarization."""
        llm = AsyncMock()
        return llm
    
    @pytest.fixture
    def chat_tool(self, mock_repository, mock_llm):
        """Create ChatSummaryTool instance."""
        return ChatSummaryTool(repository=mock_repository, llm=mock_llm)
    
    @pytest.mark.asyncio
    async def test_get_recent_chat_summary(self, chat_tool, mock_repository, mock_llm):
        """Test getting recent chat summary."""
        # Mock chat messages
        mock_messages = [
            {
                "id": "msg-1",
                "user_message": "What is microservices architecture?",
                "assistant_response": "Microservices architecture is...",
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "id": "msg-2",
                "user_message": "How do we implement authentication?",
                "assistant_response": "Authentication can be implemented using...",
                "timestamp": "2024-01-01T10:05:00Z"
            }
        ]
        
        # Mock summary
        mock_summary = "Recent conversation covered microservices architecture and authentication implementation."
        
        mock_repository.get_recent_messages.return_value = mock_messages
        mock_llm.agenerate.return_value = MagicMock(
            generations=[[MagicMock(text=mock_summary)]]
        )
        
        result = await chat_tool._arun(
            project_id="test-project",
            last_n_messages=10
        )
        
        assert result == mock_summary
        
        mock_repository.get_recent_messages.assert_called_once_with(
            project_id="test-project",
            limit=10
        )
    
    @pytest.mark.asyncio
    async def test_empty_chat_history(self, chat_tool, mock_repository, mock_llm):
        """Test handling empty chat history."""
        mock_repository.get_recent_messages.return_value = []
        
        result = await chat_tool._arun(
            project_id="test-project",
            last_n_messages=10
        )
        
        assert result == "No recent conversation history available."
        # LLM should not be called for empty history
        mock_llm.agenerate.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_configurable_message_limit(self, chat_tool, mock_repository, mock_llm):
        """Test configurable message limit."""
        mock_messages = [{"id": f"msg-{i}"} for i in range(5)]
        mock_repository.get_recent_messages.return_value = mock_messages
        mock_llm.agenerate.return_value = MagicMock(
            generations=[[MagicMock(text="Summary of 5 messages")]]
        )
        
        result = await chat_tool._arun(
            project_id="test-project",
            last_n_messages=5
        )
        
        mock_repository.get_recent_messages.assert_called_once_with(
            project_id="test-project",
            limit=5
        )
        
        assert "Summary" in result


class TestContextAssemblyIntegration:
    """Integration tests for context assembly tools."""
    
    @pytest.mark.asyncio
    async def test_parallel_context_assembly(self):
        """Test parallel execution of context assembly tools."""
        from app.services.agent.performance.parallel import ParallelContextAssembler, ParallelExecutor
        
        # Mock tools
        mock_so_tool = AsyncMock()
        mock_req_tool = AsyncMock()
        mock_diagram_tool = AsyncMock()
        mock_chat_tool = AsyncMock()
        
        # Mock responses
        mock_so_tool._execute.return_value = {"sections": [{"id": "SEC-2.1"}]}
        mock_req_tool._execute.return_value = {"requirements": [{"id": "REQ-001"}]}
        mock_diagram_tool._execute.return_value = {"diagrams": [{"id": "SEQ-001"}]}
        mock_chat_tool._execute.return_value = "Recent chat summary"
        
        tools = {
            "so_tool": mock_so_tool,
            "requirement_tool": mock_req_tool,
            "diagram_tool": mock_diagram_tool,
            "chat_tool": mock_chat_tool
        }
        
        targets = {
            "so_ids": ["SEC-2.1"],
            "requirement_ids": ["REQ-001"],
            "diagram_ids": ["SEQ-001"]
        }
        
        executor = ParallelExecutor(max_workers=4)
        assembler = ParallelContextAssembler(executor)
        
        result = await assembler.assemble_context_parallel(
            project_id="test-project",
            targets=targets,
            intent="integration_check",
            tools=tools
        )
        
        # Verify all tools were called
        mock_so_tool._execute.assert_called_once()
        mock_req_tool._execute.assert_called_once()
        mock_diagram_tool._execute.assert_called_once()
        mock_chat_tool._execute.assert_called_once()
        
        # Verify results are assembled
        assert len(result["so_sections"]) == 1
        assert len(result["requirements"]) == 1
        assert len(result["diagrams"]) == 1
        assert result["chat_summary"] == "Recent chat summary"
        assert result["metadata"]["parallel_execution"] is True
    
    @pytest.mark.asyncio
    async def test_context_caching(self):
        """Test context assembly with caching."""
        from app.services.agent.performance.caching import context_cache
        
        # Clear cache
        await context_cache.clear()
        
        # Mock context data
        mock_context = {
            "so_sections": [{"id": "SEC-2.1"}],
            "requirements": [{"id": "REQ-001"}],
            "diagrams": [{"id": "SEQ-001"}],
            "chat_summary": "Cached summary"
        }
        
        project_id = "test-project"
        targets = {"so_ids": ["SEC-2.1"]}
        intent = "integration_check"
        
        # Set cache
        await context_cache.set_context(project_id, targets, intent, mock_context)
        
        # Retrieve from cache
        cached_result = await context_cache.get_context(project_id, targets, intent)
        
        assert cached_result == mock_context
        assert cached_result["so_sections"][0]["id"] == "SEC-2.1"