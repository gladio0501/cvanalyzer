"""
LangChain Integration Module for Resume-Job Matcher LoRA Model.
"""

import requests
from typing import Dict, Any, Optional, Union, Type, List
from langchain_core.tools import BaseTool
from langchain_core.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field


# Type alias for cleaner type annotations
ArgsSchema = Optional[Type[BaseModel]]


class ResumeJobMatcherInput(BaseModel):
    """
    Input schema for ResumeJobMatcherTool validation.
    """
    resume_text: str = Field(description="The resume text to analyze")
    job_description: str = Field(description="The job description to match against")


class BatchResumeJobMatchInput(BaseModel):
    """Input schema for batch resume-job matching tool"""
    resume_text: str = Field(description="The resume text to analyze")
    job_descriptions: str = Field(description="Comma-separated job descriptions to match against")


class ResumeJobMatcherTool(BaseTool):
    """
    LangChain tool for matching resumes to job descriptions using LoRA models.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Define the fields that can be set
    api_url: str
    api_key: str
    headers: Dict[str, str] = Field(default_factory=dict)

    def __init__(self, api_url: str, api_key: str, **kwargs):
        """
        Initialize the ResumeJobMatcherTool.
        """
        # Set tool attributes via kwargs
        kwargs.setdefault('name', "resume_job_matcher")
        kwargs.setdefault('description', """
        A tool for matching resumes with job descriptions using AI.
        Useful when you need to:
        - Calculate similarity between a resume and job posting
        - Assess how well a candidate fits a role
        - Get confidence scores for job matches
        
        Input should be the resume text and job description.
        Returns a match score (0-1) and confidence level (Low/Medium/High).
        """)
        kwargs.setdefault('args_schema', ResumeJobMatcherInput)
        
        # Set instance attributes
        kwargs['api_url'] = api_url.rstrip('/')
        kwargs['api_key'] = api_key
        kwargs['headers'] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        super().__init__(**kwargs)
    
    def _run(
        self, 
        resume_text: str, 
        job_description: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Execute the LoRA model API call for resume-job matching.
        """
        try:
            # Validate inputs
            if not resume_text or not job_description:
                return "Error: Both resume_text and job_description are required"
            
            # Prepare the request payload
            payload = {
                "resume_text": resume_text,
                "job_description": job_description
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}/match",
                json=payload,
                headers=self.headers,
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                score = result.get('match_score', 0)
                confidence = result.get('confidence', 'Unknown')
                
                return f"Match Score: {score:.3f} (Confidence: {confidence})"
            else:
                return f"Error: {response.status_code} - {response.text}"
            
        except requests.exceptions.RequestException as e:
            return f"Request failed: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    async def _arun(
        self, 
        resume_text: str, 
        job_description: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async version of the LoRA model API call using aiohttp.
        """
        try:
            import aiohttp
            
            # Validate inputs
            if not resume_text or not job_description:
                return "Error: Both resume_text and job_description are required"
            
            # Prepare the request payload
            payload = {
                "resume_text": resume_text,
                "job_description": job_description
            }
            
            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/match",
                    json=payload,
                    headers=self.headers,
                    timeout=30
                ) as response:
                    
                    # Check if request was successful
                    if response.status == 200:
                        result = await response.json()
                        score = result.get('match_score', 0)
                        confidence = result.get('confidence', 'Unknown')
                        
                        return f"Match Score: {score:.3f} (Confidence: {confidence})"
                    else:
                        text = await response.text()
                        return f"Error: {response.status} - {text}"
            
        except ImportError:
            return "Error: aiohttp library not installed. Please install it to use async features."
        except Exception as e:
            return f"Async request failed: {str(e)}"
    
    def match_resume_job(self, resume_text: Optional[str] = None, job_description: Optional[str] = None, cv_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Convenience method to match a resume to a job description.
        Returns raw API response.
        """
        # Handle backward compatibility - cv_text parameter
        if cv_text is not None and resume_text is None:
            resume_text = cv_text
        
        try:
            # Validate inputs
            if not resume_text or not job_description:
                return {"match_score": 0, "status": "error", "error_message": "Both resume_text and job_description are required"}
            
            # Prepare the request payload
            payload = {
                "resume_text": resume_text,
                "job_description": job_description
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}/match",
                json=payload,
                headers=self.headers,
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {
                    "match_score": 0,
                    "status": "error", 
                    "error_message": f"API Error: {response.status_code} - {response.text}"
                }
            
        except requests.exceptions.RequestException as e:
            return {
                "match_score": 0,
                "status": "error",
                "error_message": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "match_score": 0,
                "status": "error", 
                "error_message": f"Unexpected error: {str(e)}"
            }


