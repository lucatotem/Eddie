"""
Onboarding config models - because storing everything in Confluence got old fast
TODO: Maybe add validation for page IDs later?
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class OnboardingSettings(BaseModel):
    """Settings for how the onboarding course behaves"""
    folder_recursion: bool = Field(
        default=True,
        description="Auto-expand folders to include all child pages"
    )
    test_at_end: bool = Field(
        default=True,
        description="Show quiz at the end of the course"
    )
    # TODO: add more settings like quiz_passing_score, estimated_time, etc.


class OnboardingConfigFile(BaseModel):
    """
    The actual config file structure
    This is what gets saved to the onboarding/ folder
    """
    id: str = Field(description="Unique identifier (filename without .json)")
    name: str = Field(description="Human-readable course name")
    emoji: str = Field(default="📚", description="Emoji for the course card")
    color: str = Field(default="#4C9AFF", description="Color for the course card")
    
    settings: OnboardingSettings = Field(default_factory=OnboardingSettings)
    
    instructions: str = Field(
        description="Custom prompt/instructions for what this onboarding covers"
    )
    
    linked_pages: List[str] = Field(
        default_factory=list,
        description="List of Confluence page IDs to include in this course"
    )
    
    # metadata - auto-managed
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "backend-dev-onboarding",
                "name": "Backend Developer Onboarding",
                "emoji": "🚀",
                "color": "#36B37E",
                "settings": {
                    "folder_recursion": True,
                    "test_at_end": True
                },
                "instructions": "This course teaches new backend devs about our FastAPI architecture, database design, and API patterns.",
                "linked_pages": ["123456", "789012"],
                "created_at": "2025-10-05T10:00:00",
                "updated_at": "2025-10-05T10:00:00"
            }
        }


class CreateOnboardingRequest(BaseModel):
    """Request body for creating a new onboarding config"""
    name: str
    emoji: str = "📚"
    color: str = "#4C9AFF"
    settings: OnboardingSettings = Field(default_factory=OnboardingSettings)
    instructions: str
    linked_pages: List[str] = []


class UpdateOnboardingRequest(BaseModel):
    """Request body for updating an existing config"""
    name: Optional[str] = None
    emoji: Optional[str] = None
    color: Optional[str] = None
    settings: Optional[OnboardingSettings] = None
    instructions: Optional[str] = None
    linked_pages: Optional[List[str]] = None
