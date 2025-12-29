# CV Analyzer - AI-Powered Resume Analysis System

A sophisticated CV analysis system with a modern React frontend and dual backend architecture (Flask + FastAPI) providing comprehensive resume-job matching analysis with Google OAuth authentication.

## 🚀 Features

### Core Capabilities

- **Modern React Frontend**: Built with React 18, TypeScript, Vite, and Tailwind CSS
- **Secure Authentication**: Google OAuth integration with JWT tokens
- **Multi-format CV Parsing**: Supports PDF, DOC, DOCX, and TXT formats
- **RAG-based Skill Extraction**: Uses FAISS vector store with OpenAI embeddings
- **Dual Job Sources**: 
  - Jobicy API (fast, curated remote jobs)
  - JobSpy Scraper (Indeed, LinkedIn, ZipRecruiter, Glassdoor)
- **AI-Powered Analysis**: GPT-powered CV matching and feedback generation
- **Real-time Results**: Interactive job search with filtering and sorting
- **Comprehensive Monitoring**: LangSmith tracing integration

### Advanced Features

- **Drag-and-Drop Upload**: Intuitive file upload with react-dropzone
- **Form Validation**: Client-side validation with zod and react-hook-form
- **Protected Routes**: JWT-based authentication with automatic token refresh
- **State Management**: Zustand for global state with localStorage persistence
- **Responsive Design**: Mobile-first Tailwind CSS design system
- **Region-based Filtering**: Filter jobs by location (Remote, USA, Europe, etc.)
- **Match Scoring**: AI-powered relevance scoring with visual badges
- **Save Jobs**: Bookmark jobs for later review

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│                   Port 5173 (Development)                    │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Auth Pages  │  │   CV Upload  │  │  Job Search  │     │
│  │  - Login     │  │  - Dropzone  │  │  - Filters   │     │
│  │  - Callback  │  │  - Analysis  │  │  - Results   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  State Management (Zustand) + API Client (Axios)     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Flask Backend (API Mode)                  │
│                        Port 5001                             │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  OAuth       │  │  CV Upload   │  │  Job Sources │     │
│  │  Routes      │  │  Processing  │  │  Management  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  SQLAlchemy ORM + Alembic Migrations               │  │
│  │  Models: User, CVUpload, JobSearch, SavedJob        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Internal API Calls
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (AI/ML)                    │
│                        Port 8000                             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  RAG Pipeline + FAISS Vector Store + OpenAI LLM     │  │
│  │  - CV Analysis       - Job Matching                  │  │
│  │  - Skill Extraction  - Feedback Generation           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
                  ┌─────────────────┐
                  │   External APIs  │
                  │  - OpenAI GPT    │
                  │  - Jobicy API    │
                  │  - JobSpy        │
                  └─────────────────┘
```

## 📦 Installation

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- OpenAI API key
- Google Cloud OAuth credentials
- (Optional) LangSmith account for tracing

### Backend Setup

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

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
alembic upgrade head
```

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install npm dependencies**
```bash
npm install
```

3. **Configure frontend environment** (if needed)
```bash
# Vite automatically proxies /api to Flask backend
```

### Google OAuth Setup

Follow [OAUTH_SETUP.md](OAUTH_SETUP.md) for detailed instructions:

1. Create Google Cloud project
2. Configure OAuth consent screen
3. Create OAuth 2.0 credentials
4. Add authorized redirect URI: `http://localhost:5001/api/auth/callback/google`
5. Update `.env` with `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`

### Environment Variables

See [PORT_CONFIGURATION.md](PORT_CONFIGURATION.md) for port details.

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_PORT` | No | Flask server port (default: 5001) |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `JWT_SECRET_KEY` | Yes | Secret key for JWT tokens |
| `JWT_ACCESS_TOKEN_EXPIRES` | No | Access token expiry in seconds (default: 86400) |
| `JWT_REFRESH_TOKEN_EXPIRES` | No | Refresh token expiry in seconds (default: 2592000) |
| `FRONTEND_URL` | No | React dev server URL (default: http://localhost:5173) |
| `CORS_ORIGINS` | No | Allowed CORS origins |
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM and embeddings |
| `DATABASE_URL` | No | SQLite database path (default: sqlite:///cvanalyzer.db) |

## 🚀 Usage

### Starting the Services

**Development Mode (3 terminals required):**

1. **Terminal 1: FastAPI Backend (AI/ML)**
```bash
cd /path/to/cvanalyzer
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Terminal 2: Flask Backend (OAuth & API)**
```bash
cd /path/to/cvanalyzer
source venv/bin/activate
python app.py
# Runs on port 5001 (port 5000 conflicts with macOS AirPlay)
```

