# Frontend Modernization & OAuth Implementation Plan

## Executive Summary
Transform CVAnalyzer from a Flask-rendered application to a modern Single Page Application (SPA) with React frontend and OAuth authentication, while maintaining API compatibility with existing backend services.

## Goals
1. **Modern Frontend**: Migrate to React + TypeScript with Vite for better UX and maintainability
2. **User Authentication**: Implement OAuth 2.0 for secure user login (Google, GitHub, LinkedIn)
3. **User Persistence**: Store CVs, search history, and preferences per user
4. **Improved UX**: Add real-time updates, better loading states, and responsive design
5. **API Architecture**: Transform Flask from template rendering to pure REST API

## Technology Stack

### Frontend
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (fast HMR, optimized builds)
- **UI Library**: shadcn/ui (customizable, Tailwind-based components)
- **Styling**: Tailwind CSS 3.x
- **Routing**: React Router v6
- **State Management**: Zustand (simpler than Redux)
- **Forms**: react-hook-form + zod validation
- **HTTP Client**: Axios with interceptors
- **Real-time**: Socket.IO client (optional Phase 3)

### Backend Additions
- **OAuth**: Authlib (OAuth 2.0 client)
- **Database**: SQLAlchemy + Alembic migrations
- **DB Engine**: SQLite (dev) / PostgreSQL (prod)
- **Auth**: Flask-JWT-Extended for token management
- **WebSockets**: Flask-SocketIO (optional Phase 3)
- **API Validation**: Pydantic (already in use)

### Infrastructure
- **Development**: Vite dev server (port 5173) + Flask API (port 8000)
- **Production**: Nginx serving React build + proxying to Flask
- **Deployment**: Docker + docker-compose

## Implementation Phases

---

## **PHASE 1: Foundation & Authentication** (Week 1-2)
**Goal**: Set up database, OAuth backend, and basic React structure

### Chunk 1.1: Database Setup (2-3 days)
**Files to create**:
- `models.py` - SQLAlchemy models
- `database.py` - Database configuration
- `migrations/` - Alembic migration scripts

**Tasks**:
1. Install dependencies: `sqlalchemy`, `alembic`, `psycopg2-binary`
2. Create User model:
   ```python
   class User(Base):
       id = Column(Integer, primary_key=True)
       email = Column(String, unique=True, nullable=False)
       name = Column(String)
       oauth_provider = Column(String)  # google, github, linkedin
       oauth_id = Column(String)
       profile_picture = Column(String)
       created_at = Column(DateTime, default=datetime.utcnow)
   ```
3. Create CVUpload model (links to User)
4. Create JobSearch model (stores search history)
5. Initialize Alembic: `alembic init migrations`
6. Create initial migration: `alembic revision --autogenerate -m "Initial schema"`
7. Apply migration: `alembic upgrade head`

**Testing**: Verify database creation and models work

---

### Chunk 1.2: OAuth Backend (3-4 days)
**Files to create**:
- `auth/routes.py` - OAuth endpoints
- `auth/oauth_config.py` - Provider configurations
- `auth/middleware.py` - Authentication decorators

**Tasks**:
1. Install Authlib: `pip install Authlib`
2. Register apps with OAuth providers:
   - Google: https://console.cloud.google.com/
   - GitHub: https://github.com/settings/developers
   - LinkedIn: https://www.linkedin.com/developers/apps
3. Add environment variables to `config.py`:
   ```python
   GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
   GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
   # ... repeat for GitHub, LinkedIn
   JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
   ```
4. Implement OAuth routes:
   - `GET /api/auth/login/<provider>` - Redirect to OAuth provider
   - `GET /api/auth/callback/<provider>` - Handle OAuth callback
   - `POST /api/auth/logout` - Clear session/token
   - `GET /api/auth/me` - Get current user info
5. Implement JWT token generation and validation
6. Create `@require_auth` decorator for protected routes

**Testing**: Test OAuth flow manually with Postman/browser

---

### Chunk 1.3: React Project Setup (2 days)
**Commands**:
```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install react-router-dom axios zustand react-dropzone react-hook-form zod
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
npx shadcn-ui@latest init
```

