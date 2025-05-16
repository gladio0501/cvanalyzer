# main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from tools.cv_parser import parse_cv
from tools.skill_extractor import extract_skills
from tools.feedback_generator import generate_feedback
import os
import logging
from fastapi.requests import Request

# Ensure the logs directory exists
if not os.path.exists("logs"):
    os.makedirs("logs")

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
async def analyze_cv(file: UploadFile = File(...), job_description: str = ""):
    logging.debug("Received request to /analyze_cv")

    # Save the uploaded file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    logging.debug(f"File saved to {file_path}")

    # Parse the CV
    cv_text = parse_cv(file_path)
    logging.debug("CV parsing completed")

    # Extract skills
    cv_skills = extract_skills(cv_text)
    job_skills = extract_skills(job_description)
    logging.debug(f"Extracted skills from CV: {cv_skills}")
    logging.debug(f"Extracted skills from job description: {job_skills}")

    # Match skills and generate feedback
    matched = list(set(cv_skills) & set(job_skills))
    missing = list(set(job_skills) - set(cv_skills))
    feedback = generate_feedback(matched, missing, file_path)
    logging.debug("Feedback generation completed")


    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "feedback": feedback
    }