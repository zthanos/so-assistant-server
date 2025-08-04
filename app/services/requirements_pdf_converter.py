"""LLM-powered PDF to requirements markdown conversion."""

import logging
from typing import Optional, Dict, Any
import re

from app.services.llm.client import StreamingOllamaClient
from app.exceptions.pdf_exceptions import PDFProcessingError

logger = logging.getLogger(__name__)


class LLMConversionError(Exception):
    """Base exception for LLM conversion errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class MarkdownValidationError(LLMConversionError):
    """Raised when LLM output is not valid markdown."""
    pass


class RequirementsPDFConverter:
    """Converts PDF text to structured requirements markdown using LLM."""
    
    def __init__(self, llm_client: Optional[StreamingOllamaClient] = None):
        """Initialize the converter.
        
        Args:
            llm_client: Optional LLM client instance. If not provided, creates a new one.
        """
        self.llm_client = llm_client or StreamingOllamaClient()
        self.max_text_length = 50000  # Maximum characters to send to LLM
        
    async def convert_pdf_text_to_markdown(
        self, 
        pdf_text: str, 
        filename: str,
        project_context: Optional[str] = None
    ) -> str:
        """Convert extracted PDF text to structured requirements markdown.
        
        Args:
            pdf_text: Raw text extracted from PDF
            filename: Original filename for context
            project_context: Optional project context for better conversion
            
        Returns:
            Structured requirements markdown
            
        Raises:
            LLMConversionError: If LLM conversion fails
            MarkdownValidationError: If output is not valid markdown
        """
        try:
            # Truncate text if too long
            if len(pdf_text) > self.max_text_length:
                logger.warning(f"PDF text too long ({len(pdf_text)} chars), truncating to {self.max_text_length}")
                pdf_text = pdf_text[:self.max_text_length] + "\n\n[... content truncated ...]"
            
            # Generate conversion prompt
            prompt = self.generate_conversion_prompt(pdf_text, filename, project_context)
            
            # Call LLM for conversion
            logger.info(f"Converting PDF text to markdown using LLM (text length: {len(pdf_text)})")
            markdown_content = await self.llm_client.generate(
                prompt=prompt,
                prompt_key="pdf_to_requirements_conversion"
            )
            
            # Validate the output
            if not self.validate_markdown_output(markdown_content):
                # Try to clean up the output
                cleaned_content = self.cleanup_markdown_output(markdown_content)
                if not self.validate_markdown_output(cleaned_content):
                    raise MarkdownValidationError(
                        "LLM output is not valid markdown format",
                        details={
                            "filename": filename,
                            "output_length": len(markdown_content),
                            "original_output": markdown_content[:500] + "..." if len(markdown_content) > 500 else markdown_content
                        }
                    )
                markdown_content = cleaned_content
            
            logger.info(f"Successfully converted PDF to markdown ({len(markdown_content)} characters)")
            return markdown_content
            
        except MarkdownValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"LLM conversion failed: {e}")
            raise LLMConversionError(
                f"Failed to convert PDF to markdown: {str(e)}",
                details={
                    "filename": filename,
                    "pdf_text_length": len(pdf_text),
                    "error_type": type(e).__name__
                }
            )
    
    def generate_conversion_prompt(
        self, 
        pdf_text: str, 
        filename: str,
        project_context: Optional[str] = None
    ) -> str:
        """Generate prompt for LLM to convert PDF to requirements markdown.
        
        Args:
            pdf_text: Raw text from PDF
            filename: Original filename
            project_context: Optional project context
            
        Returns:
            Formatted prompt for LLM
        """
        context_section = ""
        if project_context:
            context_section = f"""
Project Context:
{project_context}

"""
        
        prompt = f"""
You are an expert in technical documentation and Markdown formatting.

Your task is to **convert the provided text into clean and properly formatted Markdown**.

