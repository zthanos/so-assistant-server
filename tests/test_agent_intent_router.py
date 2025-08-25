"""Unit tests for Intent Router Tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.agent.tools.intent_router import IntentRouterTool
from app.services.agent.config import agent_config


class TestIntentRouterTool:
    """Test cases for IntentRouterTool."""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client."""
        llm = AsyncMock()
        llm.agenerate.return_value = MagicMock()
        return llm
    
    @pytest.fixture
    def intent_router(self, mock_llm):
        """Create IntentRouterTool instance."""
        return IntentRouterTool(llm=mock_llm)
    
    @pytest.mark.asyncio
    async def test_integration_check_intent_english(self, intent_router, mock_llm):
        """Test integration check intent detection in English."""
        # Mock LLM response
        mock_response = {
            "intent": "integration_check",
            "targets": {
                "so_ids": ["SEC-2.1"],
                "diagram_ids": ["SEQ-001", "C4-001"]
            },
            "confidence": 0.9,
            "reason": "User wants to check consistency between solution architecture and diagrams"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        # Test
        result = await intent_router._arun(
            user_message="Check if the solution architecture in SEC-2.1 is consistent with SEQ-001 and C4-001",
            language="en"
        )
        
        # Assertions
        assert result["intent"] == "integration_check"
        assert "SEC-2.1" in result["targets"]["so_ids"]
        assert "SEQ-001" in result["targets"]["diagram_ids"]
        assert "C4-001" in result["targets"]["diagram_ids"]
        assert result["confidence"] == 0.9
        assert "consistency" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_requirements_coverage_intent_greek(self, intent_router, mock_llm):
        """Test requirements coverage intent detection in Greek."""
        mock_response = {
            "intent": "requirements_coverage",
            "targets": {
                "requirement_ids": ["REQ-001", "REQ-002"],
                "so_ids": ["SEC-2.1", "SEC-3.1"]
            },
            "confidence": 0.85,
            "reason": "User wants to check requirements coverage"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        # Test with Greek message
        result = await intent_router._arun(
            user_message="Ελέγξτε αν οι απαιτήσεις REQ-001 και REQ-002 καλύπτονται από τις ενότητες SEC-2.1 και SEC-3.1",
            language="el"
        )
        
        # Assertions
        assert result["intent"] == "requirements_coverage"
        assert "REQ-001" in result["targets"]["requirement_ids"]
        assert "REQ-002" in result["targets"]["requirement_ids"]
        assert "SEC-2.1" in result["targets"]["so_ids"]
        assert result["confidence"] == 0.85
    
    @pytest.mark.asyncio
    async def test_improve_paragraph_intent(self, intent_router, mock_llm):
        """Test improve paragraph intent detection."""
        mock_response = {
            "intent": "improve_paragraph",
            "targets": {
                "so_ids": ["SEC-4.2"]
            },
            "confidence": 0.95,
            "reason": "User wants to improve a specific section"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        result = await intent_router._arun(
            user_message="Can you help me improve the security architecture section SEC-4.2?",
            language="en"
        )
        
        assert result["intent"] == "improve_paragraph"
        assert "SEC-4.2" in result["targets"]["so_ids"]
        assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_qna_intent_fallback(self, intent_router, mock_llm):
        """Test Q&A intent as fallback."""
        mock_response = {
            "intent": "qna",
            "targets": {},
            "confidence": 0.6,
            "reason": "General question without specific targets"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        result = await intent_router._arun(
            user_message="What is microservices architecture?",
            language="en"
        )
        
        assert result["intent"] == "qna"
        assert result["targets"] == {}
        assert result["confidence"] == 0.6
    
    @pytest.mark.asyncio
    async def test_malformed_llm_response_retry(self, intent_router, mock_llm):
        """Test retry mechanism for malformed LLM responses."""
        # First call returns malformed JSON
        # Second call returns valid JSON
        mock_llm.agenerate.side_effect = [
            MagicMock(generations=[[MagicMock(text="invalid json")]]),
            MagicMock(generations=[[MagicMock(text=json.dumps({
                "intent": "qna",
                "targets": {},
                "confidence": 0.5,
                "reason": "Fallback after parsing error"
            }))]])
        ]
        
        result = await intent_router._arun(
            user_message="Test message",
            language="en"
        )
        
        # Should fallback to qna after retry
        assert result["intent"] == "qna"
        assert result["confidence"] == 0.5
        assert mock_llm.agenerate.call_count == 2
    
    @pytest.mark.asyncio
    async def test_confidence_scoring(self, intent_router, mock_llm):
        """Test confidence scoring mechanism."""
        test_cases = [
            {
                "message": "Check integration between SEC-2.1 and SEQ-001",
                "expected_confidence": 0.9,
                "intent": "integration_check"
            },
            {
                "message": "Maybe check something",
                "expected_confidence": 0.6,
                "intent": "qna"
            }
        ]
        
        for case in test_cases:
            mock_response = {
                "intent": case["intent"],
                "targets": {"so_ids": ["SEC-2.1"]} if case["intent"] != "qna" else {},
                "confidence": case["expected_confidence"],
                "reason": f"Test case for {case['intent']}"
            }
            
            mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
            
            result = await intent_router._arun(case["message"], "en")
            
            assert result["confidence"] == case["expected_confidence"]
            assert result["intent"] == case["intent"]
    
    @pytest.mark.asyncio
    async def test_target_id_extraction(self, intent_router, mock_llm):
        """Test target ID extraction from various formats."""
        test_cases = [
            {
                "message": "Check SEC-2.1, SEC-3.2 with REQ-001 and SEQ-001, C4-002",
                "expected_targets": {
                    "so_ids": ["SEC-2.1", "SEC-3.2"],
                    "requirement_ids": ["REQ-001"],
                    "diagram_ids": ["SEQ-001", "C4-002"]
                }
            },
            {
                "message": "Analyze section 2.1 (SEC-2.1) and requirement REQ-123",
                "expected_targets": {
                    "so_ids": ["SEC-2.1"],
                    "requirement_ids": ["REQ-123"],
                    "diagram_ids": []
                }
            }
        ]
        
        for case in test_cases:
            mock_response = {
                "intent": "integration_check",
                "targets": case["expected_targets"],
                "confidence": 0.8,
                "reason": "Test target extraction"
            }
            
            mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
            
            result = await intent_router._arun(case["message"], "en")
            
            assert result["targets"]["so_ids"] == case["expected_targets"]["so_ids"]
            assert result["targets"]["requirement_ids"] == case["expected_targets"]["requirement_ids"]
            assert result["targets"]["diagram_ids"] == case["expected_targets"]["diagram_ids"]
    
    @pytest.mark.asyncio
    async def test_language_detection(self, intent_router, mock_llm):
        """Test automatic language detection."""
        # Test Greek detection
        mock_response = {
            "intent": "qna",
            "targets": {},
            "confidence": 0.7,
            "reason": "Greek language detected"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        result = await intent_router._arun(
            user_message="Τι είναι η αρχιτεκτονική μικροϋπηρεσιών;",
            language="auto"
        )
        
        assert result["intent"] == "qna"
        
        # Verify LLM was called with appropriate language context
        call_args = mock_llm.agenerate.call_args
        prompt_text = str(call_args)
        assert "Greek" in prompt_text or "ελληνικά" in prompt_text.lower()
    
    def test_sync_run_method(self, intent_router, mock_llm):
        """Test synchronous _run method."""
        mock_response = {
            "intent": "qna",
            "targets": {},
            "confidence": 0.7,
            "reason": "Sync test"
        }
        
        # Mock the async method
        with patch.object(intent_router, '_arun', return_value=mock_response) as mock_arun:
            result = intent_router._run("Test message", "en")
            
            assert result == mock_response
            mock_arun.assert_called_once_with("Test message", "en")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, intent_router, mock_llm):
        """Test error handling in intent detection."""
        # Mock LLM to raise an exception
        mock_llm.agenerate.side_effect = Exception("LLM connection error")
        
        result = await intent_router._arun("Test message", "en")
        
        # Should return fallback response
        assert result["intent"] == "qna"
        assert result["confidence"] < 0.5
        assert "error" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_caching_integration(self, intent_router, mock_llm):
        """Test integration with caching system."""
        from app.services.agent.performance.caching import intent_cache
        
        # Clear cache
        await intent_cache.clear()
        
        mock_response = {
            "intent": "integration_check",
            "targets": {"so_ids": ["SEC-2.1"]},
            "confidence": 0.9,
            "reason": "Cached test"
        }
        
        mock_llm.agenerate.return_value.generations = [[MagicMock(text=json.dumps(mock_response))]]
        
        # First call should hit LLM
        result1 = await intent_router._arun("Test caching", "en")
        
        # Second call should hit cache
        result2 = await intent_router._arun("Test caching", "en")
        
        assert result1 == result2
        # LLM should only be called once due to caching
        assert mock_llm.agenerate.call_count == 1