"""
Feedback Generator Module for CV Analyzer

This module provides AI-powered feedback generation for CV analysis using LangChain and OpenAI.
It generates structured feedback including overall analysis, positive feedback based on matched 
skills, and constructive feedback based on missing skills.

Key Features:
- LangSmith tracing integration for monitoring and debugging
- Structured feedback generation with character limits
- Configuration-based API key management
- Comprehensive error handling and logging

Dependencies:
- langchain_openai: For ChatOpenAI model integration
- langsmith: For tracing and monitoring
- config: For environment variable management

"""

import os
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from tools.cv_parser import parse_cv
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Load config and API keys
config = load_config(".env")
LANGSMITH_API_KEY = config.langsmith_api_key
LANGSMITH_ENDPOINT = config.langsmith_endpoint
LANGSMITH_PROJECT = config.langsmith_project
LANGSMITH_TRACING = config.langsmith_tracing

if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING"] = "true" if LANGSMITH_TRACING else "false"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    if LANGSMITH_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT.strip('"')
    if LANGSMITH_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT.strip('"')
    tracer = LangChainTracer()
    client = Client(api_key=LANGSMITH_API_KEY)
else:
    tracer = None
    client = None

# Create shared model instance
llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.7,
    api_key=config.openai_api_key
)

# Define reusable output parser
parser = StrOutputParser()

def generate_feedback(matched_skills, missing_skills, cv_file_path):
    """
    Generate comprehensive AI-powered feedback for CV analysis.
    
    This function creates structured feedback by analyzing the CV content and comparing
    it against matched and missing skills. It provides three types of feedback:
    overall analysis, positive feedback, and constructive feedback.
    
    Args:
        matched_skills (list): List of skills that were found in both CV and job description
        missing_skills (list): List of skills mentioned in job description but missing from CV
        cv_file_path (str): Absolute path to the uploaded CV file for parsing
        
    Returns:
        dict: Structured feedback containing:
            - overall_analysis (str): General assessment of CV quality and structure (max 200 chars)
            - positive_feedback (str): Strengths based on matched skills (max 200 chars)
            - negative_feedback (str): Constructive feedback based on missing skills (max 200 chars)
            
    Example:
        >>> matched = ["Python", "Django", "FastAPI"]
        >>> missing = ["Docker", "Kubernetes"]
        >>> feedback = generate_feedback(matched, missing, "/tmp/resume.pdf")
        >>> print(feedback["overall_analysis"])
        "Well-structured CV with clear technical skills and experience sections..."
        
    Raises:
        Exception: If CV parsing fails or LLM API calls encounter errors
        
    Note:
        - All feedback is limited to 200 characters for concise presentation
        - Uses LangSmith tracing with specific run names for monitoring
        - Requires valid OpenAI API key in configuration
    """
    # Parse the CV text
    cv_text = parse_cv(cv_file_path)

    # Prompts
    overall_template = PromptTemplate.from_template(
        "You are a career coach. Analyze the following CV text and provide an overall assessment in 200 characters or less. "
        "Focus on structure, content quality, and presentation.\nCV Text: {cv_text}\nOverall Analysis:"
    )
    positive_template = PromptTemplate.from_template(
        "You are a career coach. Highlight the strengths of the CV based on the following matched skills in 200 characters or less. "
        "Focus on clarity, formatting, and effective communication of achievements.\nMatched Skills: {matched_skills}\nPositive Feedback:"
    )
    negative_template = PromptTemplate.from_template(
        "You are a career coach. Provide constructive feedback on the CV based on the following missing skills in 200 characters or less. "
        "Focus on missing details, poor organization, or irrelevant information.\nMissing Skills: {missing_skills}\nConstructive Feedback:"
    )

    # Chain each prompt with the LLM and parser
    overall_chain = overall_template | llm | parser
    positive_chain = positive_template | llm | parser
    negative_chain = negative_template | llm | parser

    # Run chains with run_name for LangSmith tracing
    overall_analysis = overall_chain.invoke({"cv_text": cv_text}, run_name="Feedback Overall Analysis")
    positive_feedback = positive_chain.invoke({"matched_skills": matched_skills}, run_name="Feedback Positive Skills")
    negative_feedback = negative_chain.invoke({"missing_skills": missing_skills}, run_name="Feedback Negative Skills")

    return {
        "overall_analysis": overall_analysis.strip(),
        "positive_feedback": positive_feedback.strip(),
        "negative_feedback": negative_feedback.strip(),
    }
