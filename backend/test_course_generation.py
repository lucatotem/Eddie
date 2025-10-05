"""
Manual test of course processing to debug embedding issues
Run this directly without uvicorn to avoid auto-reload cancellation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.services.config_storage import get_storage
from app.services.course_processor import course_processor
from app.services.gemini_service import gemini_service
import traceback

print("=" * 60)
print("MANUAL COURSE PROCESSING TEST")
print("=" * 60)

# Load the backend-dev config
storage = get_storage()
config = storage.get("backend-dev")

if not config:
    print("❌ Config 'backend-dev' not found!")
    exit(1)

print(f"\n✅ Loaded config: {config.name}")
print(f"   Pages: {config.linked_pages}")
print(f"   Settings: {config.settings}")

# Step 1: Process the course
print("\n" + "=" * 60)
print("STEP 1: PROCESSING COURSE (Embeddings)")
print("=" * 60)
try:
    result = course_processor.process_course(config)
    print(f"\n✅ Processing complete!")
    print(f"   Total pages: {result['total_pages']}")
    print(f"   Processed: {result['processed_pages']}")
    print(f"   Failed: {result['failed_pages']}")
except Exception as e:
    print(f"\n❌ ERROR during processing: {e}")
    print(f"\nTraceback:\n{traceback.format_exc()}")
    exit(1)

# Step 2: Generate course content
print("\n" + "=" * 60)
print("STEP 2: GENERATING COURSE CONTENT (AI)")
print("=" * 60)
try:
    course_data = gemini_service.generate_course_content(
        course_id=config.id,
        course_title=config.name,
        course_description=config.instructions,
        num_modules=5
    )
    print(f"\n✅ Course generation complete!")
    print(f"   Modules: {len(course_data.get('modules', []))}")
    print(f"   Title: {course_data.get('title')}")
except Exception as e:
    print(f"\n❌ ERROR during course generation: {e}")
    print(f"\nTraceback:\n{traceback.format_exc()}")
    exit(1)

# Step 3: Generate quiz
if config.settings.test_at_end:
    print("\n" + "=" * 60)
    print("STEP 3: GENERATING QUIZ")
    print("=" * 60)
    try:
        quiz_data = gemini_service.generate_quiz(
            course_id=config.id,
            module_number=None,
            num_questions=5,
            difficulty="medium"
        )
        print(f"\n✅ Quiz generation complete!")
        print(f"   Questions: {quiz_data.get('total_questions')}")
    except Exception as e:
        print(f"\n❌ ERROR during quiz generation: {e}")
        print(f"\nTraceback:\n{traceback.format_exc()}")
        exit(1)

print("\n" + "=" * 60)
print("🎉 ALL STEPS COMPLETE!")
print("=" * 60)
