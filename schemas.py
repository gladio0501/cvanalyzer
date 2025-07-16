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
    """
    Input schema for CV parsing requests.
    
    This model defines the required data structure for initiating
    CV document parsing operations.
    
    Attributes:
        cv_id (str): Unique identifier for the CV document
        file_path (str): Absolute path to the CV file for parsing
        
    Example:
        >>> parse_input = CVParseInput(
        ...     cv_id="cv_123",
        ...     file_path="/tmp/john_doe_resume.pdf"
        ... )
    """
    cv_id: str
    file_path: str

class CVParseOutput(BaseModel):
    """
    Output schema for CV parsing results.
    
    This model defines the structure of data returned after
    successful CV document parsing and text extraction.
    
    Attributes:
        cv_id (str): Unique identifier matching the input request
        text (str): Extracted plain text content from the CV
        
    Example:
        >>> parse_output = CVParseOutput(
        ...     cv_id="cv_123",
        ...     text="John Doe\\nSoftware Engineer\\n..."
        ... )
    """
    cv_id: str
    text: str

class CVInput(BaseModel):
    """
    Input schema for CV analysis with pre-extracted text.
    
    This model is used when CV text has already been extracted
    and is ready for skill analysis and scoring.
    
    Attributes:
        cv_id (str): Unique identifier for the CV
        cv_text (str): Pre-extracted text content of the CV
        
    Example:
        >>> cv_input = CVInput(
        ...     cv_id="cv_123",
        ...     cv_text="Experienced Python developer with Django..."
        ... )
    """
    cv_id: str
    cv_text: str

class JobInput(BaseModel):
    """
    Input schema for job description data.
    
    This model defines the structure for job description
    information used in CV-job matching analysis.
    
    Attributes:
        job_id (str): Unique identifier for the job posting
        job_text (str): Complete job description text content
        
    Example:
        >>> job_input = JobInput(
        ...     job_id="job_456",
        ...     job_text="We are looking for a Python developer..."
        ... )
    """
    job_id: str
    job_text: str

class SkillMatchOutput(BaseModel):
    cv_id: str
    job_id: str
    matched_skills: List[str]
    missing_skills: List[str]
    score: float
    explanation: str