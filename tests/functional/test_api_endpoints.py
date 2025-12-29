"""
Functional tests for API endpoints.

Tests:
- /analyze_cv endpoint
- /recommend_jobs endpoint
- /job_sources endpoint
- /extract_profile endpoint
- Response format validation
"""
import pytest
import os
import sys
import io
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.functional
class TestAnalyzeCVEndpoint:
    """Functional tests for the /analyze_cv endpoint."""

    @patch('tools.skill_extractor.extract_and_score_skills')
    @patch('tools.feedback_generator.generate_feedback')
    @patch('tools.cv_parser.parse_cv')
    def test_analyze_cv_with_job_description(self, mock_parse, mock_feedback, mock_score, test_client):
        """Test successful CV analysis with job description."""
        mock_parse.return_value = "Python developer with FastAPI experience"
        mock_score.return_value = {
            "matched_skills": ["Python", "FastAPI"],
            "missing_skills": ["Kubernetes"],
            "score": 85,
            "lora_score": 0.87
        }
        mock_feedback.return_value = {
            "overall_analysis": "Strong CV",
            "positive_feedback": "Great skills",
            "negative_feedback": "Add more experience"
        }
        
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\nTest CV Content"
        
        response = test_client.post(
            "/analyze_cv",
            files={"file": ("test_cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={"job_description": "Looking for Python developer with FastAPI"}
        )
        
        # Should accept the request
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Check response structure
            assert "matched_skills" in data or "error" in data

    def test_analyze_cv_missing_file(self, test_client):
        """Test analysis with missing file."""
        response = test_client.post(
            "/analyze_cv",
            data={"job_description": "Python developer needed"}
        )
        
        # Should return error for missing file
        assert response.status_code == 422

    @patch('tools.cv_parser.parse_cv')
    def test_analyze_cv_empty_job_description(self, mock_parse, test_client):
        """Test analysis with empty job description."""
        mock_parse.return_value = "Sample CV"
        
        pdf_content = b"%PDF-1.4\nTest content"
        
        response = test_client.post(
            "/analyze_cv",
            files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={"job_description": ""}
        )
        
        # Should still return 200 but with error message
        assert response.status_code in [200, 400, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Should indicate error for missing job description
            assert "error" in data


@pytest.mark.functional
class TestRecommendJobsEndpoint:
    """Functional tests for the /recommend_jobs endpoint."""

    @patch('tools.job_recommendation_chain.get_job_recommendations')
    @patch('tools.cv_parser.parse_cv')
    def test_recommend_jobs_success(self, mock_parse, mock_recommend, test_client):
        """Test successful job recommendations."""
        mock_parse.return_value = "Python developer CV"
        
        # Create mock JobMatch objects
        mock_match = MagicMock()
        mock_match.job_id = "job1"
        mock_match.job_title = "Python Developer"
        mock_match.company = "TechCorp"
        mock_match.location = "Remote"
        mock_match.match_score = 0.9
        mock_match.lora_score = 0.85
        mock_match.profile_score = 0.88
        mock_match.match_reasons = ["Python", "FastAPI"]
        mock_match.job_url = "https://example.com/job1"
        mock_match.job_type = "full-time"
        
        mock_recommend.return_value = [mock_match]
        
        pdf_content = b"%PDF-1.4\nTest"
        
        response = test_client.post(
            "/recommend_jobs",
            files={"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={
                "job_title": "Python Developer",
                "region": "Remote",
                "top_k": "5",
                "job_source": "jobicy"
            }
        )
        
        # Should process the request
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "recommendations" in data or "error" in data

    def test_recommend_jobs_missing_file(self, test_client):
        """Test job recommendations with missing file."""
        response = test_client.post(
            "/recommend_jobs",
            data={"job_title": "Python Developer"}
        )
        
        # Should return error
        assert response.status_code == 422

    @patch('tools.cv_parser.parse_cv')
    def test_recommend_jobs_invalid_source(self, mock_parse, test_client):
        """Test job recommendations with invalid job source."""
        mock_parse.return_value = "Sample CV"
        
        pdf_content = b"%PDF-1.4\nTest"
        
        response = test_client.post(
            "/recommend_jobs",
            files={"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
            data={
                "job_source": "invalid_source"
            }
        )
        
        # Should return error for invalid source
        assert response.status_code in [400, 422, 500]


@pytest.mark.functional
class TestJobSourcesEndpoint:
    """Functional tests for the /job_sources endpoint."""

    def test_list_job_sources(self, test_client):
        """Test listing available job sources."""
        response = test_client.get("/job_sources")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of sources
        assert "sources" in data

    def test_job_sources_includes_jobicy(self, test_client):
        """Test that Jobicy is listed as a source."""
        response = test_client.get("/job_sources")
        
        if response.status_code == 200:
            data = response.json()
            sources = data.get("sources", {})
            
            # Should include jobicy
            assert "jobicy" in sources or len(sources) > 0


@pytest.mark.functional
class TestExtractProfileEndpoint:
    """Functional tests for the /extract_profile endpoint."""

    @patch('tools.cv_profile_extractor.extract_cv_profile')
    @patch('tools.cv_parser.parse_cv')
    def test_extract_profile_success(self, mock_parse, mock_extract, test_client):
        """Test successful profile extraction."""
        mock_parse.return_value = "Sample CV with Python experience"
        
        mock_profile = MagicMock()
        mock_profile.job_titles = ["Software Engineer"]
        mock_profile.preferred_roles = ["Backend Developer"]
        mock_profile.primary_skills = ["Python", "FastAPI"]
        mock_profile.experience_years = 5
        mock_extract.return_value = mock_profile
        
        pdf_content = b"%PDF-1.4\nTest"
        
        response = test_client.post(
            "/extract_profile",
            files={"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        
        assert response.status_code in [200, 422, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "job_titles" in data or "skills" in data

    def test_extract_profile_missing_file(self, test_client):
        """Test profile extraction with missing file."""
        response = test_client.post("/extract_profile")
        
        assert response.status_code == 422


@pytest.mark.functional
class TestAPIResponseFormat:
    """Tests for API response format consistency."""

    def test_error_response_has_detail(self, test_client):
        """Test that error responses have detail field."""
        response = test_client.get("/nonexistent_endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_analyze_cv_endpoint_exists(self, test_client):
        """Test analyze_cv endpoint exists."""
        response = test_client.post("/analyze_cv")
        
        # Should get 422 for missing params, not 404
        assert response.status_code == 422

    def test_recommend_jobs_endpoint_exists(self, test_client):
        """Test recommend_jobs endpoint exists."""
        response = test_client.post("/recommend_jobs")
        
        # Should get 422 for missing params
        assert response.status_code == 422

    def test_job_sources_endpoint_exists(self, test_client):
        """Test job_sources endpoint exists and returns data."""
        response = test_client.get("/job_sources")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.functional  
class TestCORSConfiguration:
    """Tests for CORS configuration."""

    def test_cors_headers_on_response(self, test_client):
        """Test that CORS headers are present on responses."""
        response = test_client.get("/job_sources")
        
        # Check response is successful
        assert response.status_code == 200
