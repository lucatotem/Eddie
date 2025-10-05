"""
Vector database service using ChromaDB
Handles embeddings and semantic search for course content
Uses Gemini text-embedding-004 for embeddings
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
import google.generativeai as genai
from typing import List, Dict, Optional
import hashlib
import re
from pathlib import Path
from app.config import get_settings

settings = get_settings()


def strip_html(html_content: str) -> str:
    """
    Strip HTML tags and extract clean text from Confluence HTML
    """
    if not html_content:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Decode common HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&amp;', '&')
    text = text.replace('&quot;', '"')
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


class VectorStoreService:
    """
    Manages embeddings and vector search for Confluence page content
    Uses ChromaDB for storage and Gemini text-embedding-004 for embeddings
    """
    
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        Initialize the vector store
        Creates persistent storage so embeddings survive server restarts
        """
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,  # Don't send usage data
                allow_reset=True
            )
        )
        
        # Configure Gemini API
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            print("[VectorStore] Gemini API configured successfully")
        else:
            print("[VectorStore] WARNING: No Gemini API key found in settings")
    
    def get_or_create_collection(self, course_id: str):
        """
        Get or create a collection for a specific course
        Each course gets its own collection for isolation
        """
        collection_name = f"course_{course_id}"
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"course_id": course_id}
        )
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of text chunks using Gemini
        Returns: List of embedding vectors (each is a list of floats)
        """
        if not texts:
            return []
        
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        print(f"[VectorStore] Generating embeddings for {len(texts)} chunks using Gemini...")
        
        embeddings = []
        # Gemini has a batch limit, so we process in batches
        batch_size = 100
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            print(f"[VectorStore] Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            # Generate embeddings for this batch
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=batch,
                task_type="retrieval_document"  # For storing documents
            )
            
            # Extract embeddings from result
            if isinstance(result, dict) and 'embedding' in result:
                # Single text case
                embeddings.append(result['embedding'])
            else:
                # Batch case - result has an 'embeddings' field
                for embedding in result['embedding']:
                    embeddings.append(embedding)
        
        print(f"[VectorStore] Generated {len(embeddings)} embeddings")
        return embeddings
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation
        
        Args:
            text: The text to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
        
        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end of this chunk
            end = start + chunk_size
            
            # If we're not at the end, try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence end (., !, ?)
                sentence_end = max(
                    text.rfind('. ', start, end),
                    text.rfind('! ', start, end),
                    text.rfind('? ', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
                else:
                    # Fall back to word boundary
                    space = text.rfind(' ', start, end)
                    if space > start:
                        end = space
            
            chunks.append(text[start:end].strip())
            start = end - overlap if end < len(text) else end
        
        return chunks
    
    def add_page_content(
        self,
        course_id: str,
        page_id: str,
        page_title: str,
        page_content: str,
        page_url: Optional[str] = None
    ):
        """
        Add a Confluence page's content to the vector store
        
        Args:
            course_id: The course this page belongs to
            page_id: Confluence page ID
            page_title: Page title
            page_content: Full page content (HTML will be stripped)
            page_url: Optional URL to the page
        """
        collection = self.get_or_create_collection(course_id)
        
        # Strip HTML tags from content
        clean_content = strip_html(page_content)
        
        # Chunk the content
        chunks = self.chunk_text(clean_content)
        
        if not chunks:
            print(f"[VectorStore] No content to embed for page {page_id}")
            return
        
        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)
        
        # Create IDs for each chunk
        chunk_ids = [
            f"{page_id}_chunk_{i}_{self._hash_text(chunk)[:8]}"
            for i, chunk in enumerate(chunks)
        ]
        
        # Create metadata for each chunk
        metadatas = [
            {
                "page_id": page_id,
                "page_title": page_title,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "page_url": page_url or ""
            }
            for i in range(len(chunks))
        ]
        
        # Add to ChromaDB
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        print(f"[VectorStore] Added {len(chunks)} chunks for page {page_id} ({page_title})")
    
    def search_similar(
        self,
        course_id: str,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Search for similar content in a course
        
        Args:
            course_id: The course to search in
            query: Search query
            n_results: Number of results to return
        
        Returns:
            List of dicts with 'text', 'metadata', and 'distance' keys
        """
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
            
        collection = self.get_or_create_collection(course_id)
        
        # Generate query embedding using Gemini
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"  # For searching/queries
        )
        
        query_embedding = result['embedding']
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        formatted = []
        for i in range(len(results['ids'][0])):
            formatted.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else None
            })
        
        return formatted
    
    def delete_page_content(self, course_id: str, page_id: str):
        """
        Remove all chunks for a specific page
        Useful when a page is deleted or needs to be re-embedded
        """
        collection = self.get_or_create_collection(course_id)
        
        # Get all chunks for this page
        results = collection.get(
            where={"page_id": page_id}
        )
        
        if results['ids']:
            collection.delete(ids=results['ids'])
            print(f"[VectorStore] Deleted {len(results['ids'])} chunks for page {page_id}")
    
    def delete_course_collection(self, course_id: str):
        """
        Delete entire course collection
        Useful when a course is deleted
        """
        collection_name = f"course_{course_id}"
        try:
            self.client.delete_collection(name=collection_name)
            print(f"[VectorStore] Deleted collection for course {course_id}")
        except Exception as e:
            print(f"[VectorStore] Collection {course_id} doesn't exist or error: {e}")
    
    def get_all_page_ids(self, course_id: str) -> List[str]:
        """
        Get all unique page IDs stored for a course
        Useful for detecting which pages need updates
        """
        collection = self.get_or_create_collection(course_id)
        
        # Get all documents
        results = collection.get()
        
        # Extract unique page IDs
        page_ids = set()
        for metadata in results['metadatas']:
            page_ids.add(metadata['page_id'])
        
        return list(page_ids)
    
    @staticmethod
    def _hash_text(text: str) -> str:
        """Generate a short hash of text for unique IDs"""
        return hashlib.md5(text.encode()).hexdigest()


# Singleton instance
vector_store = VectorStoreService()
