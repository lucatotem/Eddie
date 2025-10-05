"""
Course processing service
Handles embedding Confluence pages and generating course structure
"""

from typing import List, Dict, Optional
from app.services.confluence_service import confluence_service
from app.services.vector_store import vector_store
from app.models.onboarding_config import OnboardingConfigFile
import json
from pathlib import Path


class CourseProcessor:
    """
    Processes courses: fetches pages, generates embeddings, creates structure
    """
    
    def __init__(self):
        self.processed_courses_dir = Path("onboarding/processed")
        self.processed_courses_dir.mkdir(parents=True, exist_ok=True)
    
    def process_course(self, config: OnboardingConfigFile) -> Dict:
        """
        Process a course: embed all pages and prepare for AI generation
        
        Args:
            config: The onboarding configuration
            
        Returns:
            Dict with processing status and page count
        """
        print(f"\n[CourseProcessor] Processing course: {config.name} ({config.id})")
        
        # Step 1: Fetch all Confluence pages
        page_ids = config.linked_pages.copy()
        
        # Expand folders if enabled
        if config.settings.folder_recursion:
            print("[CourseProcessor] Folder recursion enabled, expanding...")
            expanded_ids = set()
            for page_id in config.linked_pages:
                try:
                    if confluence_service.is_page_a_folder(page_id):
                        child_ids = confluence_service.get_child_pages(page_id, recursive=True)
                        expanded_ids.update(child_ids)
                        print(f"   Found {len(child_ids)} child pages for {page_id}")
                    else:
                        expanded_ids.add(page_id)
                except Exception as e:
                    print(f"   Warning: Could not expand {page_id}: {e}")
                    expanded_ids.add(page_id)
            page_ids = list(expanded_ids)
        
        print(f"[CourseProcessor] Total pages to process: {len(page_ids)}")
        
        # Step 2: Clear existing embeddings for this course
        print("[CourseProcessor] Clearing old embeddings...")
        stored_page_ids = vector_store.get_all_page_ids(config.id)
        for old_page_id in stored_page_ids:
            if old_page_id not in page_ids:
                # Page was removed from course
                vector_store.delete_page_content(config.id, old_page_id)
        
        # Step 3: Fetch and embed each page
        processed_pages = []
        failed_pages = []
        
        for i, page_id in enumerate(page_ids, 1):
            try:
                print(f"\n[CourseProcessor] [{i}/{len(page_ids)}] Processing page {page_id}...")
                
                # Fetch page from Confluence
                page_data = confluence_service.get_page_by_id(page_id)
                
                if not page_data:
                    print(f"   Failed: Page not found")
                    failed_pages.append({
                        "id": page_id,
                        "error": "Page not found or no access"
                    })
                    continue
                
                page_title = page_data.get("title", "Untitled")
                page_body = page_data.get("body", {}).get("storage", {}).get("value", "")
                page_url = f"{confluence_service.base_url.replace('/rest/api', '')}{page_data.get('_links', {}).get('webui', '')}"
                page_version = page_data.get("version", {}).get("number", 0)
                
                print(f"   Title: {page_title}")
                print(f"   Version: {page_version}")
                print(f"   Content length: {len(page_body)} chars")
                
                # Embed the page content
                vector_store.add_page_content(
                    course_id=config.id,
                    page_id=page_id,
                    page_title=page_title,
                    page_content=page_body,
                    page_url=page_url
                )
                
                processed_pages.append({
                    "page_id": page_id,
                    "title": page_title,
                    "url": page_url,
                    "content_length": len(page_body),
                    "version": page_version
                })
                
                print(f"   ✓ Successfully embedded")
                
            except Exception as e:
                print(f"   ✗ Error: {e}")
                failed_pages.append({
                    "id": page_id,
                    "error": str(e)
                })
        
        # Step 4: Store processing metadata
        processing_result = {
            "course_id": config.id,
            "course_name": config.name,
            "total_pages": len(page_ids),
            "processed_pages": len(processed_pages),
            "failed_pages": len(failed_pages),
            "pages": processed_pages,
            "failures": failed_pages,
            "embeddings_generated": True,
            "ai_course_generated": False  # Will be set to True in task 4
        }
        
        # Save processing result
        result_file = self.processed_courses_dir / f"{config.id}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(processing_result, f, indent=2)
        
        print(f"\n[CourseProcessor] ✅ Course processing complete!")
        print(f"   Processed: {len(processed_pages)}/{len(page_ids)} pages")
        print(f"   Failed: {len(failed_pages)} pages")
        
        return processing_result
    
    def get_processing_status(self, course_id: str) -> Optional[Dict]:
        """
        Get the processing status for a course
        
        Returns:
            Processing result dict or None if not processed yet
        """
        result_file = self.processed_courses_dir / f"{course_id}.json"
        
        if not result_file.exists():
            return None
        
        with open(result_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def is_course_processed(self, course_id: str) -> bool:
        """Check if a course has been processed"""
        return (self.processed_courses_dir / f"{course_id}.json").exists()
    
    def delete_course_data(self, course_id: str):
        """
        Delete all data for a course (embeddings and processing results)
        """
        print(f"[CourseProcessor] Deleting data for course {course_id}")
        
        # Delete embeddings
        vector_store.delete_course_collection(course_id)
        
        # Delete processing result
        result_file = self.processed_courses_dir / f"{course_id}.json"
        if result_file.exists():
            result_file.unlink()
        
        print(f"[CourseProcessor] ✓ Deleted course data")
    
    def check_for_updates(self, course_id: str, config: OnboardingConfigFile) -> Dict:
        """
        Check if any Confluence pages have been updated since last processing
        
        Args:
            course_id: The course ID
            config: The onboarding configuration
            
        Returns:
            Dict with update status and details
        """
        print(f"[CourseProcessor] Checking for updates: {course_id}")
        
        # Get processing status
        status = self.get_processing_status(course_id)
        if not status:
            return {
                "needs_update": True,
                "reason": "Course has never been processed",
                "changed_pages": [],
                "new_pages": [],
                "deleted_pages": []
            }
        
        # Get current page list
        page_ids = config.linked_pages.copy()
        if config.settings.folder_recursion:
            expanded_ids = set()
            for page_id in config.linked_pages:
                try:
                    if confluence_service.is_page_a_folder(page_id):
                        child_ids = confluence_service.get_child_pages(page_id, recursive=True)
                        expanded_ids.update(child_ids)
                    else:
                        expanded_ids.add(page_id)
                except Exception as e:
                    print(f"   Error expanding {page_id}: {e}")
            page_ids = list(expanded_ids)
        
        # Compare with previously processed pages
        processed_page_ids = {p["page_id"] for p in status.get("processed_pages", [])}
        current_page_ids = set(page_ids)
        
        new_pages = current_page_ids - processed_page_ids
        deleted_pages = processed_page_ids - current_page_ids
        potentially_changed = current_page_ids & processed_page_ids
        
        # Check versions for potentially changed pages
        changed_pages = []
        for page_id in potentially_changed:
            try:
                page = confluence_service.get_page_by_id(page_id)
                if page:
                    current_version = page.get("version", {}).get("number", 0)
                    
                    # Find the stored version
                    stored_page = next(
                        (p for p in status.get("processed_pages", []) if p["page_id"] == page_id),
                        None
                    )
                    
                    if stored_page:
                        stored_version = stored_page.get("version", 0)
                        if current_version > stored_version:
                            changed_pages.append({
                                "page_id": page_id,
                                "title": page.get("title", "Unknown"),
                                "old_version": stored_version,
                                "new_version": current_version
                            })
            except Exception as e:
                print(f"   Error checking page {page_id}: {e}")
        
        needs_update = bool(new_pages or deleted_pages or changed_pages)
        
        return {
            "needs_update": needs_update,
            "reason": self._get_update_reason(new_pages, deleted_pages, changed_pages),
            "new_pages": list(new_pages),
            "deleted_pages": list(deleted_pages),
            "changed_pages": changed_pages,
            "total_changes": len(new_pages) + len(deleted_pages) + len(changed_pages)
        }
    
    def _get_update_reason(self, new_pages: set, deleted_pages: set, changed_pages: List) -> str:
        """Generate a human-readable update reason"""
        reasons = []
        if new_pages:
            reasons.append(f"{len(new_pages)} new page(s)")
        if deleted_pages:
            reasons.append(f"{len(deleted_pages)} deleted page(s)")
        if changed_pages:
            reasons.append(f"{len(changed_pages)} updated page(s)")
        
        if not reasons:
            return "No changes detected"
        
        return ", ".join(reasons)


# Singleton instance
course_processor = CourseProcessor()
