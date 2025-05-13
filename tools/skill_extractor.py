from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load OpenAI key from .env
config = load_config(".env")
OPENAI_API_KEY = config.openai_api_key

# Initialize LLM
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

# Prompt template
prompt_template = PromptTemplate.from_template(
    "You are an expert in analyzing CVs. Extract a list of relevant skills from the following text. "
    "Ensure the skills are specific, relevant, and include any implied skills that make sense for the context.\n"
    "Text: {text}\n"
    "Skills (comma-separated):"
)

# Chain
chain = prompt_template | llm | StrOutputParser()

# Skill extraction function
def extract_skills(text):
    response = chain.invoke({"text": text})
    return [skill.strip() for skill in response.split(",") if skill.strip()]
