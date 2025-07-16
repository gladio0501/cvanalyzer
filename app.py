"""
CV Analyzer Flask Web Application

This module implements the web-based frontend for the CV Analyzer system using Flask.
It provides a user-friendly web interface for uploading CV documents and entering
job descriptions, then displays comprehensive analysis results.

Key Features:
- Web-based user interface with HTML templates
- File upload handling with security validation
- Integration with FastAPI backend for analysis
- Responsive design for various screen sizes
- Comprehensive logging and error handling
- Configuration-based backend URL management

Architecture:
1. Frontend (Flask): Handles web interface and user interactions
2. Backend Integration: Communicates with FastAPI service for analysis
3. File Management: Secure file upload and temporary storage
4. Result Display: Formatted presentation of analysis results

Routes:
- GET /: Main upload page
- GET /result: Results display page  
- POST /process: Form processing and analysis trigger

Dependencies:
- flask: Web framework for frontend interface
- requests: HTTP client for backend communication
- werkzeug: File upload security utilities
- config: Configuration management

Author: CV Analyzer Team
Version: 1.0
"""

from flask import Flask, render_template, request
import requests
import os
from werkzeug.utils import secure_filename
import logging
from config import load_config

app = Flask(__name__)

# Load configuration from .env
config = load_config()

# Update constants from config
API_URL = config.api_url  # FastAPI backend endpoint
app.config['MAX_CONTENT_LENGTH'] = config.max_content_length

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
    Render the main upload page for CV analysis.
    
    This route handles GET requests to display the main interface where
    users can upload their CV files and enter job descriptions.
    
    Returns:
        str: Rendered HTML template for the index page
        
    Note:
        - Displays clean form without any previous results
        - Provides file upload and text input components
        - Includes client-side validation for better UX
    """
    return render_template('index.html', result=None)

@app.route('/result', methods=['GET'])
def result_page():
    """
    Render the results display page.
    
    This route provides a dedicated page for displaying analysis results
    with clean formatting and structured presentation.
    
    Returns:
        str: Rendered HTML template for the result page
        
    Note:
        - Used for displaying comprehensive analysis results
        - Includes charts and formatted feedback sections
        - Provides navigation back to main upload page
    """
    return render_template('result.html', result=None)

@app.route('/process', methods=['POST'])
def process_form():
    """
    Process CV upload and job description form submission.
    
    This route handles the main form processing logic, including file upload
    validation, backend API communication, and result presentation. It coordinates
    the entire analysis workflow from user input to result display.
    
    Returns:
        str: Rendered HTML template with analysis results or error messages
        
    Form Data Expected:
        - job_text (str): Job description text from textarea
        - cv_file (FileStorage): Uploaded CV file (PDF/DOCX)
        
    Response Scenarios:
        1. Success: Displays comprehensive analysis results
        2. Validation Error: Shows error message for missing/invalid inputs
        3. Backend Error: Displays API communication or processing errors
        
    Example Flow:
        1. User uploads CV and enters job description
        2. Form data is validated and sanitized
        3. File is securely saved to temporary storage
        4. Backend API is called for analysis
        5. Results are formatted and displayed
        
    Error Handling:
        - Missing job description: User-friendly error message
        - Missing CV file: File upload validation error
        - Invalid file format: Backend format validation
        - API communication: Network/service error handling
        
    Note:
        - Uses secure_filename for upload security
        - Implements comprehensive logging for debugging
        - Handles both validation and processing errors gracefully
        - Temporary files are cleaned up after processing
    """
    logging.debug("Entering /process route")
    logging.debug(f"request object: {request}")
    result = None
    job_text = request.form.get('job_text')
    cv_file = request.files.get('cv_file')
    logging.debug(f"Received job_text: '{job_text}' (length: {len(job_text) if job_text else 0})")
    logging.debug(f"Received cv_file: '{cv_file.filename if cv_file else None}'")
    if not job_text or not job_text.strip():
        logging.error("job_text is missing or empty from the request")
        result = {"error": "Job description is missing or empty. Please provide a valid job description."}
        return render_template('result.html', result=result)
    if not cv_file:
        logging.error("cv_file is missing from the request")
        result = {"error": "CV file is missing. Please upload a valid CV file."}
        return render_template('result.html', result=result)

    # Handle potential None filename
    if not cv_file.filename:
        logging.error("cv_file has no filename")
        result = {"error": "Invalid file upload. Please select a valid CV file."}
        return render_template('result.html', result=result)
        
    filename = secure_filename(cv_file.filename)
    file_path = os.path.join('/tmp', filename)
    cv_file.save(file_path)
    logging.debug(f"File saved to {file_path}")

    with open(file_path, "rb") as f:
        files = {"file": (filename, f, "application/octet-stream")}
        data = {"job_description": job_text}

        try:
            logging.debug(f"Sending POST request to {API_URL} with files and data")
            response = requests.post(API_URL, files=files, data=data)
            logging.debug(f"Response status code: {response.status_code}")
            logging.debug(f"Response headers: {response.headers}")

            if response.ok:
                result = response.json()
            else:
                result = {"error": "Backend error: " + response.text}
        except Exception as e:
            logging.error(f"Error during POST request: {e}")
            result = {"error": str(e)}
        finally:
            os.remove(file_path)
            logging.debug(f"Temporary file {file_path} removed")

    logging.debug("Exiting /process route")
    return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
