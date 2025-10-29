"""
Job Recommendation Chain

Lightweight chain for matching CVs against multiple job listings.
Uses CV profile extraction + LoRA for efficient, accurate matching.

Features:
- Batch job scoring against CV profile
- LoRA integration for semantic similarity
- Ranking and filtering of job matches
- Explanation generation for top matches
- Optimized for speed (no heavy RAG)

Dependencies:
- langchain: For chain orchestration
- openai: For LLM
"""

from typing import List, Dict, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from tools.cv_profile_extractor import CVProfile, extract_cv_profile
from tools.job_sources import UnifiedJobFetcher, JobSource
from langchain_integration import ResumeJobMatcherTool

logger = logging.getLogger(__name__)


class JobMatch(BaseModel):
    """Represents a job match result."""
    
    job_id: str = Field(description="Job ID")
    job_title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Job location")
    match_score: float = Field(description="Overall match score (0-100)")
    lora_score: float = Field(description="LoRA semantic similarity score")
    profile_score: float = Field(description="Profile-based match score")
    match_reasons: List[str] = Field(description="Why this job matches", default_factory=list)
    job_url: str = Field(description="Job posting URL", default="")
    job_type: str = Field(description="Job type (Full-time, Contract, etc.)", default="")


class JobRecommendationChain:
    """
    Lightweight chain for job recommendations.
    
    Matches CV profile against multiple jobs efficiently using:
    1. Quick profile extraction
    2. LoRA semantic matching
    3. Skills/experience alignment
    4. Intelligent ranking
    """
    
    def __init__(
        self,
        lora_api_url: Optional[str] = None,
        lora_api_key: Optional[str] = None,
        use_lora: bool = True,
        model_name: str = "gpt-3.5-turbo",
        job_source: JobSource = JobSource.JOBICY
    ):
        """
        Initialize the job recommendation chain.
        
        Args:
            lora_api_url (str): LoRA model API URL
            lora_api_key (str): LoRA model API key  
            use_lora (bool): Whether to use LoRA for scoring
            model_name (str): OpenAI model for explanations
            job_source (JobSource): Which job source to use (JOBICY or JOBSPY)
        """
        self.job_fetcher = UnifiedJobFetcher(source=job_source)
        self.job_source = job_source
        self.use_lora = use_lora and lora_api_url is not None and lora_api_key is not None
        
        if self.use_lora and lora_api_url and lora_api_key:
            self.lora_matcher: Optional[ResumeJobMatcherTool] = ResumeJobMatcherTool(
                api_url=lora_api_url,
                api_key=lora_api_key
            )
        else:
            self.lora_matcher: Optional[ResumeJobMatcherTool] = None
            
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)
    
    def recommend_jobs(
        self,
        cv_text: str,
        region: Optional[str] = None,
        job_title: Optional[str] = None,
        limit: int = 50,
        top_k: int = 10,
        min_score: float = 50.0,
        jobspy_sites: Optional[List[str]] = None
    ) -> List[JobMatch]:
        """
        Get job recommendations for a CV.
        
        Args:
            cv_text (str): Raw CV text
            region (str): Filter jobs by region (e.g., "Remote", "USA")
            job_title (str): Job title to search for (primarily for JobSpy)
            limit (int): Max jobs to fetch from source
            top_k (int): Return top K matches
            min_score (float): Minimum match score threshold (NOTE: If no jobs meet threshold, all jobs are returned with their scores)
            jobspy_sites (List[str]): Sites to scrape for JobSpy: 'indeed', 'linkedin', 'zip_recruiter', 'glassdoor'
            
        Returns:
            List[JobMatch]: Ranked job matches (all jobs if none meet threshold)
            
        Example:
            >>> chain = JobRecommendationChain(lora_api_url="...", lora_api_key="...")
            >>> matches = chain.recommend_jobs(cv_text, region="Remote", top_k=10)
            >>> for match in matches[:5]:
            ...     print(f"{match.match_score:.1f}% - {match.job_title} at {match.company}")
        """
        try:
            logger.info(f"Starting job recommendation for region: {region}, source: {self.job_source.value}")
            
            # Step 1: Extract CV profile (quick)
            logger.info("Extracting CV profile...")
            cv_profile = extract_cv_profile(cv_text, fast_mode=False)
            
            # Step 2: Fetch relevant jobs
            logger.info(f"Fetching jobs (limit: {limit})...")
            jobs = self.job_fetcher.fetch_jobs(
                region=region,
                job_title=job_title,
                limit=limit,
                site_names=jobspy_sites
            )
            
            if not jobs:
                logger.warning("No jobs fetched")
                return []
            
            logger.info(f"Found {len(jobs)} jobs, scoring against CV profile...")
            
            # Step 3: Score all jobs
            job_matches = self._score_jobs(cv_text, cv_profile, jobs)
            
            # Step 4: Sort all jobs by score
            job_matches.sort(key=lambda x: x.match_score, reverse=True)
            
            # Step 5: Filter by minimum score
            filtered_matches = [m for m in job_matches if m.match_score >= min_score]
            
            # IMPORTANT: If no jobs meet the threshold, return all jobs anyway so user can see what's available
            if not filtered_matches:
                logger.warning(f"No jobs met minimum score of {min_score}%. Returning all {len(job_matches)} jobs with their scores.")
                top_matches = job_matches[:top_k]
            else:
                logger.info(f"Found {len(filtered_matches)} jobs above {min_score}% threshold")
                top_matches = filtered_matches[:top_k]
            
            # Step 6: Add match explanations for top results
            logger.info(f"Adding match explanations for top {len(top_matches)} jobs...")
            self._add_match_reasons(cv_profile, top_matches)
            
            logger.info(f"Recommendation complete: returning {len(top_matches)} jobs")
            
            return top_matches
            
        except Exception as e:
            logger.error(f"Error in job recommendation: {e}")
            return []
    
    def _score_jobs(
        self,
        cv_text: str,
        cv_profile: CVProfile,
        jobs: List[Dict[str, Any]]
    ) -> List[JobMatch]:
        """
        Score all jobs against CV profile.
        
        Uses parallel processing for speed when LoRA is enabled.
        """
        job_matches = []
        
        if self.use_lora and self.lora_matcher:
            # Use parallel LoRA scoring for speed
            job_matches = self._score_jobs_with_lora(cv_text, cv_profile, jobs)
        else:
            # Use profile-based scoring only
            for job in jobs:
                match = self._score_job_profile_only(cv_profile, job)
                job_matches.append(match)
        
        return job_matches
    
    def _score_jobs_with_lora(
        self,
        cv_text: str,
        cv_profile: CVProfile,
        jobs: List[Dict[str, Any]],
        max_workers: int = 5
    ) -> List[JobMatch]:
        """
        Score jobs using LoRA + profile matching in parallel.
        """
        job_matches = []
        
        # Use ThreadPoolExecutor for parallel LoRA API calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(self._score_single_job, cv_text, cv_profile, job): job
                for job in jobs
            }
            
            for future in as_completed(future_to_job):
                try:
                    match = future.result()
                    job_matches.append(match)
                except Exception as e:
                    job = future_to_job[future]
                    logger.error(f"Error scoring job {job.get('title', 'Unknown')}: {e}")
                    # Add with profile score only as fallback
                    match = self._score_job_profile_only(cv_profile, job)
                    job_matches.append(match)
        
        return job_matches
    
    def _score_single_job(
        self,
        cv_text: str,
        cv_profile: CVProfile,
        job: Dict[str, Any]
    ) -> JobMatch:
        """Score a single job using both LoRA and profile matching."""
        
        # Get LoRA score with error handling
        lora_score = 0.0
        if self.lora_matcher:
            try:
                lora_result = self.lora_matcher.match_resume_job(
                    resume_text=cv_text,
                    job_description=job['description']
                )
                lora_score = lora_result.get('match_score', 0) * 100  # Convert to 0-100
            except Exception as e:
                logger.warning(f"LoRA API call failed for job {job.get('title', 'Unknown')}: {e}. Using profile score only.")
                lora_score = 0.0
        
        # Get profile-based score
        profile_score = self._calculate_profile_score(cv_profile, job)
        
        # Combined score (weighted average)
        # If LoRA score is 0 (failed or not available), use profile score only
        if lora_score > 0:
            match_score = (lora_score * 0.6) + (profile_score * 0.4)
        else:
            match_score = profile_score
        
        return JobMatch(
            job_id=job['id'],
            job_title=job['title'],
            company=job['company'],
            location=job['location'],
            match_score=round(match_score, 1),
            lora_score=round(lora_score, 1),
            profile_score=round(profile_score, 1),
            job_url=job['url'],
            job_type=job.get('job_type', 'Full-time'),
            match_reasons=[]
        )
    
    def _score_job_profile_only(
        self,
        cv_profile: CVProfile,
        job: Dict[str, Any]
    ) -> JobMatch:
        """Score job using only profile matching (no LoRA)."""
        
        profile_score = self._calculate_profile_score(cv_profile, job)
        
        return JobMatch(
            job_id=job['id'],
            job_title=job['title'],
            company=job['company'],
            location=job['location'],
            match_score=round(profile_score, 1),
            lora_score=0.0,
            profile_score=round(profile_score, 1),
            job_url=job['url'],
            job_type=job.get('job_type', 'Full-time'),
            match_reasons=[]
        )
    
    def _calculate_profile_score(
        self,
        cv_profile: CVProfile,
        job: Dict[str, Any]
    ) -> float:
        """
        Calculate match score based on CV profile and job data.
        
        Factors:
        - Skills overlap
        - Job title match
        - Location match
        - Experience level
        """
        score = 0.0
        
        job_text = f"{job['title']} {job['description']} {' '.join(job.get('categories', []))}".lower()
        
        # Skills matching (50% weight)
        matching_skills = sum(
            1 for skill in cv_profile.primary_skills
            if skill.lower() in job_text
        )
        if cv_profile.primary_skills:
            skills_ratio = matching_skills / len(cv_profile.primary_skills)
            score += skills_ratio * 50
        
        # Job title relevance (20% weight)
        for cv_title in cv_profile.job_titles:
            if any(word.lower() in job['title'].lower() for word in cv_title.split() if len(word) > 3):
                score += 20
                break
        
        # Role match (15% weight)
        for preferred_role in cv_profile.preferred_roles:
            if preferred_role.lower() in job_text:
                score += 15
                break
        
        # Location preference (10% weight)
        if cv_profile.location_preferences:
            for pref in cv_profile.location_preferences:
                if pref.lower() in job['location'].lower():
                    score += 10
                    break
        
        # Industry match (5% weight)
        for industry in cv_profile.industries:
            if industry.lower() in job_text:
                score += 5
                break
        
        return min(score, 100)  # Cap at 100
    
    def _add_match_reasons(
        self,
        cv_profile: CVProfile,
        matches: List[JobMatch]
    ):
        """Add human-readable match reasons to top jobs."""
        
        for match in matches:
            reasons = []
            
            # Skills match
            if match.profile_score > 40:
                reasons.append(f"Strong skills alignment ({match.profile_score:.0f}%)")
            
            # LoRA score
            if match.lora_score > 70:
                reasons.append(f"High semantic similarity ({match.lora_score:.0f}%)")
            elif match.lora_score > 50:
                reasons.append(f"Good semantic match ({match.lora_score:.0f}%)")
            
            # Job title match
            for cv_title in cv_profile.job_titles:
                if any(word.lower() in match.job_title.lower() for word in cv_title.split() if len(word) > 3):
                    reasons.append(f"Similar role to your {cv_title} experience")
                    break
            
            # Location match
            if "remote" in match.location.lower() and "remote" in str(cv_profile.location_preferences).lower():
                reasons.append("Matches your remote work preference")
            
            # Experience level
            if cv_profile.experience_years >= 5:
                if any(word in match.job_title.lower() for word in ['senior', 'lead', 'principal']):
                    reasons.append("Appropriate seniority level")
            
            match.match_reasons = reasons[:3]  # Limit to top 3 reasons


