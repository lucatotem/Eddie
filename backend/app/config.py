from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Confluence stuff (the wiki where all the docs live)
    confluence_url: str
    confluence_user_email: str
    confluence_api_token: str  # get this from your confluence profile
    
    # Google Gemini for AI magic ✨
    gemini_api_key: str = ""
    
    # Other settings
    environment: str = "development"
    debug: bool = True  # always True because we're still figuring things out
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    # lru_cache = fancy way to only load the .env file once
    # (found this on stack overflow, seems to work great!)
    return Settings()
