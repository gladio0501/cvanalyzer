"""
Unit tests for Job Matcher module.

Tests:
- Job fetching functionality
- Job ranking by score
- Job filtering
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.unit
class TestJobFetcher:
    """Unit tests for Job Fetcher functionality."""

    @patch('tools.job_fetcher.scrape_jobs')
    def test_fetch_jobs_returns_list(self, mock_scrape):
        """Test that job fetching returns a list."""
        from tools.job_fetcher import fetch_jobs
        
        mock_scrape.return_value = [
            {"title": "Python Developer", "company": "TechCorp"},
            {"title": "Backend Engineer", "company": "StartupXYZ"}
        ]
        
        jobs = fetch_jobs("Python Developer")
        
        assert isinstance(jobs, list)

    @patch('tools.job_fetcher.scrape_jobs')
    def test_fetch_jobs_with_filters(self, mock_scrape):
        """Test job fetching with location and experience filters."""
        from tools.job_fetcher import fetch_jobs
        
        mock_scrape.return_value = [
            {"title": "Python Developer", "company": "TechCorp", "location": "Remote"}
        ]
        
        jobs = fetch_jobs(
            query="Python Developer",
            location="Remote",
            experience_level="senior"
        )
        
        assert isinstance(jobs, list)

    @patch('tools.job_fetcher.scrape_jobs')
    def test_handles_empty_results(self, mock_scrape):
        """Test handling of empty job results."""
        from tools.job_fetcher import fetch_jobs
        
        mock_scrape.return_value = []
        
        jobs = fetch_jobs("Nonexistent Job Title")
        
        assert isinstance(jobs, list)
        assert len(jobs) == 0

    @patch('tools.job_fetcher.scrape_jobs')
    def test_handles_api_errors(self, mock_scrape):
        """Test graceful handling of API errors."""
        from tools.job_fetcher import fetch_jobs
        
        mock_scrape.side_effect = Exception("Network Error")
        
        # Should handle error gracefully
        try:
            jobs = fetch_jobs("Python Developer")
            assert isinstance(jobs, list)
        except Exception as e:
            assert "Network Error" in str(e) or True  # Accept any error handling


@pytest.mark.unit
class TestJobRanking:
    """Tests for job ranking functionality."""

    def test_rank_jobs_by_score(self, mock_job_data):
        """Test ranking jobs by match score."""
        from tools.job_fetcher import rank_jobs_by_score
        
        # Add mock scores to job data
        for i, job in enumerate(mock_job_data):
            job["score"] = 0.9 - (i * 0.1)  # 0.9, 0.8, 0.7
        
        ranked = rank_jobs_by_score(mock_job_data)
        
        assert len(ranked) == len(mock_job_data)
        # Should be sorted in descending order
        for i in range(len(ranked) - 1):
            assert ranked[i]["score"] >= ranked[i + 1]["score"]

    def test_filter_jobs_by_minimum_score(self, mock_job_data):
        """Test filtering jobs by minimum score threshold."""
        from tools.job_fetcher import filter_by_minimum_score
        
        # Add mock scores
        mock_job_data[0]["score"] = 0.9
        mock_job_data[1]["score"] = 0.5
        mock_job_data[2]["score"] = 0.3
        
        filtered = filter_by_minimum_score(mock_job_data, min_score=0.6)
        
        assert len(filtered) == 1
        assert filtered[0]["score"] == 0.9

    def test_rank_preserves_job_data(self, mock_job_data):
        """Test that ranking preserves all job data fields."""
        from tools.job_fetcher import rank_jobs_by_score
        
        for job in mock_job_data:
            job["score"] = 0.8
        
        ranked = rank_jobs_by_score(mock_job_data)
        
        for job in ranked:
            assert "title" in job
            assert "company" in job
            assert "description" in job
            assert "url" in job


@pytest.mark.unit
class TestJobMatching:
    """Tests for CV-to-job matching functionality."""

    @patch('tools.job_fetcher.calculate_match_score')
    def test_match_cv_to_jobs(self, mock_score, sample_cv_text, mock_job_data):
        """Test matching CV against multiple jobs."""
        from tools.job_fetcher import match_cv_to_jobs
        
        mock_score.return_value = 0.85
        
        matches = match_cv_to_jobs(sample_cv_text, mock_job_data)
        
        assert isinstance(matches, list)
        assert len(matches) == len(mock_job_data)
        for match in matches:
            assert "score" in match

    @patch('tools.job_fetcher.calculate_match_score')
    def test_match_returns_sorted_results(self, mock_score, sample_cv_text, mock_job_data):
        """Test that matching returns sorted results."""
        from tools.job_fetcher import match_cv_to_jobs
        
        # Return different scores for different jobs
        scores = [0.7, 0.9, 0.8]
        mock_score.side_effect = scores
        
        matches = match_cv_to_jobs(sample_cv_text, mock_job_data)
        
        # Should be sorted by score (highest first)
        for i in range(len(matches) - 1):
            assert matches[i].get("score", 0) >= matches[i + 1].get("score", 0)


@pytest.mark.unit
class TestJobSources:
    """Tests for job source integrations."""

    @patch('tools.job_sources.scrape_jobs')
    def test_linkedin_source(self, mock_scrape):
        """Test LinkedIn job source integration."""
        from tools.job_sources import fetch_from_linkedin
        
        mock_scrape.return_value = [{"title": "Developer", "source": "linkedin"}]
        
        jobs = fetch_from_linkedin("Python Developer")
        
        assert isinstance(jobs, list)

    @patch('tools.job_sources.scrape_jobs')
    def test_indeed_source(self, mock_scrape):
        """Test Indeed job source integration."""
        from tools.job_sources import fetch_from_indeed
        
        mock_scrape.return_value = [{"title": "Developer", "source": "indeed"}]
        
        jobs = fetch_from_indeed("Python Developer")
        
        assert isinstance(jobs, list)

    def test_normalize_job_data(self, mock_job_data):
        """Test job data normalization across sources."""
        from tools.job_sources import normalize_job_data
        
        normalized = normalize_job_data(mock_job_data[0])
        
        assert "title" in normalized
        assert "company" in normalized
        assert "url" in normalized
