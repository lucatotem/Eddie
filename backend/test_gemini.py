"""
Test script to verify Gemini API connection
Run this to check if your API key works
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {api_key[:20]}..." if api_key else "❌ No API key found!")

if not api_key:
    print("\nERROR: GEMINI_API_KEY not found in .env file")
    exit(1)

# Configure Gemini
print("\n1. Configuring Gemini API...")
genai.configure(api_key=api_key)

# List available models
print("\n2. Listing available models...")
try:
    models = genai.list_models()
    print("✅ Available models:")
    for m in models:
        if 'generateContent' in m.supported_generation_methods:
            print(f"   - {m.name}")
except Exception as e:
    print(f"❌ Error listing models: {e}")
    exit(1)

# Test with gemini-2.0-flash-exp (experimental)
print("\n3. Testing model: gemini-2.0-flash-exp")
try:
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Say 'Hello, Eddie!' if you can hear me.")
    print(f"✅ Response: {response.text}")
except Exception as e:
    print(f"❌ Error with gemini-2.0-flash-exp: {e}")

# Test with gemini-1.5-flash
print("\n4. Testing model: gemini-1.5-flash")
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say 'Hello, Eddie!' if you can hear me.")
    print(f"✅ Response: {response.text}")
except Exception as e:
    print(f"❌ Error with gemini-1.5-flash: {e}")

# Test embeddings
print("\n5. Testing embeddings: models/text-embedding-004")
try:
    result = genai.embed_content(
        model="models/text-embedding-004",
        content="This is a test embedding",
        task_type="retrieval_document"
    )
    print(f"✅ Embedding dimension: {len(result['embedding'])}")
except Exception as e:
    print(f"❌ Error with embeddings: {e}")

print("\n✅ All tests complete!")
