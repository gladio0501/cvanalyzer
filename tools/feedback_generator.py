import os
from tools.cv_parser import parse_cv
from tools.skill_matcher import match_skills
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load config and API key
config = load_config(".env")
OPENAI_API_KEY = config.openai_api_key

# Create shared model instance
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY
)

# Define reusable output parser
parser = StrOutputParser()

def generate_feedback(matched_skills, missing_skills, cv_file_path):
    # Parse the CV text
    cv_text = parse_cv(cv_file_path)

    # Prompts
    overall_template = PromptTemplate.from_template(
        "You are a career coach. Analyze the following CV text and provide an overall assessment in 100 characters or less. "
        "Focus on structure, content quality, and presentation.\nCV Text: {cv_text}\nOverall Analysis:"
    )
    positive_template = PromptTemplate.from_template(
        "You are a career coach. Highlight the strengths of the CV based on the following matched skills in 100 characters or less. "
        "Focus on clarity, formatting, and effective communication of achievements.\nMatched Skills: {matched_skills}\nPositive Feedback:"
    )
    negative_template = PromptTemplate.from_template(
        "You are a career coach. Provide constructive feedback on the CV based on the following missing skills in 100 characters or less. "
        "Focus on missing details, poor organization, or irrelevant information.\nMissing Skills: {missing_skills}\nConstructive Feedback:"
    )

    # Chain each prompt with the LLM and parser
    overall_chain = overall_template | llm | parser
    positive_chain = positive_template | llm | parser
    negative_chain = negative_template | llm | parser

    # Run chains
    overall_analysis = overall_chain.invoke({"cv_text": cv_text})
    positive_feedback = positive_chain.invoke({"matched_skills": matched_skills})
    negative_feedback = negative_chain.invoke({"missing_skills": missing_skills})

    # Match score
    score = match_skills(matched_skills, missing_skills)

    return {
        "overall_analysis": overall_analysis.strip(),
        "positive_feedback": positive_feedback.strip(),
        "negative_feedback": negative_feedback.strip(),
        "score": round(score, 2)
    }
