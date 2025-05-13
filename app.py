from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

API_URL = "http://localhost:8000/match_skills"  # FastAPI backend endpoint

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        cv_text = request.form.get('cv_text', '')
        job_text = request.form.get('job_text', '')
        payload = {
            "cv": {
                "cv_id": "cv1",
                "cv_text": cv_text
            },
            "job": {
                "job_id": "job1",
                "job_text": job_text
            }
        }
        try:
            response = requests.post(API_URL, json=payload)
            if response.ok:
                result = response.json()
            else:
                result = {"error": "Backend error: " + response.text}
        except Exception as e:
            result = {"error": str(e)}
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
