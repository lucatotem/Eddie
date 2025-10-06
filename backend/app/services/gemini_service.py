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
import time
import re

class GeminiService:
    def __init__(self):
        self.settings = get_settings()
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the Gemini 2.5 Flash model"""
        if not self.settings.gemini_api_key:
            print("Warning: GEMINI_API_KEY not set. AI generation will not work.")
            return
        
        try:
            genai.configure(api_key=self.settings.gemini_api_key)
            # Use Gemini 2.5 Flash for better rate limits on free tier
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            print("[Gemini] Model initialized: gemini-2.5-flash")
        except Exception as e:
            print(f"[Gemini] Error initializing model: {e}")
            self.model = None
    
    def _calculate_optimal_module_count(self, total_content_length: int, num_pages: int) -> int:
        """
        Calculate optimal number of modules based on content length
        
        Args:
            total_content_length: Total character count of all content
            num_pages: Number of Confluence pages
            
        Returns:
            Recommended number of modules (between 2 and 12)
        """
        # Base calculation: ~500-1000 chars per module for engagement
        chars_per_module = 750
        content_based = max(2, min(12, total_content_length // chars_per_module))
        
        # Also consider page count (at least 1 module per 2 pages, max 1 per page)
        page_based = max(2, min(num_pages, num_pages // 2 + 1))
        
        # Use the average, weighted toward content length
        optimal = int((content_based * 0.7) + (page_based * 0.3))
        
        # Clamp between 2 and 12 modules
        return max(2, min(12, optimal))
    
    def _calculate_optimal_question_count(self, num_modules: int, total_content_length: int) -> int:
        """
        Calculate optimal number of quiz questions based on module count and content
        
        Args:
            num_modules: Number of modules in the course
            total_content_length: Total character count of all content
            
        Returns:
            Recommended number of questions (between 3 and 20)
        """
        # Base: 1.5-2 questions per module
        module_based = int(num_modules * 1.75)
        
        # Also consider content length: ~1 question per 400 chars
        content_based = max(3, total_content_length // 400)
        
        # Use weighted average
        optimal = int((module_based * 0.6) + (content_based * 0.4))
        
        # Clamp between 3 and 20 questions
        return max(3, min(20, optimal))
    
    def _call_gemini_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Call Gemini API with retry logic and rate limiting
        Returns the response text or None if all retries fail
        """
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Exponential backoff: 2s, 4s, 8s
                    wait_time = 2 ** attempt
                    print(f"[Gemini] Retry {attempt + 1}/{max_retries}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                
                response = self.model.generate_content(prompt)
                
                if not response or not hasattr(response, 'text'):
                    print(f"[Gemini] Empty response on attempt {attempt + 1}")
                    continue
                    
                return response.text
                
            except Exception as e:
                print(f"[Gemini] Error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Any]:
        """
        Extract JSON from Gemini response, handling markdown code blocks
        """
        if not response_text:
            return None
        
        text = response_text.strip()
        
        # Remove markdown code blocks
        if '```' in text:
            # Find JSON between code blocks
            match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"[Gemini] JSON decode error: {e}")
            print(f"[Gemini] Response preview: {text[:200]}...")
            return None
    
    def generate_course_content(
        self, 
        course_id: str, 
        course_title: str,
        course_description: str,
        num_modules: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate an interactive course with multiple modules
        Uses vector search to retrieve relevant content and AI to create engaging summaries
        
        Args:
            course_id: The ID of the course config
            course_title: Title of the course
            course_description: Description/instructions for the course
            num_modules: Number of modules to generate (None = auto-calculate based on content)
        
        Returns:
            Dictionary with course structure and generated content
        """
        if not self.model:
            raise Exception("Gemini API not configured. Please set GEMINI_API_KEY.")
        
        # Step 1: Get all content from vector store for this course
        # We'll use the course description as a query to find relevant content
        search_results = vector_store.search_similar(
            course_id=course_id,
            query=course_description or course_title,
            n_results=50  # Get more chunks to have comprehensive coverage
        )
        
        if not search_results:
            raise Exception(f"No content found for course {course_id}. Has it been processed?")
        
        # Step 2: Organize content by page
        pages_content = {}
        total_content_length = 0
        for result in search_results:
            page_id = result["metadata"].get("page_id")
            page_title = result["metadata"].get("page_title", "Untitled")
            
            if page_id not in pages_content:
                pages_content[page_id] = {
                    "title": page_title,
                    "chunks": []
                }
            pages_content[page_id]["chunks"].append(result["text"])
            total_content_length += len(result["text"])
        
        # Calculate optimal module count if not specified
        if num_modules is None:
            num_modules = self._calculate_optimal_module_count(
                total_content_length=total_content_length,
                num_pages=len(pages_content)
            )
            print(f"[Gemini] Auto-calculated {num_modules} modules based on {total_content_length} chars across {len(pages_content)} pages")
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

        response_text = self._call_gemini_with_retry(module_breakdown_prompt)
        module_structure = None
        
        if response_text:
            module_structure = self._extract_json_from_response(response_text)
        
        if not module_structure:
            print(f"[Gemini] Failed to generate module structure, using intelligent fallback")
            # Intelligent fallback: distribute pages across modules
            pages_list = list(pages_content.items())
            pages_per_module = max(1, len(pages_list) // num_modules)
            
            module_structure = []
            for i in range(num_modules):
                start_idx = i * pages_per_module
                end_idx = start_idx + pages_per_module if i < num_modules - 1 else len(pages_list)
                module_pages = pages_list[start_idx:end_idx]
                
                # Use actual page titles for module titles
                if module_pages:
                    first_page_title = module_pages[0][1]["title"]
                    module_structure.append({
                        "module_number": i + 1,
                        "title": first_page_title,
                        "description": f"Learn about {first_page_title.lower()}",
                        "topics": [page[1]["title"] for page in module_pages]
                    })
        
        # Add delay to respect free tier quota (2 requests per minute)
        print("[Gemini] Waiting 35 seconds to respect API rate limit...")
        time.sleep(35)
        
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
            query=module_query,
            n_results=10  # Top 10 most relevant chunks for this module
        )
        
        # Combine relevant chunks
        relevant_content = "\n\n".join([result["text"] for result in search_results])
        
        # Generate engaging module content
        content_prompt = f"""You are creating onboarding content based on existing documentation.

Module Title: {module_info['title']}
Module Description: {module_info['description']}

SOURCE DOCUMENTATION (use this as your PRIMARY source):
{relevant_content[:5000]}

IMPORTANT: 
- Base your content DIRECTLY on the source documentation above
- Quote and reference specific details from the source
- DO NOT add generic information not found in the source
- Keep the technical accuracy of the original documentation
- Make it readable and well-organized, but stay faithful to the source

Create a well-structured module that:
1. Provides a brief overview based on the source material
2. Presents the key information from the documentation clearly
3. Uses actual examples from the source when available
4. Highlights important takeaways from the documentation

Return ONLY a JSON object with this structure:
{{
  "overview": "Brief introduction based on source material",
  "content": "Main content in markdown format, BASED ON SOURCE DOCUMENTATION",
  "key_points": ["actual point 1 from source", "actual point 2 from source", "actual point 3 from source"],
  "takeaways": ["actual takeaway 1 from source", "actual takeaway 2 from source"]
}}

Do not include any markdown formatting around the JSON, just the JSON object."""

        response_text = self._call_gemini_with_retry(content_prompt)
        module_content = None
        
        if response_text:
            module_content = self._extract_json_from_response(response_text)
        
        if not module_content:
            print(f"[Gemini] Failed to generate module content, using source material")
            # Better fallback: use actual source content intelligently
            # Take complete chunks, not truncated text
            chunks_to_use = []
            total_length = 0
            max_length = 3000
            
            for result in search_results:
                chunk = result.get("text", "")
                if total_length + len(chunk) <= max_length:
                    chunks_to_use.append(chunk)
                    total_length += len(chunk)
                else:
                    break
            
            # Format the content nicely
            formatted_content = "\n\n".join(chunks_to_use)
            
            # Extract key points from topics
            topics = module_info.get("topics", [])
            key_points = topics[:5] if topics else ["Review the documentation for detailed information"]
            
            module_content = {
                "overview": module_info["description"],
                "content": formatted_content if formatted_content else "Please refer to the source documentation for detailed information.",
                "key_points": key_points,
                "takeaways": [
                    f"Understanding {module_info['title']}",
                    "Review the detailed content above",
                    "Apply these concepts in your work"
                ]
            }
        
        # Add delay to respect free tier quota (2 requests per minute)
        print("[Gemini] Waiting 35 seconds to respect API rate limit...")
        time.sleep(35)
        
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
        num_questions: Optional[int] = None,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a quiz based on course content
        
        Args:
            course_id: The ID of the course
            module_number: Specific module to quiz on (None = entire course)
            num_questions: Number of questions to generate (None = auto-calculate)
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
            query=search_query,
            n_results=20
        )
        
        source_content = "\n\n".join([result["text"] for result in search_results[:10]])
        total_content_length = sum(len(r["text"]) for r in search_results)
        
        # Calculate optimal question count if not specified
        if num_questions is None:
            num_modules = len(course_data.get("modules", []))
            num_questions = self._calculate_optimal_question_count(
                num_modules=num_modules,
                total_content_length=total_content_length
            )
            print(f"[Gemini] Auto-calculated {num_questions} questions based on {num_modules} modules and {total_content_length} chars")
        
        # Generate quiz questions
        quiz_prompt = f"""You are creating an assessment quiz for an onboarding course.

Course Title: {course_data['title']}
Quiz Topic: {quiz_title}
Difficulty Level: {difficulty}

Content to Quiz On:
{json.dumps(quiz_content, indent=2)[:3000]}

Additional Source Material:
{source_content[:3000]}

Create {num_questions} comprehensive multiple-choice questions that:
1. Test understanding of the MOST IMPORTANT concepts and key information
2. Are clear, specific, and unambiguous
3. Have 4 answer options each (one correct, three plausible distractors)
4. Include detailed explanations for the correct answer
5. Match the {difficulty} difficulty level
6. Cover different aspects of the content (don't repeat topics)
7. Focus on practical application and real understanding, not just memorization
8. Are directly based on the source material provided

IMPORTANT: 
- Quality over quantity - each question should test critical knowledge
- Avoid trivial or overly specific details
- Questions should help verify the learner truly understands the material
- Make distractors realistic but clearly incorrect to someone who learned the material

Return ONLY a JSON array with this structure:
[
  {{
    "question": "The question text (clear and specific)",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0,
    "explanation": "Detailed explanation of why this is correct and what concept it tests",
    "difficulty": "{difficulty}"
  }}
]

Do not include any markdown formatting or explanation, just the JSON array."""

        response_text = self._call_gemini_with_retry(quiz_prompt)
        questions = None
        
        if response_text:
            questions = self._extract_json_from_response(response_text)
        
        if not questions:
            print(f"[Gemini] Failed to generate quiz, using source-based fallback")
            # Better fallback: create questions from source content
            content_snippets = source_content[:1000].split('. ')[:num_questions]
            
            questions = []
            for i, snippet in enumerate(content_snippets):
                if len(snippet) < 20:  # Skip very short snippets
                    continue
                questions.append({
                    "question": f"According to the course material: {snippet[:100]}?",
                    "options": [
                        "True - this is covered in the material",
                        "False - this is not mentioned",
                        "Partially true",
                        "Not applicable"
                    ],
                    "correct_answer": 0,
                    "explanation": "This information is directly from the course content.",
                    "difficulty": difficulty
                })
            
            # Ensure we have at least one question
            if not questions:
                questions = [{
                    "question": f"What does this course cover about {course_data['title']}?",
                    "options": [
                        "Key concepts and practical knowledge",
                        "Unrelated information",
                        "Random topics",
                        "None of the above"
                    ],
                    "correct_answer": 0,
                    "explanation": "This course provides essential onboarding knowledge.",
                    "difficulty": difficulty
                }]
        
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
