from langchain.llms import OpenAI

def extract_skills(text):
    llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0)
    prompt = (
        "You are an expert in analyzing CVs. Extract a list of relevant skills from the following text. "
        "Ensure the skills are specific, relevant, and include any implied skills that make sense for the context.\n"
        f"Text: {text}\n"
        "Skills (comma-separated):"
    )
    response = llm(prompt)
    return [skill.strip() for skill in response.split(",") if skill.strip()]
