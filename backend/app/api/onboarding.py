from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from app.services.confluence_service import confluence_service
from app.services.config_storage import get_storage
from app.services.course_processor import course_processor
from app.models.onboarding_config import (
    OnboardingConfigFile,
    CreateOnboardingRequest,
    UpdateOnboardingRequest
)

router = APIRouter()

# Legacy models for backward compatibility with Confluence-based configs
class OnboardingConfig(BaseModel):
    """An onboarding configuration created by admins"""
    id: str
    title: str
    instructions: str
    source_page_ids: List[str]
    labels: List[str]

class SourcePage(BaseModel):
    """A page containing learning material"""
    id: str
    title: str
    body: str

class OnboardingCourse(BaseModel):
    """A complete onboarding course with config + source material"""
    config: OnboardingConfig
    source_pages: List[SourcePage]

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int
    explanation: str

class QuizResponse(BaseModel):
    questions: List[QuizQuestion]
    page_title: str


# NEW: File-based config management endpoints

@router.post("/configs", response_model=OnboardingConfigFile)
async def create_config(request: CreateOnboardingRequest, background_tasks: BackgroundTasks):
    """
    Create a new onboarding config and save it to a file
    Automatically processes the course in the background to embed all pages
    """
    storage = get_storage()
    config = storage.create(request)
    
    # Process the course in the background (fetch pages, embed content)
    background_tasks.add_task(course_processor.process_course, config)
    
    return config


@router.get("/configs", response_model=List[OnboardingConfigFile])
async def list_configs():
    """
    Get all saved onboarding configs from the onboarding/ folder
    Returns most recently updated first
    """
    storage = get_storage()
    return storage.list_all()


@router.get("/configs/{config_id}", response_model=OnboardingConfigFile)
async def get_config(config_id: str):
    """Get a specific config by ID"""
    storage = get_storage()
    config = storage.get(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config


@router.put("/configs/{config_id}", response_model=OnboardingConfigFile)
async def update_config(config_id: str, request: UpdateOnboardingRequest, background_tasks: BackgroundTasks):
    """
    Update an existing config and re-process the course
    Automatically re-embeds all pages when configuration changes
    """
    storage = get_storage()
    config = storage.update(config_id, request)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Re-process the course in the background
    background_tasks.add_task(course_processor.process_course, config)
    
    return config


@router.delete("/configs/{config_id}")
async def delete_config(config_id: str):
    """Delete a config file and all associated course data"""
    storage = get_storage()
    if not storage.delete(config_id):
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Clean up all embeddings and processing data
    course_processor.delete_course_data(config_id)
    
    return {"message": "Config deleted successfully"}

@router.get("/configs/{config_id}/processing-status")
async def get_processing_status(config_id: str):
    """
    Get the processing status of a course
    Shows how many pages have been processed and embedded
    """
    status = course_processor.get_processing_status(config_id)
    if not status:
        return {
            "processed": False,
            "message": "Course has not been processed yet"
        }
    return status


@router.get("/course/{config_id}", response_model=OnboardingCourse)
async def get_onboarding_course(config_id: str):
    """
    Get a complete onboarding course with all Confluence pages
    Now uses file-based configs instead of Confluence labels
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Fetch all the linked Confluence pages
    source_pages = []
    all_page_ids = config.linked_pages.copy()
    failed_pages = []  # Track which pages failed to load
    
    # Expand folders if the setting is enabled
    if config.settings.folder_recursion:
        expanded_ids = set()
        for page_id in config.linked_pages:
            try:
                # Check if this is a folder (has children)
                if confluence_service.is_page_a_folder(page_id):
                    # Get all children recursively
                    child_ids = confluence_service.get_child_pages(page_id, recursive=True)
                    expanded_ids.update(child_ids)
                else:
                    expanded_ids.add(page_id)
            except Exception as e:
                # Page doesn't exist or no access
                print(f"Warning: Could not check page {page_id}: {e}")
                failed_pages.append({"id": page_id, "error": str(e)})
        all_page_ids = list(expanded_ids)
    
    # Fetch each page from Confluence
    for page_id in all_page_ids:
        try:
            page = confluence_service.get_page_by_id(page_id)
            if page:
                source_pages.append(SourcePage(
                    id=page["id"],
                    title=page["title"],
                    body=page.get("body", {}).get("storage", {}).get("value", "")
                ))
        except Exception as e:
            print(f"Warning: Could not fetch page {page_id}: {e}")
            failed_pages.append({"id": page_id, "error": str(e)})
    
    # Log failures for debugging
    if failed_pages:
        print(f"Failed to load {len(failed_pages)} pages: {failed_pages}")
    
    # Convert to legacy format for backward compatibility
    legacy_config = OnboardingConfig(
        id=config.id,
        title=config.name,
        instructions=config.instructions,
        source_page_ids=all_page_ids,
        labels=[]  # No longer using Confluence labels
    )
    
    return OnboardingCourse(
        config=legacy_config,
        source_pages=source_pages
    )

@router.get("/summary/{config_id}")
async def get_course_summary(config_id: str):
    """
    Generate a summary of the entire onboarding course
    TODO: integrate OpenAI here to create intelligent summaries
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Get all page IDs (with folder expansion if enabled)
    all_page_ids = config.linked_pages.copy()
    if config.settings.folder_recursion:
        expanded_ids = set()
        for page_id in config.linked_pages:
            if confluence_service.is_page_a_folder(page_id):
                child_ids = confluence_service.get_child_pages(page_id, recursive=True)
                expanded_ids.update(child_ids)
            else:
                expanded_ids.add(page_id)
        all_page_ids = list(expanded_ids)
    
    # Fetch source pages for summary
    source_pages = []
    for page_id in all_page_ids:
        page = confluence_service.get_page_by_id(page_id)
        if page:
            source_pages.append({
                "title": page["title"],
                "id": page["id"]
            })
    
    # Mock response - replace with actual AI call
    return {
        "config_title": config.name,
        "summary": f"This onboarding course covers {len(source_pages)} topics. {config.instructions}",
        "source_pages": source_pages,
        "key_points": [
            "Follow the instructions in the config",
            f"Study the {len(source_pages)} linked pages",
            "Take the quiz at the end" if config.settings.test_at_end else "No quiz required"
        ]
    }

@router.get("/quiz/{config_id}", response_model=QuizResponse)
async def generate_course_quiz(config_id: str, question_count: int = 5):
    """
    Generate quiz questions from the entire course
    TODO: implement actual AI generation based on ALL source pages
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Check if quiz is enabled in settings
    if not config.settings.test_at_end:
        return QuizResponse(
            questions=[],
            page_title=config.name
        )
    
    # Mock quiz - this should use AI to generate from actual content
    mock_questions = [
        QuizQuestion(
            question="Based on the onboarding materials, what's the first thing you should do?",
            options=[
                "Read all the linked documentation",
                "Start coding immediately",
                "Ask for help on Slack",
                "Set up your environment"
            ],
            correct_answer=3,
            explanation="Always set up your environment first. The docs will tell you how."
        ),
        QuizQuestion(
            question="What's covered in this onboarding course?",
            options=[
                "Only frontend concepts",
                "Only backend concepts",
                "Whatever the admin linked in the config",
                "Random stuff from the internet"
            ],
            correct_answer=2,
            explanation="The admin decides what you learn by linking relevant pages."
        )
    ]
    
    return QuizResponse(
        questions=mock_questions[:question_count],
        page_title=config_data["title"]
    )
