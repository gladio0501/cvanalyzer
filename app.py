"""
CV Analyzer Flask Web Application

Web-based frontend for the CV Analyzer system.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_jwt_extended import JWTManager
from flask_cors import CORS
import requests
import os
from werkzeug.utils import secure_filename
import logging
from config import load_config
from auth import init_oauth, auth_bp, token_required
from database import init_database

app = Flask(__name__)

# Load configuration from .env
config = load_config()

# Update constants from config
API_URL = config.api_url  # FastAPI backend endpoint
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length

# Configure Flask app for OAuth and JWT
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', os.urandom(32).hex())
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000))  # 30 days
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize OAuth
oauth = init_oauth(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize database
init_database()

# Configure CORS for React frontend
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5000').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Ensure the logs directory exists
log_dir = "/tmp/logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Suppress verbose DEBUG logs from pdfminer
logging.getLogger("pdfminer").setLevel(logging.WARNING)

# Configure logging to save logs in the logs folder
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "frontend.log")),
        logging.StreamHandler()
    ]
)

@app.route('/', methods=['GET'])
def get_index():
    """
    Serve the React frontend (for backward compatibility).
    """
    # In development, redirect to Vite dev server
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    return redirect(frontend_url)







@app.route('/api/job-sources', methods=['GET'])
def get_job_sources():
    """
    Get available job sources and their configuration.
    """
    job_sources = [
        {
            "name": "jobicy",
            "display_name": "Jobicy API",
            "description": "Fast API with curated remote job listings",
            "requires_sites": False
        },
        {
            "name": "jobspy",
            "display_name": "JobSpy Scraper",
            "description": "Scrapes live jobs from Indeed, LinkedIn, ZipRecruiter, and Glassdoor",
            "requires_sites": True,
            "available_sites": ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
        }
    ]
    return jsonify(job_sources), 200




@app.route('/api/process', methods=['POST'])
@token_required
def process_form(current_user):
    """
    Process CV upload and job description for analysis (API endpoint).
    """
    logging.debug("Entering /process route (API mode)")
    
    job_text = request.form.get('job_text')
    cv_file = request.files.get('cv_file')
    
    logging.debug(f"Received job_text: '{job_text}' (length: {len(job_text) if job_text else 0})")
    logging.debug(f"Received cv_file: '{cv_file.filename if cv_file else None}'")
    
    if not job_text or not job_text.strip():
        logging.error("job_text is missing or empty")
        return jsonify({"error": "Job description is required"}), 400
    
    if not cv_file or not cv_file.filename:
        logging.error("cv_file is missing")
        return jsonify({"error": "CV file is required"}), 400
        
    filename = secure_filename(cv_file.filename)
    file_path = os.path.join('/tmp', filename)
    cv_file.save(file_path)
    logging.debug(f"File saved to {file_path}")

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            data = {"job_description": job_text}

            logging.debug(f"Sending POST request to {API_URL}")
            response = requests.post(API_URL, files=files, data=data)
            logging.debug(f"Response status code: {response.status_code}")

            if response.ok:
                result = response.json()
                
                # Save CV upload to database
                try:
                    from database import get_db_session
                    from models import CVUpload
                    import shutil
                    
                    with get_db_session() as db_session:
                        # Create uploads directory if it doesn't exist
                        uploads_dir = os.path.join(os.getcwd(), 'uploads')
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        # Read file size
                        file_size = os.path.getsize(file_path)
                        
                        # Copy file to permanent storage
                        stored_filename = f"{current_user.id}_{filename}"
                        stored_path = os.path.join(uploads_dir, stored_filename)
                        shutil.copy2(file_path, stored_path)
                        
                        # Create CV upload record
                        cv_upload = CVUpload(
                            user_id=current_user.id,
                            filename=stored_filename,
                            original_filename=filename,
                            file_path=stored_path,
                            file_size=file_size,
                            profile_data=None  # Can be populated later if needed
                        )
                        db_session.add(cv_upload)
                        db_session.commit()
                        logging.info(f"CV upload saved to database for user {current_user.email}")
                except Exception as db_error:
                    logging.error(f"Failed to save CV upload to database: {db_error}")
                    # Don't fail the request if database save fails
                
                return jsonify(result), 200
            else:
                logging.error(f"Backend error: {response.text}")
                return jsonify({"error": f"Backend error: {response.text}"}), response.status_code
                
    except Exception as e:
        logging.error(f"Error during analysis request: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.debug(f"Temporary file {file_path} removed")


@app.route('/api/jobs/process', methods=['POST'])
@token_required
def process_jobs(current_user):
    """
    Process CV upload for job recommendations (API endpoint).
    """
    logging.debug("Entering /jobs/process route (API mode)")
    
    cv_file = request.files.get('cv_file')
    job_source = request.form.get('job_source', 'jobicy')
    region = request.form.get('region', '').strip() or None
    job_title = request.form.get('job_title', '').strip() or None
    top_k = int(request.form.get('top_k', 10))
    jobspy_sites = request.form.get('jobspy_sites', '').strip() or None
    
    logging.debug(f"Received: job_source={job_source}, region={region}, job_title={job_title}, top_k={top_k}, jobspy_sites={jobspy_sites}")
    
    if not cv_file or not cv_file.filename:
        logging.error("cv_file is missing")
        return jsonify({"error": "CV file is required"}), 400
    
    filename = secure_filename(cv_file.filename)
    file_path = os.path.join('/tmp', filename)
    cv_file.save(file_path)
    logging.debug(f"File saved to {file_path}")
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            data = {
                "job_source": job_source,
                "region": region if region else "",
                "job_title": job_title if job_title else "",
                "top_k": str(top_k),
                "jobspy_sites": jobspy_sites if jobspy_sites else ""
            }
            
            # Call backend recommend_jobs endpoint
            backend_url = config.api_url.replace('/analyze_cv', '/recommend_jobs')
            logging.debug(f"Sending POST request to {backend_url}")
            
            response = requests.post(backend_url, files=files, data=data, timeout=180)  # 3 minutes for JobSpy
            logging.debug(f"Response status code: {response.status_code}")
            
            if response.ok:
                results = response.json()
                logging.info(f"Got {len(results.get('recommendations', []))} job recommendations from {results.get('job_source_used', 'unknown')}")
                return jsonify(results), 200
            else:
                logging.error(f"Backend error: {response.text}")
                return jsonify({"error": f"Backend error: {response.text}"}), response.status_code
                
    except Exception as e:
        logging.error(f"Error during job recommendation request: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.debug(f"Temporary file {file_path} removed")


@app.route('/api/jobs/save', methods=['POST'])
@token_required
def save_job(current_user):
    """
    Save a job for the current user.
    """
    try:
        data = request.get_json()
        logging.info(f"Received save job request: {data}")
        
        from database import get_db_session
        from models import SavedJob
        from datetime import datetime
        import json
        
        with get_db_session() as db_session:
            # Check if job is already saved
            existing = db_session.query(SavedJob).filter_by(
                user_id=current_user.id,
                job_title=data.get('job_title'),
                company=data.get('company')
            ).first()
            
            if existing:
                logging.info(f"Job already saved for user {current_user.email}")
                return jsonify({'message': 'Job already saved', 'job': existing.to_dict()}), 200
            
            # Prepare match_reasons (convert array to JSON string if provided)
            match_reasons = data.get('match_reasons') or data.get('reasons')
            if match_reasons and isinstance(match_reasons, list):
                match_reasons = json.dumps(match_reasons)
            
            # Create new saved job
            saved_job = SavedJob(
                user_id=current_user.id,
                job_title=data.get('job_title'),
                company=data.get('company'),
                location=data.get('location'),
                job_url=data.get('job_url'),
                description=data.get('description'),
                job_type=data.get('job_type'),
                match_score=data.get('match_score'),
                match_reasons=match_reasons,
                application_status='saved'
            )
            db_session.add(saved_job)
            db_session.commit()
            
            logging.info(f"Job saved successfully for user {current_user.email}: {data.get('job_title')} at {data.get('company')}")
            
            return jsonify({'message': 'Job saved successfully', 'job': saved_job.to_dict()}), 201
            
    except Exception as e:
        logging.error(f"Error saving job: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/saved', methods=['GET'])
@token_required
def get_saved_jobs(current_user):
    """
    Get all saved jobs for the current user.
    """
    try:
        from database import get_db_session
        from models import SavedJob
        
        with get_db_session() as db_session:
            saved_jobs = db_session.query(SavedJob).filter_by(user_id=current_user.id).order_by(SavedJob.saved_at.desc()).all()
            
            return jsonify({'jobs': [job.to_dict() for job in saved_jobs]}), 200
            
    except Exception as e:
        logging.error(f"Error fetching saved jobs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/saved/<int:job_id>', methods=['DELETE'])
@token_required
def delete_saved_job(current_user, job_id):
    """
    Delete a saved job.
    """
    try:
        from database import get_db_session
        from models import SavedJob
        
        with get_db_session() as db_session:
            saved_job = db_session.query(SavedJob).filter_by(id=job_id, user_id=current_user.id).first()
            
            if not saved_job:
                return jsonify({'error': 'Job not found'}), 404
            
            db_session.delete(saved_job)
            db_session.commit()
            
            logging.info(f"Job deleted for user {current_user.email}: {saved_job.job_title}")
            
            return jsonify({'message': 'Job deleted successfully'}), 200
            
    except Exception as e:
        logging.error(f"Error deleting saved job: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/saved/<int:job_id>', methods=['PUT'])
@token_required
def update_saved_job(current_user, job_id):
    """
    Update a saved job's status or notes.
    """
    try:
        data = request.get_json()
        
        from database import get_db_session
        from models import SavedJob
        
        with get_db_session() as db_session:
            saved_job = db_session.query(SavedJob).filter_by(id=job_id, user_id=current_user.id).first()
            
            if not saved_job:
                return jsonify({'error': 'Job not found'}), 404
            
            # Update fields
            if 'status' in data:
                saved_job.application_status = data['status']
            if 'notes' in data:
                saved_job.notes = data['notes']
            
            db_session.commit()
            
            logging.info(f"Job updated for user {current_user.email}: {saved_job.job_title}")
            
            return jsonify({'message': 'Job updated successfully', 'job': saved_job.to_dict()}), 200
            
    except Exception as e:
        logging.error(f"Error updating saved job: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
@token_required
def get_user_stats(current_user):
    """
    Get user statistics for dashboard.
    """
    try:
        from database import get_db_session
        from models import CVUpload, JobSearch, SavedJob
        
        with get_db_session() as db_session:
            cv_count = db_session.query(CVUpload).filter_by(user_id=current_user.id).count()
            job_search_count = db_session.query(JobSearch).filter_by(user_id=current_user.id).count()
            saved_jobs_count = db_session.query(SavedJob).filter_by(user_id=current_user.id).count()
            applications_count = db_session.query(SavedJob).filter_by(user_id=current_user.id, application_status='applied').count()
            
            return jsonify({
                'cvs_uploaded': cv_count,
                'job_searches': job_search_count,
                'saved_jobs': saved_jobs_count,
                'applications': applications_count
            }), 200
            
    except Exception as e:
        logging.error(f"Error fetching user stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/suggest-title', methods=['POST'])
@token_required
def suggest_job_title(current_user):
    """
    Analyze CV and suggest a job title for search.
    """
    cv_file = request.files.get('cv_file')
    
    if not cv_file or not cv_file.filename:
        return jsonify({"error": "CV file is required"}), 400
    
    filename = secure_filename(cv_file.filename)
    file_path = os.path.join('/tmp', filename)
    cv_file.save(file_path)
    
    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            
            # Call backend extract_profile endpoint
            backend_url = config.api_url.replace('/analyze_cv', '/extract_profile')
            logging.debug(f"Sending POST request to {backend_url}")
            
            response = requests.post(backend_url, files=files, timeout=60)
            
            if response.ok:
                data = response.json()
                preferred_roles = data.get('preferred_roles', [])
                job_titles = data.get('job_titles', [])
                
                # Logic to pick the best title
                suggestion = ""
                if preferred_roles:
                    suggestion = preferred_roles[0]
                elif job_titles:
                    suggestion = job_titles[0]
                    
                return jsonify({"suggested_title": suggestion, "debug_data": data}), 200
            else:
                return jsonify({"error": "Failed to analyze CV for title suggestion"}), response.status_code
                
    except Exception as e:
        logging.error(f"Error suggesting title: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    # Port 5000 is often used by macOS AirPlay, use 5001 instead
    port = int(os.getenv('FLASK_PORT', 5001))
    app.run(debug=True, port=port)
