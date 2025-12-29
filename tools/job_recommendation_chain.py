"""
Job Recommendation Chain.
matches CVs against multiple job listings suitable for speed.
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
    Matches CV profile against multiple jobs efficiently.
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
        
        # Load skills knowledge base for better matching
        self.known_skills = self._load_skills_kb()

    def _load_skills_kb(self) -> set:
        """Load skills from the shared knowledge base."""
        try:
            import json
            import os
            
            # Try to find the file relative to this script
            current_dir = os.path.dirname(os.path.abspath(__file__))
            kb_path = os.path.join(current_dir, 'skills_kb.json')
            
            if os.path.exists(kb_path):
                with open(kb_path, 'r') as f:
                    skills_data = json.load(f)
                    return {s['skill'].lower() for s in skills_data}
            
            # Fallback for when running from project root
            elif os.path.exists('tools/skills_kb.json'):
                with open('tools/skills_kb.json', 'r') as f:
                    skills_data = json.load(f)
                    return {s['skill'].lower() for s in skills_data}
            
            logger.warning("Could not find skills_kb.json, using empty skill set")
            return set()
        except Exception as e:
            logger.error(f"Error loading skills KB: {e}")
            return set()

    def _extract_job_skills(self, job_text: str) -> set:
        """Extract skills mentioned in the job text using the KB."""
        job_text_lower = job_text.lower()
        found_skills = set()
        
        # Simple string matching for now (fast)
        # Could be optimized with regex for word boundaries
        for skill in self.known_skills:
            # Basic check: is the skill name in the text?
            # Ideally we want word boundaries, e.g. " Go " not "Golang" matched by "Go"
            if len(skill) <= 3:
                # For short skills (C++, Go, AWS), require boundaries
                import re
                if re.search(r'\b' + re.escape(skill) + r'\b', job_text_lower):
                    found_skills.add(skill)
            else:
                if skill in job_text_lower:
                    found_skills.add(skill)
                    
        return found_skills

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
        
        Weights:
        - Skills Coverage: 60%
        - Job Title Match: 20%
        - Experience Match: 10%
        - Location: 5%
        - Industry: 5%
        """
        score = 0.0
        
        job_text = f"{job['title']} {job['description']} {' '.join(job.get('categories', []))}".lower()
        
        # 1. Skills Coverage (60% weight)
        # Fix: We now check how many of the JOB's required skills the candidate has.
        job_required_skills = self._extract_job_skills(job_text)
        
        if not job_required_skills:
             # Fallback if no skills detected in job: check if CV skills are in job text
             # This prevents 0 score on poorly parsed jobs
             matching_cv_skills = sum(1 for s in cv_profile.primary_skills if s.lower() in job_text)
             denom = len(cv_profile.primary_skills) if cv_profile.primary_skills else 1
             skills_score = (matching_cv_skills / denom) * 60
        else:
            # We have identified skills in the job. How many does the candidate have?
            # Normalize CV skills to lower case set
            cv_skills_set = {s.lower() for s in cv_profile.primary_skills}
            
            # Intersection
            matching_skills = job_required_skills.intersection(cv_skills_set)
            
            # Coverage ratio
            coverage = len(matching_skills) / len(job_required_skills)
            skills_score = coverage * 60
            
        score += skills_score
        
        # 2. Job title relevance (20% weight)
        title_score = 0
        job_title_lower = job['title'].lower()
        for cv_title in cv_profile.job_titles:
            # Split title into words to find partial matches (e.g. "Engineer" in "Software Engineer")
            cv_title_words = [w.lower() for w in cv_title.split() if len(w) > 3]
            match_count = sum(1 for w in cv_title_words if w in job_title_lower)
            if match_count > 0:
                # Proportional score based on how many words matched
                # e.g. "Senior Python Engineer" vs "Python Engineer" -> Good match
                title_score = 20
                break
        score += title_score
        
        # 3. Experience Match (10% weight)
        # Penalize if job is Senior and candidate is Junior
        exp_score = 10 # Default full points
        
        is_job_senior = any(w in job_title_lower for w in ['senior', 'lead', 'principal', 'architect', 'manager'])
        is_candidate_junior = cv_profile.experience_years < 3
        
        if is_job_senior and is_candidate_junior:
            exp_score = 0 # Significant penalty/mismatch
        elif is_job_senior and cv_profile.experience_years < 5:
            exp_score = 5 # Partial penalty
            
        score += exp_score
        
        # 4. Location preference (5% weight)
        loc_score = 0
        if cv_profile.location_preferences:
            for pref in cv_profile.location_preferences:
                if pref.lower() in job['location'].lower():
                    loc_score = 5
                    break
        score += loc_score
        
        # 5. Industry match (5% weight)
        ind_score = 0
        for industry in cv_profile.industries:
            if industry.lower() in job_text:
                ind_score = 5
                break
        score += ind_score
        
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
    
    # Load environment variables
    try:
        from config import load_config
        config = load_config()
        # Ensure OpenAI key is set in environment for LangChain
        import os
        if config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = config.openai_api_key.get_secret_value()
            print("✅ Loaded OpenAI API key from config")
    except ImportError:
        print("⚠️ Could not import config, verifying manually...")
        from dotenv import load_dotenv
        load_dotenv()
    
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
