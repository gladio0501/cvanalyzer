"""
Configuration Management Module for CV Analyzer

This module handles environment variable loading and configuration management
for the CV Analyzer application. It provides a centralized way to manage
API keys, service endpoints, and application settings.

Key Features:
- Environment variable loading from .env files
- Type-safe configuration with dataclasses and pydantic
- Support for optional configuration values
- Secure handling of API keys using SecretStr

Configuration Categories:
- OpenAI: API keys for LLM and embedding services
- LangSmith: Tracing and monitoring configuration
- LoRA Matcher: External API settings for neural similarity scoring
- Application: General application settings

Dependencies:
- environs: For environment variable parsing
- pydantic: For secure string handling
- dataclasses: For structured configuration objects

"""

from dataclasses import dataclass
from environs import Env
from pydantic import SecretStr
from typing import Optional



@dataclass
class Config:
    """
    Application configuration data class.
    
    This class defines all configuration parameters needed for the CV Analyzer
    application, including API keys, service endpoints, and application settings.
    
    Attributes:
        openai_api_key (SecretStr): Secure OpenAI API key for LLM and embeddings
        api_url (str): Base URL for the CV analyzer API endpoint
        max_content_length (int): Maximum file size limit for uploads in bytes
        langsmith_api_key (Optional[str]): API key for LangSmith tracing service
        langsmith_endpoint (Optional[str]): LangSmith service endpoint URL
        langsmith_project (Optional[str]): Project name for LangSmith organization
        langsmith_tracing (bool): Enable/disable LangSmith tracing
        lora_matcher_api_url (Optional[str]): URL for external LoRA model API
        lora_matcher_api_key (Optional[str]): Authentication key for LoRA API
        
    Note:
        - SecretStr is used for sensitive data to prevent accidental logging
        - Optional fields default to None and can be omitted from environment
        - Boolean fields have sensible defaults for development environments
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
    
    This function reads environment variables from the specified .env file
    (or default locations) and creates a validated Config object with all
    necessary application settings.
    
    Args:
        path (Optional[str]): Path to the .env file. If None, uses default
                             locations (.env in current directory or environment)
                             
    Returns:
        Config: Validated configuration object with all loaded settings
        
    Example:
        >>> config = load_config(".env")
        >>> print(config.api_url)
        "http://localhost:8000/analyze_cv"
        
        >>> config = load_config("/path/to/custom/.env")
        >>> print(config.openai_api_key.get_secret_value())
        "sk-..."
        
    Raises:
        ValueError: If required environment variables are missing
        ValidationError: If environment variables have invalid values
        
    Environment Variables:
        Required:
        - OPENAI_API_KEY: OpenAI API key for LLM services
        
        Optional with defaults:
        - API_URL: API endpoint (default: http://localhost:8000/analyze_cv)
        - MAX_CONTENT_LENGTH: File size limit (default: 16MB)
        - LANGSMITH_API_KEY: LangSmith tracing key
        - LANGSMITH_ENDPOINT: LangSmith service URL
        - LANGSMITH_PROJECT: LangSmith project name
        - LANGSMITH_TRACING: Enable tracing (default: False)
        - LORA_MATCHER_API_URL: LoRA model API URL
        - LORA_MATCHER_API_KEY: LoRA model API key
        
    Note:
        - Uses environs library for robust environment variable parsing
        - Supports type conversion and validation
        - Sensitive values are wrapped in SecretStr for security
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
