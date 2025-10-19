"""
Skill Extraction and Scoring Module for CV Analyzer

This module implements a sophisticated RAG (Retrieval Augmented Generation) pipeline 
for extracting and scoring skills from CVs against job descriptions. It combines 
multiple AI techniques including vector search, LLM-based analysis, and external 
LoRA model integration.

Key Features:
- RAG pipeline with FAISS vector store for skill matching
- Hybrid skill extraction (LLM + keyword-based fallback)
- Knowledge base filtering and normalization
- LoRA model integration for semantic similarity scoring
- LangSmith tracing for comprehensive monitoring
- Robust error handling and input validation

Architecture:
1. Skills Knowledge Base: JSON-based structured skill definitions
2. Vector Store: FAISS index with OpenAI embeddings for semantic search
3. LLM Chain: GPT-4 based skill extraction and scoring
4. LoRA Integration: External API for neural similarity scoring

Dependencies:
- langchain_openai: For ChatOpenAI and OpenAI embeddings
- langchain_community: For FAISS vector store
- langsmith: For tracing and monitoring
- pydantic: For data validation and structured outputs
"""

import json
import re
import os
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from config import load_config
from langchain_integration import ResumeJobMatcherTool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda


# Load config and API keys

config = load_config(".env")
LANGSMITH_API_KEY = config.langsmith_api_key
LANGSMITH_ENDPOINT = config.langsmith_endpoint
LANGSMITH_PROJECT = config.langsmith_project
LANGSMITH_TRACING = config.langsmith_tracing

# Add ResumeJobMatcherTool config values (always from config)
LORA_MATCHER_API_URL = config.lora_matcher_api_url
LORA_MATCHER_API_KEY = config.lora_matcher_api_key

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


# Initialize LLM and Embeddings
# See: https://python.langchain.com/docs/integrations/llms/openai
llm = ChatOpenAI(
    model="gpt-4.1-2025-04-14",
    api_key=config.openai_api_key
)
# See: https://python.langchain.com/docs/integrations/text_embedding/openai
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=config.openai_api_key
)

# Initialize ResumeJobMatcherTool (LoRA matcher)
if LORA_MATCHER_API_URL and LORA_MATCHER_API_KEY:
    matcher = ResumeJobMatcherTool(
        api_url=LORA_MATCHER_API_URL,
        api_key=LORA_MATCHER_API_KEY
    )
else:
    matcher = None
    print("[LoRA Matcher] WARNING: API URL or API key not configured. LoRA matching will be disabled.")

# --- RAG Pipeline Setup ---

# 1. Load skills from the knowledge base
# This file acts as our source of truth for skills.
# See: https://python.langchain.com/docs/get_started/introduction
with open('tools/skills_kb.json', 'r') as f:
    skills_data = json.load(f)

# 2. Create LangChain Documents
# We convert each skill into a LangChain Document object, which is the standard
# format for data in LangChain.
# See: https://python.langchain.com/docs/core_modules/data_connection/documents
documents = [
    Document(
        page_content=f"{skill['skill']}: {skill['description']}",
        metadata={"category": skill['category']}
    ) for skill in skills_data
]

# 3. Create FAISS Vector Store
# This creates an in-memory vector store using FAISS for efficient similarity searches.
# The documents are embedded using OpenAI's models and stored in the index.
# See: https://python.langchain.com/docs/integrations/vectorstores/faiss
vector_store = FAISS.from_documents(documents, embeddings)

# 4. Create a Retriever
# The retriever is responsible for fetching relevant documents from the vector store
# based on a query.
# See: https://python.langchain.com/docs/chains/retrieval
retriever = vector_store.as_retriever()

# --- AI-Powered Scoring with RAG ---

class SkillComparison(BaseModel):
    """
    Pydantic model for structured skill comparison output.
    
    This model defines the expected output format for the RAG pipeline,
    ensuring consistent and validated responses from the LLM.
    
    Attributes:
        matched_skills (List[str]): Skills found in both CV and job description
        missing_skills (List[str]): Skills mentioned in job description but missing from CV
        score (int): Compatibility score from 0-100 based on skill matching ratio
    """
    matched_skills: List[str] = Field(description="Skills present in both the CV and job description, based on the provided context")
    missing_skills: List[str] = Field(description="Skills from the context that are in the job description but not in the CV")
    score: int = Field(description="A score from 0 to 100 representing how well the CV matches the job description, based on the context")

