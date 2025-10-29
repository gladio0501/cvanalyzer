# Job Sources Integration

The CV Analyzer now supports **two job data sources** for job recommendations:

## 🔧 Available Sources

### 1. **Jobicy API** (Default)
- **Speed**: ⚡ Fast (< 5 seconds)
- **Coverage**: Remote jobs from Jobicy.com
- **Reliability**: Very high (stable API)
- **Best for**: Quick searches, remote job seekers
- **Data**: Curated remote job listings with detailed metadata

**Pros:**
- Very fast responses
- Reliable and stable
- Well-structured job data
- Good for remote work seekers

**Cons:**
- Limited to remote jobs only
- Smaller job pool compared to scraping

### 2. **JobSpy Scraper**
- **Speed**: 🐢 Slower (30-120 seconds depending on sites)
- **Coverage**: Indeed, LinkedIn, ZipRecruiter, Glassdoor
- **Reliability**: Medium (depends on site availability)
- **Best for**: Comprehensive searches, location-specific jobs
- **Data**: Live jobs from major job boards

**Pros:**
- Much larger job pool
- Fresh, up-to-date listings
- Multiple sources (Indeed, LinkedIn, etc.)
- Location-specific searches
- Job title-based filtering

**Cons:**
- Slower (requires web scraping)
- May occasionally fail if sites block scraping
- More resource-intensive

## 🎯 How to Choose

| Your Need | Recommended Source |
|-----------|-------------------|
| Quick remote job matches | **Jobicy API** |
| Location-specific jobs (NYC, SF, etc.) | **JobSpy** |
| Searching for specific role (e.g., "Data Scientist") | **JobSpy** |
| Maximum speed | **Jobicy API** |
| Maximum job coverage | **JobSpy** |
| International remote jobs | **Jobicy API** |

## 💻 Usage

### Web Interface (Flask)

1. Navigate to http://localhost:5000/jobs
2. Upload your CV
3. Select job source:
   - **Jobicy API**: Fast, remote jobs
   - **JobSpy Scraper**: Scrape major job boards
4. If using JobSpy:
   - Enter job title (e.g., "Python Developer")
   - Select sites to scrape (Indeed, LinkedIn, etc.)
5. Choose region and number of results
6. Submit and wait for results

### API Endpoint (FastAPI)

```python
import requests

# Example 1: Jobicy API (fast)
with open("my_cv.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/recommend_jobs",
        files={"file": f},
        data={
            "job_source": "jobicy",
            "region": "Remote",
            "top_k": 10
        }
    )

# Example 2: JobSpy Scraper (comprehensive)
with open("my_cv.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/recommend_jobs",
        files={"file": f},
        data={
            "job_source": "jobspy",
            "job_title": "Software Engineer",
            "region": "USA",
            "jobspy_sites": "indeed,linkedin",
            "top_k": 20
        }
    )

print(response.json())
```

## 🛠️ Technical Implementation

### Architecture

```
┌─────────────────┐
│  Flask Frontend │
│  (jobs.html)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Backend│
│  (main.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  UnifiedJobFetcher          │
│  (job_sources.py)           │
└────────┬────────────────────┘
         │
    ┌────┴─────┐
    ▼          ▼
┌─────────┐  ┌──────────┐
│ Jobicy  │  │ JobSpy   │
│ API     │  │ Scraper  │
└─────────┘  └──────────┘
```

### Key Components

1. **`tools/job_sources.py`**: Unified interface for job fetching
   - `JobSource` enum: JOBICY, JOBSPY
   - `UnifiedJobFetcher`: Abstracts source selection
   - Normalizes data from different sources to common format

2. **`tools/job_recommendation_chain.py`**: Updated to support multiple sources
   - Accepts `job_source` parameter
   - Passes additional parameters (job_title, jobspy_sites)
   
3. **`main.py`**: FastAPI endpoint updates
   - New parameters: `job_source`, `job_title`, `jobspy_sites`
   - Validates job source selection
   - Increased timeout for JobSpy (120s)

4. **`templates/jobs.html`**: Dynamic UI
   - Job source selector
   - Conditional fields for JobSpy (job title, site selection)
   - Loading states adapted to source speed

## 📊 Data Format

Both sources return normalized job data:

```python
{
    "id": "job_12345",
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "location": "Remote",
    "description": "Full job description...",
    "url": "https://job-link.com",
    "job_type": "Full-time",
    "categories": ["Engineering", "Remote"],
    "published_date": "2025-10-18",
    "salary": "$120k - $150k USD",
    "salary_min": 120000,
    "salary_max": 150000,
    "salary_currency": "USD",
    "level": "Senior",
    "source": "Jobicy API"  # or "JobSpy (indeed)"
}
```

## 🔧 Configuration

No additional configuration needed! JobSpy is installed via:

```bash
pip install python-jobspy
```

Already included in `requirements.txt`.

## 🐛 Troubleshooting

### JobSpy Returns No Results
- Check if job title is too specific
- Try selecting more sites
- Verify region format (use "USA" not "United States")
- Check internet connection (scraping requires external access)

### JobSpy Timeout Error
- Reduce number of sites selected
- Reduce `top_k` parameter
- Try again later (site may be temporarily slow)

### Jobicy Returns Few Results
- Try broader region ("Remote" instead of specific country)
- Increase `limit` parameter
- Check if region filter is too restrictive

## 📈 Performance Comparison

| Metric | Jobicy API | JobSpy (1 site) | JobSpy (4 sites) |
|--------|-----------|----------------|-----------------|
| **Speed** | 2-5s | 15-30s | 60-120s |
| **Jobs Returned** | 10-50 | 10-100+ | 40-400+ |
| **Success Rate** | 99%+ | 90-95% | 85-90% |
| **Network Usage** | Low | Medium | High |
| **CPU Usage** | Minimal | Low-Med | Medium |

## 🚀 Future Enhancements

Potential additions:
- [ ] Cache JobSpy results for common searches
- [ ] Add more job boards (Monster, Dice, etc.)
- [ ] Background job scraping with webhooks
- [ ] Job alert subscriptions
- [ ] Advanced filters (salary range, seniority level)

## 📝 Credits

- **Jobicy API**: https://jobicy.com/api/v2/remote-jobs
- **JobSpy**: https://github.com/speedyapply/JobSpy
