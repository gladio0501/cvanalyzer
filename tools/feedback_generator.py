import os
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from tools.cv_parser import parse_cv
from tools.skill_matcher import match_skills
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load config and API key
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
config = load_config(".env")

# Create shared model instance
llm = ChatOpenAI(
    model="gpt-4.1",
    temperature=0.7,
    openai_api_key=config.openai_api_key
)

# Define reusable output parser
parser = StrOutputParser()

def generate_feedback(matched_skills, missing_skills, cv_file_path):
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
