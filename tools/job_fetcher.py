"""
Job Fetcher Module - RSS Feed Integration

This module fetches and parses job listings from external RSS feeds,
specifically designed to work with the Jobicy.com jobs API.

Features:
- RSS feed parsing with XML support
- Job filtering by region/location
- Caching for performance
- Error handling and retry logic
- Job data normalization

Dependencies:
- feedparser: For RSS feed parsing
- requests: For HTTP communication
"""

import feedparser
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class JobFetcher:
    """
    Fetches and filters job listings from RSS feeds.
    
    Attributes:
        base_url (str): Base URL for the job RSS feed
        cache (dict): In-memory cache for job listings
        cache_expiry (datetime): When the cache expires
        cache_duration (int): Cache duration in minutes
    """
    
    def __init__(
        self, 
        base_url: str = "https://jobicy.com/api/v2/remote-jobs",
        cache_duration: int = 30
    ):
        """
        Initialize the JobFetcher.
        
        Args:
            base_url (str): Base URL for job API
            cache_duration (int): Cache duration in minutes
        """
        self.base_url = base_url
        self.cache = {}
        self.cache_expiry = None
        self.cache_duration = cache_duration
    
    def fetch_jobs(
        self, 
        region: Optional[str] = None,
        limit: Optional[int] = 50,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch job listings from RSS feed with optional filtering.
        
        Args:
            region (str): Filter jobs by region/location (e.g., "USA", "Europe", "Remote")
            limit (int): Maximum number of jobs to return
            force_refresh (bool): Force cache refresh
            
        Returns:
            List[Dict[str, Any]]: List of job listings with normalized data
            
        Example:
            >>> fetcher = JobFetcher()
            >>> jobs = fetcher.fetch_jobs(region="Remote", limit=20)
            >>> print(f"Found {len(jobs)} remote jobs")
        """
        cache_key = f"{region}_{limit}"
        
        # Check cache
        if not force_refresh and self._is_cache_valid(cache_key):
            logger.info(f"Returning cached jobs for region: {region}")
            return self.cache[cache_key]
        
        try:
            logger.info(f"Fetching jobs from Jobicy API")
            
            # Fetch from JSON API
            response = requests.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if API returned expected format
            if not data.get('success'):
                logger.error("API returned unsuccessful response")
                return []
            
            # Extract jobs from response
            job_data = data.get('jobs', [])
            
            # Extract jobs from response
            jobs = []
            for job_entry in job_data:
                job = self._normalize_job_entry(job_entry)
                
                # Apply region filter if specified
                if region and not self._matches_region(job, region):
                    continue
                
                jobs.append(job)
                
                # Stop if we have enough jobs matching the region
                if limit and len(jobs) >= limit:
                    break
            
            # Update cache
            self.cache[cache_key] = jobs
            self.cache_expiry = datetime.now() + timedelta(minutes=self.cache_duration)
            
            logger.info(f"Fetched {len(jobs)} jobs (filtered by region: {region})")
            return jobs
            
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            # Return cached data if available, even if expired
            if cache_key in self.cache:
                logger.warning("Returning expired cache due to fetch error")
                return self.cache[cache_key]
            return []
    
    def _build_url(self, region: Optional[str] = None) -> str:
        """
        Build RSS feed URL with parameters.
        
        Args:
            region (str): Region/location filter
            
        Returns:
            str: Complete RSS feed URL
        """
        if not region:
            return self.base_url
        
        # Jobicy RSS feed supports location filtering
        params = {}
        if region:
            params['location'] = region
        
        if params:
            return f"{self.base_url}?{urlencode(params)}"
        return self.base_url
    
    def _normalize_job_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize API job entry into standardized job format.
        
        Args:
            entry: Job data from API
            
        Returns:
            Dict[str, Any]: Normalized job data
        """
        # Build normalized job object from Jobicy API format
        job = {
            "id": str(entry.get("id", "")),
            "title": entry.get("jobTitle", "Unknown Title"),
            "company": entry.get("companyName", "Unknown Company"),
            "location": entry.get("jobGeo", "Remote"),
            "job_type": ", ".join(entry.get("jobType", [])) if isinstance(entry.get("jobType"), list) else entry.get("jobType", "Full-Time"),
            "description": self._clean_description(entry.get("jobDescription", entry.get("jobExcerpt", ""))),
            "url": entry.get("url", ""),
            "published_date": entry.get("pubDate", ""),
            "categories": entry.get("jobIndustry", []),
            "tags": entry.get("jobIndustry", []),
            "level": entry.get("jobLevel", ""),
            "salary_min": entry.get("salaryMin"),
            "salary_max": entry.get("salaryMax"),
            "salary_currency": entry.get("salaryCurrency"),
            "raw_entry": entry  # Keep original for debugging
        }
        
        return job
    
    def _extract_location(self, entry: Any) -> str:
        """Extract location from job entry."""
        # Check tags for location
        tags = entry.get("tags", [])
        for tag in tags:
            term = tag.get("term", "")
            if any(loc in term.lower() for loc in ["remote", "usa", "europe", "asia", "worldwide"]):
                return term
        
        # Try to extract from title or description
        title = entry.get("title", "").lower()
        if "remote" in title:
            return "Remote"
        
        return "Not specified"
    
    def _extract_company(self, entry: Any) -> str:
        """Extract company name from job entry."""
        # Try author field
        author = entry.get("author", "")
        if author:
            return author
        
        # Try to extract from title (format: "Title at Company")
        title = entry.get("title", "")
        if " at " in title:
            return title.split(" at ")[-1].strip()
        
        return "Not specified"
    
    def _extract_job_type(self, entry: Any) -> str:
        """Extract job type from entry."""
        tags = entry.get("tags", [])
        for tag in tags:
            term = tag.get("term", "").lower()
            if any(jtype in term for jtype in ["full-time", "part-time", "contract", "freelance"]):
                return tag.get("term", "")
        
        return "Full-time"  # Default
    
    def _clean_description(self, description: str) -> str:
        """Clean and truncate job description."""
        # Remove HTML tags
        import re
        clean = re.sub(r'<[^>]+>', '', description)
        
        # Truncate if too long
        max_length = 1000
        if len(clean) > max_length:
            clean = clean[:max_length] + "..."
        
        return clean.strip()
    
    def _parse_date(self, date_str: str) -> str:
        """Parse and format publication date."""
        try:
            # feedparser usually provides parsed date
            return date_str if date_str else "Unknown"
        except:
            return "Unknown"
    
    def _matches_region(self, job: Dict[str, Any], region: str) -> bool:
        """
        Check if job matches the specified region.
        
        Args:
            job (dict): Job data
            region (str): Target region
            
        Returns:
            bool: True if job matches region
        """
        region_lower = region.lower()
        
        # Check location field
        if region_lower in job["location"].lower():
            return True
        
        # Check categories
        for category in job.get("categories", []):
            if region_lower in category.lower():
                return True
        
        # Special handling for "Remote"
        if region_lower == "remote":
            if "remote" in job["location"].lower():
                return True
            if "remote" in job["title"].lower():
                return True
        
        return False
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid."""
        if cache_key not in self.cache:
            return False
        
        if not self.cache_expiry:
            return False
        
        return datetime.now() < self.cache_expiry
    
    def clear_cache(self):
        """Clear the job cache."""
        self.cache.clear()
        self.cache_expiry = None
        logger.info("Job cache cleared")


def fetch_jobs_for_region(region: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch jobs.
    
    Args:
        region (str): Filter by region
        limit (int): Maximum number of jobs
        
    Returns:
        List[Dict[str, Any]]: Job listings
        
    Example:
        >>> jobs = fetch_jobs_for_region("Remote", limit=20)
        >>> for job in jobs[:5]:
        ...     print(f"{job['title']} at {job['company']}")
    """
    fetcher = JobFetcher()
    return fetcher.fetch_jobs(region=region, limit=limit)


if __name__ == "__main__":
    # Test the job fetcher
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Testing Job Fetcher...")
    print("=" * 60)
    
    fetcher = JobFetcher()
    
    # Test 1: Fetch all jobs
    print("\n📋 Test 1: Fetching all jobs (limit 10)")
    jobs = fetcher.fetch_jobs(limit=10)
    print(f"Found {len(jobs)} jobs")
    if jobs:
        print(f"Sample job: {jobs[0]['title']} at {jobs[0]['company']}")
    
    # Test 2: Fetch remote jobs
    print("\n🌍 Test 2: Fetching remote jobs (limit 10)")
    remote_jobs = fetcher.fetch_jobs(region="Remote", limit=10)
    print(f"Found {len(remote_jobs)} remote jobs")
    if remote_jobs:
        for i, job in enumerate(remote_jobs[:3], 1):
            print(f"{i}. {job['title']} - {job['location']}")
    
    # Test 3: Cache test
    print("\n💾 Test 3: Testing cache")
    import time
    start = time.time()
    cached_jobs = fetcher.fetch_jobs(region="Remote", limit=10)
    elapsed = time.time() - start
    print(f"Cached fetch took {elapsed:.3f} seconds")
    print(f"Got {len(cached_jobs)} jobs from cache")
    
    print("\n✅ Job fetcher tests complete!")
