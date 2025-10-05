"""
Gemini AI service for generating interactive courses and quizzes
Uses Gemini 2.0 Flash Lite for fast, cost-effective generation
"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.services.vector_store import vector_store
import json
import os

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini 2.0 Flash Lite model"""
        if not self.settings.gemini_api_key:
            print("Warning: GEMINI_API_KEY not set. AI generation will not work.")
            return
        
        genai.configure(api_key=self.settings.gemini_api_key)
        # Use Gemini 2.0 Flash Lite for fast, efficient generation
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
    
    def generate_course_content(
        self, 
        course_id: str, 
        course_title: str,
        course_description: str,
        num_modules: int = 5
    ) -> Dict[str, Any]:
        """
        Generate an interactive course with multiple modules
        Uses vector search to retrieve relevant content and AI to create engaging summaries
        
        Args:
            course_id: The ID of the course config
            course_title: Title of the course
            course_description: Description/instructions for the course
            num_modules: Number of modules to generate (default: 5)
        
        Returns:
            Dictionary with course structure and generated content
        """
        if not self.model:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY.")
        
        # Step 1: Get all content from vector store for this course
        # We'll use the course description as a query to find relevant content
        search_results = vector_store.search_similar(
            course_id=course_id,
            query_text=course_description or course_title,
            top_k=50  # Get more chunks to have comprehensive coverage
        )
        
        if not search_results:
            raise Exception(f"No content found for course {course_id}. Has it been processed?")
        
        # Step 2: Organize content by page
        pages_content = {}
        for result in search_results:
            page_id = result["metadata"].get("page_id")
            page_title = result["metadata"].get("page_title", "Untitled")
            
            if page_id not in pages_content:
                pages_content[page_id] = {
                    "title": page_title,
                    "chunks": []
                }
            pages_content[page_id]["chunks"].append(result["text"])
        
        # Step 3: Generate module breakdown using AI
        content_summary = self._create_content_summary(pages_content)
        
        module_breakdown_prompt = f"""You are an expert instructional designer creating an engaging onboarding course.

Course Title: {course_title}
Course Description: {course_description}

Available Content Summary:
{content_summary}

Create a structured course outline with {num_modules} modules. Each module should:
1. Have a clear, engaging title
2. Cover a specific topic or concept
3. Build progressively from basics to advanced
4. Be practical and actionable

Return ONLY a JSON array with this structure:
[
  {{
    "module_number": 1,
    "title": "Module title",
    "description": "What this module covers",
    "topics": ["topic1", "topic2", "topic3"]
  }}
]

Do not include any markdown formatting or explanation, just the JSON array."""

        try:
            response = self.model.generate_content(module_breakdown_prompt)
            # Parse the JSON response
            module_structure = json.loads(response.text.strip())
        except Exception as e:
            print(f"Error generating module structure: {e}")
            # Fallback: create simple modules
            module_structure = [
                {
                    "module_number": i + 1,
                    "title": f"Module {i + 1}",
                    "description": f"Part {i + 1} of {course_title}",
                    "topics": []
                }
                for i in range(num_modules)
            ]
        
        # Step 4: Generate detailed content for each module
        modules = []
        for module_info in module_structure:
            module_content = self._generate_module_content(
                course_id=course_id,
                module_info=module_info,
                pages_content=pages_content
            )
            modules.append(module_content)
        
        # Step 5: Create the complete course structure
        course_data = {
            "course_id": course_id,
            "title": course_title,
            "description": course_description,
            "total_modules": len(modules),
            "modules": modules,
            "source_pages": [
                {"id": page_id, "title": info["title"]}
                for page_id, info in pages_content.items()
            ]
        }
        
        # Save the generated course
        self._save_course(course_id, course_data)
        
        return course_data
    
    def _create_content_summary(self, pages_content: Dict[str, Dict]) -> str:
        """Create a summary of available content for AI context"""
        summary_lines = []
        for page_id, info in pages_content.items():
            total_chars = sum(len(chunk) for chunk in info["chunks"])
            summary_lines.append(f"- {info['title']} ({len(info['chunks'])} sections, ~{total_chars} characters)")
        return "\n".join(summary_lines)
    
    def _generate_module_content(
        self,
        course_id: str,
        module_info: Dict[str, Any],
        pages_content: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Generate detailed content for a single module"""
        # Use vector search to find relevant content for this module
        module_query = f"{module_info['title']} {module_info['description']}"
        search_results = vector_store.search_similar(
            course_id=course_id,
            query_text=module_query,
            top_k=10  # Top 10 most relevant chunks for this module
        )
        
        # Combine relevant chunks
        relevant_content = "\n\n".join([result["text"] for result in search_results])
        
        # Generate engaging module content
        content_prompt = f"""You are creating engaging onboarding content for employees.

Module Title: {module_info['title']}
Module Description: {module_info['description']}
Topics to Cover: {', '.join(module_info.get('topics', []))}

Source Material:
{relevant_content[:4000]}  # Limit to avoid token overflow

Create an engaging, easy-to-understand module that:
1. Starts with a brief overview (2-3 sentences)
2. Explains key concepts clearly
3. Uses practical examples
4. Includes actionable takeaways
5. Is written in a friendly, conversational tone

Return ONLY a JSON object with this structure:
{{
  "overview": "Brief introduction to the module",
  "content": "Main content in markdown format",
  "key_points": ["point 1", "point 2", "point 3"],
  "takeaways": ["takeaway 1", "takeaway 2"]
}}

Do not include any markdown formatting around the JSON, just the JSON object."""

        try:
            response = self.model.generate_content(content_prompt)
            module_content = json.loads(response.text.strip())
        except Exception as e:
            print(f"Error generating module content: {e}")
            # Fallback content
            module_content = {
                "overview": module_info["description"],
                "content": relevant_content[:1000],
                "key_points": module_info.get("topics", []),
                "takeaways": []
            }
        
        return {
            "module_number": module_info["module_number"],
            "title": module_info["title"],
            "description": module_info["description"],
            **module_content
        }
    
    def _save_course(self, course_id: str, course_data: Dict[str, Any]):
        """Save the generated course to a JSON file"""
        courses_dir = os.path.join("onboarding", "courses")
        os.makedirs(courses_dir, exist_ok=True)
        
        course_file = os.path.join(courses_dir, f"{course_id}.json")
        with open(course_file, "w", encoding="utf-8") as f:
            json.dump(course_data, f, indent=2, ensure_ascii=False)
    
    def get_generated_course(self, course_id: str) -> Optional[Dict[str, Any]]:
        """Load a previously generated course"""
        course_file = os.path.join("onboarding", "courses", f"{course_id}.json")
        
        if not os.path.exists(course_file):
            return None
        
        with open(course_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def delete_generated_course(self, course_id: str):
        """Delete a generated course file"""
        course_file = os.path.join("onboarding", "courses", f"{course_id}.json")
        if os.path.exists(course_file):
            os.remove(course_file)


# Singleton instance
gemini_service = GeminiService()