**Files to create**:
- `frontend/src/api/client.ts` - Axios instance with interceptors
- `frontend/src/store/authStore.ts` - Zustand auth store
- `frontend/src/hooks/useAuth.ts` - Auth hook
- `frontend/src/context/AuthContext.tsx` - Auth context provider

**Tasks**:
1. Configure Vite proxy in `vite.config.ts`:
   ```typescript
   server: {
     proxy: {
       '/api': 'http://localhost:8000'
     }
   }
   ```
2. Set up Tailwind CSS
3. Install shadcn/ui components: `button`, `dropdown-menu`, `card`, `input`, `badge`
4. Create axios instance with auth token interceptor
5. Create basic folder structure
6. Create placeholder pages (Login, Dashboard, Upload, Jobs)

**Testing**: Verify React app runs on `npm run dev`

---

### Chunk 1.4: Authentication UI (2-3 days)
**Files to create**:
- `frontend/src/pages/LoginPage.tsx`
- `frontend/src/components/AuthCallback.tsx`
- `frontend/src/components/ProtectedRoute.tsx`
- `frontend/src/components/Navbar.tsx`

**Tasks**:
1. Create login page with provider buttons
2. Implement OAuth redirect logic
3. Create callback handler that exchanges code for JWT
4. Store JWT in localStorage and Zustand store
5. Create navbar with user dropdown (avatar, logout)
6. Implement protected route wrapper
7. Add auto-redirect to login for unauthenticated users

**Testing**: Complete OAuth flow end-to-end

---

## **PHASE 2: Core Features Migration** (Week 3-4)
**Goal**: Migrate existing Flask templates to React components

### Chunk 2.1: Update Flask Backend to API-only (2 days)
**Files to modify**:
- `app.py` - Remove template rendering
- `main.py` - Add CORS, update responses

**Tasks**:
1. Install Flask-CORS: `pip install flask-cors`
2. Configure CORS for React dev server:
   ```python
   from flask_cors import CORS
   CORS(app, origins=["http://localhost:5173"])
   ```
3. Update all routes to return JSON instead of `render_template()`
4. Add `/api/v1/` prefix to all endpoints
5. Standardize error responses:
   ```python
   {"error": "message", "code": "ERROR_CODE"}
   ```
6. Remove `templates/` directory dependencies
7. Update file upload handling for API mode

**Testing**: Test all endpoints with Postman/curl

---

### Chunk 2.2: CV Upload Page (3 days)
**Files to create**:
- `frontend/src/pages/UploadPage.tsx`
- `frontend/src/components/CVUploader.tsx`
- `frontend/src/components/CVList.tsx`
- `frontend/src/api/cvAPI.ts`

**Tasks**:
1. Create drag-and-drop upload zone with react-dropzone
2. Implement file validation (PDF only, max 10MB)
3. Show upload progress with progress bar
4. Display uploaded CV list from database
5. Add delete CV functionality
6. Create API endpoints in Flask:
   - `POST /api/v1/cv/upload` (protected)
   - `GET /api/v1/cv/list` (protected)
   - `DELETE /api/v1/cv/:id` (protected)
7. Link CVs to authenticated user in database

**Testing**: Upload, list, delete CVs; verify database storage

---

### Chunk 2.3: Job Search Page (3 days)
**Files to create**:
- `frontend/src/pages/JobSearchPage.tsx`
- `frontend/src/components/JobSourceSelector.tsx`
- `frontend/src/components/JobicyForm.tsx`
- `frontend/src/components/JobSpyForm.tsx`
- `frontend/src/api/jobsAPI.ts`

**Tasks**:
1. Create job source selector (radio buttons: Jobicy vs JobSpy)
2. Build Jobicy form (CV selector, region dropdown)
3. Build JobSpy form (CV selector, job title, sites checkboxes, region)
4. Add form validation with react-hook-form + zod
5. Implement conditional rendering based on source selection
6. Show loading state during job fetching (30-120s for JobSpy)
7. Integrate with existing `/api/v1/jobs/recommend` endpoint
8. Store search parameters in database for history

**Testing**: Submit searches with both sources, verify results

---

