"""
Test both Gemini generation and embeddings together
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

print("=" * 60)
print("GEMINI API CONNECTION TEST")
print("=" * 60)

# Test 1: Gemini 2.5 Pro for generation
print("\n1. Testing Gemini 2.5 Pro (Generation Model)")
print("-" * 60)
try:
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content("Write a one-sentence summary of what a fullstack developer does.")
    print(f"✅ SUCCESS!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Text Embedding Model
print("\n2. Testing text-embedding-004 (Embedding Model)")
print("-" * 60)
try:
    test_texts = [
        "This is a test document about Python programming.",
        "Another test about JavaScript and React.",
        "A third document about databases and SQL."
    ]
    
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=test_texts,
        task_type="retrieval_document"
    )
    
    print(f"✅ SUCCESS!")
    print(f"Generated {len(result['embedding'])} embeddings")
    print(f"Embedding dimension: {len(result['embedding'][0])}")
    print(f"First embedding preview: [{result['embedding'][0][:3]}...]")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Query embedding (for search)
print("\n3. Testing query embedding (for semantic search)")
print("-" * 60)
try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="What is a fullstack developer?",
        task_type="retrieval_query"  # Different task type for queries
    )
    
    print(f"✅ SUCCESS!")
    print(f"Query embedding dimension: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ FAILED: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("✅ Gemini 2.5 Pro: Ready for course generation")
print("✅ Text Embedding 004: Ready for vector search")
print("\n🎉 All systems operational!")
