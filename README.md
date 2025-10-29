# CV Analyzer - AI-Powered Resume Analysis System

A sophisticated CV analysis system that combines multiple AI techniques including RAG (Retrieval Augmented Generation) pipelines, LoRA model integration, and advanced NLP to provide comprehensive resume-job matching analysis.

## 🚀 Features

### Core Capabilities

- **Multi-format CV Parsing**: Supports PDF and DOCX document formats
- **RAG-based Skill Extraction**: Uses FAISS vector store with OpenAI embeddings
- **Dual Scoring System**: 
  - Skills-based matching using knowledge base
  - Neural similarity scoring via LoRA model integration
- **AI-Powered Feedback**: Structured feedback generation using GPT-4
- **Job Recommendations**: Match CV against real-time job listings from Jobicy RSS feed
- **Web Interface**: User-friendly Flask frontend with FastAPI backend
- **Comprehensive Monitoring**: LangSmith tracing integration

### Advanced Features

- **Hybrid Skill Detection**: LLM + keyword-based fallback
- **Knowledge Base Filtering**: Curated skills database with normalization
- **External API Integration**: LoRA model for semantic similarity
- **Parallel Processing**: Concurrent LoRA scoring for multiple jobs
- **Lightweight CV Extraction**: Fast profile extraction for job matching
- **Region-based Filtering**: Filter jobs by location (Remote, USA, Europe, etc.)
- **Robust Error Handling**: Comprehensive validation and logging
- **Type-Safe Configuration**: Pydantic-based settings management

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web     │    │   FastAPI       │    │   External      │
│   Frontend      │────│   Backend       │────│   LoRA API      │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTML/CSS      │    │   RAG Pipeline  │    │   Neural        │
│   Templates     │    │   FAISS Vector  │    │   Similarity    │
│                 │    │   Store         │    │   Scoring       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                                v
                       ┌─────────────────┐
                       │   OpenAI LLM    │
                       │   Embeddings    │
                       │   GPT-4         │
                       └─────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- (Optional) LangSmith account for tracing
- (Optional) External LoRA model API

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/gladio0501/cvanalyzer.git
cd cvanalyzer
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM and embeddings |
| `LANGSMITH_API_KEY` | No | LangSmith tracing API key |
| `LANGSMITH_PROJECT` | No | LangSmith project name |
| `LANGSMITH_TRACING` | No | Enable/disable tracing (default: false) |
| `LORA_MATCHER_API_URL` | No | External LoRA model API URL |
| `LORA_MATCHER_API_KEY` | No | LoRA model API authentication key |

## 🚀 Usage

### Starting the Services

1. **Start FastAPI Backend**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Start Flask Frontend**
```bash
python app.py
```

3. **Access the Web Interface**
- Open browser to `http://localhost:5000`
- Choose between two features:
  - **CV Analysis**: Compare CV against a specific job description
  - **Job Recommendations**: Find matching jobs from current listings

### Web Interface Usage

#### CV Analysis (Traditional Mode)
1. Upload CV file (PDF/DOCX)
2. Enter job description
3. Get comprehensive analysis with:
   - Matched and missing skills
   - Skills-based score
   - LoRA semantic similarity score
   - Detailed AI feedback

#### Job Recommendations (New Feature)
1. Navigate to "Job Recommendations" from the homepage
2. Upload your CV (PDF/DOCX)
3. Select target region (Remote, USA, Europe, Asia, etc.)
4. Choose number of top jobs to display (default: 10)
5. Get ranked job matches with:
   - Match score (combined LoRA + profile scoring)
   - Match reasons (why the job fits)
   - Job details (title, company, location, tags)
   - Direct application links

### API Usage

#### Analyze CV Endpoint

```bash
curl -X POST "http://localhost:8000/analyze_cv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf" \
  -F "job_description=Looking for Python developer with web frameworks"
```

#### Job Recommendations Endpoint

```bash
curl -X POST "http://localhost:8000/recommend_jobs" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@resume.pdf" \
  -F "region=Remote" \
  -F "top_k=10"
```

