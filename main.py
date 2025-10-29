"""
CV Analyzer FastAPI Application

This module implements the main FastAPI application for the CV Analyzer system.
It provides a REST API endpoint for analyzing CVs against job descriptions using
advanced AI techniques including RAG pipelines and LoRA model integration.

Key Features:
- FastAPI-based REST API with automatic documentation
- File upload handling for CV documents (PDF, DOC, DOCX)
- AI-powered skill extraction and matching
- Dual scoring system (skills-based + neural LoRA scoring)
- Comprehensive feedback generation
- Request/response logging and monitoring
- CORS support for web applications

API Endpoints:
- POST /analyze_cv: Main endpoint for CV analysis

Architecture:
1. File Upload: Receives CV files via multipart form data
2. CV Parsing: Extracts text content from various document formats
3. Skill Analysis: Uses RAG pipeline for skill extraction and matching
4. LoRA Scoring: Integrates neural model for semantic similarity
5. Feedback Generation: Creates structured feedback using AI
6. Response: Returns comprehensive analysis results

Dependencies:
- fastapi: Web framework and API development
- tools.cv_parser: Document parsing and text extraction
- tools.skill_extractor: RAG-based skill analysis
- tools.feedback_generator: AI-powered feedback creation

"""

# main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from tools.cv_parser import parse_cv
from tools.skill_extractor import extract_and_score_skills
from tools.feedback_generator import generate_feedback
from tools.job_recommendation_chain import get_job_recommendations, JobMatch
from tools.job_sources import JobSource, get_available_job_sources
from config import load_config
import os
import logging
from fastapi.requests import Request
from typing import Optional

# Load configuration and set environment variables
config = load_config()
os.environ["OPENAI_API_KEY"] = config.openai_api_key.get_secret_value()

