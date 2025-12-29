"""
Unit tests for Skill Extractor module.

Tests:
- Skill extraction from CV text
- Knowledge base matching
- Semantic similarity scoring
"""
import pytest
import os
import sys
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.unit
class TestSkillExtractor:
    """Unit tests for Skill Extractor functionality."""

    def test_extract_skills_from_text(self, sample_cv_text):
        """Test skill extraction from CV text."""
        from tools.skill_extractor import extract_skills_from_text
        
        skills = extract_skills_from_text(sample_cv_text)
        
        assert isinstance(skills, list)
        # Should find some skills mentioned in the sample CV
        expected_skills = ["Python", "JavaScript", "FastAPI", "Django"]
        found_any = any(skill in skills for skill in expected_skills)
        assert found_any, f"Expected to find at least one of {expected_skills} in {skills}"

    def test_extract_skills_handles_empty_text(self):
        """Test skill extraction with empty text."""
        from tools.skill_extractor import extract_skills_from_text
        
        skills = extract_skills_from_text("")
        
        assert isinstance(skills, list)
        assert len(skills) == 0

    def test_knowledge_base_matching(self, sample_cv_text):
        """Test matching against knowledge base."""
        from tools.skill_extractor import match_against_knowledge_base
        
        # Assuming knowledge base contains common tech skills
        matches = match_against_knowledge_base(sample_cv_text)
        
        assert isinstance(matches, dict) or isinstance(matches, list)

    def test_calculate_kb_score(self, sample_cv_text, sample_job_description):
        """Test Knowledge Base score calculation."""
        from tools.skill_extractor import calculate_kb_score
        
        score = calculate_kb_score(sample_cv_text, sample_job_description)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1

    @patch('tools.skill_extractor.OpenAIEmbeddings')
    def test_semantic_similarity_calculation(self, mock_embeddings):
        """Test semantic similarity score calculation."""
        from tools.skill_extractor import calculate_semantic_similarity
        import numpy as np
        
        # Mock embeddings
        mock_instance = MagicMock()
        mock_instance.embed_query.return_value = np.random.rand(1536).tolist()
        mock_embeddings.return_value = mock_instance
        
        cv_text = "Python developer with machine learning experience"
        job_text = "Looking for Python developer with ML skills"
        
        score = calculate_semantic_similarity(cv_text, job_text)
        
        assert isinstance(score, (int, float))
        assert 0 <= score <= 1


@pytest.mark.unit
class TestDualScoringAlgorithm:
    """Tests for the dual scoring algorithm (KB + Semantic)."""

    @patch('tools.skill_extractor.calculate_kb_score')
    @patch('tools.skill_extractor.calculate_semantic_similarity')
    def test_final_score_calculation(self, mock_semantic, mock_kb):
        """Test final weighted score calculation."""
        from tools.skill_extractor import calculate_final_score
        
        mock_kb.return_value = 0.8
        mock_semantic.return_value = 0.9
        
        final_score = calculate_final_score("cv text", "job text")
        
        # Final score should be weighted average: (0.4 * 0.8) + (0.6 * 0.9) = 0.86
        expected = (0.4 * 0.8) + (0.6 * 0.9)
        assert abs(final_score - expected) < 0.01

    def test_score_weights_sum_to_one(self):
        """Test that scoring weights sum to 1."""
        from tools.skill_extractor import KB_WEIGHT, SEMANTIC_WEIGHT
        
        assert abs((KB_WEIGHT + SEMANTIC_WEIGHT) - 1.0) < 0.001

    def test_score_is_bounded(self, sample_cv_text, sample_job_description):
        """Test that scores are always between 0 and 1."""
        from tools.skill_extractor import calculate_final_score
        
        score = calculate_final_score(sample_cv_text, sample_job_description)
        
        assert 0 <= score <= 1


@pytest.mark.unit
class TestSkillCategorization:
    """Tests for skill categorization functionality."""

    def test_categorize_technical_skills(self):
        """Test categorization of technical skills."""
        from tools.skill_extractor import categorize_skill
        
        assert categorize_skill("Python") == "programming_language"
        assert categorize_skill("AWS") == "cloud"
        assert categorize_skill("Docker") == "devops"

    def test_identify_missing_skills(self, sample_cv_text, sample_job_description):
        """Test identification of missing skills."""
        from tools.skill_extractor import identify_missing_skills
        
        cv_skills, job_skills, missing = identify_missing_skills(
            sample_cv_text, 
            sample_job_description
        )
        
        assert isinstance(missing, list)

    def test_identify_matched_skills(self, sample_cv_text, sample_job_description):
        """Test identification of matched skills."""
        from tools.skill_extractor import identify_matched_skills
        
        matched = identify_matched_skills(sample_cv_text, sample_job_description)
        
        assert isinstance(matched, list)
        # Should find some matches between sample CV and job description
        assert len(matched) > 0
