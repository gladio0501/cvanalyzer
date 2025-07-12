# main.py
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from tools.cv_parser import parse_cv
from tools.skill_extractor import extract_and_score_skills
from tools.feedback_generator import generate_feedback
import os
import logging
from fastapi.requests import Request

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
            "feedback": {},
            "error": "Job description is missing or empty. Please provide a valid job description."
        }
    if not cv_text or not cv_text.strip():
        logging.error("CV text is missing or empty.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
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
        "score": analysis['score']
    }