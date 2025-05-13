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