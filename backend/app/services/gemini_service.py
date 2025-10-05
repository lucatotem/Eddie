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
    
    def generate_quiz(
        self,
        course_id: str,
        module_number: Optional[int] = None,
        num_questions: int = 5,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on course content
        
        Args:
            course_id: The ID of the course
            module_number: Specific module to quiz on (None = entire course)
            num_questions: Number of questions to generate (default: 5)
            difficulty: Question difficulty - "easy", "medium", or "hard"
        
        Returns:
            Dictionary with quiz questions and metadata
        """
        if not self.model:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY.")
        
        # Load the generated course
        course_data = self.get_generated_course(course_id)
        if not course_data:
            raise Exception(f"Course {course_id} has not been generated yet.")
        
        # Determine which content to quiz on
        if module_number is not None:
            # Quiz on specific module
            modules = [m for m in course_data["modules"] if m["module_number"] == module_number]
            if not modules:
                raise Exception(f"Module {module_number} not found in course.")
            quiz_content = modules[0]
            quiz_title = f"{course_data['title']} - {quiz_content['title']} Quiz"
        else:
            # Quiz on entire course
            quiz_content = course_data
            quiz_title = f"{course_data['title']} - Final Assessment"
        
        # Get relevant content from vector store for more context
        search_query = quiz_content.get("title", course_data["title"])
        search_results = vector_store.search_similar(
            course_id=course_id,
            query_text=search_query,
            top_k=20
        )
        
        source_content = "\n\n".join([result["text"] for result in search_results[:10]])
        
        # Generate quiz questions
        quiz_prompt = f"""You are creating an assessment quiz for an onboarding course.

Course Title: {course_data['title']}
Quiz Topic: {quiz_title}
Difficulty Level: {difficulty}

Content to Quiz On:
{json.dumps(quiz_content, indent=2)[:3000]}

Additional Source Material:
{source_content[:2000]}

Create {num_questions} multiple-choice questions that:
1. Test understanding of key concepts
2. Are clear and unambiguous
3. Have 4 answer options each
4. Include detailed explanations for the correct answer
5. Match the {difficulty} difficulty level
6. Cover different aspects of the content

Return ONLY a JSON array with this structure:
[
  {{
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Why this is correct and what concept it tests",
    "difficulty": "{difficulty}"
  }}
]

Do not include any markdown formatting or explanation, just the JSON array."""

        try:
            response = self.model.generate_content(quiz_prompt)
            questions = json.loads(response.text.strip())
        except Exception as e:
            print(f"Error generating quiz: {e}")
            # Fallback: simple questions
            questions = [
                {
                    "question": f"What is covered in {course_data['title']}?",
                    "options": [
                        "Important concepts for new employees",
                        "Random information",
                        "Unrelated topics",
                        "None of the above"
                    ],
                    "correct_answer": 0,
                    "explanation": "This course covers essential onboarding information.",
                    "difficulty": difficulty
                }
            ]
        
        quiz_data = {
            "course_id": course_id,
            "quiz_title": quiz_title,
            "module_number": module_number,
            "difficulty": difficulty,
            "total_questions": len(questions),
            "questions": questions
        }
        
        # Save the quiz
        self._save_quiz(course_id, module_number, quiz_data)
        
        return quiz_data
    
    def _save_quiz(self, course_id: str, module_number: Optional[int], quiz_data: Dict[str, Any]):
        """Save generated quiz to a JSON file"""
        quizzes_dir = os.path.join("onboarding", "quizzes")
        os.makedirs(quizzes_dir, exist_ok=True)
        
        if module_number is not None:
            quiz_file = os.path.join(quizzes_dir, f"{course_id}_module_{module_number}.json")
        else:
            quiz_file = os.path.join(quizzes_dir, f"{course_id}_final.json")
        
        with open(quiz_file, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=2, ensure_ascii=False)
    
    def get_quiz(self, course_id: str, module_number: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Load a previously generated quiz"""
        quizzes_dir = os.path.join("onboarding", "quizzes")
        
        if module_number is not None:
            quiz_file = os.path.join(quizzes_dir, f"{course_id}_module_{module_number}.json")
        else:
            quiz_file = os.path.join(quizzes_dir, f"{course_id}_final.json")
        
        if not os.path.exists(quiz_file):
            return None
        
        with open(quiz_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def submit_quiz_answers(
        self,
        course_id: str,
        user_answers: List[int],
        module_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Grade a quiz submission
        
        Args:
            course_id: The course ID
            user_answers: List of answer indices chosen by the user
            module_number: Which module quiz (None = final quiz)
        
        Returns:
            Grading results with score, feedback, and detailed explanations
        """
        quiz_data = self.get_quiz(course_id, module_number)
        if not quiz_data:
            raise Exception("Quiz not found. Generate it first.")
        
        questions = quiz_data["questions"]
        if len(user_answers) != len(questions):
            raise Exception(f"Expected {len(questions)} answers, got {len(user_answers)}")
        
        # Grade each answer
        results = []
        correct_count = 0
        
        for i, (question, user_answer) in enumerate(zip(questions, user_answers)):
            correct = user_answer == question["correct_answer"]
            if correct:
                correct_count += 1
            
            results.append({
                "question_number": i + 1,
                "question": question["question"],
                "user_answer": user_answer,
                "correct_answer": question["correct_answer"],
                "is_correct": correct,
                "explanation": question["explanation"],
                "selected_option": question["options"][user_answer] if 0 <= user_answer < len(question["options"]) else "Invalid",
                "correct_option": question["options"][question["correct_answer"]]
            })
        
        score_percentage = (correct_count / len(questions)) * 100
        
        return {
            "course_id": course_id,
            "module_number": module_number,
            "quiz_title": quiz_data["quiz_title"],
            "total_questions": len(questions),
            "correct_answers": correct_count,
            "score_percentage": round(score_percentage, 1),
            "passed": score_percentage >= 70,  # 70% passing grade
            "results": results
        }


# Singleton instance
gemini_service = GeminiService()
