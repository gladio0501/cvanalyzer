# tools/skill_matcher.py
from typing import List
from schemas import CVInput, JobInput, SkillMatchOutput

def extract_skills(text: str) -> List[str]:
    # Use LangChain or simple keyword extraction for now
    # Placeholder: split by commas, etc.
    return [skill.strip() for skill in text.split(",")]

def skill_matcher(cv: CVInput, job: JobInput) -> SkillMatchOutput:
    cv_skills = set(extract_skills(cv.cv_text))
    job_skills = set(extract_skills(job.job_text))
    matched = list(cv_skills & job_skills)
    missing = list(job_skills - cv_skills)
    score = len(matched) / max(1, len(job_skills))
    explanation = f"Matched: {matched}, Missing: {missing}"
    return SkillMatchOutput(
        cv_id=cv.cv_id,
        job_id=job.job_id,
        matched_skills=matched,
        missing_skills=missing,
        score=score,
        explanation=explanation
    )

def match_skills(matched_skills, missing_skills):
    """
    Calculate a score based on the ratio of matched skills to total skills,
    with additional weighting for critical skills if needed.
    """
    total_skills = len(matched_skills) + len(missing_skills)
    if total_skills == 0:
        return 0

    # Example: Weight critical skills higher (if applicable)
    critical_skills = {"teamwork", "communication", "problem-solving"}  # Example critical skills
    critical_matched = len(set(matched_skills) & critical_skills)

    # Weighted score: 70% normal skills, 30% critical skills
    weighted_score = (len(matched_skills) / total_skills) * 70 + (critical_matched / total_skills) * 30
    return weighted_score