# 5. Update the Prompt Template
scoring_prompt = PromptTemplate(
    template='''You are a world-class expert in talent assessment. Your task is to analyze a candidate's CV against a job description and output a JSON object with matched skills, missing skills, and a score.\n\n**Instructions:**\n1.  **Analyze Job Requirements:** Carefully read the **Job Description** to identify the key skills required.\n2.  **Analyze CV Skills:** Carefully read the **CV Text** to identify the skills the candidate possesses.\n3.  **Identify Matched Skills:** List the skills that are present in BOTH the **Job Description** AND the **CV**.\n4.  **Identify Missing Skills:** List the key skills that are explicitly mentioned in the **Job Description** but are NOT found in the **CV**.\n5.  **Calculate Score:** The score should reflect the proportion of matched skills to the total required skills. `Score = (Number of Matched Skills / (Number of Matched Skills + Number of Missing Skills)) * 100`. If there are no required skills, the score should be 100. Round to the nearest integer.\n6.  **Use Context for Guidance:** The **Context** provides a list of skills and their descriptions. Use this to understand and identify skills accurately, but only list skills as matched or missing if they meet the criteria above.\n\n**Context (Relevant Skills from Knowledge Base):**\n{context}\n\n**Job Description:**\n{job_description}\n\n**CV Text:**\n{cv_text}\n\n**Your Output (JSON format):**\n{format_instructions}\n''',
    input_variables=["context", "cv_text", "job_description"],
    partial_variables={"format_instructions": JsonOutputParser(pydantic_object=SkillComparison).get_format_instructions()},
)

# --- Skill Extraction via LLM ---

def extract_skills_llm(cv_text: str, job_description: str) -> list:
    """
    Extract skills using LLM with knowledge base filtering and keyword fallback.
    
    This function uses a hybrid approach to skill extraction:
    1. LLM-based extraction from CV and job description texts
    2. Knowledge base filtering to ensure only valid skills are returned
    3. Keyword-based fallback for skills missed by the LLM
    4. Normalization and deduplication of results
    
    Args:
        cv_text (str): The parsed text content of the CV/resume
        job_description (str): The job description text to analyze
        
    Returns:
        list: Sorted list of normalized skill names from the knowledge base
        
    Example:
        >>> skills = extract_skills_llm("Python developer with Django", "Need Python and React skills")
        >>> print(skills)
        ['Django', 'Python', 'React']
        
    Note:
        - Only returns skills present in the skills knowledge base
        - Uses case-insensitive matching with word boundaries for multi-word skills
        - Includes LangSmith tracing for monitoring extraction performance
    """
    kb_skill_names = [skill['skill'] for skill in skills_data]
    skill_extraction_prompt = PromptTemplate(
        template='''You are an expert in resume and job description analysis. Your task is to select, from the provided list, all skills that are explicitly mentioned or strongly implied in the following texts. Only choose skills from the list below. Return the result as a JSON array of strings, with no extra commentary.

Allowed Skills:
{allowed_skills}

Job Description:
{job_description}

CV Text:
{cv_text}

Skills (JSON array):''',
        input_variables=["cv_text", "job_description", "allowed_skills"]
    )
    chain = skill_extraction_prompt | llm
    import json
    raw = chain.invoke({
        "cv_text": cv_text,
        "job_description": job_description,
        "allowed_skills": ', '.join(kb_skill_names)
    }, run_name="Skill Extraction Chain")
    if hasattr(raw, 'content'):
        raw_text = raw.content
    else:
        raw_text = raw
    if isinstance(raw_text, list):
        skills = raw_text
    else:
        try:
            skills = json.loads(str(raw_text).strip())
        except Exception:
            skills = []
    if isinstance(skills, list):
        # Only keep skills that are in the KB
        kb_skills_set = set(kb_skill_names)
        # Normalize KB skill names for matching
        kb_skill_names_norm = {s.lower().strip(): s for s in kb_skill_names}
        llm_skills_norm = set()
        for s in skills:
            s_norm = str(s).lower().strip()
            if s_norm in kb_skill_names_norm:
                llm_skills_norm.add(kb_skill_names_norm[s_norm])

        # Keyword fallback: search for KB skills in CV text (case-insensitive)
        cv_text_lower = cv_text.lower()
        for s_norm, s_orig in kb_skill_names_norm.items():
            # Use word boundaries for multi-word skills, substring for single-word
            if ' ' in s_norm:
                pattern = r'\b' + re.escape(s_norm) + r'\b'
                if re.search(pattern, cv_text_lower):
                    llm_skills_norm.add(s_orig)
            else:
                if s_norm in cv_text_lower:
                    llm_skills_norm.add(s_orig)

        return sorted(llm_skills_norm)
    return []


