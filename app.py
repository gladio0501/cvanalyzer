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
    """Handle GET requests to render the index page."""
    return render_template('index.html', result=None)

@app.route('/result', methods=['GET'])
def result_page():
    """Render the result page."""
    return render_template('result.html', result=None)

@app.route('/process', methods=['POST'])
def process_form():
    """Handle POST requests to process the file upload and job description."""
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
