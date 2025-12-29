"""
Skill Extraction and Scoring Module for CV Analyzer.
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
    """
    critical_skills_matched: List[str] = Field(description="Critical/Must-have skills present in both CV and Job Description")
    bonus_skills_matched: List[str] = Field(description="Bonus/Nice-to-have skills present in both CV and Job Description")
    critical_skills_missing: List[str] = Field(description="Critical/Must-have skills required by Job but missing in CV")
    bonus_skills_missing: List[str] = Field(description="Bonus/Nice-to-have skills mentioned in Job but missing in CV")
    reasoning: str = Field(description="Brief explanation of the assessment")

# 5. Update the Prompt Template
scoring_prompt = PromptTemplate(
    template='''You are a world-class expert in technical talent assessment. Your task is to analyze a candidate's CV against a job description and compare their skills.

**Instructions:**
1.  **Analyze Job Requirements:** Identify skills in the **Job Description** and classify them into:
    *   **Critical Skills:** "Must have", "Required", "Essential", or core technologies for the role.
    *   **Bonus Skills:** "Nice to have", "Preferred", "Plus", or auxiliary technologies.
2.  **Analyze CV:** Identify skills possessed by the candidate in the **CV Text**.
3.  **Compare:**
    *   List **Critical Skills Matched**: Critical skills found in both.
    *   List **Bonus Skills Matched**: Bonus skills found in both.
    *   List **Critical Skills Missing**: Critical skills in Job but NOT in CV.
    *   List **Bonus Skills Missing**: Bonus skills in Job but NOT in CV.
4.  **Context:** Use the provided **Context** to understand skill synonyms and categories.

**Context (Relevant Skills from Knowledge Base):**
{context}

**Job Description:**
{job_description}

**CV Text:**
{cv_text}

**Your Output (JSON format):**
{format_instructions}
''',
    input_variables=["context", "cv_text", "job_description"],
    partial_variables={"format_instructions": JsonOutputParser(pydantic_object=SkillComparison).get_format_instructions()},
)

# --- Skill Extraction via LLM ---

def extract_skills_llm(cv_text: str, job_description: str) -> list:
    """
    Extract skills using LLM with knowledge base filtering and keyword fallback.
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
    
    # Calculate weighted score
    # Weights: Critical = 1.5, Bonus = 0.5
    # Score = ( (Critical_Matched * 1.5) + (Bonus_Matched * 0.5) ) / Total_Potential_Score * 100
    
    n_critical_matched = len(rag_result.get('critical_skills_matched', []))
    n_bonus_matched = len(rag_result.get('bonus_skills_matched', []))
    n_critical_missing = len(rag_result.get('critical_skills_missing', []))
    n_bonus_missing = len(rag_result.get('bonus_skills_missing', []))
    
    total_critical = n_critical_matched + n_critical_missing
    total_bonus = n_bonus_matched + n_bonus_missing
    
    if total_critical + total_bonus == 0:
        skill_score = 0
    else:
        weighted_points = (n_critical_matched * 1.5) + (n_bonus_matched * 0.5)
        max_points = (total_critical * 1.5) + (total_bonus * 0.5)
        skill_score = int((weighted_points / max_points) * 100) if max_points > 0 else 0
        
    print(f"[RAG] Calculated Score: {skill_score} (Critical: {n_critical_matched}/{total_critical}, Bonus: {n_bonus_matched}/{total_bonus})")
    
    # Get the LoRA score separately
    lora_result = get_lora_score(cv_text, job_description)
    lora_score = lora_result.get("match_score", 0)
    
    print(f"[LoRA Matcher] Raw result: {lora_result}")
    
    # Convert LoRA score from 0-1 range to 0-100 range if needed
    if isinstance(lora_score, float) and 0 <= lora_score <= 1:
        lora_score_converted = int(lora_score * 100)
        lora_score = lora_score_converted
    elif isinstance(lora_score, float):
        lora_score_converted = int(lora_score)
        lora_score = lora_score_converted
    
    print(f"[LoRA Matcher] Final lora_score: {lora_score}")
    
    # Combine the results
    # Flatten structure for frontend compatibility
    final_result = {
        "score": skill_score,
        "matched_skills": rag_result.get('critical_skills_matched', []) + rag_result.get('bonus_skills_matched', []),
        "missing_skills": rag_result.get('critical_skills_missing', []) + rag_result.get('bonus_skills_missing', []),
        "critical_matched": rag_result.get('critical_skills_matched', []),
        "bonus_matched": rag_result.get('bonus_skills_matched', []),
        "critical_missing": rag_result.get('critical_skills_missing', []),
        "bonus_missing": rag_result.get('bonus_skills_missing', []),
        "reasoning": rag_result.get('reasoning', ''),
        "lora_score": lora_score,
        "lora_status": lora_result.get('status'),
        "lora_confidence": lora_result.get('confidence')
    }
    
    return final_result