def get_job_recommendations(
    cv_text: str,
    region: Optional[str] = None,
    job_title: Optional[str] = None,
    top_k: int = 10,
    lora_api_url: Optional[str] = None,
    lora_api_key: Optional[str] = None,
    job_source: JobSource = JobSource.JOBICY,
    jobspy_sites: Optional[List[str]] = None
) -> List[JobMatch]:
    """
    Convenience function for job recommendations.
    
    Args:
        cv_text (str): Raw CV text
        region (str): Filter by region
        job_title (str): Job title to search for (for JobSpy)
        top_k (int): Number of top matches to return
        lora_api_url (str): LoRA API URL
        lora_api_key (str): LoRA API key
        job_source (JobSource): Which job source to use
        jobspy_sites (List[str]): Sites for JobSpy scraping
        
    Returns:
        List[JobMatch]: Top job matches
        
    Example:
        >>> matches = get_job_recommendations(
        ...     cv_text=my_cv,
        ...     region="Remote",
        ...     top_k=10,
        ...     job_source=JobSource.JOBSPY
        ... )
        >>> for match in matches:
        ...     print(f"{match.match_score}% - {match.job_title}")
    """
    chain = JobRecommendationChain(
        lora_api_url=lora_api_url,
        lora_api_key=lora_api_key,
        use_lora=bool(lora_api_url and lora_api_key),
        job_source=job_source
    )
    
    return chain.recommend_jobs(
        cv_text=cv_text,
        region=region,
        job_title=job_title,
        top_k=top_k,
        jobspy_sites=jobspy_sites
    )