Follow these instructions:
- Preserve the original structure and meaning of the document
- Use proper Markdown syntax:
  - Use `#`, `##`, etc., for headings
  - Numbered lists for requirements (1., 2., etc.)
  - Bullet points for sub-items
  - Markdown tables for tabular data
  - `code blocks` for technical content
- Keep the original text intact; do not rewrite or simplify
- Do not comment on the document, explain, or summarize
- Return **only** the converted Markdown, no explanations

Here is the content to convert:
---
{pdf_text}
---
"""

        return prompt
    
    def validate_markdown_output(self, markdown: str) -> bool:
        """Validate that LLM output is properly formatted markdown.
        
        Args:
            markdown: The markdown content to validate
            
        Returns:
            True if valid markdown, False otherwise
        """
        if not markdown or not markdown.strip():
            return False
        
        # Basic markdown validation checks
        checks = [
            # Should have some content
            len(markdown.strip()) > 50,
            
            # Should have at least one heading
            bool(re.search(r'^#+\s+.+', markdown, re.MULTILINE)),
            
            # Should not have obvious LLM artifacts
            not any(phrase in markdown.lower() for phrase in [
                "i cannot", "i'm sorry", "as an ai", "i don't have access",
                "please provide", "i need more information"
            ]),
            
            # Should not be mostly code or technical jargon without structure
            not (markdown.count('```') > len(markdown) / 100),
            
            # Should have reasonable line breaks
            '\n' in markdown
        ]
        
        return all(checks)
    
    def cleanup_markdown_output(self, markdown: str) -> str:
        """Clean up LLM output to improve markdown formatting.
        
        Args:
            markdown: Raw markdown output from LLM
            
        Returns:
            Cleaned up markdown
        """
        # Remove any leading/trailing whitespace
        cleaned = markdown.strip()
        
        # Fix common markdown issues
        # Ensure headers have proper spacing
        cleaned = re.sub(r'^(#+)([^\s])', r'\1 \2', cleaned, flags=re.MULTILINE)
        
        # Ensure proper line breaks around headers
        cleaned = re.sub(r'\n(#+\s+.+)\n', r'\n\n\1\n\n', cleaned)
        
        # Remove excessive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        # Ensure lists have proper formatting
        cleaned = re.sub(r'\n(\d+\.)([^\s])', r'\n\1 \2', cleaned)
        cleaned = re.sub(r'\n([-*])([^\s])', r'\n\1 \2', cleaned)
        
        return cleaned.strip()
    
    async def convert_with_fallback(
        self,
        pdf_text: str,
        filename: str,
        project_context: Optional[str] = None
    ) -> str:
        """Convert PDF text to markdown with fallback to plain text.
        
        This method attempts LLM conversion first, and falls back to
        structured plain text if LLM conversion fails.
        
        Args:
            pdf_text: Raw text from PDF
            filename: Original filename
            project_context: Optional project context
            
        Returns:
            Structured requirements content (markdown or formatted text)
        """
        try:
            # Try LLM conversion first
            return await self.convert_pdf_text_to_markdown(pdf_text, filename, project_context)
        except (LLMConversionError, MarkdownValidationError) as e:
            logger.warning(f"LLM conversion failed, falling back to plain text: {e}")
            return self.create_fallback_markdown(pdf_text, filename)
    
    def create_fallback_markdown(self, pdf_text: str, filename: str) -> str:
        """Create a basic markdown structure from plain text as fallback.
        
        Args:
            pdf_text: Raw text from PDF
            filename: Original filename
            
        Returns:
            Basic markdown formatted content
        """
        # Create a basic markdown structure
        fallback_content = f"""# Requirements Document

*Converted from: {filename}*

## Overview

This document contains requirements extracted from the uploaded PDF file. The content has been preserved in its original form for manual review and structuring.

## Content

{pdf_text}

---

*Note: This document was automatically generated from a PDF file. Please review and structure the content as needed.*
"""
        
        return fallback_content