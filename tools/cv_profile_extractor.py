"""
Lightweight CV Profile Extractor.
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import logging
import re

logger = logging.getLogger(__name__)


class CVProfile(BaseModel):
    """Lightweight CV profile for job matching."""
    
    job_titles: List[str] = Field(
        description="Current and past job titles/roles",
        default_factory=list
    )
    
    experience_years: int = Field(
        description="Total years of professional experience",
        default=0
    )
    
    primary_skills: List[str] = Field(
        description="Top 10 most important technical and professional skills",
        default_factory=list
    )
    
    industries: List[str] = Field(
        description="Industries worked in (e.g., Tech, Finance, Healthcare)",
        default_factory=list
    )
    
    education_level: str = Field(
        description="Highest education level (e.g., Bachelor's, Master's, PhD)",
        default="Not specified"
    )
    
    preferred_roles: List[str] = Field(
        description="Types of roles the candidate is qualified for",
        default_factory=list
    )
    
    location_preferences: List[str] = Field(
        description="Work location preferences (Remote, specific cities, etc.)",
        default_factory=list
    )
    
    summary: str = Field(
        description="Brief 2-3 sentence professional summary",
        default=""
    )


class LightweightCVExtractor:
    """
    Lightweight CV profile extractor for efficient job matching.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.1
    ):
        """
        Initialize the CV extractor.
        
        Args:
            model_name (str): OpenAI model to use
            temperature (float): LLM temperature (lower = more consistent)
        """
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature
        )
        self.parser = PydanticOutputParser(pydantic_object=CVProfile)
    
    def extract_profile(self, cv_text: str) -> CVProfile:
        """
        Extract CV profile from text.
        """
        try:
            # Create extraction prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a CV analysis expert. Extract key information from the CV text.
                
Focus on:
- Job titles and roles held
- Years of experience (estimate if not explicit)
- Top 10 most relevant technical and professional skills
- Industries worked in
- Education level
- Types of roles they're qualified for
- Location preferences if mentioned

Be concise and extract only the most important information.

