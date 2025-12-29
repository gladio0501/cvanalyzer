"""
Accuracy tests for scoring accuracy.

Tests:
- Dual scoring algorithm
- Knowledge Base score calculation
- Semantic score calculation
- Final weighted score
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.accuracy
class TestDualScoringAccuracy:
    """
    Tests for the dual scoring algorithm accuracy.
    
    The dual scoring algorithm combines:
    - Knowledge Base (KB) Score: Deterministic keyword matching (40% weight)
    - Semantic Score: Vector similarity score (60% weight)
    
    Final = (0.4 × KB_Score) + (0.6 × Semantic_Score)
    """

    def test_weights_are_correct(self):
        """Test that the scoring weights are correctly configured."""
        from tools.skill_extractor import KB_WEIGHT, SEMANTIC_WEIGHT
        
        assert KB_WEIGHT == 0.4, f"Expected KB_WEIGHT = 0.4, got {KB_WEIGHT}"
        assert SEMANTIC_WEIGHT == 0.6, f"Expected SEMANTIC_WEIGHT = 0.6, got {SEMANTIC_WEIGHT}"
        assert abs(KB_WEIGHT + SEMANTIC_WEIGHT - 1.0) < 0.001

    @patch('tools.skill_extractor.calculate_kb_score')
    @patch('tools.skill_extractor.calculate_semantic_similarity')
    def test_final_score_formula(self, mock_semantic, mock_kb):
        """Test that the final score formula is correctly applied."""
        from tools.skill_extractor import calculate_final_score
        
        # Set known values
        mock_kb.return_value = 0.8
        mock_semantic.return_value = 0.9
        
        final_score = calculate_final_score("cv", "job")
        
        # Expected: (0.4 * 0.8) + (0.6 * 0.9) = 0.32 + 0.54 = 0.86
        expected = (0.4 * 0.8) + (0.6 * 0.9)
        
        assert abs(final_score - expected) < 0.01, f"Expected {expected}, got {final_score}"

    @patch('tools.skill_extractor.calculate_kb_score')
    @patch('tools.skill_extractor.calculate_semantic_similarity')
    def test_perfect_scores_give_one(self, mock_semantic, mock_kb):
        """Test that perfect KB and semantic scores give final score of 1.0."""
        from tools.skill_extractor import calculate_final_score
        
        mock_kb.return_value = 1.0
        mock_semantic.return_value = 1.0
        
        final_score = calculate_final_score("cv", "job")
        
        assert abs(final_score - 1.0) < 0.01

    @patch('tools.skill_extractor.calculate_kb_score')
    @patch('tools.skill_extractor.calculate_semantic_similarity')
    def test_zero_scores_give_zero(self, mock_semantic, mock_kb):
        """Test that zero KB and semantic scores give final score of 0.0."""
        from tools.skill_extractor import calculate_final_score
        
        mock_kb.return_value = 0.0
        mock_semantic.return_value = 0.0
        
        final_score = calculate_final_score("cv", "job")
        
        assert abs(final_score - 0.0) < 0.01


@pytest.mark.accuracy
class TestKBScoreCalculation:
    """
    Tests for Knowledge Base (KB) score calculation accuracy.
    
    KB Score = MatchesFound / TotalKeywordsInJD
    """

    def test_all_keywords_found(self):
        """Test KB score when all job keywords are in CV."""
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Experience with Python, JavaScript, Docker, and AWS"
        job_text = "Required: Python, Docker, AWS"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # All job keywords found in CV, should be close to 1.0
        assert score >= 0.9, f"Expected ~1.0 for all keywords found, got {score}"

    def test_half_keywords_found(self):
        """Test KB score when half of job keywords are in CV."""
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Experience with Python and JavaScript"
        job_text = "Required: Python, Docker, Kubernetes, AWS"  # 4 keywords
        
        score = calculate_kb_score(cv_text, job_text)
        
        # 1 out of 4 keywords found (Python), should be ~0.25
        assert 0.2 <= score <= 0.5, f"Expected ~0.25 for 1/4 keywords, got {score}"

    def test_no_keywords_found(self):
        """Test KB score when no job keywords are in CV."""
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Experience with Photoshop and Illustrator"
        job_text = "Required: Python, Docker, Kubernetes"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # No keywords found, should be close to 0.0
        assert score <= 0.1, f"Expected ~0.0 for no keywords found, got {score}"

    def test_handles_empty_job_description(self):
        """Test KB score with empty job description."""
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Experience with Python"
        job_text = ""
        
        score = calculate_kb_score(cv_text, job_text)
        
        # Should handle gracefully (return 0 or 1 depending on implementation)
        assert 0 <= score <= 1


@pytest.mark.accuracy
class TestSemanticScoreCalculation:
    """
    Tests for semantic similarity score calculation accuracy.
    
    Uses cosine similarity between vector embeddings.
    """

    def test_identical_texts_high_similarity(self):
        """Test that identical texts have very high similarity."""
        from tools.skill_extractor import calculate_semantic_similarity
        
        text = "Python developer with 5 years of experience in web development"
        
        similarity = calculate_semantic_similarity(text, text)
        
        # Identical texts should have similarity close to 1.0
        assert similarity >= 0.95, f"Expected ~1.0 for identical texts, got {similarity}"

    def test_similar_texts_moderate_similarity(self):
        """Test that similar texts have moderate similarity."""
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "Experienced Python developer specializing in REST API development"
        job_text = "Looking for a Python developer to build REST APIs"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        # Similar topics should have moderate to high similarity
        assert similarity >= 0.5, f"Expected moderate similarity for similar texts, got {similarity}"

    def test_unrelated_texts_low_similarity(self):
        """Test that unrelated texts have low similarity."""
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "Chef with expertise in Italian cuisine and pastry making"
        job_text = "DevOps engineer with Kubernetes and Terraform skills"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        # Unrelated topics should have low similarity
        assert similarity < 0.3, f"Expected low similarity for unrelated texts, got {similarity}"

    def test_similarity_score_bounded(self):
        """Test that similarity scores are always between 0 and 1."""
        from tools.skill_extractor import calculate_semantic_similarity
        
        texts = [
            ("Python developer", "JavaScript developer"),
            ("Data scientist", "Machine learning engineer"),
            ("Marketing manager", "Sales director"),
        ]
        
        for cv, job in texts:
            similarity = calculate_semantic_similarity(cv, job)
            assert 0 <= similarity <= 1, f"Score {similarity} out of bounds for ({cv}, {job})"


@pytest.mark.accuracy
class TestScoreConsistency:
    """
    Tests for scoring consistency and reliability.
    """

    def test_deterministic_kb_score(self):
        """Test that KB score is deterministic (same input = same output)."""
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Python developer with Docker experience"
        job_text = "Required: Python, Docker"
        
        scores = [calculate_kb_score(cv_text, job_text) for _ in range(5)]
        
        # All scores should be identical
        assert all(s == scores[0] for s in scores), "KB scores should be deterministic"

    def test_score_order_consistency(self, sample_job_description):
        """Test that score ordering is consistent across multiple runs."""
        from tools.skill_extractor import calculate_final_score
        
        cv1 = "Senior Python developer with AWS and Docker expertise"
        cv2 = "Junior developer with some Python knowledge"
        cv3 = "Marketing professional with no tech background"
        
        # Run multiple times
        for _ in range(3):
            s1 = calculate_final_score(cv1, sample_job_description)
            s2 = calculate_final_score(cv2, sample_job_description)
            s3 = calculate_final_score(cv3, sample_job_description)
            
            # Order should always be s1 > s2 > s3
            assert s1 > s2 > s3, f"Score order inconsistent: {s1}, {s2}, {s3}"


@pytest.mark.accuracy
class TestEdgeCases:
    """
    Tests for edge cases in scoring.
    """

    def test_very_short_cv(self):
        """Test scoring with very short CV text."""
        from tools.skill_extractor import calculate_final_score
        
        cv_text = "Python"
        job_text = "Looking for Python developer with extensive experience"
        
        score = calculate_final_score(cv_text, job_text)
        
        # Should still produce a valid score
        assert 0 <= score <= 1

    def test_very_long_cv(self):
        """Test scoring with very long CV text."""
        from tools.skill_extractor import calculate_final_score
        
        cv_text = " ".join(["Python developer experience"] * 1000)
        job_text = "Looking for Python developer"
        
        score = calculate_final_score(cv_text, job_text)
        
        # Should still produce a valid score
        assert 0 <= score <= 1

    def test_special_characters_in_text(self):
        """Test scoring with special characters."""
        from tools.skill_extractor import calculate_final_score
        
        cv_text = "Python<3developer @company #fullstack $100k+ C++ C#"
        job_text = "Need Python, C++, and C# developer"
        
        score = calculate_final_score(cv_text, job_text)
        
        # Should handle special characters gracefully
        assert 0 <= score <= 1

    def test_unicode_characters(self):
        """Test scoring with Unicode characters."""
        from tools.skill_extractor import calculate_final_score
        
        cv_text = "Développeur Python avec expérience en IA"
        job_text = "Looking for Python developer with AI experience"
        
        score = calculate_final_score(cv_text, job_text)
        
        # Should handle Unicode gracefully
        assert 0 <= score <= 1
