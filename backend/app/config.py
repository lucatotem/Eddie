from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Confluence settings
    confluence_url: str
    confluence_user_email: str
    confluence_api_token: str
    
    # Gemini API (for AI features)
    gemini_api_key: str = ""
    
    # App settings
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    """
    Using lru_cache so we don't load env vars every single time
    Learned this from a senior dev review - apparently it's "best practice"
    """
    return Settings()
