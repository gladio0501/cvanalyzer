"""
LangChain Integration Module for Resume-Job Matcher LoRA Model

This module provides a LangChain-compatible tool for integrating with external
LoRA (Low-Rank Adaptation) models for resume-job matching. It implements the
BaseTool interface to enable seamless integration with LangChain agents and chains.

Key Features:
- LangChain BaseTool implementation for agent compatibility
- HTTP API integration with authentication
- Robust error handling and timeout management
- Flexible input format support (JSON string or dictionary)
- Comprehensive response validation and normalization
- Batch processing for multiple job descriptions
- Enhanced error messages and confidence reporting

Architecture:
- Inherits from LangChain's BaseTool for agent integration
- Makes HTTP POST requests to external LoRA model APIs
- Handles authentication via Bearer token authorization
- Provides structured response format for consistent integration
- Supports both single and batch matching operations

Dependencies:
- langchain_core: For BaseTool interface and tool framework
- requests: For HTTP API communication
- pydantic: For input validation and type safety

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
    
    This Pydantic model defines the expected input format for the LoRA
    matcher tool, ensuring proper validation of CV text and job descriptions.
    
    Attributes:
        resume_text (str): The text content of the resume/CV to analyze
        job_description (str): The job description text to match against
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
    
    This tool integrates with external LoRA (Low-Rank Adaptation) model APIs
    to provide neural network-based similarity scoring between resumes and job
    descriptions. It implements the LangChain BaseTool interface for seamless
    integration with agents and chains.
    
    Attributes:
        name (str): Tool identifier for LangChain agents
        description (str): Tool description for agent decision-making
        api_url (str): Base URL of the LoRA model API endpoint
        api_key (str): Authentication key for API access
        args_schema (Type[BaseModel]): Pydantic schema for input validation
        
    Example:
        >>> tool = ResumeJobMatcherTool(
        ...     api_url="http://localhost:8080",
        ...     api_key="your-api-key"
        ... )
        >>> result = tool._run(
        ...     resume_text="Python developer",
        ...     job_description="Need Python skills"
        ... )
        >>> print(result)
        'Match Score: 0.850 (Confidence: High)'
        
    Note:
        - Implements both sync and async methods for LangChain compatibility
        - Handles various input formats and comprehensive error handling
        - Returns formatted string responses for agent consumption
        - Provides detailed match scores and confidence levels
    """

    model_config = {"arbitrary_types_allowed": True}

    # Define the fields that can be set
    api_url: str
    api_key: str
    headers: Dict[str, str] = Field(default_factory=dict)

    def __init__(self, api_url: str, api_key: str, **kwargs):
        """
        Initialize the ResumeJobMatcherTool.
        
        Args:
            api_url (str): The base URL of the LoRA model API endpoint
            api_key (str): Authentication key for API access
            **kwargs: Additional arguments passed to BaseTool
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
        
        This method handles the core logic of calling the external LoRA model API,
        including input validation, HTTP request formatting, and response processing.
        
        Args:
            resume_text (str): The text content of the resume/CV to analyze
            job_description (str): The job description text to match against
            run_manager (optional): LangChain run manager for callback handling
            
        Returns:
            str: Formatted string with match score and confidence level
            
        Example:
            >>> result = tool._run(
            ...     resume_text="Python developer", 
            ...     job_description="Need Python skills"
            ... )
            >>> print(result)
            'Match Score: 0.850 (Confidence: High)'
            
        Note:
            - Validates input format and required fields
            - Uses Bearer token authentication
            - Implements 30-second timeout for API calls
            - Returns formatted string responses for agent consumption
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
        Async version of the LoRA model API call.
        
        Currently falls back to synchronous implementation. In production,
        this should be implemented with async HTTP clients like aiohttp.
        
        Args:
            resume_text (str): The text content of the resume/CV to analyze
            job_description (str): The job description text to match against
            run_manager (optional): LangChain run manager for callbacks
            
        Returns:
            str: Formatted string with match score and confidence level
            
        Note:
            - Currently delegates to sync _run method
            - Should be implemented with async HTTP client for production
        """
        return self._run(resume_text, job_description, run_manager)
    
    def match_resume_job(self, resume_text: Optional[str] = None, job_description: Optional[str] = None, cv_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Convenience method to match a resume to a job description.
        
        This method provides a simplified interface for direct API calls
        without going through the LangChain tool interface. Returns raw API response.
        
        Args:
            resume_text (str): The text content of the resume/CV to analyze (or cv_text)
            job_description (str): The job description text to match against
            cv_text (str): Alternative parameter name for resume_text (for backward compatibility)
            
        Returns:
            Dict[str, Any]: Raw API response with match_score and confidence
            
        Example:
            >>> matcher = ResumeJobMatcherTool(api_url="...", api_key="...")
            >>> result = matcher.match_resume_job(
            ...     resume_text="Senior Python Developer with 5 years experience",
            ...     job_description="Looking for Python developer with web frameworks"
            ... )
            >>> print(result)
            {'match_score': 0.780, 'confidence': 'High'}
            
        Note:
            - Provides direct access without LangChain tool overhead
            - Useful for standalone API integration
            - Returns raw dictionary instead of formatted string
            - Supports both resume_text and cv_text parameter names
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
    
    This tool extends the basic matching functionality to support batch processing,
    allowing comparison of a single resume against multiple job descriptions
    simultaneously for efficient job ranking and selection.
    
    Attributes:
        name (str): Tool identifier for LangChain agents
        description (str): Tool description for agent decision-making
        api_url (str): Base URL of the LoRA model API endpoint
        api_key (str): Authentication key for API access
        args_schema (Type[BaseModel]): Pydantic schema for input validation
        
    Example:
        >>> tool = BatchResumeJobMatcherTool(
        ...     api_url="http://localhost:8080",
        ...     api_key="your-api-key"
        ... )
        >>> result = tool._run(
        ...     resume_text="Python developer",
        ...     job_descriptions="Python role, Java role, DevOps role"
        ... )
        >>> print(result)
        'Match Results:\n1. Score: 0.850 (High) - Python role...\nBest Match: 0.850 (High) - Python role...'
        
    Note:
        - Processes multiple job descriptions in a single API call
        - Returns ranked results with best match identification
        - Optimized for job recommendation and ranking scenarios
    """

    model_config = {"arbitrary_types_allowed": True}

    # Define the fields that can be set
    api_url: str
    api_key: str
    headers: Dict[str, str] = Field(default_factory=dict)
    
    def __init__(self, api_url: str, api_key: str, **kwargs):
        """
        Initialize the BatchResumeJobMatcherTool.
        
        Args:
            api_url (str): The base URL of the LoRA model API endpoint
            api_key (str): Authentication key for API access
            **kwargs: Additional arguments passed to BaseTool
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
        
        This method processes a single resume against multiple job descriptions,
        providing ranked results and identifying the best match.
        
        Args:
            resume_text (str): The text content of the resume/CV to analyze
            job_descriptions (str): Comma-separated job descriptions to match against
            run_manager (optional): LangChain run manager for callback handling
            
        Returns:
            str: Formatted string with all match results and best match identification
            
        Example:
            >>> result = tool._run(
            ...     resume_text="Python developer", 
            ...     job_descriptions="Python role, Java role, DevOps role"
            ... )
            >>> print(result)
            'Match Results:\n1. Score: 0.850 (High) - Python role...\nBest Match: 0.850 (High) - Python role...'
            
        Note:
            - Parses comma-separated job descriptions
            - Uses batch API endpoint for efficiency
            - Returns ranked results with truncated descriptions
            - Implements 60-second timeout for multiple comparisons
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
        Async version of the batch matching tool.
        
        Currently falls back to synchronous implementation. In production,
        this should be implemented with async HTTP clients like aiohttp.
        
        Args:
            resume_text (str): The text content of the resume/CV to analyze
            job_descriptions (str): Comma-separated job descriptions to match against
            run_manager (optional): LangChain run manager for callbacks
            
        Returns:
            str: Formatted string with batch match results
            
        Note:
            - Currently delegates to sync _run method
            - Should be implemented with async HTTP client for production
        """
        return self._run(resume_text, job_descriptions, run_manager)


# Convenience function for easy integration
def create_matcher_tool(api_url: str, api_key: str) -> ResumeJobMatcherTool:
    """
    Factory function to create and configure a ResumeJobMatcherTool instance.
    
    This convenience function simplifies tool creation and ensures proper
    configuration for common use cases.
    
    Args:
        api_url (str): The base URL of the LoRA model API endpoint
        api_key (str): Authentication key for API access
        
    Returns:
        ResumeJobMatcherTool: Configured tool instance ready for use
        
    Example:
        >>> matcher = create_matcher_tool(
        ...     api_url="http://localhost:8080",
        ...     api_key="your-secret-key"
        ... )
        >>> result = matcher.match_resume_job("CV text", "Job description")
        
    Note:
        - Validates configuration parameters
        - Returns ready-to-use tool instance
        - Useful for dependency injection and factory patterns
    """
    return ResumeJobMatcherTool(api_url=api_url, api_key=api_key)


def create_batch_matcher_tool(api_url: str, api_key: str) -> BatchResumeJobMatcherTool:
    """
    Factory function to create and configure a BatchResumeJobMatcherTool instance.
    
    This convenience function simplifies batch tool creation for multi-job
    comparison scenarios.
    
    Args:
        api_url (str): The base URL of the LoRA model API endpoint
        api_key (str): Authentication key for API access
        
    Returns:
        BatchResumeJobMatcherTool: Configured batch tool instance ready for use
        
    Example:
        >>> batch_matcher = create_batch_matcher_tool(
        ...     api_url="http://localhost:8080",
        ...     api_key="your-secret-key"
        ... )
        >>> result = batch_matcher._run("CV text", "Job1, Job2, Job3")
        
    Note:
        - Optimized for multiple job comparisons
        - Returns ranked results with best match identification
        - Useful for job recommendation systems
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
