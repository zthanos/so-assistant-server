"""Specialized analysis tools for different intents."""
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.services.agent.tools.base import BaseAgentTool
from app.services.agent.tools.context_orchestrator import ContextAssemblyOrchestrator, ContextFormatter
from app.services.agent.tools.validation import validate_structured_response, RetryHandler, JSONResponseParser
from app.services.agent.prompts.templates import prompt_manager, Language
from app.services.agent.llm_client import streaming_ollama_client

logger = logging.getLogger(__name__)


class IntegrationCheckTool(BaseAgentTool):
    """Tool for analyzing integration consistency between SO and diagrams."""
    
    name = "integration_check_analysis"
    description = "Analyze integration consistency between Solution Outline sections and diagrams"
    tool_category = "analysis"
    requires_project_id = True
    
    def __init__(self):
        """Initialize the integration check tool."""
        super().__init__()
        self.context_orchestrator = ContextAssemblyOrchestrator()
    
    async def _execute(self, project_id: str, targets: Dict[str, List[str]], 
                      language: str = "en", **kwargs) -> Dict[str, Any]:
        """Execute integration consistency analysis."""
        try:
            # Assemble context for integration check
            context = await self.context_orchestrator._execute(
                project_id=project_id,
                targets=targets,
                intent="integration_check",
                include_chat=False
            )
            
            # Check if we have sufficient context
            if not context.get("so_sections") or not context.get("diagrams"):
                return {
                    "suggestions": [],
                    "scores": self._default_scores(),
                    "status": "insufficient",
                    "reason": "Need both SO sections and diagrams for integration analysis"
                }
            
            # Format context for prompt
            formatted_context = ContextFormatter.format_context_for_prompt(
                context, "integration_check", language
            )
            
            # Generate analysis using LLM
            analysis_result = await self._generate_integration_analysis(
                project_id, formatted_context, language
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in integration check analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": str(e)
            }
    
    async def _generate_integration_analysis(self, project_id: str, context: Dict[str, str], 
                                           language: str) -> Dict[str, Any]:
        """Generate integration analysis using LLM."""
        
        try:
            # Use retry handler with validation
            async def llm_analysis():
                # Convert language string to Language enum
                lang = Language.GREEK if language == "el" else Language.ENGLISH
                
                # Create prompt using template manager
                prompt = prompt_manager.format_prompt(
                    "integration_check",
                    language=lang,
                    project_id=project_id,
                    so_sections=context.get("so_sections", ""),
                    diagrams=context.get("diagrams", ""),
                    requirements=context.get("requirements", "")
                )
                
                # Get LLM response
                response = await streaming_ollama_client.generate(prompt, "integration_check")
                
                # Parse and validate JSON response
                return JSONResponseParser.parse_json_response(response)
            
            # Execute with retry and validation
            result = await RetryHandler.retry_with_validation(
                llm_analysis,
                validate_structured_response,
                max_retries=1
            )
            
            # Enhance suggestions with integration-specific scoring
            enhanced_result = self._enhance_integration_analysis(result, context)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error generating integration analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": f"Analysis generation failed: {str(e)}"
            }
    
    def _enhance_integration_analysis(self, result: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
        """Enhance analysis with integration-specific improvements."""
        
        # Calculate integration consistency score based on suggestions
        suggestions = result.get("suggestions", [])
        integration_issues = len([s for s in suggestions if s.get("type") == "integration"])
        total_diagrams = len(context.get("diagrams", "").split("##")) - 1  # Rough count
        
        if total_diagrams > 0:
            consistency_score = max(0.0, 1.0 - (integration_issues / (total_diagrams * 2)))
        else:
            consistency_score = 0.5
        
        # Update scores
        scores = result.get("scores", {})
        scores["integration_consistency"] = consistency_score
        
        # Add integration-specific metadata to suggestions
        for suggestion in suggestions:
            if suggestion.get("type") == "integration":
                suggestion["metadata"] = {
                    "analysis_type": "integration_check",
                    "consistency_impact": self._calculate_consistency_impact(suggestion)
                }
        
        result["scores"] = scores
        return result
    
    def _calculate_consistency_impact(self, suggestion: Dict[str, Any]) -> str:
        """Calculate consistency impact of a suggestion."""
        severity = suggestion.get("severity", "minor")
        if severity == "critical":
            return "high"
        elif severity == "major":
            return "medium"
        else:
            return "low"
    
    def _default_scores(self) -> Dict[str, float]:
        """Return default analysis scores."""
        return {
            "integration_consistency": 0.5,
            "requirements_coverage": 0.5,
            "security_readiness": 0.5,
            "operability": 0.5
        }


class RequirementsCoverageTool(BaseAgentTool):
    """Tool for analyzing requirements coverage in SO and diagrams."""
    
    name = "requirements_coverage_analysis"
    description = "Analyze how well requirements are covered in SO sections and diagrams"
    tool_category = "analysis"
    requires_project_id = True
    
    def __init__(self):
        """Initialize the requirements coverage tool."""
        super().__init__()
        self.context_orchestrator = ContextAssemblyOrchestrator()
    
    async def _execute(self, project_id: str, targets: Dict[str, List[str]], 
                      language: str = "en", **kwargs) -> Dict[str, Any]:
        """Execute requirements coverage analysis."""
        try:
            # Assemble context for requirements coverage
            context = await self.context_orchestrator._execute(
                project_id=project_id,
                targets=targets,
                intent="requirements_coverage",
                include_chat=False
            )
            
            # Check if we have sufficient context
            if not context.get("requirements"):
                return {
                    "suggestions": [],
                    "scores": self._default_scores(),
                    "status": "insufficient",
                    "reason": "Need requirements for coverage analysis"
                }
            
            # Format context for prompt
            formatted_context = ContextFormatter.format_context_for_prompt(
                context, "requirements_coverage", language
            )
            
            # Generate analysis using LLM
            analysis_result = await self._generate_coverage_analysis(
                project_id, formatted_context, language
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in requirements coverage analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": str(e)
            }
    
    async def _generate_coverage_analysis(self, project_id: str, context: Dict[str, str], 
                                        language: str) -> Dict[str, Any]:
        """Generate requirements coverage analysis using LLM."""
        
        try:
            # Use retry handler with validation
            async def llm_analysis():
                # Convert language string to Language enum
                lang = Language.GREEK if language == "el" else Language.ENGLISH
                
                # Create prompt using template manager
                prompt = prompt_manager.format_prompt(
                    "requirements_coverage",
                    language=lang,
                    project_id=project_id,
                    requirements=context.get("requirements", ""),
                    so_sections=context.get("so_sections", ""),
                    diagrams=context.get("diagrams", "")
                )
                
                # Get LLM response
                response = await streaming_ollama_client.generate(prompt, "requirements_coverage")
                
                # Parse and validate JSON response
                return JSONResponseParser.parse_json_response(response)
            
            # Execute with retry and validation
            result = await RetryHandler.retry_with_validation(
                llm_analysis,
                validate_structured_response,
                max_retries=1
            )
            
            # Enhance suggestions with coverage-specific scoring
            enhanced_result = self._enhance_coverage_analysis(result, context)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error generating coverage analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": f"Analysis generation failed: {str(e)}"
            }
    
    def _enhance_coverage_analysis(self, result: Dict[str, Any], context: Dict[str, str]) -> Dict[str, Any]:
        """Enhance analysis with coverage-specific improvements."""
        
        # Calculate requirements coverage score
        suggestions = result.get("suggestions", [])
        coverage_issues = len([s for s in suggestions if s.get("type") == "coverage"])
        total_requirements = len(context.get("requirements", "").split("**REQ-")) - 1  # Rough count
        
        if total_requirements > 0:
            coverage_score = max(0.0, 1.0 - (coverage_issues / total_requirements))
        else:
            coverage_score = 0.5
        
        # Update scores
        scores = result.get("scores", {})
        scores["requirements_coverage"] = coverage_score
        
        # Add coverage-specific metadata to suggestions
        for suggestion in suggestions:
            if suggestion.get("type") == "coverage":
                suggestion["metadata"] = {
                    "analysis_type": "requirements_coverage",
                    "coverage_gap": self._identify_coverage_gap(suggestion)
                }
        
        result["scores"] = scores
        return result
    
    def _identify_coverage_gap(self, suggestion: Dict[str, Any]) -> str:
        """Identify the type of coverage gap."""
        summary = suggestion.get("summary", "").lower()
        if "not covered" in summary or "missing" in summary:
            return "not_covered"
        elif "partially" in summary or "incomplete" in summary:
            return "partial_coverage"
        elif "over-specified" in summary or "redundant" in summary:
            return "over_coverage"
        else:
            return "unclear"
    
    def _default_scores(self) -> Dict[str, float]:
        """Return default analysis scores."""
        return {
            "integration_consistency": 0.5,
            "requirements_coverage": 0.5,
            "security_readiness": 0.5,
            "operability": 0.5
        }


