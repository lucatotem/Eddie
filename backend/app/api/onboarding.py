from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel
from app.services.confluence_service import confluence_service
from app.services.config_storage import get_storage
from app.services.course_processor import course_processor
from app.services.gemini_service import gemini_service
from app.services.progress_tracker import progress_tracker
from app.models.onboarding_config import (
    OnboardingConfigFile,
    CreateOnboardingRequest,
    UpdateOnboardingRequest
)
import traceback

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
    Automatically processes the course, generates AI content, and creates quizzes
    """
    storage = get_storage()
    config = storage.create(request)
    
    # Background task chain: process → generate course → generate quiz
    def process_and_generate():
        try:
            # Step 1: Process the course (fetch pages, embed content)
            print(f"[Create Config] Processing course: {config.id}")
            course_processor.process_course(config)
            print(f"[Create Config] ✅ Processing complete: {config.id}")
            
            # Step 2: Generate AI course content
            print(f"[Create Config] Generating course content: {config.id}")
            gemini_service.generate_course_content(
                course_id=config.id,
                course_title=config.name,
                course_description=config.instructions,
                num_modules=5
            )
            print(f"[Create Config] ✅ Course generation complete: {config.id}")
            
            # Step 3: Generate final quiz if test_at_end is enabled
            if config.settings.test_at_end:
                print(f"[Create Config] Generating final quiz: {config.id}")
                gemini_service.generate_quiz(
                    course_id=config.id,
                    module_number=None,  # Final quiz
                    num_questions=5,
                    difficulty="medium"
                )
                print(f"[Create Config] ✅ Quiz generation complete: {config.id}")
            
            print(f"[Create Config] ✅✅✅ ALL COMPLETE: {config.id}")
        except Exception as e:
            print(f"[Create Config] ❌ ERROR for {config.id}: {e}")
            print(f"[Create Config] Traceback:\n{traceback.format_exc()}")
    
    background_tasks.add_task(process_and_generate)
    
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
    Automatically re-embeds pages and regenerates AI content when configuration changes
    """
    storage = get_storage()
    config = storage.update(config_id, request)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Background task chain: reprocess → regenerate course → regenerate quiz
    def reprocess_and_regenerate():
        try:
            # Step 1: Re-process the course (fetch pages, embed content)
            print(f"[Update Config] Re-processing course: {config.id}")
            course_processor.process_course(config)
            
            # Step 2: Regenerate AI course content
            print(f"[Update Config] Regenerating course content: {config.id}")
            gemini_service.generate_course_content(
                course_id=config.id,
                course_title=config.name,
                course_description=config.instructions,
                num_modules=5
            )
            
            # Step 3: Regenerate final quiz if test_at_end is enabled
            if config.settings.test_at_end:
                print(f"[Update Config] Regenerating final quiz: {config.id}")
                gemini_service.generate_quiz(
                    course_id=config.id,
                    module_number=None,  # Final quiz
                    num_questions=5,
                    difficulty="medium"
                )
            
            print(f"[Update Config] ✅ Complete: {config.id}")
        except Exception as e:
            print(f"[Update Config] Error for {config.id}: {e}")
    
    background_tasks.add_task(reprocess_and_regenerate)
    
    return config


@router.delete("/configs/{config_id}")
async def delete_config(config_id: str):
    """Delete a config file and all associated course data"""
    storage = get_storage()
    if not storage.delete(config_id):
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Clean up all embeddings, processing data, and generated courses
    course_processor.delete_course_data(config_id)
    gemini_service.delete_generated_course(config_id)
    
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

@router.get("/configs/{config_id}/progress")
async def get_processing_progress(config_id: str):
    """
    Get real-time progress of course processing
    Returns step-by-step progress with detailed logs
    """
    task_id = f"process_{config_id}"
    progress = progress_tracker.get_task_progress(task_id)
    
    if not progress:
        # Check if processing is complete
        status = course_processor.get_processing_status(config_id)
        if status:
            return {
                "status": "completed",
                "message": "Processing completed",
                "result": status
            }
        return {
            "status": "not_started",
            "message": "Processing has not started yet"
        }
    
    return progress

@router.get("/configs/{config_id}/check-updates")
async def check_for_updates(config_id: str):
    """
    Check if any Confluence pages have been updated since last processing
    Returns details about new, deleted, or modified pages
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    update_status = course_processor.check_for_updates(config_id, config)
    return update_status

@router.post("/configs/{config_id}/reprocess")
async def reprocess_course(config_id: str, background_tasks: BackgroundTasks):
    """
    Manually trigger re-processing of a course
    Useful when you know pages have been updated
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Trigger re-processing in background
    background_tasks.add_task(course_processor.process_course, config)
    
    return {
        "message": "Course re-processing started",
        "course_id": config_id
    }


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


# AI-Generated Course Endpoints

