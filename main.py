"""
CV Analyzer FastAPI Application

Main API endpoint for analyzing CVs against job descriptions using RAG and LoRA.
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


@app.post("/extract_profile")
async def extract_profile_endpoint(file: UploadFile = File(...)):
    """
    Extract profile metadata from CV (job titles, preferred roles, etc).
    """
    logging.info(f"Received request to /extract_profile for file: {file.filename}")
    
    try:
        # Save the uploaded file
        file_path = f"/tmp/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # Parse content
        cv_text = parse_cv(file_path)
        
        if not cv_text or not cv_text.strip():
            raise HTTPException(status_code=400, detail="Could not parse text from CV")
            
        # Extract profile specifically
        from tools.cv_profile_extractor import extract_cv_profile
        profile = extract_cv_profile(cv_text, fast_mode=False)
        
        return {
            "job_titles": profile.job_titles,
            "preferred_roles": profile.preferred_roles,
            "skills": profile.primary_skills,
            "experience_years": profile.experience_years
        }
        
    except Exception as e:
        logging.error(f"Error extracting profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)