class ParagraphImprovementTool(BaseAgentTool):
    """Tool for providing targeted improvement suggestions for SO sections."""
    
    name = "paragraph_improvement_analysis"
    description = "Provide targeted improvement suggestions for specific SO sections"
    tool_category = "analysis"
    requires_project_id = True
    
    def __init__(self):
        """Initialize the paragraph improvement tool."""
        super().__init__()
        self.context_orchestrator = ContextAssemblyOrchestrator()
    
    async def _execute(self, project_id: str, targets: Dict[str, List[str]], 
                      focus_area: str = "general", language: str = "en", **kwargs) -> Dict[str, Any]:
        """Execute paragraph improvement analysis."""
        try:
            # Assemble context for paragraph improvement
            context = await self.context_orchestrator._execute(
                project_id=project_id,
                targets=targets,
                intent="improve_paragraph",
                include_chat=True
            )
            
            # Check if we have sufficient context
            if not context.get("so_sections"):
                return {
                    "suggestions": [],
                    "scores": self._default_scores(),
                    "status": "insufficient",
                    "reason": "Need SO sections for improvement analysis"
                }
            
            # Format context for prompt
            formatted_context = ContextFormatter.format_context_for_prompt(
                context, "improve_paragraph", language
            )
            
            # Generate analysis using LLM
            analysis_result = await self._generate_improvement_analysis(
                project_id, formatted_context, focus_area, language
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in paragraph improvement analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": str(e)
            }
    
    async def _generate_improvement_analysis(self, project_id: str, context: Dict[str, str], 
                                           focus_area: str, language: str) -> Dict[str, Any]:
        """Generate paragraph improvement analysis using LLM."""
        
        try:
            # Use retry handler with validation
            async def llm_analysis():
                # Convert language string to Language enum
                lang = Language.GREEK if language == "el" else Language.ENGLISH
                
                # Create prompt using template manager
                prompt = prompt_manager.format_prompt(
                    "paragraph_improvement",
                    language=lang,
                    project_id=project_id,
                    focus_area=focus_area,
                    target_sections=context.get("so_sections", ""),
                    requirements=context.get("requirements", ""),
                    diagrams=context.get("diagrams", "")
                )
                
                # Get LLM response
                response = await streaming_ollama_client.generate(prompt, "paragraph_improvement")
                
                # Parse and validate JSON response
                return JSONResponseParser.parse_json_response(response)
            
            # Execute with retry and validation
            result = await RetryHandler.retry_with_validation(
                llm_analysis,
                validate_structured_response,
                max_retries=1
            )
            
            # Enhance suggestions with improvement-specific scoring
            enhanced_result = self._enhance_improvement_analysis(result, focus_area)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Error generating improvement analysis: {str(e)}")
            return {
                "suggestions": [],
                "scores": self._default_scores(),
                "status": "insufficient",
                "error": f"Analysis generation failed: {str(e)}"
            }
    
    def _enhance_improvement_analysis(self, result: Dict[str, Any], focus_area: str) -> Dict[str, Any]:
        """Enhance analysis with improvement-specific enhancements."""
        
        # Calculate improvement scores based on focus area
        suggestions = result.get("suggestions", [])
        
        # Update scores based on improvement suggestions
        scores = result.get("scores", {})
        
        if focus_area == "security":
            security_improvements = len([s for s in suggestions if "security" in s.get("summary", "").lower()])
            scores["security_readiness"] = min(1.0, scores.get("security_readiness", 0.5) + (security_improvements * 0.1))
        elif focus_area == "scalability":
            operability_improvements = len([s for s in suggestions if "scalability" in s.get("summary", "").lower()])
            scores["operability"] = min(1.0, scores.get("operability", 0.5) + (operability_improvements * 0.1))
        
        # Add improvement-specific metadata to suggestions
        for suggestion in suggestions:
            suggestion["metadata"] = {
                "analysis_type": "paragraph_improvement",
                "focus_area": focus_area,
                "improvement_category": self._categorize_improvement(suggestion)
            }
        
        result["scores"] = scores
        return result
    
    def _categorize_improvement(self, suggestion: Dict[str, Any]) -> str:
        """Categorize the type of improvement."""
        summary = suggestion.get("summary", "").lower()
        if "clarity" in summary or "readability" in summary:
            return "clarity"
        elif "technical" in summary or "accuracy" in summary:
            return "technical"
        elif "structure" in summary or "organization" in summary:
            return "structure"
        elif "completeness" in summary or "missing" in summary:
            return "completeness"
        else:
            return "general"
    
    def _default_scores(self) -> Dict[str, float]:
        """Return default analysis scores."""
        return {
            "integration_consistency": 0.5,
            "requirements_coverage": 0.5,
            "security_readiness": 0.5,
            "operability": 0.5
        }


