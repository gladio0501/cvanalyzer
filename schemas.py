"""
Data Schemas and Models for CV Analyzer

This module defines Pydantic data models used for API request/response validation
and data structure standardization across the CV Analyzer system. These schemas
ensure type safety and provide clear contracts for data exchange.

Key Features:
- Type-safe data validation using Pydantic
- Clear API contracts for frontend-backend communication
- Structured data models for CV and job processing
- Input validation and serialization support

Schema Categories:
- CV Processing: Models for CV parsing and text extraction
- Job Processing: Models for job description handling
- Analysis: Models for skill analysis and scoring results

Dependencies:
- pydantic: For data validation and serialization
- typing: For type hints and collections

"""

# schemas.py
from pydantic import BaseModel
from typing import List, Dict

class CVParseInput(BaseModel):

    cv_id: str
    file_path: str

class CVParseOutput(BaseModel):
    cv_id: str
    text: str

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