### Chunk 2.4: Job Results Page (3-4 days)
**Files to create**:
- `frontend/src/pages/JobResultsPage.tsx`
- `frontend/src/components/JobCard.tsx`
- `frontend/src/components/JobDetailModal.tsx`
- `frontend/src/components/JobFilters.tsx`

**Tasks**:
1. Create job card component with:
   - Job title, company, location
   - Color-coded score badge
   - Match reasons
   - Save/bookmark button
2. Implement filtering (score range, job type, location)
3. Add sorting (by score, date posted)
4. Create modal for full job details
5. Add pagination or infinite scroll
6. Implement save job functionality:
   - `POST /api/v1/jobs/save` (protected)
   - `GET /api/v1/jobs/saved` (protected)
7. Show low-score warning from backend
8. Add "Apply" button linking to external URL

**Testing**: Filter, sort, save jobs; verify saved jobs persist

---

## **PHASE 3: Enhanced Features** (Week 5-6)
**Goal**: Add new user-centric features and polish

### Chunk 3.1: User Dashboard (3 days)
**Files to create**:
- `frontend/src/pages/DashboardPage.tsx`
- `frontend/src/components/RecentSearches.tsx`
- `frontend/src/components/SavedJobsWidget.tsx`
- `frontend/src/components/SearchAnalytics.tsx`

**Tasks**:
1. Show recent job searches (last 10)
2. Display saved jobs count
3. Show match score statistics (average, trend)
4. Add quick actions (new search, view saved jobs)
5. Implement "re-run search" button
6. Create analytics API endpoints:
   - `GET /api/v1/analytics/searches` (protected)
   - `GET /api/v1/analytics/scores` (protected)

**Testing**: Verify dashboard loads user-specific data

---

### Chunk 3.2: Profile & Settings (2 days)
**Files to create**:
- `frontend/src/pages/ProfilePage.tsx`
- `frontend/src/pages/SettingsPage.tsx`
- `frontend/src/components/OAuthConnections.tsx`

**Tasks**:
1. Display user info (name, email, avatar)
2. Show connected OAuth providers
3. Add "Connect another account" functionality
4. Create settings for:
   - Default region
   - Email notifications (future)
   - Preferred job sources
5. Implement profile update:
   - `PUT /api/v1/user/profile` (protected)

**Testing**: Update profile, connect multiple OAuth providers

---

### Chunk 3.3: Real-time Updates (3-4 days) [OPTIONAL]
**Files to create**:
- `frontend/src/hooks/useSocket.ts`
- `socketio_events.py` (backend)

**Tasks**:
1. Install Flask-SocketIO: `pip install flask-socketio python-socketio`
2. Install Socket.IO client: `npm install socket.io-client`
3. Emit progress events during JobSpy scraping:
   ```python
   socketio.emit('job_progress', {
       'current': 10,
       'total': 50,
       'message': 'Scraping LinkedIn...'
   })
   ```
4. Create React hook to listen for events
5. Show real-time progress bar during job search
6. Add connection status indicator

**Testing**: Verify progress updates during long searches

---

### Chunk 3.4: Responsive Design & Polish (3 days)
**Tasks**:
1. Test all pages on mobile (375px), tablet (768px), desktop (1024px+)
2. Implement dark mode toggle with system preference detection
3. Add loading skeletons for all async content
4. Create error boundaries for graceful error handling
5. Add toast notifications for success/error messages
6. Optimize images and assets
7. Add meta tags for SEO
8. Create 404 page

**Testing**: Full responsive testing on multiple devices

---

## **PHASE 4: Production & Testing** (Week 7)

### Chunk 4.1: Testing (3 days)
**Tasks**:
1. Write backend tests:
   - OAuth flow tests
   - API endpoint tests
   - Database operation tests
2. Write frontend tests:
   - Component unit tests (Vitest + RTL)
   - Integration tests for user flows
3. Create E2E tests with Playwright:
   - Login flow
   - CV upload → Job search → Save jobs
4. Achieve >80% code coverage

---

### Chunk 4.2: Production Setup (2-3 days)
**Files to create**:
- `Dockerfile` (multi-stage)
- `docker-compose.yml`
- `nginx.conf`
- `.env.production`

