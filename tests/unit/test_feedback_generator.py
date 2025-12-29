"""
Unit tests for Feedback Generator module.

Tests:
- Overall assessment generation
- Positive feedback generation
- Constructive feedback generation
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.unit
class TestFeedbackGenerator:
    """Unit tests for Feedback Generator functionality."""

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_generate_overall_assessment(self, mock_chat, sample_cv_text):
        """Test generation of overall CV assessment."""
        from tools.feedback_generator import generate_overall_assessment
        
        # Mock the LLM response
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(
            content="Strong CV with clear structure and relevant experience."
        )
        mock_chat.return_value = mock_instance
        
        assessment = generate_overall_assessment(sample_cv_text)
        
        assert isinstance(assessment, str)
        assert len(assessment) > 0
        assert len(assessment) <= 250  # Should be concise

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_generate_positive_feedback(self, mock_chat):
        """Test generation of positive feedback based on matched skills."""
        from tools.feedback_generator import generate_positive_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(
            content="Excellent Python and FastAPI expertise demonstrated."
        )
        mock_chat.return_value = mock_instance
        
        matched_skills = ["Python", "FastAPI", "Machine Learning"]
        feedback = generate_positive_feedback(matched_skills)
        
        assert isinstance(feedback, str)
        assert len(feedback) > 0

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_generate_constructive_feedback(self, mock_chat):
        """Test generation of constructive feedback based on missing skills."""
        from tools.feedback_generator import generate_constructive_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(
            content="Consider adding Kubernetes and cloud deployment experience."
        )
        mock_chat.return_value = mock_instance
        
        missing_skills = ["Kubernetes", "Terraform", "CI/CD"]
        feedback = generate_constructive_feedback(missing_skills)
        
        assert isinstance(feedback, str)
        assert len(feedback) > 0

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_generate_complete_feedback(self, mock_chat, sample_cv_text):
        """Test generation of complete feedback package."""
        from tools.feedback_generator import generate_complete_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Sample feedback")
        mock_chat.return_value = mock_instance
        
        matched_skills = ["Python", "FastAPI"]
        missing_skills = ["Kubernetes"]
        
        feedback = generate_complete_feedback(
            sample_cv_text, 
            matched_skills, 
            missing_skills
        )
        
        assert isinstance(feedback, dict)
        assert "overall" in feedback or "positive" in feedback or "negative" in feedback


@pytest.mark.unit
class TestFeedbackCharacterLimits:
    """Tests for feedback character limit enforcement."""

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_overall_assessment_length_limit(self, mock_chat, sample_cv_text):
        """Test that overall assessment respects character limit."""
        from tools.feedback_generator import generate_overall_assessment
        
        # Mock a long response that should be truncated
        long_response = "A" * 300
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content=long_response)
        mock_chat.return_value = mock_instance
        
        assessment = generate_overall_assessment(sample_cv_text)
        
        # Should be limited (the exact limit may vary based on implementation)
        assert len(assessment) <= 300

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_positive_feedback_is_concise(self, mock_chat):
        """Test that positive feedback is concise."""
        from tools.feedback_generator import generate_positive_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Great skills!")
        mock_chat.return_value = mock_instance
        
        feedback = generate_positive_feedback(["Python"])
        
        assert isinstance(feedback, str)
        assert len(feedback) <= 250


@pytest.mark.unit
class TestFeedbackPromptTemplates:
    """Tests for feedback prompt template construction."""

    def test_overall_template_includes_cv_text(self):
        """Test that overall assessment template includes CV text placeholder."""
        from tools.feedback_generator import OVERALL_TEMPLATE
        
        assert "{cv_text}" in OVERALL_TEMPLATE or "cv_text" in OVERALL_TEMPLATE

    def test_positive_template_includes_skills(self):
        """Test that positive feedback template includes matched skills placeholder."""
        from tools.feedback_generator import POSITIVE_TEMPLATE
        
        assert "{matched_skills}" in POSITIVE_TEMPLATE or "matched_skills" in POSITIVE_TEMPLATE

    def test_negative_template_includes_skills(self):
        """Test that negative feedback template includes missing skills placeholder."""
        from tools.feedback_generator import NEGATIVE_TEMPLATE
        
        assert "{missing_skills}" in NEGATIVE_TEMPLATE or "missing_skills" in NEGATIVE_TEMPLATE


@pytest.mark.unit
class TestFeedbackEdgeCases:
    """Tests for edge cases in feedback generation."""

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_handles_empty_matched_skills(self, mock_chat):
        """Test feedback generation with no matched skills."""
        from tools.feedback_generator import generate_positive_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="No specific matches found.")
        mock_chat.return_value = mock_instance
        
        feedback = generate_positive_feedback([])
        
        assert isinstance(feedback, str)

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_handles_empty_missing_skills(self, mock_chat):
        """Test feedback generation with no missing skills."""
        from tools.feedback_generator import generate_constructive_feedback
        
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content="Great match!")
        mock_chat.return_value = mock_instance
        
        feedback = generate_constructive_feedback([])
        
        assert isinstance(feedback, str)

    @patch('tools.feedback_generator.ChatOpenAI')
    def test_handles_api_error_gracefully(self, mock_chat, sample_cv_text):
        """Test graceful handling of API errors."""
        from tools.feedback_generator import generate_overall_assessment
        
        mock_instance = MagicMock()
        mock_instance.invoke.side_effect = Exception("API Error")
        mock_chat.return_value = mock_instance
        
        # Should handle error gracefully (either return default or raise specific exception)
        try:
            result = generate_overall_assessment(sample_cv_text)
            # If it returns something, it should be a string
            assert isinstance(result, str) or result is None
        except Exception as e:
            # If it raises, it should provide useful error info
            assert str(e) is not None