{format_instructions}"""),
                ("human", "CV Text:\n\n{cv_text}")
            ])
            
            # Format with parser instructions
            formatted_prompt = prompt.format_messages(
                cv_text=cv_text[:4000],  # Limit text length for speed
                format_instructions=self.parser.get_format_instructions()
            )
            
            # Get LLM response
            response = self.llm.invoke(formatted_prompt)
            
            # Parse into CVProfile
            content = response.content if isinstance(response.content, str) else str(response.content)
            profile = self.parser.parse(content)
            
            logger.info(f"Extracted CV profile: {len(profile.primary_skills)} skills, {profile.experience_years} years exp")
            
            return profile
            
        except Exception as e:
            logger.error(f"Error extracting CV profile: {e}")
            # Return empty profile on error
            return CVProfile()
    
    def extract_profile_fast(self, cv_text: str) -> Dict[str, Any]:
        """
        Ultra-fast extraction using regex and keywords.
        Fallback method when speed is critical.
        
        Args:
            cv_text (str): Raw CV text
            
        Returns:
            dict: Basic profile information
        """
        profile = {
            "job_titles": self._extract_job_titles(cv_text),
            "experience_years": self._estimate_experience(cv_text),
            "primary_skills": self._extract_skills_keywords(cv_text),
            "summary": cv_text[:300] + "..." if len(cv_text) > 300 else cv_text
        }
        
        return profile
    
    def _extract_job_titles(self, text: str) -> List[str]:
        """Extract job titles using common patterns."""
        titles = []
        
        # Common title patterns
        patterns = [
            r'(?:^|\n)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Engineer|Developer|Manager|Designer|Analyst|Specialist|Lead|Director|Architect))',
            r'(?:Position|Role|Title):\s*([A-Z][^\n]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            titles.extend(matches)
        
        # Deduplicate and limit
        return list(set(titles))[:5]
    
    def _estimate_experience(self, text: str) -> int:
        """Estimate years of experience from text."""
        # Look for explicit mentions
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience:\s*(\d+)\+?\s*years?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        # Count year ranges (e.g., "2018-2023")
        year_ranges = re.findall(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)', text, re.IGNORECASE)
        if year_ranges:
            total_years = 0
            for start, end in year_ranges:
                end_year = 2024 if end.lower() in ['present', 'current'] else int(end)
                total_years += max(0, end_year - int(start))
            return min(total_years, 50)  # Cap at 50 years
        
        return 0
    
    def _extract_skills_keywords(self, text: str) -> List[str]:
        """Extract skills using keyword matching."""
        # Common tech skills to look for
        common_skills = [
            "Python", "Java", "JavaScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
            "React", "Angular", "Vue", "Node.js", "Django", "Flask", "FastAPI", "Spring",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Machine Learning", "AI", "Deep Learning", "TensorFlow", "PyTorch",
            "Git", "CI/CD", "Agile", "Scrum", "DevOps",
            "HTML", "CSS", "TypeScript", "SQL", "NoSQL",
            "REST API", "GraphQL", "Microservices"
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return found_skills[:15]  # Limit to top 15


def extract_cv_profile(cv_text: str, fast_mode: bool = False) -> CVProfile:
    """
    Convenience function to extract CV profile.
    
    Args:
        cv_text (str): Raw CV text
        fast_mode (bool): Use fast keyword-based extraction
        
    Returns:
        CVProfile: Extracted profile
        
    Example:
        >>> profile = extract_cv_profile(cv_text)
        >>> print(f"Experience: {profile.experience_years} years")
        >>> print(f"Skills: {', '.join(profile.primary_skills[:5])}")
    """
    extractor = LightweightCVExtractor()
    
    if fast_mode:
        data = extractor.extract_profile_fast(cv_text)
        return CVProfile(**data)
    else:
        return extractor.extract_profile(cv_text)


if __name__ == "__main__":
    # Test the extractor
    logging.basicConfig(level=logging.INFO)
    
    sample_cv = """
    John Smith
    Senior Software Engineer
    
    Professional Summary:
    Experienced software engineer with 7+ years in full-stack development.
    Specializing in Python, Django, and AWS cloud infrastructure.
    
    Experience:
    Senior Software Engineer at Tech Corp (2020-Present)
    - Led development of microservices architecture
    - Built RESTful APIs serving 1M+ requests/day
    - Technologies: Python, Django, PostgreSQL, Redis, AWS
    
    Software Engineer at StartupXYZ (2017-2020)
    - Developed web applications using React and Node.js
    - Implemented CI/CD pipelines with Jenkins
    - Technologies: JavaScript, React, Node.js, MongoDB
    
    Skills:
    - Languages: Python, JavaScript, SQL
    - Frameworks: Django, FastAPI, React, Node.js
    - Cloud: AWS (EC2, S3, Lambda), Docker, Kubernetes
    - Databases: PostgreSQL, MySQL, Redis, MongoDB
    
    Education:
    Bachelor of Science in Computer Science
    University of Technology, 2017
    
    Looking for: Remote senior engineering roles in tech companies
    """
    
    print("🔍 Testing Lightweight CV Extractor...")
    print("=" * 60)
    
    # Test LLM-based extraction
    print("\n📋 Test 1: LLM-based extraction")
    try:
        extractor = LightweightCVExtractor()
        profile = extractor.extract_profile(sample_cv)
        
        print(f"\n✅ Profile extracted:")
        print(f"  Job Titles: {', '.join(profile.job_titles)}")
        print(f"  Experience: {profile.experience_years} years")
        print(f"  Primary Skills: {', '.join(profile.primary_skills[:5])}")
        print(f"  Industries: {', '.join(profile.industries)}")
        print(f"  Education: {profile.education_level}")
        print(f"  Preferred Roles: {', '.join(profile.preferred_roles)}")
        print(f"  Summary: {profile.summary[:100]}...")
    except Exception as e:
        print(f"❌ LLM extraction failed: {e}")
    
    # Test fast extraction
    print("\n⚡ Test 2: Fast keyword-based extraction")
    extractor = LightweightCVExtractor()
    fast_profile = extractor.extract_profile_fast(sample_cv)
    print(f"\n✅ Fast profile extracted:")
    print(f"  Job Titles: {', '.join(fast_profile['job_titles'])}")
    print(f"  Experience: {fast_profile['experience_years']} years")
    print(f"  Skills: {', '.join(fast_profile['primary_skills'][:5])}")
    
    print("\n✅ CV extractor tests complete!")