**Tasks**:
1. Create production Dockerfile:
   - Stage 1: Build React app (`npm run build`)
   - Stage 2: Serve with Nginx + Flask
2. Configure Nginx:
   - Serve React from `/`
   - Proxy `/api` to Flask
   - Enable gzip compression
   - Configure SSL (Let's Encrypt)
3. Set up environment variables for:
   - OAuth secrets (use Docker secrets)
   - Database URL
   - JWT secret
4. Create health check endpoints
5. Configure logging (rotate logs daily)
6. Set up database backups

---

### Chunk 4.3: Documentation (1-2 days)
**Files to create**:
- Update `README.md`
- `OAUTH_SETUP.md`
- `API_DOCUMENTATION.md`
- `DEVELOPMENT.md`

**Tasks**:
1. Update README with new architecture
2. Document OAuth provider setup steps
3. Create API documentation (consider OpenAPI/Swagger)
4. Write development setup guide
5. Document environment variables
6. Create troubleshooting guide
7. Add deployment instructions

---

## Project Timeline

| Phase | Duration | Parallel Work Possible? |
|-------|----------|------------------------|
| Phase 1: Foundation | 2 weeks | Chunks 1.1-1.2 can be parallel |
| Phase 2: Migration | 2 weeks | Frontend chunks can overlap |
| Phase 3: Enhancement | 2 weeks | Most chunks can be parallel |
| Phase 4: Production | 1 week | Testing and setup sequential |
| **Total** | **7 weeks** | With 2 developers: 4-5 weeks |

## Risk Mitigation

### High-Risk Areas
1. **OAuth Security**: Use proven libraries (Authlib), never store secrets in code
2. **Database Migrations**: Always backup before migration, test rollback
3. **API Breaking Changes**: Version API endpoints, maintain backward compatibility during transition
4. **File Upload Security**: Validate file types, scan for malware, limit file sizes

### Rollback Plan
1. Keep Flask templates functional during Phase 1-2
2. Use feature flags to toggle between old/new UI
3. Maintain separate Git branches for each phase
4. Test on staging environment before production deploy

## Success Metrics
- [ ] All OAuth providers working (Google, GitHub, LinkedIn)
- [ ] 100% feature parity with current Flask app
- [ ] Page load time < 2 seconds
- [ ] Mobile responsive on all pages
- [ ] Test coverage > 80%
- [ ] Zero critical security vulnerabilities
- [ ] Successfully deployed to production

## Post-Launch Enhancements (Future)
- Email notifications for new matching jobs
- CV parsing improvements (extract skills automatically)
- Job alerts (daily/weekly digests)
- Browser extension for quick job saving
- Mobile app (React Native)
- AI-powered CV improvement suggestions
- Interview preparation resources
- Salary negotiation insights
- Company reviews integration

## Resources Needed
- **Developer Time**: 7 weeks (solo) or 4-5 weeks (2 developers)
- **Third-party Services**:
  - OAuth provider accounts (free tier sufficient)
  - PostgreSQL hosting (or use managed service like Render/Railway)
  - Domain name + SSL certificate
  - Optional: CDN for static assets (Cloudflare free tier)
- **Development Environment**:
  - Node.js 18+
  - Python 3.13
  - PostgreSQL 14+
  - Docker + docker-compose

## Getting Started

### Immediate Next Steps
1. **Review and approve this plan**
2. **Set up OAuth applications** with providers (get client IDs/secrets)
3. **Create `.env` file** with configuration:
   ```
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_secret
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_secret
   LINKEDIN_CLIENT_ID=your_client_id
   LINKEDIN_CLIENT_SECRET=your_secret
   JWT_SECRET_KEY=generate_random_string
   DATABASE_URL=sqlite:///cvanalyzer.db
   ```
4. **Start with Chunk 1.1** (Database Setup)
5. **Create feature branch**: `git checkout -b feature/frontend-modernization`

---

**Questions? Concerns? Suggestions?**
This plan is flexible and can be adjusted based on priorities, timeline, or resource constraints. Each chunk is designed to be independently testable and deployable.
