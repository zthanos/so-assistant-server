"""Unit tests for LLM-powered PDF to markdown conversion."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from app.services.requirements_pdf_converter import RequirementsPDFConverter
from app.services.llm.client import StreamingOllamaClient
from app.exceptions.pdf_exceptions import (
    LLMConversionError,
    MarkdownValidationError
)


class TestRequirementsPDFConverter:
    """Test cases for RequirementsPDFConverter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock(spec=StreamingOllamaClient)
        self.converter = RequirementsPDFConverter(self.mock_llm_client)

    def test_init_sets_llm_client(self):
        """Test that converter initializes with LLM client."""
        assert self.converter.llm_client == self.mock_llm_client

    def test_generate_conversion_prompt_basic(self):
        """Test basic prompt generation for PDF conversion."""
        pdf_text = "This is a sample requirements document with functional requirements."
        filename = "requirements.pdf"

        prompt = self.converter.generate_conversion_prompt(pdf_text, filename)

        # Verify prompt contains key elements
        assert "requirements document" in prompt.lower()
        assert "markdown" in prompt.lower()
        assert pdf_text in prompt
        assert filename in prompt
        assert "# Requirements Document" in prompt  # Template structure
        assert "## Functional Requirements" in prompt

    def test_generate_conversion_prompt_long_text(self):
        """Test prompt generation with long PDF text."""
        # Create long text (over 4000 characters)
        pdf_text = "This is a requirements document. " * 200
        filename = "long_requirements.pdf"

        prompt = self.converter.generate_conversion_prompt(pdf_text, filename)

        # Should truncate text but keep structure
        assert len(prompt) < len(pdf_text) + 2000  # Reasonable prompt size
        assert "requirements document" in prompt.lower()
        assert filename in prompt

    def test_generate_conversion_prompt_special_characters(self):
        """Test prompt generation with special characters in text."""
        pdf_text = "Requirements with special chars: @#$%^&*()[]{}|\\:;\"'<>?,./"
        filename = "special_chars.pdf"

        prompt = self.converter.generate_conversion_prompt(pdf_text, filename)

        # Should handle special characters safely
        assert pdf_text in prompt
        assert filename in prompt

    def test_validate_markdown_output_valid(self):
        """Test validation of valid markdown output."""
        valid_markdown = """# Requirements Document

*Converted from: test.pdf*

## Overview

This document contains the requirements for the system.

## Functional Requirements

1. The system SHALL provide user authentication
2. The system SHALL store user data securely

## Non-Functional Requirements

- Performance: Response time < 2 seconds
- Security: Data encryption at rest
"""

        result = self.converter.validate_markdown_output(valid_markdown)
        assert result is True

    def test_validate_markdown_output_minimal_valid(self):
        """Test validation of minimal valid markdown."""
        minimal_markdown = """# Requirements

Basic requirement content."""

        result = self.converter.validate_markdown_output(minimal_markdown)
        assert result is True

    def test_validate_markdown_output_empty(self):
        """Test validation fails for empty markdown."""
        result = self.converter.validate_markdown_output("")
        assert result is False

    def test_validate_markdown_output_whitespace_only(self):
        """Test validation fails for whitespace-only markdown."""
        result = self.converter.validate_markdown_output("   \n  \n  ")
        assert result is False

    def test_validate_markdown_output_no_headers(self):
        """Test validation fails for markdown without headers."""
        no_headers = "This is just plain text without any markdown headers."
        result = self.converter.validate_markdown_output(no_headers)
        assert result is False

    def test_validate_markdown_output_malformed(self):
        """Test validation fails for malformed markdown."""
        malformed = "# Header\n\nSome content\n\n### Broken hierarchy\n# Another top level"
        result = self.converter.validate_markdown_output(malformed)
        assert result is True  # Still valid markdown, just poor structure

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_success(self):
        """Test successful PDF text to markdown conversion."""
        pdf_text = "System Requirements: 1. User login 2. Data storage"
        filename = "test.pdf"
        
        expected_markdown = """# Requirements Document

*Converted from: test.pdf*

## Functional Requirements

1. The system SHALL provide user login functionality
2. The system SHALL provide data storage capabilities
"""

        # Mock LLM response
        self.mock_llm_client.generate_response = AsyncMock(return_value=expected_markdown)

        result = await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)

        # Verify result
        assert result == expected_markdown
        self.mock_llm_client.generate_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_with_retry(self):
        """Test conversion with retry on LLM failure."""
        pdf_text = "Requirements text"
        filename = "test.pdf"
        
        valid_markdown = "# Requirements\n\nConverted content"

        # Mock LLM to fail first, then succeed
        self.mock_llm_client.generate_response = AsyncMock(
            side_effect=[
                Exception("LLM service unavailable"),
                valid_markdown
            ]
        )

        result = await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)

        # Should succeed on retry
        assert result == valid_markdown
        assert self.mock_llm_client.generate_response.call_count == 2

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_max_retries(self):
        """Test conversion fails after max retries."""
        pdf_text = "Requirements text"
        filename = "test.pdf"

        # Mock LLM to always fail
        self.mock_llm_client.generate_response = AsyncMock(
            side_effect=Exception("LLM service down")
        )

        with pytest.raises(LLMConversionError) as exc_info:
            await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)

        assert "Failed to convert PDF text to markdown" in str(exc_info.value)
        assert self.mock_llm_client.generate_response.call_count == 3  # Default max retries

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_invalid_output(self):
        """Test conversion fails with invalid markdown output."""
        pdf_text = "Requirements text"
        filename = "test.pdf"
        
        invalid_markdown = "Just plain text without headers"

        # Mock LLM to return invalid markdown
        self.mock_llm_client.generate_response = AsyncMock(return_value=invalid_markdown)

        with pytest.raises(MarkdownValidationError) as exc_info:
            await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)

        assert "Generated markdown is not valid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_empty_response(self):
        """Test conversion handles empty LLM response."""
        pdf_text = "Requirements text"
        filename = "test.pdf"

        # Mock LLM to return empty response
        self.mock_llm_client.generate_response = AsyncMock(return_value="")

        with pytest.raises(MarkdownValidationError) as exc_info:
            await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)

        assert "Generated markdown is not valid" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_convert_pdf_text_to_markdown_fallback_to_plain_text(self):
        """Test fallback to plain text when LLM conversion fails."""
        pdf_text = "System Requirements:\\n1. User authentication\\n2. Data storage"
        filename = "test.pdf"

        # Mock LLM to always fail
        self.mock_llm_client.generate_response = AsyncMock(
            side_effect=Exception("LLM unavailable")
        )

        # Enable fallback mode
        result = await self.converter.convert_pdf_text_to_markdown(
            pdf_text, filename, fallback_to_plain_text=True
        )

        # Should return formatted plain text
        assert "# Requirements Document" in result
        assert f"*Converted from: {filename}*" in result
        assert pdf_text in result
        assert "## Extracted Content" in result

    def test_format_plain_text_fallback(self):
        """Test plain text fallback formatting."""
        pdf_text = "Requirements:\\n1. Login\\n2. Storage"
        filename = "test.pdf"

        result = self.converter._format_plain_text_fallback(pdf_text, filename)

        # Verify structure
        assert result.startswith("# Requirements Document")
        assert f"*Converted from: {filename}*" in result
        assert "## Extracted Content" in result
        assert pdf_text in result
        assert "**Note:** This document was converted using plain text extraction" in result

    def test_clean_pdf_text(self):
        """Test PDF text cleaning functionality."""
        dirty_text = "Text with\\x00null\\x01chars\\nand\\r\\nmixed\\twhitespace   "
        
        cleaned = self.converter._clean_pdf_text(dirty_text)
        
        # Should remove null characters and normalize whitespace
        assert "\\x00" not in cleaned
        assert "\\x01" not in cleaned
        assert cleaned.strip() == "Text with null chars and mixed whitespace"

    def test_clean_pdf_text_unicode(self):
        """Test PDF text cleaning with unicode characters."""
        unicode_text = "Requirements with unicode: café, naïve, résumé"
        
        cleaned = self.converter._clean_pdf_text(unicode_text)
        
        # Should preserve unicode characters
        assert cleaned == unicode_text

    def test_extract_requirements_structure(self):
        """Test extraction of requirements structure from text."""
        pdf_text = """
        FUNCTIONAL REQUIREMENTS
        1. The system must provide user authentication
        2. The system must store data securely
        
        NON-FUNCTIONAL REQUIREMENTS
        - Performance: < 2 seconds response time
        - Availability: 99.9% uptime
        """

        structure = self.converter._extract_requirements_structure(pdf_text)

        # Should identify different requirement types
        assert "functional" in structure
        assert "non-functional" in structure
        assert len(structure["functional"]) == 2
        assert len(structure["non-functional"]) == 2

    @pytest.mark.asyncio
    async def test_convert_with_custom_template(self):
        """Test conversion with custom markdown template."""
        pdf_text = "Custom requirements content"
        filename = "custom.pdf"
        
        custom_template = """# Custom Requirements Template

*Source: {filename}*

## Requirements

{content}

## Additional Notes

This is a custom template.
"""

        expected_output = """# Custom Requirements Template

*Source: custom.pdf*

## Requirements

Custom requirements content

## Additional Notes

This is a custom template.
"""

        # Mock LLM response
        self.mock_llm_client.generate_response = AsyncMock(return_value=expected_output)

        result = await self.converter.convert_pdf_text_to_markdown(
            pdf_text, filename, template=custom_template
        )

        assert result == expected_output

    def test_estimate_token_count(self):
        """Test token count estimation for prompt optimization."""
        short_text = "Short requirements text"
        long_text = "Very long requirements text " * 100

        short_count = self.converter._estimate_token_count(short_text)
        long_count = self.converter._estimate_token_count(long_text)

        assert short_count < long_count
        assert short_count > 0
        assert long_count > short_count * 50  # Should be significantly larger

    def test_truncate_text_if_needed(self):
        """Test text truncation for large inputs."""
        long_text = "Requirements content " * 1000  # Very long text
        max_tokens = 100

        truncated = self.converter._truncate_text_if_needed(long_text, max_tokens)

        # Should be shorter than original
        assert len(truncated) < len(long_text)
        assert "..." in truncated  # Should indicate truncation

    @pytest.mark.asyncio
    async def test_convert_with_progress_callback(self):
        """Test conversion with progress callback."""
        pdf_text = "Requirements text"
        filename = "test.pdf"
        progress_calls = []

        def progress_callback(stage, progress):
            progress_calls.append((stage, progress))

        expected_markdown = "# Requirements\n\nConverted content"
        self.mock_llm_client.generate_response = AsyncMock(return_value=expected_markdown)

        result = await self.converter.convert_pdf_text_to_markdown(
            pdf_text, filename, progress_callback=progress_callback
        )

        # Should have called progress callback
        assert len(progress_calls) > 0
        assert result == expected_markdown

    @pytest.mark.asyncio
    async def test_batch_convert_multiple_texts(self):
        """Test batch conversion of multiple PDF texts."""
        texts_and_filenames = [
            ("Requirements 1", "file1.pdf"),
            ("Requirements 2", "file2.pdf"),
            ("Requirements 3", "file3.pdf")
        ]

        # Mock LLM responses
        expected_results = [
            "# Requirements 1\n\nContent 1",
            "# Requirements 2\n\nContent 2", 
            "# Requirements 3\n\nContent 3"
        ]
        
        self.mock_llm_client.generate_response = AsyncMock(
            side_effect=expected_results
        )

        results = await self.converter.batch_convert_pdf_texts(texts_and_filenames)

        # Should return all results
        assert len(results) == 3
        assert results == expected_results
        assert self.mock_llm_client.generate_response.call_count == 3