class BatchResumeJobMatcherTool(BaseTool):
    """
    LangChain tool for matching a resume with multiple job descriptions at once.
    """

    model_config = {"arbitrary_types_allowed": True}

    # Define the fields that can be set
    api_url: str
    api_key: str
    headers: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, api_url: str, api_key: str, **kwargs):
        """
        Initialize the BatchResumeJobMatcherTool.
        """
        # Set tool attributes via kwargs
        kwargs.setdefault('name', "batch_resume_job_matcher")
        kwargs.setdefault('description', """
        A tool for matching a resume with multiple job descriptions at once.
        Useful when you need to:
        - Compare a resume against multiple job postings
        - Find the best matching jobs for a candidate
        - Rank job opportunities by fit
        
        Input should be the resume text and comma-separated job descriptions.
        Returns all match scores and identifies the best match.
        """)
        kwargs.setdefault('args_schema', BatchResumeJobMatchInput)
        
        # Set instance attributes
        kwargs['api_url'] = api_url.rstrip('/')
        kwargs['api_key'] = api_key
        kwargs['headers'] = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        super().__init__(**kwargs)
    
    def _run(
        self, 
        resume_text: str, 
        job_descriptions: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Execute the batch matching tool for multiple job descriptions.
        """
        try:
            # Parse job descriptions
            job_list = [desc.strip() for desc in job_descriptions.split(',')]
            
            if not resume_text or not job_list:
                return "Error: Both resume_text and job_descriptions are required"
            
            payload = {
                "resume_text": resume_text,
                "job_descriptions": job_list
            }
            
            response = requests.post(
                f"{self.api_url}/batch-match",
                json=payload,
                headers=self.headers,
                timeout=60  # 60 second timeout for batch processing
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Format results
                output = "Match Results:\n"
                for i, match in enumerate(result['results'], 1):
                    desc_preview = match['job_description'][:100] + "..." if len(match['job_description']) > 100 else match['job_description']
                    output += f"{i}. Score: {match['score']:.3f} ({match['confidence']}) - {desc_preview}\n"
                
                best = result['best_match']
                best_desc_preview = best['job_description'][:100] + "..." if len(best['job_description']) > 100 else best['job_description']
                output += f"\nBest Match: {best['score']:.3f} ({best['confidence']}) - {best_desc_preview}"
                
                return output
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"Request failed: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    async def _arun(
        self, 
        resume_text: str, 
        job_descriptions: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """
        Async version of the batch matching tool using aiohttp.
        """
        try:
            import aiohttp
            
            # Parse job descriptions
            job_list = [desc.strip() for desc in job_descriptions.split(',')]
            
            if not resume_text or not job_list:
                return "Error: Both resume_text and job_descriptions are required"
            
            payload = {
                "resume_text": resume_text,
                "job_descriptions": job_list
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/batch-match",
                    json=payload,
                    headers=self.headers,
                    timeout=60
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Format results
                        output = "Match Results:\n"
                        for i, match in enumerate(result['results'], 1):
                            desc_preview = match['job_description'][:100] + "..." if len(match['job_description']) > 100 else match['job_description']
                            output += f"{i}. Score: {match['score']:.3f} ({match['confidence']}) - {desc_preview}\n"
                        
                        best = result['best_match']
                        best_desc_preview = best['job_description'][:100] + "..." if len(best['job_description']) > 100 else best['job_description']
                        output += f"\nBest Match: {best['score']:.3f} ({best['confidence']}) - {best_desc_preview}"
                        
                        return output
                    else:
                        text = await response.text()
                        return f"Error: {response.status} - {text}"
                
        except ImportError:
            return "Error: aiohttp library not installed. Please install it to use async features."
        except Exception as e:
            return f"Async request failed: {str(e)}"


# Convenience function for easy integration
def create_matcher_tool(api_url: str, api_key: str) -> ResumeJobMatcherTool:
    """
    Factory function to create and configure a ResumeJobMatcherTool instance.
    """
    return ResumeJobMatcherTool(api_url=api_url, api_key=api_key)


def create_batch_matcher_tool(api_url: str, api_key: str) -> BatchResumeJobMatcherTool:
    """
    Factory function to create and configure a BatchResumeJobMatcherTool instance.
    """
    return BatchResumeJobMatcherTool(api_url=api_url, api_key=api_key)


# Legacy function for backward compatibility
def create_resume_job_matcher(api_url: str, api_key: str) -> ResumeJobMatcherTool:
    """
    Create and return a configured ResumeJobMatcherTool instance.
    
    Args:
        api_url: The URL of the resume-job-matcher API endpoint
        api_key: API key for authentication
        
    Returns:
        Configured ResumeJobMatcherTool instance
        
    Note:
        This function is kept for backward compatibility.
        Use create_matcher_tool() for new implementations.
    """
    return ResumeJobMatcherTool(api_url=api_url, api_key=api_key)


# Example usage
if __name__ == "__main__":
    """
    Example usage of the Resume-Job Matcher LangChain tools.
    
    This section demonstrates how to use both the single and batch
    matching tools with real-world examples.
    """
    
    # Initialize the tools
    api_url = "http://localhost:8080"
    api_key = "your-api-key-here"
    
    single_matcher = ResumeJobMatcherTool(api_url=api_url, api_key=api_key)
    batch_matcher = BatchResumeJobMatcherTool(api_url=api_url, api_key=api_key)
    
    # Example resume and job descriptions
    resume = """
    John Doe
    Senior Software Engineer
    
    Experience:
    - 5 years of Python development with Django and FastAPI
    - Machine learning experience with PyTorch and TensorFlow
    - AWS cloud services (EC2, S3, Lambda, RDS)
    - RESTful API design and microservices architecture
    - Agile development and CI/CD pipelines
    
    Skills:
    - Programming: Python, JavaScript, SQL, Git
    - Frameworks: Django, FastAPI, React, Node.js
    - Databases: PostgreSQL, MySQL, Redis
    - Cloud: AWS, Docker, Kubernetes
    """
    
    # Single job matching example
    job_description = """
    We are seeking a Senior Python Developer with experience in:
    - Web frameworks (FastAPI, Django preferred)
    - Machine learning frameworks (PyTorch/TensorFlow)
    - Cloud platforms (AWS strongly preferred)
    - Microservices architecture
    - 3+ years experience required
    """
    
    print("=== Single Job Match Example ===")
    single_result = single_matcher._run(resume, job_description)
    print(single_result)
    print()
    
    # Batch matching example
    multiple_jobs = """
    Senior Python Developer role with ML focus,
    Full Stack JavaScript Developer with React,
    DevOps Engineer with AWS and Kubernetes,
    Data Scientist with Python and ML experience,
    Backend Engineer with microservices experience
    """
    
    print("=== Batch Job Match Example ===")
    batch_result = batch_matcher._run(resume, multiple_jobs)
    print(batch_result)
    print()
    
    # Direct API call example (non-LangChain)
    print("=== Direct API Call Example ===")
    direct_result = single_matcher.match_resume_job(resume, job_description)
    print(direct_result)
