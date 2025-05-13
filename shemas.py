# schemas.py
from pydantic import BaseModel
from typing import List, Dict

class CVInput(BaseModel):
    cv_id: str
    cv_text: str

class JobInput(BaseModel):
    job_id: str
    job_text: str

class SkillMatchOutput(BaseModel):
    cv_id: str
    job_id: str
    matched_skills: List[str]
    missing_skills: List[str]
    score: float
    explanation: str