**Parameters:**
- `file`: CV file (PDF/DOCX)
- `region`: Target job location (optional, e.g., "Remote", "USA", "Europe")
- `top_k`: Number of top jobs to return (default: 10)

#### Response Formats

**CV Analysis Response:**

```json
{
  "matched_skills": ["Python", "Django", "FastAPI"],
  "missing_skills": ["Docker", "Kubernetes"],
  "score": 75,
  "lora_score": 82,
  "feedback": {
    "overall_analysis": "Well-structured CV with clear sections...",
    "positive_feedback": "Strong Python and web development experience...",
    "negative_feedback": "Consider adding containerization skills..."
  }
}
```

**Job Recommendations Response:**

```json
{
  "jobs": [
    {
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "Remote",
      "match_score": 0.87,
      "match_reason": "Strong match: 5+ years Python, FastAPI experience, remote work",
      "description": "Looking for experienced Python developer...",
      "tags": ["Python", "FastAPI", "Docker", "AWS"],
      "url": "https://jobicy.com/job/12345"
    }
  ],
  "total_jobs_analyzed": 150,
  "region_filter": "Remote"
}
```

## 🔧 Configuration

### Skills Knowledge Base
The system uses a curated skills database (`tools/skills_kb.json`) with categories:
- Programming Languages
- Web Frameworks
- Databases
- DevOps Tools
- Machine Learning
- Cloud Platforms

### LoRA Model Integration
For enhanced semantic matching, configure external LoRA API:
```bash
LORA_MATCHER_API_URL=http://your-lora-api:8080
LORA_MATCHER_API_KEY=your-secret-key
```

## 📁 Project Structure

```
cvanalyzer/
├── main.py                    # FastAPI backend application
├── app.py                     # Flask frontend application
├── config.py                  # Configuration management
├── langchain_integration.py   # LoRA model integration
├── schemas.py                 # Pydantic data models
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── tools/                     # Core analysis modules
│   ├── skill_extractor.py     # RAG pipeline & skill analysis
│   ├── feedback_generator.py  # AI feedback generation
│   ├── cv_parser.py          # Document parsing utilities
│   └── skills_kb.json        # Skills knowledge base
├── templates/                 # HTML templates
│   ├── index.html            # Upload page
│   └── result.html           # Results display
├── static/                   # CSS and assets
│   └── styles/
└── logs/                     # Application logs
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/
```

### Manual Testing
```bash
# Test CV parsing
python -c "from tools.cv_parser import parse_cv; print(parse_cv('sample.pdf'))"

# Test skill extraction
python -c "from tools.skill_extractor import extract_and_score_skills; print(extract_and_score_skills('Python developer', 'Need Python skills'))"
```

## 📊 Monitoring

### LangSmith Integration
When configured, the system provides comprehensive tracing:
- Skill extraction chain performance
- LLM prompt/response tracking
- Error tracking and debugging
- Performance metrics

### Logging
- Frontend logs: `/tmp/logs/frontend.log`
- Backend logs: `logs/backend.log`
- Debug level logging for all components

## 🔧 Development

### Adding New Skills
1. Edit `tools/skills_kb.json`
2. Add new skill with category and description
3. Restart the application to reload the knowledge base

### Custom LoRA Models
Implement the API interface:
```
POST /match
Content-Type: application/json
Authorization: Bearer <api_key>

{
  "resume_text": "CV content",
  "job_description": "Job requirements"
}

Response:
{
  "match_score": 0.85,
  "confidence": "High"
}
```

### Extending Feedback
Modify `tools/feedback_generator.py` to add new feedback categories or customize prompts.

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key in `.env`
   - Check rate limits and billing

2. **File Upload Issues**
   - Ensure file size under 16MB
   - Verify PDF/DOCX format

3. **LoRA API Timeouts**
   - Check external API availability
   - Verify network connectivity
   - Review API key configuration

### Debug Mode
Enable detailed logging:
```bash
export LANGSMITH_TRACING=true
export DEBUG=true
```


