import json
import re
import os
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from config import load_config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

# Load OpenAI key from .env
config = load_config(".env")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"

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
    Uses the LLM to extract a clean, deduplicated list of skills mentioned in either the job description or CV,
    but only allows skills present in the skills knowledge base.
    Returns a list of normalized skill names.
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

# 6. Build the RAG Chain
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
    Uses a RAG pipeline to extract matched and missing skills, and provide a score.
    The job_description is used to retrieve relevant skills from the knowledge base.
    Returns an error dict if job_description is empty or only whitespace.
    """
    if not job_description or not job_description.strip():
        print("[RAG] ERROR: Job description is empty or missing.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "error": "Job description is empty. Please provide a valid job description."
        }
    if not cv_text or not cv_text.strip():
        print("[RAG] ERROR: CV text is empty or missing.")
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0,
            "error": "CV text is empty. Please upload a valid CV file."
        }
    print(f"[RAG] job_description length: {len(job_description)}")
    print(f"[RAG] cv_text length: {len(cv_text)}")
    return rag_chain.invoke({"cv_text": cv_text, "job_description": job_description}, run_name="RAG Scoring Chain")
