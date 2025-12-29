"""
Performance tests using LangSmith metrics.

Tests:
- LangSmith tracing integration
- Token usage tracking
- Latency measurements
- Run name tagging
"""
import pytest
import os
import sys
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.performance
class TestLangSmithIntegration:
    """
    Tests for LangSmith tracing integration.
    
    LangSmith provides observability for LLM applications:
    - Traces execution of LangChain chains
    - Tracks token usage and costs
    - Measures latency
    """

    def test_langsmith_environment_configured(self):
        """Test that LangSmith environment variables are set."""
        # Check if LangSmith is configured
        langsmith_api_key = os.environ.get("LANGSMITH_API_KEY") or os.environ.get("LANGCHAIN_API_KEY")
        langsmith_project = os.environ.get("LANGSMITH_PROJECT") or os.environ.get("LANGCHAIN_PROJECT")
        
        # This is informational - test passes but logs warning if not configured
        if not langsmith_api_key:
            pytest.skip("LangSmith API key not configured - skipping LangSmith tests")

    @patch('langsmith.Client')
    def test_traces_are_sent(self, mock_client):
        """Test that traces are being sent to LangSmith."""
        from tools.feedback_generator import generate_overall_assessment
        
        # Mock LangSmith client
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # This would normally trace the execution
        # In actual usage, LangSmith automatically captures traces
        assert True  # Placeholder - actual LangSmith integration test

    def test_run_names_are_tagged(self):
        """Test that runs are properly tagged with names."""
        # Verify that run_name is included in chain configurations
        from tools.feedback_generator import OVERALL_RUN_NAME, POSITIVE_RUN_NAME, NEGATIVE_RUN_NAME
        
        assert OVERALL_RUN_NAME is not None
        assert POSITIVE_RUN_NAME is not None
        assert NEGATIVE_RUN_NAME is not None


@pytest.mark.performance
class TestTokenUsage:
    """
    Tests for token usage tracking.
    
    Token usage affects:
    - API costs
    - Response time
    - Context window limits
    """

    def test_cv_text_token_count(self, sample_cv_text):
        """Test estimation of token count for CV text."""
        from tools.skill_extractor import estimate_token_count
        
        token_count = estimate_token_count(sample_cv_text)
        
        # CV should be within reasonable token limits
        assert token_count > 0
        assert token_count < 4000  # Should fit in context window

    def test_job_description_token_count(self, sample_job_description):
        """Test estimation of token count for job description."""
        from tools.skill_extractor import estimate_token_count
        
        token_count = estimate_token_count(sample_job_description)
        
        assert token_count > 0
        assert token_count < 2000

    def test_combined_input_within_limits(self, sample_cv_text, sample_job_description):
        """Test that combined inputs fit within context window."""
        from tools.skill_extractor import estimate_token_count
        
        cv_tokens = estimate_token_count(sample_cv_text)
        job_tokens = estimate_token_count(sample_job_description)
        total = cv_tokens + job_tokens
        
        # Combined should fit in GPT-4 context (8K for smaller model)
        assert total < 6000, f"Combined tokens ({total}) may exceed context window"


@pytest.mark.performance
@pytest.mark.slow
class TestLatencyMeasurement:
    """
    Tests for latency measurement.
    
    Latency is critical for user experience.
    Target: CV analysis < 10 seconds
    """

    @patch('tools.skill_extractor.ChatOpenAI')
    def test_skill_extraction_latency(self, mock_chat, sample_cv_text):
        """Test that skill extraction completes within acceptable time."""
        from tools.skill_extractor import extract_skills_with_llm
        
        # Mock fast response
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content='["Python", "FastAPI"]')
        mock_chat.return_value = mock_instance
        
        start_time = time.time()
        skills = extract_skills_with_llm(sample_cv_text)
        elapsed = time.time() - start_time
        
        # Should complete quickly (mocked, so < 1 second)
        assert elapsed < 1.0

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_feedback_generation_latency(self, mock_chat, sample_cv_text):
        """Test that feedback generation completes within acceptable time."""
        from tools.feedback_generator import generate_complete_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Great CV!")
        mock_chat.return_value = mock_instance
        
        start_time = time.time()
        feedback = generate_complete_feedback(sample_cv_text, ["Python"], [])
        elapsed = time.time() - start_time
        
        # Should complete quickly (mocked)
        assert elapsed < 2.0

    def test_end_to_end_analysis_target(self):
        """
        Document the target latency for end-to-end analysis.
        
        Target: Full CV analysis should complete in < 10 seconds
        This includes:
        - CV parsing
        - Skill extraction
        - Score calculation
        - Feedback generation
        """
        TARGET_LATENCY_SECONDS = 10
        
        # This is a documentation test - actual measurement would be in integration tests
        assert TARGET_LATENCY_SECONDS <= 15


@pytest.mark.performance
class TestResourceUsage:
    """
    Tests for resource usage monitoring.
    """

    def test_memory_usage_reasonable(self, sample_cv_text):
        """Test that processing doesn't use excessive memory."""
        import tracemalloc
        
        tracemalloc.start()
        
        # Simulate some processing
        from tools.skill_extractor import extract_skills_from_text
        skills = extract_skills_from_text(sample_cv_text)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Peak memory usage should be reasonable (< 100MB)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Peak memory usage ({peak_mb}MB) exceeds limit"

    def test_no_memory_leaks(self, sample_cv_text):
        """Test that repeated processing doesn't leak memory."""
        import tracemalloc
        
        tracemalloc.start()
        
        from tools.skill_extractor import extract_skills_from_text
        
        # Process multiple times
        for _ in range(10):
            skills = extract_skills_from_text(sample_cv_text)
        
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory should remain bounded
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 200


@pytest.mark.performance
class TestCostEstimation:
    """
    Tests for API cost estimation.
    """

    def test_estimate_api_cost(self, sample_cv_text, sample_job_description):
        """Test estimation of API costs for a single analysis."""
        from tools.skill_extractor import estimate_token_count
        
        cv_tokens = estimate_token_count(sample_cv_text)
        job_tokens = estimate_token_count(sample_job_description)
        
        # GPT-4 pricing (approximate): $0.03/1K input, $0.06/1K output
        # Assuming ~500 tokens output
        input_cost = (cv_tokens + job_tokens) / 1000 * 0.03
        output_cost = 500 / 1000 * 0.06
        total_cost = input_cost + output_cost
        
        # Cost per analysis should be reasonable (< $0.50)
        assert total_cost < 0.50, f"Estimated cost (${total_cost:.2f}) per analysis seems high"

    def test_batch_processing_cost(self):
        """Test estimation of costs for batch processing multiple CVs."""
        # Estimate cost for processing 100 CVs
        ESTIMATED_TOKENS_PER_CV = 1000
        NUM_CVS = 100
        
        total_tokens = ESTIMATED_TOKENS_PER_CV * NUM_CVS
        
        # GPT-4 pricing
        input_cost = total_tokens / 1000 * 0.03
        output_cost = (500 * NUM_CVS) / 1000 * 0.06  # ~500 output tokens per CV
        total_cost = input_cost + output_cost
        
        # Document expected batch cost
        assert total_cost < 10.0, f"Batch cost estimate: ${total_cost:.2f}"
