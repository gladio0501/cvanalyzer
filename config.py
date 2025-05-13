from dataclasses import dataclass
from environs import Env

@dataclass
class Config:
    openai_api_key: str
    api_url: str
    max_content_length: int


def load_config(path: str = None) -> Config:
    """Load environment variables from a .env file and return a Config object."""
    env = Env()
    # Read .env from the project root if path is None
    env.read_env(path)

    return Config(
        openai_api_key=env.str("OPENAI_API_KEY"),
        api_url=env.str("API_URL", "http://localhost:8000/analyze_cv"),
        max_content_length=env.int("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    )
