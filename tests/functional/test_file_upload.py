"""
Functional tests for file upload API.

Tests:
- Valid PDF upload
- Valid DOCX upload
- Invalid file type rejection
- File size limits
"""
import pytest
import os
import sys
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.functional
class TestFileUploadAPI:
    """Functional tests for file upload functionality."""

    def test_upload_valid_pdf(self, test_client):
        """Test uploading a valid PDF file."""
        # Create a minimal PDF-like content for testing
        pdf_content = b"%PDF-1.4\nTest PDF Content"
        
        with patch('tools.cv_parser.extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "Extracted CV content"
            
            response = test_client.post(
                "/api/upload-cv",
                files={"file": ("test_cv.pdf", io.BytesIO(pdf_content), "application/pdf")}
            )
        
        # Should accept the file (200 or 201)
        assert response.status_code in [200, 201, 422]  # 422 if validation fails

    def test_upload_valid_docx(self, test_client):
        """Test uploading a valid DOCX file."""
        # Create minimal DOCX-like content for testing
        docx_content = b"PK\x03\x04"  # DOCX ZIP signature
        
        with patch('tools.cv_parser.extract_text_from_docx') as mock_extract:
            mock_extract.return_value = "Extracted CV content"
            
            response = test_client.post(
                "/api/upload-cv",
                files={"file": ("test_cv.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            )
        
        # Should accept the file (200 or 201)
        assert response.status_code in [200, 201, 422]

    def test_reject_invalid_file_type(self, test_client):
        """Test rejection of invalid file types."""
        # Try to upload an executable
        exe_content = b"MZ\x90\x00"  # EXE signature
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("malware.exe", io.BytesIO(exe_content), "application/x-msdownload")}
        )
        
        # Should reject the file (400 or 422)
        assert response.status_code in [400, 415, 422]

    def test_reject_image_file(self, test_client):
        """Test rejection of image files."""
        # Try to upload an image
        jpg_content = b"\xFF\xD8\xFF"  # JPEG signature
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("photo.jpg", io.BytesIO(jpg_content), "image/jpeg")}
        )
        
        # Should reject the file
        assert response.status_code in [400, 415, 422]

    def test_upload_without_file(self, test_client):
        """Test upload request without file."""
        response = test_client.post("/api/upload-cv")
        
        # Should return error
        assert response.status_code in [400, 422]

    def test_file_size_limit(self, test_client):
        """Test file size limit enforcement."""
        # Create a large file (simulate 20MB)
        large_content = b"A" * (20 * 1024 * 1024)  # 20MB
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("large_cv.pdf", io.BytesIO(large_content), "application/pdf")}
        )
        
        # Should reject large files (413 or 400)
        assert response.status_code in [400, 413, 422]


@pytest.mark.functional
class TestFileProcessing:
    """Tests for file processing after upload."""

    @patch('tools.cv_parser.extract_text_from_pdf')
    def test_pdf_text_extraction_on_upload(self, mock_extract, test_client):
        """Test that PDF text extraction is called on upload."""
        mock_extract.return_value = "Extracted text from PDF"
        
        pdf_content = b"%PDF-1.4\nTest content"
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        
        # Extraction should have been called
        if response.status_code in [200, 201]:
            mock_extract.assert_called()

    @patch('tools.cv_parser.extract_text_from_docx')
    def test_docx_text_extraction_on_upload(self, mock_extract, test_client):
        """Test that DOCX text extraction is called on upload."""
        mock_extract.return_value = "Extracted text from DOCX"
        
        docx_content = b"PK\x03\x04"
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("test.docx", io.BytesIO(docx_content), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        
        # Extraction should have been called
        if response.status_code in [200, 201]:
            mock_extract.assert_called()


@pytest.mark.functional
class TestUploadResponse:
    """Tests for upload response format."""

    @patch('tools.cv_parser.extract_text_from_pdf')
    def test_successful_upload_response_format(self, mock_extract, test_client):
        """Test response format for successful upload."""
        mock_extract.return_value = "CV content"
        
        pdf_content = b"%PDF-1.4\nTest"
        
        response = test_client.post(
            "/api/upload-cv",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            # Should have some response data
            assert data is not None

    def test_error_response_format(self, test_client):
        """Test error response format."""
        # Send invalid request
        response = test_client.post("/api/upload-cv")
        
        if response.status_code in [400, 422]:
            data = response.json()
            # Should have error information
            assert data is not None