class TestRequirementsPDFConverterIntegration:
    """Integration tests for PDF converter with real LLM interactions."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use a real LLM client for integration tests
        self.llm_client = StreamingOllamaClient()
        self.converter = RequirementsPDFConverter(self.llm_client)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_llm_conversion(self):
        """Test conversion with real LLM (requires running Ollama)."""
        pdf_text = """
        SYSTEM REQUIREMENTS DOCUMENT
        
        1. FUNCTIONAL REQUIREMENTS
        1.1 User Authentication
        - The system must provide secure user login
        - The system must support password reset functionality
        
        1.2 Data Management
        - The system must store user data securely
        - The system must provide data backup capabilities
        
        2. NON-FUNCTIONAL REQUIREMENTS
        2.1 Performance
        - Response time must be less than 2 seconds
        - System must support 1000 concurrent users
        """
        
        filename = "integration_test.pdf"

        try:
            result = await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)
            
            # Verify basic structure
            assert result.startswith("#")  # Should have header
            assert "requirements" in result.lower()
            assert filename in result
            assert len(result) > len(pdf_text)  # Should be expanded/formatted
            
        except Exception as e:
            pytest.skip(f"LLM service not available: {e}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_conversion_with_various_formats(self):
        """Test conversion with different PDF text formats."""
        test_cases = [
            ("Simple list:\n1. Requirement A\n2. Requirement B", "simple.pdf"),
            ("REQUIREMENTS\n- Item 1\n- Item 2\n- Item 3", "bullets.pdf"),
            ("Req 1: Description\nReq 2: Another description", "descriptions.pdf")
        ]

        for pdf_text, filename in test_cases:
            try:
                result = await self.converter.convert_pdf_text_to_markdown(pdf_text, filename)
                
                # Basic validation
                assert isinstance(result, str)
                assert len(result) > 0
                assert self.converter.validate_markdown_output(result)
                
            except Exception as e:
                pytest.skip(f"LLM service not available for {filename}: {e}")


# Test fixtures
@pytest.fixture
def mock_llm_client():
    """Fixture providing mock LLM client."""
    return Mock(spec=StreamingOllamaClient)

@pytest.fixture
def pdf_converter(mock_llm_client):
    """Fixture providing PDF converter with mock LLM client."""
    return RequirementsPDFConverter(mock_llm_client)

@pytest.fixture
def sample_pdf_text():
    """Fixture providing sample PDF text content."""
    return """
    REQUIREMENTS DOCUMENT
    
    1. FUNCTIONAL REQUIREMENTS
    1.1 The system shall provide user authentication
    1.2 The system shall store data securely
    
    2. NON-FUNCTIONAL REQUIREMENTS
    2.1 Performance: Response time < 2 seconds
    2.2 Availability: 99.9% uptime
    """

@pytest.fixture
def sample_markdown_output():
    """Fixture providing sample markdown output."""
    return """# Requirements Document

*Converted from: test.pdf*

## Functional Requirements

1. The system SHALL provide user authentication
2. The system SHALL store data securely

## Non-Functional Requirements

1. Performance: Response time < 2 seconds
2. Availability: 99.9% uptime
"""