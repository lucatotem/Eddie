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
            batch_num = i//batch_size + 1
            total_batches = (len(texts)-1)//batch_size + 1
            print(f"[VectorStore] Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")
            
            try:
                # Generate embeddings for this batch
                print(f"[VectorStore] Calling Gemini API...")
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=batch,
                    task_type="retrieval_document"  # For storing documents
                )
                print(f"[VectorStore] ✓ Gemini API returned successfully")
                
                # Extract embeddings from result
                # The API returns a dict with 'embedding' key containing the embeddings
                batch_embeddings = result['embedding']
                
                # Check if it's a single embedding or batch
                if isinstance(batch_embeddings[0], (int, float)):
                    # Single embedding - wrap in list
                    embeddings.append(batch_embeddings)
                    print(f"[VectorStore] Added 1 embedding (single mode)")
                else:
                    # Batch of embeddings - extend directly
                    embeddings.extend(batch_embeddings)
                    print(f"[VectorStore] Added {len(batch_embeddings)} embeddings (batch mode)")
                    
            except Exception as e:
                print(f"[VectorStore] ❌ ERROR in batch {batch_num}: {e}")
                raise
        
        print(f"[VectorStore] ✓ Generated {len(embeddings)} embeddings total")
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
        print(f"[VectorStore] chunk_text called with text length: {len(text) if text else 0}, chunk_size: {chunk_size}")
        
        if not text or len(text) <= chunk_size:
            result = [text] if text else []
            print(f"[VectorStore] Text fits in one chunk, returning {len(result)} chunks")
            return result
        
        chunks = []
        start = 0
        iteration = 0
        
        while start < len(text):
            iteration += 1
            print(f"[VectorStore] Chunk iteration {iteration}: start={start}, text_len={len(text)}")
            
            if iteration > 100:
                print(f"[VectorStore] ERROR: Too many iterations! Breaking to prevent infinite loop")
                break
            
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
            else:
                # We're at or past the end of the text
                end = len(text)
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
                print(f"[VectorStore] Added chunk {len(chunks)}: length={len(chunk)}")
            
            # Move start position for next chunk
            if end >= len(text):
                print(f"[VectorStore] Reached end of text (end={end}, text_len={len(text)}), breaking")
                break  # We've reached the end
            else:
                new_start = end - overlap
                # Ensure we always move forward by a significant amount
                # to avoid creating tiny overlapping chunks
                min_progress = chunk_size // 4  # Move at least 25% of chunk size
                if new_start <= start + min_progress:
                    new_start = start + min_progress
                start = new_start
                print(f"[VectorStore] Moving to next chunk: new start={start}")
        
        print(f"[VectorStore] chunk_text complete: created {len(chunks)} chunks")
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
        print(f"[VectorStore] Adding page {page_id} to course {course_id}")
        collection = self.get_or_create_collection(course_id)
        
        # Strip HTML tags from content
        print(f"[VectorStore] Stripping HTML from {len(page_content)} chars...")
        clean_content = strip_html(page_content)
        print(f"[VectorStore] Clean content: {len(clean_content)} chars")
        
        # Chunk the content
        print(f"[VectorStore] Chunking text...")
        chunks = self.chunk_text(clean_content)
        print(f"[VectorStore] Created {len(chunks)} chunks")
        
        if not chunks:
            print(f"[VectorStore] No content to embed for page {page_id}")
            return
        
        # Generate embeddings
        print(f"[VectorStore] Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.generate_embeddings(chunks)
        print(f"[VectorStore] ✓ Embeddings generated")
        
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
        try:
            print(f"[VectorStore] Adding to ChromaDB collection...")
            collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas
            )
            print(f"[VectorStore] ✓ Successfully added to ChromaDB")
        except Exception as e:
            print(f"[VectorStore] ✗ ChromaDB add failed: {e}")
            import traceback
            print(f"[VectorStore] Traceback: {traceback.format_exc()}")
            raise
        
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