class QnATool(BaseAgentTool):
    """Tool for answering general questions using project context."""
    
    name = "qna_response"
    description = "Answer general questions using available project context"
    tool_category = "analysis"
    requires_project_id = True
    
    def __init__(self):
        """Initialize the Q&A tool."""
        super().__init__()
        self.context_orchestrator = ContextAssemblyOrchestrator()
    
    async def _execute(self, project_id: str, question: str, targets: Dict[str, List[str]], 
                      language: str = "en", **kwargs) -> str:
        """Execute Q&A response generation."""
        try:
            # Assemble context for Q&A
            context = await self.context_orchestrator._execute(
                project_id=project_id,
                targets=targets,
                intent="qna",
                include_chat=True
            )
            
            # Format context for prompt
            formatted_context = ContextFormatter.format_context_for_prompt(
                context, "qna", language
            )
            
            # Generate answer using LLM
            answer = await self._generate_qna_response(
                project_id, question, formatted_context, language
            )
            
            return answer
            
        except Exception as e:
            logger.error(f"Error in Q&A response: {str(e)}")
            return "INSUFFICIENT"
    
    async def _generate_qna_response(self, project_id: str, question: str, 
                                   context: Dict[str, str], language: str) -> str:
        """Generate Q&A response using LLM."""
        
        try:
            # Convert language string to Language enum
            lang = Language.GREEK if language == "el" else Language.ENGLISH
            
            # Create prompt using template manager
            prompt = prompt_manager.format_prompt(
                "qna",
                language=lang,
                project_id=project_id,
                question=question,
                so_sections=context.get("so_sections", ""),
                requirements=context.get("requirements", ""),
                diagrams=context.get("diagrams", ""),
                chat_summary=context.get("chat_summary", "")
            )
            
            # Get LLM response
            response = await streaming_ollama_client.generate(prompt, "qna")
            
            # Clean and validate response
            cleaned_response = response.strip()
            
            # Check if response indicates insufficient context
            if not cleaned_response or len(cleaned_response) < 10:
                return "INSUFFICIENT"
            
            # Remove any markdown formatting
            cleaned_response = self._clean_markdown(cleaned_response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating Q&A response: {str(e)}")
            return "INSUFFICIENT"
    
    def _clean_markdown(self, text: str) -> str:
        """Remove markdown formatting from text."""
        import re
        
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove bold/italic formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        return text.strip()


# Register the analysis tools
from app.services.agent.tools.base import tool_registry

integration_check_tool = IntegrationCheckTool()
requirements_coverage_tool = RequirementsCoverageTool()
paragraph_improvement_tool = ParagraphImprovementTool()
qna_tool = QnATool()

tool_registry.register_tool(integration_check_tool)
tool_registry.register_tool(requirements_coverage_tool)
tool_registry.register_tool(paragraph_improvement_tool)
tool_registry.register_tool(qna_tool)