if __name__ == "__main__":
    # Test the recommendation chain
    logging.basicConfig(level=logging.INFO)
    
    sample_cv = """
    Sarah Johnson
    Senior Python Developer
    
    Professional Summary:
    Experienced software engineer with 8 years in full-stack development.
    Specializing in Python, Django, and cloud infrastructure. Looking for remote opportunities.
    
    Experience:
    Senior Python Developer at Tech Corp (2019-Present)
    - Led development of microservices using Python and Django
    - Built RESTful APIs handling millions of requests
    - Deployed on AWS using Docker and Kubernetes
    
    Software Engineer at StartupXYZ (2016-2019)
    - Full-stack development with Python and React
    - Database optimization with PostgreSQL
    
    Skills:
    Python, Django, FastAPI, PostgreSQL, Redis, AWS, Docker, Kubernetes,
    React, JavaScript, Git, CI/CD, Agile
    
    Education:
    Master's in Computer Science, 2016
    
    Preferences: Remote work, flexible hours
    """
    
    print("🎯 Testing Job Recommendation Chain...")
    print("=" * 60)
    
    # Test without LoRA (profile-based only)
    print("\n📋 Test: Profile-based recommendations (no LoRA)")
    try:
        chain = JobRecommendationChain(use_lora=False)
        matches = chain.recommend_jobs(
            cv_text=sample_cv,
            region="Remote",
            limit=20,
            top_k=5
        )
        
        print(f"\n✅ Found {len(matches)} matching jobs:")
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match.job_title} at {match.company}")
            print(f"   Match Score: {match.match_score}%")
            print(f"   Location: {match.location}")
            print(f"   Reasons: {', '.join(match.match_reasons)}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Job recommendation tests complete!")
