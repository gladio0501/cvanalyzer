"""
Accuracy tests for skill matching.

Tests:
- Good Match scenario (CV aligns with job description)
- Bad Match scenario (CV doesn't align)
- Semantic matching (synonymous skills)
- Keyword matching accuracy
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@pytest.mark.accuracy
class TestGoodMatchScenario:
    """
    Tests for "Good Match" scenarios.
    
    A good match occurs when the CV closely aligns with the job description,
    containing most or all required skills and relevant experience.
    """

    def test_good_match_has_high_score(self, good_match_cv, sample_job_description):
        """
        Test that a well-matching CV produces a high match score.
        
        Expected: Score >= 0.7 for a CV that matches job requirements well.
        """
        from tools.skill_extractor import calculate_final_score
        
        score = calculate_final_score(good_match_cv, sample_job_description)
        
        assert score >= 0.7, f"Expected high match score (>=0.7), got {score}"

    def test_good_match_identifies_relevant_skills(self, good_match_cv, sample_job_description):
        """
        Test that relevant skills are correctly identified in a matching CV.
        """
        from tools.skill_extractor import identify_matched_skills
        
        matched = identify_matched_skills(good_match_cv, sample_job_description)
        
        # Should find key skills like Python, FastAPI, AWS
        expected_skills = ["python", "fastapi", "aws", "docker"]
        found_skills = [s.lower() for s in matched]
        
        matches_found = sum(1 for s in expected_skills if any(s in fs for fs in found_skills))
        assert matches_found >= 2, f"Expected at least 2 skill matches, found {matches_found}"

    def test_good_match_few_missing_skills(self, good_match_cv, sample_job_description):
        """
        Test that a good match has few missing skills.
        """
        from tools.skill_extractor import identify_missing_skills
        
        _, _, missing = identify_missing_skills(good_match_cv, sample_job_description)
        
        # A good match should have minimal missing skills
        assert len(missing) <= 3, f"Expected few missing skills, found {len(missing)}: {missing}"


@pytest.mark.accuracy
class TestBadMatchScenario:
    """
    Tests for "Bad Match" scenarios.
    
    A bad match occurs when the CV has little to no alignment with 
    the job description (e.g., different field entirely).
    """

    def test_bad_match_has_low_score(self, bad_match_cv, sample_job_description):
        """
        Test that a non-matching CV produces a low match score.
        
        Expected: Score < 0.5 for a CV from a completely different field.
        """
        from tools.skill_extractor import calculate_final_score
        
        score = calculate_final_score(bad_match_cv, sample_job_description)
        
        assert score < 0.5, f"Expected low match score (<0.5), got {score}"

    def test_bad_match_identifies_few_skills(self, bad_match_cv, sample_job_description):
        """
        Test that few skills are matched for a non-matching CV.
        """
        from tools.skill_extractor import identify_matched_skills
        
        matched = identify_matched_skills(bad_match_cv, sample_job_description)
        
        # Should find very few or no matching skills
        assert len(matched) <= 2, f"Expected few skill matches, found {len(matched)}: {matched}"

    def test_bad_match_many_missing_skills(self, bad_match_cv, sample_job_description):
        """
        Test that a bad match has many missing skills.
        """
        from tools.skill_extractor import identify_missing_skills
        
        _, job_skills, missing = identify_missing_skills(bad_match_cv, sample_job_description)
        
        # Most job skills should be missing
        if len(job_skills) > 0:
            missing_ratio = len(missing) / len(job_skills)
            assert missing_ratio >= 0.7, f"Expected most skills to be missing, got ratio {missing_ratio}"


@pytest.mark.accuracy
class TestSemanticMatching:
    """
    Tests for semantic similarity matching.
    
    Tests that the system correctly matches synonymous or related terms
    (e.g., "Backend Development" ≈ "Server-side Engineering").
    """

    def test_backend_synonyms_match(self):
        """
        Test that 'Backend Development' and 'Server-side Engineering' 
        are recognized as semantically similar.
        """
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "Experienced in server-side engineering and API development"
        job_text = "Looking for backend development experience"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        # Should have reasonably high similarity
        assert similarity >= 0.5, f"Expected semantic match for synonyms, got {similarity}"

    def test_ml_ai_synonyms_match(self):
        """
        Test that 'Machine Learning' and 'AI' are recognized as related.
        """
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "Strong experience in machine learning and deep learning"
        job_text = "AI and artificial intelligence expertise required"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        assert similarity >= 0.4, f"Expected semantic match for ML/AI, got {similarity}"

    def test_django_python_relationship(self):
        """
        Test that Django experience implies Python knowledge.
        """
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "5 years of Django web development experience"
        job_text = "Must have strong Python programming skills"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        # Django implies Python knowledge
        assert similarity >= 0.3, f"Expected some semantic match for Django/Python, got {similarity}"

    def test_unrelated_terms_low_similarity(self):
        """
        Test that completely unrelated terms have low similarity.
        """
        from tools.skill_extractor import calculate_semantic_similarity
        
        cv_text = "Expert in watercolor painting and oil canvas techniques"
        job_text = "Must have experience with Kubernetes and Docker containers"
        
        similarity = calculate_semantic_similarity(cv_text, job_text)
        
        # Should have low similarity
        assert similarity < 0.3, f"Expected low similarity for unrelated terms, got {similarity}"


@pytest.mark.accuracy
class TestKeywordMatchingAccuracy:
    """
    Tests for keyword matching accuracy.
    
    Tests that the Knowledge Base (KB) scoring correctly matches
    exact keywords from the job description.
    """

    def test_exact_keyword_match(self):
        """
        Test that exact keyword matches are found.
        """
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Skills: Python, FastAPI, Docker, AWS, PostgreSQL"
        job_text = "Required: Python, Docker, AWS"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # Should have high KB score with exact matches
        assert score >= 0.8, f"Expected high KB score for exact matches, got {score}"

    def test_partial_keyword_match(self):
        """
        Test partial keyword matching.
        """
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Skills: Python, Flask"
        job_text = "Required: Python, Django, FastAPI, AWS, Docker"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # Should have partial score
        assert 0.1 <= score <= 0.5, f"Expected partial KB score, got {score}"

    def test_no_keyword_match(self):
        """
        Test scenario with no keyword matches.
        """
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Skills: Photoshop, Illustrator, InDesign"
        job_text = "Required: Python, Django, FastAPI, AWS, Docker"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # Should have low/zero KB score
        assert score < 0.2, f"Expected low KB score for no matches, got {score}"

    def test_case_insensitive_matching(self):
        """
        Test that keyword matching is case-insensitive.
        """
        from tools.skill_extractor import calculate_kb_score
        
        cv_text = "Skills: PYTHON, fastapi, DocKer"
        job_text = "Required: python, FastAPI, Docker"
        
        score = calculate_kb_score(cv_text, job_text)
        
        # Should match regardless of case
        assert score >= 0.8, f"Expected case-insensitive matches, got {score}"


@pytest.mark.accuracy
class TestScoreDistribution:
    """
    Tests for score distribution across different scenarios.
    """

    def test_score_gradation(self, sample_job_description):
        """
        Test that scores properly gradiate from best to worst match.
        """
        from tools.skill_extractor import calculate_final_score
        
        # Perfect match
        perfect_cv = """
        Senior Backend Developer with 7 years Python experience.
        Expert in FastAPI, Django, Docker, Kubernetes, AWS.
        PostgreSQL and MongoDB database management.
        Machine Learning and team leadership experience.
        """
        
        # Partial match
        partial_cv = """
        Software Developer with 3 years experience.
        Knowledge of Python and some web development.
        Basic database experience.
        """
        
        # Poor match
        poor_cv = """
        Marketing Manager with brand development experience.
        Social media and content creation skills.
        """
        
        scores = [
            calculate_final_score(perfect_cv, sample_job_description),
            calculate_final_score(partial_cv, sample_job_description),
            calculate_final_score(poor_cv, sample_job_description)
        ]
        
        # Scores should be in descending order
        assert scores[0] > scores[1] > scores[2], f"Expected descending scores, got {scores}"