3. **Terminal 3: React Frontend**
```bash
cd /path/to/cvanalyzer/frontend
npm run dev
# Runs on port 5173, proxies /api to Flask
```

4. **Access the application**
- Open browser to `http://localhost:5173`
- Login with Google account
- Access dashboard with quick actions

### Application Features

#### 1. Dashboard
- User profile with OAuth info
- Quick action cards (Upload CV, Search Jobs, Saved Jobs)
- Activity statistics
- Logout functionality

#### 2. CV Analysis
- Drag-and-drop CV upload (PDF/DOC/DOCX/TXT)
- Enter job description (text area)
- Get comprehensive analysis:
  - Match score
  - Skills analysis
  - AI-generated feedback
  - Improvement recommendations

#### 3. Job Search
- Choose job source:
  - **Jobicy API**: Fast, curated remote jobs
  - **JobSpy**: Scrape Indeed, LinkedIn, ZipRecruiter, Glassdoor
- Optional filters:
  - Region (Remote, USA, Europe, Asia, etc.)
  - Job title (for JobSpy)
  - Number of results (5-50)
  - Sites to scrape (for JobSpy)
- Real-time progress indicators

#### 4. Job Results
- Filter by match score range
- Sort by score or date
- Search by keywords
- View detailed job descriptions
- Save jobs for later
- Direct application links

## 📁 Project Structure

```
cvanalyzer/
├── backend/
│   ├── app.py                      # Flask server (OAuth, API gateway)
│   ├── main.py                     # FastAPI server (AI/ML)
│   ├── config.py                   # Configuration management
│   ├── database.py                 # SQLAlchemy setup
│   ├── models.py                   # Database models
│   ├── schemas.py                  # Pydantic schemas
│   ├── alembic.ini                 # Alembic configuration
│   ├── migrations/                 # Database migrations
│   ├── auth/                       # OAuth module
│   │   ├── __init__.py
│   │   ├── routes.py               # Auth endpoints
│   │   ├── middleware.py           # JWT decorators
│   │   └── oauth_config.py         # OAuth setup
│   └── tools/                      # AI/ML modules
│       ├── cv_parser.py            # Document parsing
│       ├── skill_extractor.py      # RAG pipeline
│       ├── feedback_generator.py   # AI feedback
│       ├── job_fetcher.py          # Job sources
│       └── skills_kb.json          # Skills database
├── frontend/
│   ├── src/
│   │   ├── api/                    # API client layer
│   │   │   ├── client.ts           # Axios instance
│   │   │   ├── auth.ts             # Auth endpoints
│   │   │   ├── cv.ts               # CV endpoints
│   │   │   └── jobs.ts             # Job endpoints
│   │   ├── components/             # React components
│   │   │   └── ProtectedRoute.tsx  # Auth guard
│   │   ├── pages/                  # Page components
│   │   │   ├── LoginPage.tsx       # Google OAuth login
│   │   │   ├── AuthCallback.tsx    # OAuth callback
│   │   │   ├── DashboardPage.tsx   # User dashboard
│   │   │   ├── CVUploadPage.tsx    # CV analysis
│   │   │   ├── JobSearchPage.tsx   # Job search form
│   │   │   └── JobResultsPage.tsx  # Job results display
│   │   ├── hooks/                  # Custom React hooks
│   │   │   └── useAuth.ts          # Auth hook
│   │   ├── store/                  # Zustand stores
│   │   │   └── authStore.ts        # Auth state
│   │   ├── types/                  # TypeScript types
│   │   │   └── index.ts            # Type definitions
│   │   ├── App.tsx                 # Main app component
│   │   └── main.tsx                # Entry point
│   ├── package.json                # npm dependencies
│   ├── vite.config.ts              # Vite configuration
│   ├── tailwind.config.js          # Tailwind CSS config
│   └── tsconfig.json               # TypeScript config
├── .env                            # Environment variables
├── .env.example                    # Example environment
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── OAUTH_SETUP.md                  # OAuth setup guide
├── PORT_CONFIGURATION.md           # Port documentation
└── FRONTEND_MODERNIZATION_PLAN.md  # Migration plan
```


