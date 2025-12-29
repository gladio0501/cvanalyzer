"""
Job Sources Module.
Unified interface for multiple job data sources.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class JobSource(Enum):
    """Available job data sources."""
    JOBICY = "jobicy"
    JOBSPY = "jobspy"


class UnifiedJobFetcher:
    """
    Unified job fetcher that supports multiple data sources.
    """
    
    def __init__(self, source: JobSource = JobSource.JOBICY):
        """
        Initialize the job fetcher.
        
        Args:
            source (JobSource): Which job source to use
        """
        self.source = source
        self._cache: Dict[str, Any] = {}
        self._cache_duration = timedelta(minutes=30)
        
        logger.info(f"Initialized UnifiedJobFetcher with source: {source.value}")
    
    def fetch_jobs(
        self,
        region: Optional[str] = None,
        job_title: Optional[str] = None,
        limit: int = 50,
        site_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs from the configured source.
        """
        if self.source == JobSource.JOBICY:
            return self._fetch_from_jobicy(region=region, limit=limit)
        elif self.source == JobSource.JOBSPY:
            return self._fetch_from_jobspy(
                location=region,
                search_term=job_title,
                results_wanted=limit,
                site_names=site_names
            )
        else:
            logger.error(f"Unknown job source: {self.source}")
            return []
    
    def _fetch_from_jobicy(self, region: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch jobs from Jobicy API."""
        try:
            from tools.job_fetcher import JobFetcher
            
            logger.info(f"Fetching jobs from Jobicy API (region: {region}, limit: {limit})")
            
            fetcher = JobFetcher()
            jobs = fetcher.fetch_jobs(region=region, limit=limit)
            
            logger.info(f"Successfully fetched {len(jobs)} jobs from Jobicy")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching from Jobicy: {e}")
            return []
    
    def _fetch_from_jobspy(
        self,
        location: Optional[str] = None,
        search_term: Optional[str] = None,
        results_wanted: int = 50,
        site_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch jobs using JobSpy scraper.
        
        Args:
            location (str): Geographic location (e.g., "USA", "New York", "Remote")
            search_term (str): Job title or keywords to search
            results_wanted (int): Number of results to fetch
            site_names (List[str]): Sites to scrape from
        """
        try:
            from jobspy import scrape_jobs
            import pandas as pd
            
            logger.info(f"Scraping jobs using JobSpy (location: {location}, search: {search_term})")
            
            # Default to all sites if not specified
            if not site_names:
                site_names = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
            
            # Default search term if not provided
            if not search_term:
                search_term = "software engineer"
            
            # Set location - JobSpy uses "USA" format
            location = location or "USA"
            
            # Scrape jobs
            logger.info(f"JobSpy: Scraping from {', '.join(site_names)}...")
            
            jobs_df = scrape_jobs(
                site_name=site_names,
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                country_indeed='USA',  # Default country
                hours_old=72,  # Jobs posted in last 72 hours
                linkedin_fetch_description=True  # Get full descriptions
            )
            
            if jobs_df is None or jobs_df.empty:
                logger.warning("JobSpy returned no jobs")
                return []
            
            logger.info(f"JobSpy scraped {len(jobs_df)} jobs, normalizing...")
            
            # Normalize JobSpy data to our standard format
            normalized_jobs = []
            for _, row in jobs_df.iterrows():
                try:
                    normalized_job = self._normalize_jobspy_entry(row.to_dict())
                    normalized_jobs.append(normalized_job)
                except Exception as e:
                    logger.warning(f"Error normalizing JobSpy job: {e}")
                    continue
            
            logger.info(f"Successfully normalized {len(normalized_jobs)} jobs from JobSpy")
            return normalized_jobs[:results_wanted]
            
        except ImportError:
            logger.error("JobSpy not installed. Run: pip install python-jobspy")
            return []
        except Exception as e:
            logger.error(f"Error fetching from JobSpy: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _normalize_jobspy_entry(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a JobSpy job entry to our standard format.
        
        JobSpy fields:
        - title, company, location, job_type, date_posted
        - description, job_url, company_url
        - min_amount, max_amount, currency
        - site (source: indeed, linkedin, etc.)
        """
        import pandas as pd
        
        # Get salary info
        min_salary = job.get('min_amount')
        max_salary = job.get('max_amount')
        currency = job.get('currency', 'USD')
        
        # Format salary string
        salary_str = ""
        if min_salary and max_salary:
            salary_str = f"${min_salary:,.0f} - ${max_salary:,.0f} {currency}"
        elif min_salary:
            salary_str = f"${min_salary:,.0f}+ {currency}"
        
        # Determine job type
        job_type = job.get('job_type', 'Full-time')
        if pd.notna(job_type):
            job_type = str(job_type).title()
        else:
            job_type = "Not specified"
        
        # Get description
        description = job.get('description', '')
        if not description or pd.isna(description):
            description = f"Position at {job.get('company', 'Company')} for {job.get('title', 'Role')}"
        
        # Get source site
        source_site = job.get('site', 'unknown')
        
        return {
            'id': f"jobspy_{hash(job.get('job_url', job.get('title', 'unknown')))}",
            'title': job.get('title', 'Unknown Position'),
            'company': job.get('company', 'Unknown Company'),
            'location': job.get('location', 'Remote'),
            'description': description,
            'url': job.get('job_url', '#'),
            'job_type': job_type,
            'categories': [source_site.title(), job_type],  # Use source site as category
            'published_date': job.get('date_posted', 'Recently'),
            'salary': salary_str,
            'salary_min': min_salary if pd.notna(min_salary) else None,
            'salary_max': max_salary if pd.notna(max_salary) else None,
            'salary_currency': currency,
            'level': 'Not specified',
            'source': f'JobSpy ({source_site})'
        }


def get_available_job_sources() -> List[Dict[str, str]]:
    """
    Get list of available job sources with descriptions.
    
    Returns:
        List of dicts with 'value', 'name', and 'description'
    """
    return [
        {
            'value': JobSource.JOBICY.value,
            'name': 'Jobicy API',
            'description': 'Fast and reliable remote job listings from Jobicy.com'
        },
        {
            'value': JobSource.JOBSPY.value,
            'name': 'JobSpy Scraper',
            'description': 'Scrape jobs from Indeed, LinkedIn, ZipRecruiter, and Glassdoor'
        }
    ]


# For pandas type checking
try:
    import pandas as pd
except ImportError:
    pd = None


if __name__ == "__main__":
    # Test the unified job fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("Testing Unified Job Fetcher")
    print("="*60)
    
    # Test Jobicy
    print("\n📋 Test 1: Fetch from Jobicy API")
    fetcher_jobicy = UnifiedJobFetcher(source=JobSource.JOBICY)
    jobs = fetcher_jobicy.fetch_jobs(region="Remote", limit=5)
    print(f"✅ Fetched {len(jobs)} jobs from Jobicy")
    if jobs:
        print(f"   Sample: {jobs[0]['title']} at {jobs[0]['company']}")
    
    # Test JobSpy
    print("\n📋 Test 2: Fetch from JobSpy")
    fetcher_jobspy = UnifiedJobFetcher(source=JobSource.JOBSPY)
    jobs = fetcher_jobspy.fetch_jobs(
        region="USA",
        job_title="python developer",
        limit=5,
        site_names=["indeed"]  # Start with just Indeed for faster testing
    )
    print(f"✅ Fetched {len(jobs)} jobs from JobSpy")
    if jobs:
        print(f"   Sample: {jobs[0]['title']} at {jobs[0]['company']}")
    
    print("\n✅ All tests complete!")