# Ensure the logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")
# Suppress verbose DEBUG logs from pdfminer
logging.getLogger("pdfminer").setLevel(logging.WARNING)
# Configure logging to save logs in the logs folder
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/backend.log"),
        logging.StreamHandler()
    ]
)

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.debug(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logging.debug(f"Response status code: {response.status_code}")
    return response

@app.post("/analyze_cv")
async def analyze_cv(
    file: UploadFile = File(...),
    job_description: str = Form("")
):
    """
    Analyze a CV against a job description using AI-powered techniques.
    
    This endpoint performs comprehensive CV analysis by combining multiple AI
    techniques including RAG-based skill extraction, LoRA model scoring, and
    structured feedback generation.
    
    Args:
        file (UploadFile): The CV file to analyze (PDF, DOC, DOCX formats supported)
        job_description (str): The job description text to match against
        
    Returns:
        dict: Comprehensive analysis results containing:
            - matched_skills (list): Skills found in both CV and job description
            - missing_skills (list): Skills in job description but missing from CV
            - score (int): Skills-based compatibility score (0-100)
            - lora_score (int): Neural model similarity score (0-100)
            - feedback (dict): Structured AI-generated feedback with:
                - overall_analysis: General CV assessment
                - positive_feedback: Strengths based on matched skills
                - negative_feedback: Improvement areas based on missing skills
            - error (str, optional): Error message if processing fails
            
    Example Response:
        {
            "matched_skills": ["Python", "Django", "REST APIs"],
            "missing_skills": ["Docker", "Kubernetes"],
            "score": 75,
            "lora_score": 82,
            "feedback": {
                "overall_analysis": "Well-structured CV with clear technical sections...",
                "positive_feedback": "Strong Python and web development experience...",
                "negative_feedback": "Consider adding containerization skills..."
            }
        }
        
    HTTP Status Codes:
        200: Successful analysis
        400: Invalid input (missing file or job description)
        422: File parsing error or invalid format
        500: Internal server error
        
    Error Response Format:
        {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "lora_score": 0,
            "feedback": {},
            "error": "Detailed error message"
        }
        
    Note:
        - Supports PDF, DOC, and DOCX file formats
        - Maximum file size determined by MAX_CONTENT_LENGTH config
        - All processing is logged for debugging and monitoring
        - Uses temporary file storage for processing
        - Implements comprehensive input validation
    """
    logging.debug("Received request to /analyze_cv")
    # Save the uploaded file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logging.debug(f"File saved to {file_path}")

    # Parse the CV
    cv_text = parse_cv(file_path)
    logging.debug(f"CV parsing completed. cv_text length: {len(cv_text) if cv_text else 0}")

    # Debug: Log job_description
    logging.debug(f"Job description received: '{job_description}' (length: {len(job_description) if job_description else 0})")

    # Check for missing/empty inputs
    if not job_description or not job_description.strip():
        logging.error("Job description is missing or empty.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "lora_score": 0,
            "feedback": {},
            "error": "Job description is missing or empty. Please provide a valid job description."
        }
    if not cv_text or not cv_text.strip():
        logging.error("CV text is missing or empty.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "lora_score": 0,
            "feedback": {},
            "error": "CV text is missing or empty. Please upload a valid CV file."
        }

    # Extract skills, match, and score using the new AI-powered function
    analysis = extract_and_score_skills(cv_text, job_description)
    logging.debug(f"Extracted and scored skills: {analysis}")

    # If RAG returns error, propagate it
    if 'error' in analysis:
        logging.error(f"RAG error: {analysis['error']}")
        return {
            "matched_skills": analysis.get('matched_skills', []),
            "missing_skills": analysis.get('missing_skills', []),
            "score": analysis.get('score', 0),
            "lora_score": analysis.get('lora_score', 0),
            "feedback": {},
            "error": analysis['error']
        }

    # Generate feedback
    feedback = generate_feedback(analysis['matched_skills'], analysis['missing_skills'], file_path)
    logging.debug("Feedback generation completed")

    return {
        "matched_skills": analysis['matched_skills'],
        "missing_skills": analysis['missing_skills'],
        "feedback": feedback,
        "score": analysis['score'],
        "lora_score": analysis.get('lora_score', 0)
    }


@app.post("/recommend_jobs")
async def recommend_jobs(
    file: UploadFile = File(...),
    region: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    top_k: int = Form(10),
    job_source: str = Form("jobicy"),
    jobspy_sites: Optional[str] = Form(None)
):
    """
    Get job recommendations by matching CV against multiple job listings.
    
    This endpoint fetches job listings from selected source (Jobicy API or JobSpy scraper)
    and matches them against the uploaded CV using lightweight profile extraction and
    LoRA semantic matching for efficient, accurate recommendations.
    
    Args:
        file (UploadFile): The CV file to analyze (PDF, DOC, DOCX formats supported)
        region (Optional[str]): Filter jobs by region (e.g., "Remote", "USA", "Europe")
        job_title (Optional[str]): Job title to search for (primarily for JobSpy)
        top_k (int): Number of top matching jobs to return (default: 10, max: 50)
        job_source (str): Job source to use: "jobicy" or "jobspy" (default: "jobicy")
        jobspy_sites (Optional[str]): Comma-separated sites for JobSpy: "indeed,linkedin,zip_recruiter,glassdoor"
        
    Returns:
        dict: Job recommendations containing:
            - recommendations (list): Top matching jobs with:
                - job_id: Unique job identifier
                - job_title: Job title/position
                - company: Company name
                - location: Job location
                - match_score: Overall match score (0-100)
                - lora_score: LoRA semantic similarity score
                - profile_score: Profile-based match score
                - match_reasons: List of reasons why this job matches
                - job_url: Link to full job posting
                - job_type: Full-time, Contract, etc.
            - total_jobs_analyzed: Total jobs analyzed
            - region_filter: Region filter applied (if any)
            - job_source_used: Which job source was used
            - error (str, optional): Error message if processing fails
            
    Example Response:
        {
            "recommendations": [
                {
                    "job_title": "Senior Python Developer",
                    "company": "Tech Corp",
                    "location": "Remote",
                    "match_score": 87.5,
                    "lora_score": 85.2,
                    "profile_score": 91.3,
                    "match_reasons": [
                        "Strong skills alignment (91%)",
                        "High semantic similarity (85%)",
                        "Similar role to your Python Developer experience"
                    ],
                    "job_url": "https://...",
                    "job_type": "Full-time"
                },
                ...
            ],
            "total_jobs_analyzed": 50,
            "region_filter": "Remote",
            "job_source_used": "jobicy"
        }
        
    HTTP Status Codes:
        200: Successful recommendation
        400: Invalid input (missing file or invalid job source)
        422: File parsing error or invalid format
        500: Internal server error
        
    Note:
        - Jobicy: Fast API, remote jobs only
        - JobSpy: Scrapes Indeed, LinkedIn, ZipRecruiter, Glassdoor
        - Uses lightweight profile extraction for speed
        - Parallel LoRA scoring for efficiency
        - Maximum 50 jobs fetched per request
    """
    logging.info(f"Received request to /recommend_jobs with region={region}, job_source={job_source}, top_k={top_k}")
    
    try:
        # Validate job source
        try:
            source_enum = JobSource(job_source.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid job source: {job_source}. Must be 'jobicy' or 'jobspy'"
            )
        
        # Parse jobspy_sites if provided
        sites_list = None
        if jobspy_sites and job_source.lower() == "jobspy":
            sites_list = [site.strip() for site in jobspy_sites.split(",") if site.strip()]
            logging.info(f"JobSpy sites: {sites_list}")
        
        # Save the uploaded file
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug(f"File saved to {file_path}")
        
        # Parse the CV
        cv_text = parse_cv(file_path)
        logging.debug(f"CV parsing completed. Length: {len(cv_text) if cv_text else 0}")
        
        if not cv_text or not cv_text.strip():
            logging.error("CV text is missing or empty")
            raise HTTPException(
                status_code=400,
                detail="CV text is missing or empty. Please upload a valid CV file."
            )
        
        # Load configuration for LoRA
        config = load_config()
        
        # Get job recommendations
        logging.info(f"Getting job recommendations from {source_enum.value}...")
        matches = get_job_recommendations(
            cv_text=cv_text,
            region=region,
            job_title=job_title,
            top_k=min(top_k, 50),  # Cap at 50
            lora_api_url=config.lora_matcher_api_url,
            lora_api_key=config.lora_matcher_api_key,
            job_source=source_enum,
            jobspy_sites=sites_list
        )
        
        logging.info(f"Found {len(matches)} job matches")
        
        # Convert matches to dict format
        recommendations = [
            {
                "job_id": match.job_id,
                "job_title": match.job_title,
                "company": match.company,
                "location": match.location,
                "match_score": match.match_score,
                "lora_score": match.lora_score,
                "profile_score": match.profile_score,
                "match_reasons": match.match_reasons,
                "job_url": match.job_url,
                "job_type": match.job_type
            }
            for match in matches
        ]
        
        return {
            "recommendations": recommendations,
            "total_jobs_analyzed": len(recommendations),
            "region_filter": region if region else "All regions",
            "job_source_used": source_enum.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in job recommendation: {e}", exc_info=True)
        return {
            "recommendations": [],
            "total_jobs_analyzed": 0,
            "region_filter": region if region else "All regions",
            "job_source_used": job_source,
            "error": str(e)
        }


@app.get("/job_sources")
async def list_job_sources():
    """
    Get list of available job sources.
    
    Returns:
        dict: Available job sources with descriptions
    """
    return {
        "sources": get_available_job_sources()
    }