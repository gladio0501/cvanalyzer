"""
Configuration Management Module for CV Analyzer.
"""

from dataclasses import dataclass
from environs import Env
from pydantic import SecretStr
from typing import Optional



@dataclass
class Config:
    """
    Application configuration data class.
    """
    openai_api_key: SecretStr
    api_url: str
    max_content_length: int
    langsmith_api_key: Optional[str] = None
    langsmith_endpoint: Optional[str] = None
    langsmith_project: Optional[str] = None
    langsmith_tracing: bool = False
    lora_matcher_api_url: Optional[str] = None
    lora_matcher_api_key: Optional[str] = None


def load_config(path: Optional[str] = None) -> Config:
    """
    Load environment variables from a .env file and return a Config object.
    """
    env = Env()
    env.read_env(path)

    return Config(
        openai_api_key=SecretStr(env.str("OPENAI_API_KEY")),
        api_url=env.str("API_URL", "http://localhost:8000/analyze_cv"),
        max_content_length=env.int("MAX_CONTENT_LENGTH", 16 * 1024 * 1024),
        langsmith_api_key=env.str("LANGSMITH_API_KEY", None),
        langsmith_endpoint=env.str("LANGSMITH_ENDPOINT", None),
        langsmith_project=env.str("LANGSMITH_PROJECT", None),
        langsmith_tracing=env.bool("LANGSMITH_TRACING", False),
        lora_matcher_api_url=env.str("LORA_MATCHER_API_URL", None),
        lora_matcher_api_key=env.str("LORA_MATCHER_API_KEY", None)
    )
