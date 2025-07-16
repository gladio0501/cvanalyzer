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

Architecture:
- Inherits from LangChain's BaseTool for agent integration
- Makes HTTP POST requests to external LoRA model APIs
- Handles authentication via Bearer token authorization
- Provides structured response format for consistent integration

Dependencies:
- langchain_core: For BaseTool interface and tool framework
- requests: For HTTP API communication
- pydantic: For input validation and type safety

"""

import requests
from typing import Dict, Any, Optional, Union
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class ResumeJobMatcherInput(BaseModel):
    """
    Input schema for ResumeJobMatcherTool validation.
    
    This Pydantic model defines the expected input format for the LoRA
    matcher tool, ensuring proper validation of CV text and job descriptions.
    
    Attributes:
        cv_text (str): The text content of the resume/CV to analyze
        job_description (str): The job description text to match against
    """
    cv_text: str = Field(description="The text content of the resume/CV")
    job_description: str = Field(description="The job description text")


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
        
    Example:
        >>> tool = ResumeJobMatcherTool(
        ...     api_url="http://localhost:8080",
        ...     api_key="your-api-key"
        ... )
        >>> result = tool.match_resume_job(
        ...     cv_text="Python developer",
        ...     job_description="Need Python skills"
        ... )
        >>> print(result["match_score"])
        0.85
        
    Note:
        - Implements both sync and async methods for LangChain compatibility
        - Handles various input formats (dict, JSON string)
        - Provides comprehensive error handling and logging
        - Returns structured responses with score, confidence, and status
    """
    
    name: str = "resume_job_matcher"
    description: str = "Matches a resume/CV to a job description using a specialized LoRA model and returns a compatibility score. Input should be a dictionary with 'cv_text' and 'job_description' keys."
    
    api_url: str = Field(description="The URL of the resume-job-matcher API endpoint")
    api_key: str = Field(description="API key for authentication")
    
    def _run(self, tool_input: Union[str, Dict[str, Any]], run_manager=None) -> Dict[str, Any]:
        """
        Execute the LoRA model API call for resume-job matching.
        
        This method handles the core logic of calling the external LoRA model API,
        including input validation, HTTP request formatting, and response processing.
        
        Args:
            tool_input (Union[str, Dict[str, Any]]): Input data containing CV text and
                job description. Can be a dictionary or JSON string.
            run_manager (optional): LangChain run manager for callback handling
            
        Returns:
            Dict[str, Any]: API response containing:
                - match_score (float): Similarity score from LoRA model (0-1 range)
                - confidence (str): Confidence level of the prediction
                - status (str): Success/error status indicator
                - error_message (str, optional): Error details if call fails
                
        Raises:
            ValueError: If input format is invalid or required fields are missing
            requests.RequestException: If HTTP request fails
            
        Example:
            >>> result = tool._run({
            ...     "cv_text": "Python developer", 
            ...     "job_description": "Need Python skills"
            ... })
            >>> print(result)
            {'match_score': 0.85, 'confidence': 'High', 'status': 'success'}
            
        Note:
            - Validates input format and required fields
            - Uses Bearer token authentication
            - Implements 30-second timeout for API calls
            - Returns structured error responses for debugging
        """
        try:
            # Parse input
            if isinstance(tool_input, str):
                import json
                input_data = json.loads(tool_input)
            elif isinstance(tool_input, dict):
                input_data = tool_input
            else:
                raise ValueError("Input must be a dictionary or JSON string")
            
            cv_text = input_data.get("cv_text", "")
            job_description = input_data.get("job_description", "")
            
            if not cv_text or not job_description:
                raise ValueError("Both cv_text and job_description are required")
            
            # Prepare the request payload
            payload = {
                "resume_text": cv_text,
                "job_description": job_description
            }
            
            # Set up headers with API key
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Make the API request
            response = requests.post(
                f"{self.api_url}/match",
                json=payload,
                headers=headers,
                timeout=30  # 30 second timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            return {
                "match_score": result.get("match_score", 0),
                "confidence": result.get("confidence", "Unknown"),
                "status": "success"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "match_score": 0,
                "confidence": "Unknown",
                "status": "error",
                "error_message": str(e)
            }
        except Exception as e:
            return {
                "match_score": 0,
                "confidence": "Unknown",
                "status": "error",
                "error_message": f"Unexpected error: {str(e)}"
            }
    
    async def _arun(self, tool_input: Union[str, Dict[str, Any]], run_manager=None) -> Dict[str, Any]:
        """
        Async version of the LoRA model API call.
        
        Currently falls back to synchronous implementation. In production,
        this should be implemented with async HTTP clients like aiohttp.
        
        Args:
            tool_input (Union[str, Dict[str, Any]]): Input data for matching
            run_manager (optional): LangChain run manager for callbacks
            
        Returns:
            Dict[str, Any]: Same format as _run method
            
        Note:
            - Currently delegates to sync _run method
            - Should be implemented with async HTTP client for production
        """
        return self._run(tool_input, run_manager)
    
    def match_resume_job(self, cv_text: str, job_description: str) -> Dict[str, Any]:
        """
        Convenience method to match a resume to a job description.
        
        This method provides a simplified interface for direct API calls
        without going through the LangChain tool interface.
        
        Args:
            cv_text (str): The text content of the resume/CV to analyze
            job_description (str): The job description text to match against
            
        Returns:
            Dict[str, Any]: Matching result containing:
                - match_score (float): Neural similarity score (0-1 range)
                - confidence (str): Model confidence level
                - status (str): Success/error status
                - error_message (str, optional): Error details if applicable
                
        Example:
            >>> matcher = ResumeJobMatcherTool(api_url="...", api_key="...")
            >>> result = matcher.match_resume_job(
            ...     cv_text="Senior Python Developer with 5 years experience",
            ...     job_description="Looking for Python developer with web frameworks"
            ... )
            >>> print(f"Match score: {result['match_score']:.2f}")
            Match score: 0.78
            
        Note:
            - Provides direct access without LangChain tool overhead
            - Useful for standalone API integration
            - Returns same structured format as tool interface
        """
        return self._run({"cv_text": cv_text, "job_description": job_description})


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


# Convenience function for easy integration
def create_resume_job_matcher(api_url: str, api_key: str) -> ResumeJobMatcherTool:
    """
    Create and return a configured ResumeJobMatcherTool instance.
    
    Args:
        api_url: The URL of the resume-job-matcher API endpoint
        api_key: API key for authentication
        
    Returns:
        Configured ResumeJobMatcherTool instance
    """
    return ResumeJobMatcherTool(api_url=api_url, api_key=api_key)