def get_lora_score(cv_text, job_description):
    """
    Get semantic similarity score from external LoRA model API.
    
    This function calls the external LoRA (Low-Rank Adaptation) model API
    to get a neural network-based similarity score between CV and job description.
    Includes comprehensive logging and error handling.
    
    Args:
        cv_text (str): The parsed text content of the CV/resume
        job_description (str): The job description text to compare against
        
    Returns:
        dict: API response containing:
            - match_score (float): Similarity score from the LoRA model
            - confidence (str): Confidence level of the prediction
            - status (str): Success/error/disabled status
            - error_message (str, optional): Error details if call fails
            
    Example:
        >>> result = get_lora_score("Python developer", "Need Python skills")
        >>> print(result)
        {'match_score': 0.85, 'confidence': 'High', 'status': 'success'}
        
    Note:
        - Returns default values if matcher is not configured
        - Includes detailed logging for debugging API calls
        - Handles network timeouts and connection errors gracefully
    """
    if matcher is None:
        print("[LoRA Matcher] WARNING: Matcher not configured, returning default score")
        return {"match_score": 0, "status": "disabled", "error_message": "LoRA matcher not configured"}
    
    print(f"[LoRA Matcher] Making API call...")
    print(f"[LoRA Matcher] CV text length: {len(cv_text)}")
    print(f"[LoRA Matcher] Job description length: {len(job_description)}")
    
    try:
        result = matcher.match_resume_job(cv_text=cv_text, job_description=job_description)
        print(f"[LoRA Matcher] API call successful: {result}")
        return result
    except Exception as e:
        print(f"[LoRA Matcher] ERROR: {e}")
        return {"match_score": 0, "status": "error", "error_message": str(e)}

rag_chain = (
    {
        "context": lambda x: retriever.invoke(', '.join(extract_skills_llm(x["cv_text"], x["job_description"]))),
        "cv_text": lambda x: x["cv_text"],
        "job_description": lambda x: x["job_description"],
    }
    | scoring_prompt
    | llm
    | JsonOutputParser(pydantic_object=SkillComparison)
)

def extract_and_score_skills(cv_text: str, job_description: str):
    """
    Main function to extract skills and generate comprehensive scoring using RAG pipeline.
    
    This is the primary entry point that orchestrates the entire skill analysis process:
    1. Input validation and error handling
    2. RAG-based skill extraction and matching
    3. External LoRA model scoring
    4. Score normalization and result combination
    
    The function combines two scoring mechanisms:
    - Skills-based score: Traditional matching based on knowledge base
    - LoRA score: Neural network-based semantic similarity
    
    Args:
        cv_text (str): The parsed text content of the CV/resume
        job_description (str): The job description text to analyze against
        
    Returns:
        dict: Comprehensive analysis containing:
            - matched_skills (list): Skills found in both CV and job description
            - missing_skills (list): Skills in job description but missing from CV
            - score (int): Skills-based compatibility score (0-100)
            - lora_score (int): LoRA model similarity score (0-100)
            - error (str, optional): Error message if processing fails
            
    Example:
        >>> result = extract_and_score_skills("Python developer with Django", "Need Python, Django, React")
        >>> print(result)
        {
            'matched_skills': ['Python', 'Django'],
            'missing_skills': ['React'],
            'score': 67,
            'lora_score': 75
        }
        
    Raises:
        Exception: If critical errors occur in RAG pipeline or LoRA API calls
        
    Note:
        - Validates inputs and returns structured error responses
        - Includes comprehensive logging for debugging
        - Converts LoRA scores from 0-1 range to 0-100 percentage
        - Uses LangSmith tracing for monitoring pipeline performance
    """
    if not job_description or not job_description.strip():
        print("[RAG] ERROR: Job description is empty or missing.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "lora_score": 0,
            "error": "Job description is empty. Please provide a valid job description."
        }
    if not cv_text or not cv_text.strip():
        print("[RAG] ERROR: CV text is empty or missing.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "lora_score": 0,
            "error": "CV text is empty. Please upload a valid CV file."
        }
    print(f"[RAG] job_description length: {len(job_description)}")
    print(f"[RAG] cv_text length: {len(cv_text)}")
    
    # Get the skills-based RAG result
    rag_result = rag_chain.invoke({"cv_text": cv_text, "job_description": job_description}, run_name="RAG Scoring Chain")
    
    # Get the LoRA score separately
    lora_result = get_lora_score(cv_text, job_description)
    lora_score = lora_result.get("match_score", 0)
    
    print(f"[LoRA Matcher] Raw result: {lora_result}")
    print(f"[LoRA Matcher] Raw match_score: {lora_score} (type: {type(lora_score)})")
    
    # Convert LoRA score from 0-1 range to 0-100 range if needed
    if isinstance(lora_score, float) and 0 <= lora_score <= 1:
        lora_score_converted = int(lora_score * 100)
        print(f"[LoRA Matcher] Converted score from {lora_score} to {lora_score_converted} (0-1 to 0-100 range)")
        lora_score = lora_score_converted
    elif isinstance(lora_score, float):
        lora_score_converted = int(lora_score)
        print(f"[LoRA Matcher] Converted float score from {lora_score} to {lora_score_converted}")
        lora_score = lora_score_converted
    
    print(f"[LoRA Matcher] Final lora_score: {lora_score}")
    print(f"[LoRA Matcher] LoRA status: {lora_result.get('status', 'unknown')}")
    if lora_result.get('confidence'):
        print(f"[LoRA Matcher] LoRA confidence: {lora_result.get('confidence')}")
    if lora_result.get('error_message'):
        print(f"[LoRA Matcher] LoRA error: {lora_result.get('error_message')}")
    
    # Combine the results
    final_result = {
        **rag_result,
        "lora_score": lora_score
    }
    
    return final_result
