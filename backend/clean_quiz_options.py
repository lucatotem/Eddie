"""
Script to clean quiz option prefixes (A), B), C), D)) from quiz JSON files
The frontend already displays these prefixes, so they shouldn't be in the text
"""

import json
import os
import re
from pathlib import Path

def clean_option_text(option_text):
    """
    Remove A), B), C), D) prefixes from option text
    Examples:
        "A) React 18" -> "React 18"
        "B) Vue.js" -> "Vue.js"
        "C) Angular" -> "Angular"
    """
    # Match patterns like "A) ", "B) ", etc. at the start of the string
    pattern = r'^[A-D]\)\s*'
    cleaned = re.sub(pattern, '', option_text.strip())
    return cleaned

def clean_quiz_file(file_path):
    """
    Clean a single quiz JSON file by removing option prefixes
    """
    print(f"\n📝 Processing: {file_path.name}")
    
    try:
        # Read the quiz file
        with open(file_path, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
        
        if 'questions' not in quiz_data:
            print(f"   ⚠️  No questions found, skipping")
            return False
        
        cleaned_count = 0
        
        # Clean each question's options
        for i, question in enumerate(quiz_data['questions'], 1):
            if 'options' not in question:
                continue
            
            original_options = question['options'].copy()
            cleaned_options = [clean_option_text(opt) for opt in question['options']]
            
            # Check if anything changed
            if original_options != cleaned_options:
                question['options'] = cleaned_options
                cleaned_count += 1
                print(f"   ✓ Question {i}: Cleaned {len(cleaned_options)} options")
        
        if cleaned_count > 0:
            # Save the cleaned quiz
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(quiz_data, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Cleaned {cleaned_count} questions, saved!")
            return True
        else:
            print(f"   ℹ️  No changes needed")
            return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def clean_all_quizzes(quizzes_dir="onboarding/quizzes"):
    """
    Clean all quiz files in the quizzes directory
    """
    quizzes_path = Path(quizzes_dir)
    
    if not quizzes_path.exists():
        print(f"❌ Quizzes directory not found: {quizzes_dir}")
        return
    
    # Find all JSON files
    quiz_files = list(quizzes_path.glob("*.json"))
    
    if not quiz_files:
        print(f"ℹ️  No quiz files found in {quizzes_dir}")
        return
    
    print(f"🔍 Found {len(quiz_files)} quiz file(s)")
    print("=" * 60)
    
    cleaned_files = 0
    
    for quiz_file in quiz_files:
        if clean_quiz_file(quiz_file):
            cleaned_files += 1
    
    print("\n" + "=" * 60)
    print(f"✨ Done! Cleaned {cleaned_files} out of {len(quiz_files)} files")

if __name__ == "__main__":
    print("🧹 Quiz Options Cleaner")
    print("=" * 60)
    print("This script removes A), B), C), D) prefixes from quiz options")
    print("The frontend already displays these, so they're redundant")
    print()
    
    clean_all_quizzes()