@router.post("/configs/{config_id}/generate-course")
async def generate_course(config_id: str, background_tasks: BackgroundTasks, num_modules: int = 5, force: bool = False):
    """
    Generate an AI-powered interactive course from embedded Confluence content
    Uses Gemini 2.0 Flash Lite to create engaging modules with summaries and takeaways
    
    Args:
        config_id: The course configuration ID
        num_modules: Number of modules to generate (default: 5)
        force: If True, regenerate even if course already exists (default: False)
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Check if the course has been processed
    if not course_processor.is_course_processed(config_id):
        raise HTTPException(
            status_code=400, 
            detail="Course has not been processed yet. Please wait for embedding to complete."
        )
    
    # Check if course already exists (unless force regeneration)
    existing_course = gemini_service.get_generated_course(config_id)
    if existing_course and not force:
        return {
            "message": "Course already exists. Use force=true to regenerate.",
            "course_id": config_id,
            "status": "exists",
            "course": existing_course
        }
    
    # Generate the course in the background
    def generate_task():
        try:
            gemini_service.generate_course_content(
                course_id=config_id,
                course_title=config.name,
                course_description=config.instructions,
                num_modules=num_modules
            )
        except Exception as e:
            print(f"Error generating course {config_id}: {e}")
    
    background_tasks.add_task(generate_task)
    
    return {
        "message": "Course generation started" if force else "Generating new course",
        "course_id": config_id,
        "status": "generating"
    }


@router.get("/configs/{config_id}/generated-course")
async def get_generated_course(config_id: str):
    """
    Get the AI-generated course content
    Returns the complete course with all modules, or 404 if not yet generated
    """
    course_data = gemini_service.get_generated_course(config_id)
    
    if not course_data:
        raise HTTPException(
            status_code=404, 
            detail="Course has not been generated yet. Use POST /configs/{id}/generate-course first."
        )
    
    return course_data


# Quiz Generation Endpoints

class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz"""
    module_number: Optional[int] = None  # None = final quiz for entire course
    num_questions: int = 5
    difficulty: str = "medium"  # "easy", "medium", or "hard"
    force: bool = False  # Force regeneration even if quiz exists


class QuizSubmission(BaseModel):
    """User's quiz answers"""
    answers: List[int]  # List of selected answer indices


@router.post("/configs/{config_id}/generate-quiz")
async def generate_quiz(config_id: str, request: QuizGenerateRequest, background_tasks: BackgroundTasks):
    """
    Generate a quiz based on course content
    Can generate quizzes for individual modules or the entire course
    
    Args:
        config_id: The course configuration ID
        request: Quiz generation parameters including force flag
    """
    storage = get_storage()
    config = storage.get(config_id)
    
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    # Check if course has been generated
    course_data = gemini_service.get_generated_course(config_id)
    if not course_data:
        raise HTTPException(
            status_code=400,
            detail="Course has not been generated yet. Generate the course first."
        )
    
    # Check if quiz already exists (unless force regeneration)
    existing_quiz = gemini_service.get_quiz(config_id, request.module_number)
    if existing_quiz and not request.force:
        quiz_type = f"module {request.module_number}" if request.module_number else "final"
        return {
            "message": f"Quiz already exists for {quiz_type}. Use force=true to regenerate.",
            "course_id": config_id,
            "module_number": request.module_number,
            "status": "exists",
            "quiz": existing_quiz
        }
    
    # Generate quiz in background
    def generate_task():
        try:
            gemini_service.generate_quiz(
                course_id=config_id,
                module_number=request.module_number,
                num_questions=request.num_questions,
                difficulty=request.difficulty
            )
        except Exception as e:
            print(f"Error generating quiz for {config_id}: {e}")
    
    background_tasks.add_task(generate_task)
    
    quiz_type = f"module {request.module_number}" if request.module_number else "final"
    return {
        "message": f"Quiz generation started for {quiz_type}" if request.force else f"Generating new quiz for {quiz_type}",
        "course_id": config_id,
        "module_number": request.module_number,
        "status": "generating"
    }


@router.get("/configs/{config_id}/quiz")
async def get_quiz(config_id: str, module_number: Optional[int] = None):
    """
    Get a generated quiz (without answers shown)
    Use module_number query param for module-specific quiz
    """
    quiz_data = gemini_service.get_quiz(config_id, module_number)
    
    if not quiz_data:
        quiz_type = f"module {module_number}" if module_number else "final"
        raise HTTPException(
            status_code=404,
            detail=f"Quiz for {quiz_type} not found. Generate it first."
        )
    
    # Return quiz without revealing correct answers
    return {
        "course_id": quiz_data["course_id"],
        "quiz_title": quiz_data["quiz_title"],
        "module_number": quiz_data.get("module_number"),
        "difficulty": quiz_data["difficulty"],
        "total_questions": quiz_data["total_questions"],
        "questions": [
            {
                "question": q["question"],
                "options": q["options"],
                "difficulty": q["difficulty"]
            }
            for q in quiz_data["questions"]
        ]
    }


@router.post("/configs/{config_id}/quiz/submit")
async def submit_quiz(config_id: str, submission: QuizSubmission, module_number: Optional[int] = None):
    """
    Submit quiz answers for grading
    Returns score, feedback, and explanations
    """
    try:
        results = gemini_service.submit_quiz_answers(
            course_id=config_id,
            user_answers=submission.answers,
            module_number=module_number
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


