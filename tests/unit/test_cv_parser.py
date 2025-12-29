"""
Unit tests for CV Parser module.

Tests:
- PDF text extraction
- DOCX text extraction
- Text preprocessing and sanitization
- Handling of malformed files
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.unit
class TestCVParser:
    """Unit tests for CV Parser functionality."""

    def test_extract_text_from_pdf_success(self, test_pdf_path):
        """Test successful PDF text extraction."""
        from tools.cv_parser import extract_text_from_pdf
        
        if test_pdf_path is None:
            pytest.skip("PDF test file not available")
        
        with open(test_pdf_path, "rb") as f:
            text = extract_text_from_pdf(f)
        
        assert text is not None
        assert len(text) > 0

    def test_extract_text_from_pdf_handles_empty_file(self):
        """Test PDF extraction handles empty or invalid files."""
        from tools.cv_parser import extract_text_from_pdf
        import io
        
        # Create an empty bytes buffer
        empty_buffer = io.BytesIO(b"")
        
        with pytest.raises(Exception):
            extract_text_from_pdf(empty_buffer)

    @patch('tools.cv_parser.docx.Document')
    def test_extract_text_from_docx_success(self, mock_document):
        """Test successful DOCX text extraction."""
        from tools.cv_parser import extract_text_from_docx
        import io
        
        # Mock the document paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "John Doe - Software Engineer"
        mock_para2 = MagicMock()
        mock_para2.text = "Skills: Python, FastAPI"
        
        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc_instance
        
        buffer = io.BytesIO(b"fake docx content")
        text = extract_text_from_docx(buffer)
        
        assert "John Doe" in text
        assert "Python" in text

    def test_text_preprocessing_removes_extra_whitespace(self, sample_cv_text):
        """Test that preprocessing removes excessive whitespace."""
        from tools.cv_parser import preprocess_text
        
        text_with_extra_spaces = "John   Doe\n\n\n\nSoftware    Engineer"
        processed = preprocess_text(text_with_extra_spaces)
        
        # Should not have multiple consecutive spaces or newlines
        assert "   " not in processed
        assert "\n\n\n" not in processed

    def test_text_preprocessing_preserves_content(self):
        """Test that preprocessing preserves important content."""
        from tools.cv_parser import preprocess_text
        
        original_text = "Python FastAPI Machine Learning AWS Docker"
        processed = preprocess_text(original_text)
        
        # All keywords should be preserved
        for keyword in ["Python", "FastAPI", "Machine Learning", "AWS", "Docker"]:
            assert keyword in processed

    def test_cv_parser_detects_file_type(self):
        """Test that CV parser detects file type correctly."""
        from tools.cv_parser import detect_file_type
        
        assert detect_file_type("resume.pdf") == "pdf"
        assert detect_file_type("resume.docx") == "docx"
        assert detect_file_type("resume.doc") == "doc"
        assert detect_file_type("resume.txt") == "txt"

    def test_cv_parser_rejects_invalid_file_type(self):
        """Test that CV parser rejects unsupported file types."""
        from tools.cv_parser import detect_file_type
        
        with pytest.raises(ValueError):
            detect_file_type("resume.exe")
        
        with pytest.raises(ValueError):
            detect_file_type("resume.jpg")


@pytest.mark.unit
class TestTextSanitization:
    """Tests for text sanitization functionality."""

    def test_removes_non_printable_characters(self):
        """Test removal of non-printable characters."""
        from tools.cv_parser import sanitize_text
        
        text_with_special_chars = "John Doe\x00\x01\x02 Software Engineer"
        sanitized = sanitize_text(text_with_special_chars)
        
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "John Doe" in sanitized

    def test_normalizes_unicode_characters(self):
        """Test Unicode normalization."""
        from tools.cv_parser import sanitize_text
        
        # Text with various Unicode formats
        text = "résumé café naïve"
        sanitized = sanitize_text(text)
        
        # Should handle Unicode gracefully
        assert len(sanitized) > 0

    def test_handles_empty_input(self):
        """Test handling of empty input."""
        from tools.cv_parser import sanitize_text
        
        assert sanitize_text("") == ""
        assert sanitize_text(None) == "" or sanitize_text(None) is None
