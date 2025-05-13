import os
from langchain_community.llms import OpenAI
from tools.cv_parser import parse_cv
from tools.skill_matcher import match_skills
from config import load_config

# Load configuration
config = load_config()

def generate_feedback(matched_skills, missing_skills, cv_file_path):
    # Pass the API key to the OpenAI client
    llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.7, openai_api_key=config.openai_api_key)

    # Analyze the CV as a whole
    cv_text = parse_cv(cv_file_path)
    overall_analysis_prompt = (
        "You are a career coach. Analyze the following CV text and provide an overall assessment, including strengths, weaknesses, and suggestions for improvement. "
        "Focus on structure, content quality, and presentation.\n"
        f"CV Text: {cv_text}\n"
        "Overall Analysis:"
    )
    overall_analysis = llm(overall_analysis_prompt)

    # Refined positive feedback prompt
    positive_prompt = (
        "You are a career coach. Highlight the strengths of the CV based on the following matched skills. "
        "Focus on clarity, formatting, and effective communication of achievements.\n"
        f"Matched Skills: {matched_skills}\n"
        "Positive Feedback:"
    )

    # Refined negative feedback prompt
    negative_prompt = (
        "You are a career coach. Provide constructive feedback on the CV based on the following missing skills. "
        "Focus on missing details, poor organization, or irrelevant information.\n"
        f"Missing Skills: {missing_skills}\n"
        "Constructive Feedback:"
    )

    positive_feedback = llm(positive_prompt)
    negative_feedback = llm(negative_prompt)

    # Implement a matching technique for scoring
    score = match_skills(matched_skills, missing_skills)

    return {
        "overall_analysis": overall_analysis.strip(),
        "positive_feedback": positive_feedback.strip(),
        "negative_feedback": negative_feedback.strip(),
        "score": round(score, 2)
    }
