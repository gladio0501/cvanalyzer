"""
Pytest configuration and fixtures for CVAnalyzer tests.
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing without API calls."""
    return {
        "choices": [
            {
                "message": {
                    "content": '{"skills": ["Python", "FastAPI", "Machine Learning"], "experience_years": 5}'
                }
            }
        ]
    }


@pytest.fixture
def sample_cv_text():
    """Sample CV text for testing."""
    return """
    John Doe
    Software Engineer
    
    EXPERIENCE:
    Senior Software Engineer at TechCorp (2020-Present)
    - Developed REST APIs using Python and FastAPI
    - Implemented machine learning models for data analysis
    - Led a team of 5 developers
    
    Software Developer at StartupXYZ (2018-2020)
    - Built backend services using Django
    - Worked with PostgreSQL and Redis
    - Implemented CI/CD pipelines
    
    SKILLS:
    - Python, JavaScript, TypeScript
    - FastAPI, Django, Flask
    - Machine Learning, TensorFlow, PyTorch
    - Docker, Kubernetes, AWS
    - PostgreSQL, MongoDB, Redis
    
    EDUCATION:
    Master of Computer Science - MIT (2018)
    Bachelor of Computer Science - Stanford (2016)
    """


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Backend Developer
    
    We are looking for an experienced backend developer to join our team.
    
    Requirements:
    - 5+ years of experience with Python
    - Experience with FastAPI or Django
    - Strong knowledge of REST API design
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - Knowledge of containerization (Docker, Kubernetes)
    - Database experience (PostgreSQL, MongoDB)
    
    Nice to have:
    - Machine Learning experience
    - Experience leading development teams
    - Knowledge of microservices architecture
    """


@pytest.fixture
def good_match_cv():
    """CV that should have a high match score with sample_job_description."""
    return """
    Jane Smith
    Senior Backend Developer
    
    EXPERIENCE:
    Lead Backend Developer at CloudTech (2019-Present)
    - Architected REST APIs using Python and FastAPI
    - Deployed services on AWS using Docker and Kubernetes
    - Managed PostgreSQL and MongoDB databases
    - Led a team of 4 backend developers
    
    Backend Developer at DataCorp (2016-2019)
    - Built Django applications for data processing
    - Implemented microservices architecture
    - Applied machine learning for recommendation systems
    
    SKILLS:
    - Python (7 years)
    - FastAPI, Django
    - AWS, Docker, Kubernetes
    - PostgreSQL, MongoDB
    - Machine Learning, TensorFlow
    - REST API Design
    - Team Leadership
    
    EDUCATION:
    Master of Computer Science - MIT (2016)
    """


@pytest.fixture
def bad_match_cv():
    """CV that should have a low match score with sample_job_description."""
    return """
    Bob Johnson
    Marketing Manager
    
    EXPERIENCE:
    Marketing Director at AdAgency (2018-Present)
    - Managed marketing campaigns
    - Created social media strategies
    - Analyzed marketing metrics using Excel
    
    Marketing Coordinator at BrandCo (2015-2018)
    - Coordinated marketing events
    - Wrote marketing copy
    
    SKILLS:
    - Marketing Strategy
    - Social Media Management
    - Content Creation
    - Excel, PowerPoint
    - Adobe Photoshop
    - Public Speaking
    
    EDUCATION:
    MBA in Marketing - NYU (2015)
    """


@pytest.fixture
def mock_llm():
    """Mock LLM for testing without making API calls."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content='{"skills": ["Python", "FastAPI"], "score": 0.85}')
    return mock


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing."""
    import numpy as np
    return np.random.rand(1536).tolist()


@pytest.fixture(scope="session")
def test_pdf_path(tmp_path_factory):
    """Create a temporary PDF file for testing."""
    import io
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        pdf_path = tmp_path_factory.mktemp("data") / "test_cv.pdf"
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.drawString(100, 750, "Test CV Content")
        c.drawString(100, 735, "Skills: Python, FastAPI, Machine Learning")
        c.drawString(100, 720, "Experience: 5 years of software development")
        c.save()
        
        with open(pdf_path, "wb") as f:
            f.write(buffer.getvalue())
        
        return str(pdf_path)
    except ImportError:
        pytest.skip("reportlab not installed, skipping PDF tests")


@pytest.fixture
def mock_job_data():
    """Mock job data from job sources."""
    return [
        {
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "description": "We are looking for a senior Python developer...",
            "url": "https://example.com/job1",
            "date_posted": "2024-01-15"
        },
        {
            "title": "Backend Engineer",
            "company": "StartupXYZ",
            "location": "San Francisco, CA",
            "description": "Join our team as a backend engineer...",
            "url": "https://example.com/job2",
            "date_posted": "2024-01-14"
        },
        {
            "title": "Full Stack Developer",
            "company": "WebAgency",
            "location": "New York, NY",
            "description": "Looking for a full stack developer...",
            "url": "https://example.com/job3",
            "date_posted": "2024-01-13"
        }
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "functional: mark test as a functional test"
    )
    config.addinivalue_line(
        "markers", "accuracy: mark test as an accuracy test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
